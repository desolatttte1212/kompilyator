from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

from ..parser.ast_nodes import (
    ASTNode, ProgramNode, FunctionDeclNode, StructDeclNode, ParamNode,
    VarDeclStmtNode, BlockStmtNode, ExprStmtNode, IfStmtNode, WhileStmtNode,
    ForStmtNode, ReturnStmtNode, LiteralExprNode, IdentifierExprNode,
    BinaryExprNode, UnaryExprNode, CallExprNode, AssignmentExprNode,
    IndexExprNode, StatementNode, ExpressionNode, DeclarationNode, ASTVisitor
)

from .operand import OperandFactory, Temporary, Variable, Literal, Label, MemoryLocation, Operand
from .instructions import InstructionFactory, InstructionType, is_terminator
from .basic_block import BasicBlock, BlockType, IRFunction, IRProgram
from ..semantic.type_system import ArrayType, PointerType, Types


@dataclass
class GenerationContext:
    current_function: Optional[IRFunction] = None
    current_block: Optional[BasicBlock] = None
    break_target: Optional[Label] = None
    continue_target: Optional[Label] = None
    temp_counter: int = 0
    label_counter: int = 0

    def new_temp(self) -> Temporary:
        temp = Temporary(self.temp_counter)
        self.temp_counter += 1
        return temp

    def new_label(self, prefix: str = "L") -> Label:
        label = Label(f"{prefix}{self.label_counter}")
        self.label_counter += 1
        return label

    def reset(self):
        self.temp_counter = 0
        self.label_counter = 0


class IRGenerator(ASTVisitor):

    def __init__(self, symbol_table=None, type_system=None):
        self.symbol_table = symbol_table
        self.type_system = type_system
        self.program = IRProgram()
        self.context = GenerationContext()
        self.function_map: Dict[str, IRFunction] = {}

    def generate(self, ast: ProgramNode) -> IRProgram:
        ast.accept(self)
        return self.program

    def get_function_ir(self, name: str) -> Optional[IRFunction]:
        return self.program.get_function(name)

    def get_all_ir(self) -> IRProgram:
        return self.program

    def _emit(self, instruction):
        if self.context.current_block:
            self.context.current_block.add_instruction(instruction)

    def _set_block(self, block: BasicBlock):
        self.context.current_block = block

    def _create_block(self, label: str = None, block_type: BlockType = BlockType.NORMAL) -> BasicBlock:
        if self.context.current_function:
            return self.context.current_function.create_block(label, block_type)
        raise RuntimeError("No current function")

    def visit_program(self, node: ProgramNode) -> Any:
        for decl in node.declarations:
            decl.accept(self)
        return self.program

    def visit_function_decl(self, node: FunctionDeclNode) -> Any:
        params = [(p.name, p.param_type) for p in node.parameters]
        func = IRFunction(name=node.name, return_type=node.return_type, parameters=params)

        self.program.add_function(func)
        self.function_map[node.name] = func

        # 🆕 Если это extern функция (нет тела), мы НЕ генерируем для неё IR-код
        # Мы просто регистрируем её имя, чтобы x86_generator знал, что нужно сделать 'extern Name'
        if node.is_extern or node.body is None:
            return func

        old_function = self.context.current_function
        old_block = self.context.current_block
        self.context.current_function = func
        self.context.reset()

        entry_block = func.entry_block
        self._set_block(entry_block)

        for i, param in enumerate(node.parameters):
            temp = func.create_temporary()
            self._emit(InstructionFactory.alloca(temp, 4, f"param {param.name}"))
            param_temp = func.create_temporary()
            self._emit(InstructionFactory.param(i, param_temp, f"load param {i}"))
            self._emit(InstructionFactory.store(temp, param_temp))
            func.map_variable(param.name, temp)

        node.body.accept(self)

        if node.return_type == 'void':
            if self.context.current_block and not self.context.current_block.has_terminator():
                self._emit(InstructionFactory.return_stmt())
        elif not self.context.current_block or not self.context.current_block.has_terminator():
            self._emit(InstructionFactory.return_stmt(comment="implicit return"))

        self.context.current_function = old_function
        self.context.current_block = old_block
        func.link_blocks()

        return func
    def visit_struct_decl(self, node: StructDeclNode) -> Any:
        return None

    def visit_block_stmt(self, node: BlockStmtNode) -> Any:
        for stmt in node.statements:
            stmt.accept(self)
        return None

    def visit_var_decl_stmt(self, node: VarDeclStmtNode) -> Any:
        func = self.context.current_function
        if not func: return None

        sym = self.symbol_table.lookup(node.name)
        var_type = sym.type_ if sym else Types.VOID

        is_array = isinstance(var_type, ArrayType)
        if not is_array and isinstance(node.var_type, str) and '[' in node.var_type:
            is_array = True

        if is_array:
            # === ЛОГИКА ДЛЯ МАССИВОВ ===

            # 1. Создаем Variable operand для имени массива.
            # Это позволит нам хранить сам УКАЗАТЕЛЬ в стеке как обычную переменную.
            arr_ptr_var = Variable(node.name)
            func.map_variable(node.name, arr_ptr_var)

            # 2. Выделяем место под указатель (8 байт)
            # Мы эмитим Alloca, чтобы StackFrame выделил место, но результат Alloca игнорируем,
            # так как мы будем работать через Variable.
            dummy_temp = func.create_temporary()
            self._emit(InstructionFactory.alloca(dummy_temp, 8, f"alloca ptr slot for {node.name}"))

            # 3. Вызываем malloc
            size_bytes = var_type.total_size if isinstance(var_type, ArrayType) else 20
            size_arg = Literal(size_bytes)
            malloc_result = func.create_temporary()
            self._emit(InstructionFactory.call(malloc_result, "malloc", [size_arg], f"malloc({size_bytes})"))

            # 4. СОХРАНЯЕМ УКАЗАТЕЛЬ В ПЕРЕМЕННУЮ
            # Используем StoreInstr с dest=Variable.
            # __post_init__ обернет его в MemoryLocation(Variable(...)).
            # В ASM это превратится в: mov [rbp-offset], eax (прямая запись в стек)
            self._emit(InstructionFactory.store(arr_ptr_var, malloc_result, f"store array ptr -> {node.name}"))

            if node.initializer and isinstance(node.initializer, list):
                for i, init_expr in enumerate(node.initializer):
                    # Адресная арифметика для arr[i]

                    # Загружаем указатель из переменной
                    base_ptr = func.create_temporary()
                    self._emit(InstructionFactory.load(base_ptr, arr_ptr_var, f"load ptr {node.name}"))

                    index_val = Literal(i)
                    element_size = Literal(4)
                    offset = func.create_temporary()
                    self._emit(InstructionFactory.mul(offset, index_val, element_size, f"offset = {i} * 4"))

                    elem_addr = func.create_temporary()
                    self._emit(InstructionFactory.add(elem_addr, base_ptr, offset, f"addr = base + offset"))

                    init_value = init_expr.accept(self)
                    # Сохраняем значение по вычисленному адресу
                    # elem_addr - это Temporary, содержащий адрес.
                    # StoreInstr обернет его в MemoryLocation(Temp...).
                    # В ASM: mov r8, [rbp-offset_of_elem_addr]; mov [r8], value
                    self._emit(InstructionFactory.store(elem_addr, init_value, f"init {node.name}[{i}]"))
            elif node.initializer:
                node.initializer.accept(self)

        else:
            # === ЛОГИКА ДЛЯ СКАЛЯРОВ (Оставаем как было, оно работает) ===
            var_operand = Variable(node.name)
            func.map_variable(node.name, var_operand)

            if node.initializer:
                init_value = node.initializer.accept(self)
                if init_value:
                    self._emit(InstructionFactory.store(var_operand, init_value, f"init {node.name}"))

        return None
    def visit_expr_stmt(self, node: ExprStmtNode) -> Any:
        node.expression.accept(self)
        return None

    def visit_if_stmt(self, node: IfStmtNode) -> Any:
        func = self.context.current_function
        if not func: return None

        then_label = self.context.new_label("L_then")
        else_label = self.context.new_label("L_else")
        join_label = self.context.new_label("L_join")

        cond_value = node.condition.accept(self)
        self._emit(InstructionFactory.jump_if(cond_value, then_label, "if condition"))

        else_block = self._create_block(else_label, BlockType.NORMAL)
        self._set_block(else_block)
        if node.else_branch: node.else_branch.accept(self)
        if not else_block.has_terminator(): self._emit(InstructionFactory.jump(join_label))

        then_block = self._create_block(then_label, BlockType.NORMAL)
        self._set_block(then_block)
        node.then_branch.accept(self)
        if not then_block.has_terminator(): self._emit(InstructionFactory.jump(join_label))

        join_block = self._create_block(join_label, BlockType.JOIN)
        self._set_block(join_block)
        return join_label

    def visit_while_stmt(self, node: WhileStmtNode) -> Any:
        func = self.context.current_function
        if not func: return None

        header_label = self.context.new_label("L_while_header")
        body_label = self.context.new_label("L_while_body")
        exit_label = self.context.new_label("L_while_exit")

        self._emit(InstructionFactory.jump(header_label))
        header_block = self._create_block(header_label, BlockType.LOOP_HEADER)
        self._set_block(header_block)

        cond_value = node.condition.accept(self)
        self._emit(InstructionFactory.jump_if(cond_value, body_label, "while condition"))

        exit_block = self._create_block(exit_label, BlockType.NORMAL)
        self._set_block(exit_block)

        body_block = self._create_block(body_label, BlockType.LOOP_BODY)
        self._set_block(body_block)

        old_break = self.context.break_target
        old_continue = self.context.continue_target
        self.context.break_target = exit_label
        self.context.continue_target = header_label

        node.body.accept(self)

        self.context.break_target = old_break
        self.context.continue_target = old_continue

        if not body_block.has_terminator():
            self._emit(InstructionFactory.jump(header_label))

        self._set_block(exit_block)
        return exit_label

    def visit_for_stmt(self, node: ForStmtNode) -> Any:
        func = self.context.current_function
        if not func: return None

        cond_label = self.context.new_label("L_for_cond")
        body_label = self.context.new_label("L_for_body")
        update_label = self.context.new_label("L_for_update")
        exit_label = self.context.new_label("L_for_exit")

        if node.init: node.init.accept(self)
        self._emit(InstructionFactory.jump(cond_label))

        cond_block = self._create_block(cond_label, BlockType.LOOP_HEADER)
        self._set_block(cond_block)

        if node.condition:
            cond_value = node.condition.accept(self)
            self._emit(InstructionFactory.jump_if(cond_value, body_label, "for condition"))
        else:
            self._emit(InstructionFactory.jump(body_label))
        self._emit(InstructionFactory.jump(exit_label))

        body_block = self._create_block(body_label, BlockType.LOOP_BODY)
        self._set_block(body_block)

        old_break = self.context.break_target
        old_continue = self.context.continue_target
        self.context.break_target = exit_label
        self.context.continue_target = update_label

        node.body.accept(self)

        self.context.break_target = old_break
        self.context.continue_target = old_continue

        if not body_block.has_terminator():
            self._emit(InstructionFactory.jump(update_label))

        update_block = self._create_block(update_label, BlockType.NORMAL)
        self._set_block(update_block)
        if node.update: node.update.accept(self)
        self._emit(InstructionFactory.jump(cond_label))

        exit_block = self._create_block(exit_label, BlockType.NORMAL)
        self._set_block(exit_block)
        return exit_label

    def visit_return_stmt(self, node: ReturnStmtNode) -> Any:
        if node.value:
            return_value = node.value.accept(self)
            self._emit(InstructionFactory.return_stmt(return_value, "return value"))
        else:
            self._emit(InstructionFactory.return_stmt(comment="return void"))
        return None

    def visit_literal_expr(self, node: LiteralExprNode) -> Operand:
        return OperandFactory.literal(node.value)

    def visit_identifier_expr(self, node: IdentifierExprNode) -> Operand:
        func = self.context.current_function
        if not func: return OperandFactory.literal(0)

        var_operand = func.get_variable_operand(node.name)
        if var_operand:
            temp = func.create_temporary()
            self._emit(InstructionFactory.load(temp, var_operand, f"load {node.name}"))
            return temp
        return OperandFactory.variable(node.name)

    def visit_index_expr(self, node: IndexExprNode) -> Operand:
        func = self.context.current_function
        if not func: return Literal(0)

        node.array.accept(self)
        array_name = node.array.name if isinstance(node.array, IdentifierExprNode) else "unknown"
        base_ptr_temp = func.get_variable_operand(array_name)

        base_ptr = func.create_temporary()
        self._emit(InstructionFactory.load(base_ptr, base_ptr_temp, f"load ptr {array_name}"))

        index_val = node.index.accept(self)
        element_size = Literal(4)
        offset = func.create_temporary()
        self._emit(InstructionFactory.mul(offset, index_val, element_size, f"offset = idx * 4"))

        elem_addr = func.create_temporary()
        self._emit(InstructionFactory.add(elem_addr, base_ptr, offset, f"addr = base + offset"))

        result = func.create_temporary()
        idx_comment = node.index.value if hasattr(node.index, 'value') else node.index
        self._emit(InstructionFactory.load(result, elem_addr, f"load arr[{idx_comment}]"))
        return result

    def visit_binary_expr(self, node: BinaryExprNode) -> Operand:
        func = self.context.current_function
        if not func: return OperandFactory.literal(0)

        op = node.operator

        if op == '&&':
            left = node.left.accept(self)
            false_label = self.context.new_label("L_and_false")
            right_label = self.context.new_label("L_and_right")
            end_label = self.context.new_label("L_and_end")

            self._emit(InstructionFactory.jump_if_not(left, false_label, "short-circuit && left false"))

            right_block = self._create_block(right_label, BlockType.NORMAL)
            self._set_block(right_block)
            right = node.right.accept(self)
            result = func.create_temporary()
            self._emit(InstructionFactory.move(result, right, "&& result = right"))
            self._emit(InstructionFactory.jump(end_label))

            false_block = self._create_block(false_label, BlockType.NORMAL)
            self._set_block(false_block)
            self._emit(InstructionFactory.move(result, OperandFactory.literal(0), "&& result = 0"))
            self._emit(InstructionFactory.jump(end_label))

            end_block = self._create_block(end_label, BlockType.JOIN)
            self._set_block(end_block)
            return result

        elif op == '||':
            left = node.left.accept(self)
            true_label = self.context.new_label("L_or_true")
            right_label = self.context.new_label("L_or_right")
            end_label = self.context.new_label("L_or_end")

            self._emit(InstructionFactory.jump_if(left, true_label, "short-circuit || left true"))

            right_block = self._create_block(right_label, BlockType.NORMAL)
            self._set_block(right_block)
            right = node.right.accept(self)
            result = func.create_temporary()
            self._emit(InstructionFactory.move(result, right, "|| result = right"))
            self._emit(InstructionFactory.jump(end_label))

            true_block = self._create_block(true_label, BlockType.NORMAL)
            self._set_block(true_block)
            self._emit(InstructionFactory.move(result, OperandFactory.literal(1), "|| result = 1"))
            self._emit(InstructionFactory.jump(end_label))

            end_block = self._create_block(end_label, BlockType.JOIN)
            self._set_block(end_block)
            return result

        left = node.left.accept(self)
        right = node.right.accept(self)
        result = func.create_temporary()

        if op == '+':
            self._emit(InstructionFactory.add(result, left, right, f"{left} + {right}"))
        elif op == '-':
            self._emit(InstructionFactory.sub(result, left, right, f"{left} - {right}"))
        elif op == '*':
            self._emit(InstructionFactory.mul(result, left, right, f"{left} * {right}"))
        elif op == '/':
            self._emit(InstructionFactory.div(result, left, right, f"{left} / {right}"))
        elif op == '%':
            self._emit(InstructionFactory.mod(result, left, right, f"{left} % {right}"))
        elif op == '==':
            self._emit(InstructionFactory.cmp_eq(result, left, right, f"{left} == {right}"))
        elif op == '!=':
            self._emit(InstructionFactory.cmp_ne(result, left, right, f"{left} != {right}"))
        elif op == '<':
            self._emit(InstructionFactory.cmp_lt(result, left, right, f"{left} < {right}"))
        elif op == '<=':
            self._emit(InstructionFactory.cmp_le(result, left, right, f"{left} <= {right}"))
        elif op == '>':
            self._emit(InstructionFactory.cmp_gt(result, left, right, f"{left} > {right}"))
        elif op == '>=':
            self._emit(InstructionFactory.cmp_ge(result, left, right, f"{left} >= {right}"))
        elif op == '&':
            self._emit(InstructionFactory.and_op(result, left, right, f"{left} & {right}"))
        elif op == '|':
            self._emit(InstructionFactory.or_op(result, left, right, f"{left} | {right}"))

        return result

    def visit_unary_expr(self, node: UnaryExprNode) -> Operand:
        func = self.context.current_function
        if not func: return OperandFactory.literal(0)
        operand = node.operand.accept(self)
        result = func.create_temporary()
        if node.operator == '-':
            self._emit(InstructionFactory.neg(result, operand, f"-{operand}"))
        elif node.operator == '!':
            self._emit(InstructionFactory.not_op(result, operand, f"!{operand}"))
        return result

    def visit_call_expr(self, node: CallExprNode) -> Operand:
        func = self.context.current_function
        if not func: return OperandFactory.literal(0)
        arg_values = [arg.accept(self) for arg in node.arguments]
        result = func.create_temporary()
        self._emit(InstructionFactory.call(result, node.callee.name, arg_values, f"call {node.callee.name}"))
        return result

    def visit_assignment_expr(self, node: AssignmentExprNode) -> Operand:
        func = self.context.current_function
        if not func: return OperandFactory.literal(0)

        value = node.value.accept(self)

        if isinstance(node.target, IndexExprNode):
            array_name = node.target.array.name
            base_ptr_temp = func.get_variable_operand(array_name)
            base_ptr = func.create_temporary()
            self._emit(InstructionFactory.load(base_ptr, base_ptr_temp, f"load ptr {array_name}"))

            index_val = node.target.index.accept(self)
            element_size = Literal(4)
            offset = func.create_temporary()
            self._emit(InstructionFactory.mul(offset, index_val, element_size, f"offset = idx * 4"))

            elem_addr = func.create_temporary()
            self._emit(InstructionFactory.add(elem_addr, base_ptr, offset, f"addr = base + offset"))
            idx_comment = node.target.index.value if hasattr(node.target.index, 'value') else node.target.index
            self._emit(InstructionFactory.store(elem_addr, value, f"store arr[{idx_comment}]"))
            return value

        elif isinstance(node.target, IdentifierExprNode):
            var_operand = func.get_variable_operand(node.target.name)
            if var_operand:
                self._emit(InstructionFactory.store(var_operand, value, f"store {node.target.name}"))
            return value
        return value

    def visit_param(self, node: ParamNode) -> Any:
        return None