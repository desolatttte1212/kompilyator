from typing import List, Optional, Dict, Any, Union
from ..parser.ast_nodes import (
    ASTNode, ProgramNode, FunctionDeclNode, StructDeclNode, ParamNode,
    VarDeclStmtNode, BlockStmtNode, ExprStmtNode, IfStmtNode, WhileStmtNode,
    ForStmtNode, ReturnStmtNode, LiteralExprNode, IdentifierExprNode,
    BinaryExprNode, UnaryExprNode, CallExprNode, AssignmentExprNode,
    IndexExprNode, StatementNode, ExpressionNode, DeclarationNode, ASTVisitor
)
from .type_system import (
    Type, PrimitiveType, StructType, PointerType, ArrayType, FunctionType, Parameter, Types,
    get_common_type, is_numeric_type, is_boolean_type, is_void_type
)
from .symbol_table import SymbolTable, Symbol, SymbolKind, ScopeGuard
from .errors import (
    SemanticError, ErrorCollector, SemanticErrorType,
    format_type_name, suggest_similar_names
)


class SemanticAnalyzer(ASTVisitor):

    def __init__(self, filename: str = ""):
        self.filename = filename
        self.symbol_table = SymbolTable()
        self.errors = ErrorCollector(max_errors=100)
        self.current_function = None
        self.current_function_return_type = None
        self.in_loop = False
        self._pass_number = 1

    def analyze(self, ast: ProgramNode) -> ProgramNode:
        # Pass 1: Только сбор сигнатур функций и структур
        self._pass_number = 1
        ast.accept(self)

        # Pass 2: Полная проверка тел функций, типов и выражений
        self._pass_number = 2
        ast.accept(self)

        return ast

    def get_errors(self) -> List[SemanticError]:
        return self.errors.errors

    def get_symbol_table(self) -> SymbolTable:
        return self.symbol_table

    def has_errors(self) -> bool:
        return self.errors.has_errors()

    def print_report(self) -> None:
        self.errors.print_report(self.filename)

    def _parse_type_str(self, type_str: str) -> Type:
        if '[' in type_str:
            parts = type_str.split('[')
            base_name = parts[0]
            size_str = parts[1].rstrip(']')
            base_type = Types.from_name(base_name)
            if base_type:
                try:
                    return ArrayType(base_type, int(size_str))
                except ValueError:
                    pass
            return base_type or Types.VOID
        return Types.from_name(type_str) or Types.VOID

    def visit_program(self, node: ProgramNode) -> Any:
        for decl in node.declarations: decl.accept(self)
        return node

    def visit_function_decl(self, node: FunctionDeclNode) -> Any:
        return_type = Types.from_name(node.return_type) or Types.VOID
        parameters = [Parameter(name=p.name, type_=Types.from_name(p.param_type) or Types.INT,
                                line=p.line, column=p.column) for p in node.parameters]

        # Pass 1: Регистрируем только сигнатуру функции
        if self._pass_number == 1:
            self.symbol_table.insert_function(
                name=node.name, return_type=return_type, parameters=parameters,
                line=node.line, column=node.column, is_defined=True
            )
            return node

        # Pass 2: Регистрируем параметры и обрабатываем тело
        with ScopeGuard(self.symbol_table, f"function:{node.name}"):
            for param in node.parameters:
                p_type = Types.from_name(param.param_type) or Types.INT
                if not self.symbol_table.insert_parameter(param.name, p_type, param.line, param.column):
                    self.errors.add_error(SemanticError.duplicate(name=param.name, line=param.line,
                                                                  column=param.column, file=self.filename,
                                                                  context=f"function {node.name}"))

            old_ret = self.current_function_return_type
            self.current_function_return_type = return_type
            if node.body: node.body.accept(self)
            self.current_function_return_type = old_ret

        return node

    def visit_struct_decl(self, node: StructDeclNode) -> Any:
        if self._pass_number == 1:
            if not self.symbol_table.insert_struct(node.name, node.line, node.column):
                self.errors.add_error(SemanticError.duplicate(name=node.name, line=node.line,
                                                              column=node.column, file=self.filename,
                                                              context='global scope'))
                return node
            for field in node.fields:
                self.symbol_table.add_struct_field(node.name, field.name,
                                                   Types.from_name(field.var_type) or Types.INT,
                                                   field.line, field.column)
        return node

    def visit_block_stmt(self, node: BlockStmtNode) -> Any:
        # Создаём область видимости и последовательно обрабатываем все инструкции
        with ScopeGuard(self.symbol_table, "block"):
            for stmt in node.statements:
                stmt.accept(self)
        return node

    def visit_var_decl_stmt(self, node: VarDeclStmtNode) -> Any:
        var_type = self._parse_type_str(node.var_type)

        # Регистрируем переменную в текущей области видимости
        if not self.symbol_table.insert_variable(node.name, var_type, node.line, node.column):
            self.errors.add_error(SemanticError.duplicate(name=node.name, line=node.line,
                                                          column=node.column, file=self.filename,
                                                          context=self.symbol_table.current_scope.name))

        # Проверяем инициализатор
        if node.initializer:
            node.initializer.accept(self)
            init_type = getattr(node.initializer, 'inferred_type', None)
            if not isinstance(var_type, ArrayType) and init_type and isinstance(init_type, Type) and not init_type.is_compatible_with(var_type):
                self.errors.add_error(SemanticError.type_mismatch(
                    expected=str(var_type), actual=str(init_type),
                    line=node.initializer.line, column=node.initializer.column,
                    file=self.filename, context='variable initialization'
                ))
        return node

    def visit_expr_stmt(self, node: ExprStmtNode) -> Any:
        node.expression.accept(self)
        return node

    def visit_if_stmt(self, node: IfStmtNode) -> Any:
        node.condition.accept(self)
        cond_type = getattr(node.condition, 'inferred_type', None)
        if cond_type and not is_boolean_type(cond_type):
            self.errors.add_error(SemanticError.invalid_condition(actual=str(cond_type),
                                                                  line=node.condition.line,
                                                                  column=node.condition.column, file=self.filename,
                                                                  context='if statement'))

        with ScopeGuard(self.symbol_table, "if_block"):
            node.then_branch.accept(self)
        if node.else_branch:
            with ScopeGuard(self.symbol_table, "else_block"):
                node.else_branch.accept(self)
        return node

    def visit_while_stmt(self, node: WhileStmtNode) -> Any:
        node.condition.accept(self)
        cond_type = getattr(node.condition, 'inferred_type', None)
        if cond_type and not is_boolean_type(cond_type):
            self.errors.add_error(SemanticError.invalid_condition(actual=str(cond_type),
                                                                  line=node.condition.line,
                                                                  column=node.condition.column, file=self.filename,
                                                                  context='while loop'))

        old_in_loop = self.in_loop
        self.in_loop = True
        with ScopeGuard(self.symbol_table, "while_body"):
            node.body.accept(self)
        self.in_loop = old_in_loop
        return node

    def visit_for_stmt(self, node: ForStmtNode) -> Any:
        with ScopeGuard(self.symbol_table, "for_scope"):
            if node.init: node.init.accept(self)
            if node.condition:
                node.condition.accept(self)
                cond_type = getattr(node.condition, 'inferred_type', None)
                if cond_type and not is_boolean_type(cond_type):
                    self.errors.add_error(SemanticError.invalid_condition(actual=str(cond_type),
                                                                          line=node.condition.line,
                                                                          column=node.condition.column,
                                                                          file=self.filename, context='for loop'))
            if node.update: node.update.accept(self)

            old_in_loop = self.in_loop
            self.in_loop = True
            node.body.accept(self)
            self.in_loop = old_in_loop
        return node

    def visit_return_stmt(self, node: ReturnStmtNode) -> Any:
        if node.value:
            node.value.accept(self)
            return_type = getattr(node.value, 'inferred_type', None)
            if self.current_function_return_type and return_type and isinstance(return_type, Type) and \
                    not return_type.is_compatible_with(self.current_function_return_type):
                self.errors.add_error(SemanticError.type_mismatch(
                    expected=str(self.current_function_return_type), actual=str(return_type),
                    line=node.line, column=node.column, file=self.filename, context='return statement'))
        return node

    def visit_literal_expr(self, node: LiteralExprNode) -> Any:
        types_map = {'int': Types.INT, 'float': Types.FLOAT, 'bool': Types.BOOL, 'string': Types.STRING}
        node.inferred_type = types_map.get(node.literal_type, Types.VOID)
        return node

    def visit_identifier_expr(self, node: IdentifierExprNode) -> Any:
        symbol = self.symbol_table.lookup(node.name)
        if symbol is None:
            self.errors.add_error(SemanticError.undeclared(name=node.name, line=node.line,
                                                           column=node.column, file=self.filename,
                                                           context=self.symbol_table.current_scope.name))
            node.inferred_type = Types.VOID
        else:
            node.inferred_type = symbol.type_
        return node

    def visit_index_expr(self, node: IndexExprNode) -> Any:
        node.array.accept(self)
        array_type = getattr(node.array, 'inferred_type', None)
        node.index.accept(self)
        index_type = getattr(node.index, 'inferred_type', None)

        if index_type != Types.INT:
            self.errors.add_error(SemanticError(error_type=SemanticErrorType.INVALID_TYPE,
                                                message=f"Array index must be 'int', got '{index_type}'",
                                                line=node.line, column=node.column, file=self.filename))

        if isinstance(array_type, (ArrayType, PointerType)):
            node.inferred_type = array_type.element_type
        else:
            self.errors.add_error(SemanticError(error_type=SemanticErrorType.INVALID_TYPE,
                                                message=f"Cannot index type '{array_type}'",
                                                line=node.line, column=node.column, file=self.filename))
            node.inferred_type = Types.VOID
        return node.inferred_type

    def visit_binary_expr(self, node: BinaryExprNode) -> Any:
        node.left.accept(self);
        node.right.accept(self)
        left_type = getattr(node.left, 'inferred_type', None)
        right_type = getattr(node.right, 'inferred_type', None)
        op = node.operator

        if op in ('&&', '||', '==', '!=', '<', '<=', '>', '>='):
            node.inferred_type = Types.BOOL
        elif op in ('+', '-', '*', '/', '%'):
            node.inferred_type = get_common_type(left_type, right_type) or Types.INT
        elif op == '=':
            node.inferred_type = right_type
        else:
            node.inferred_type = Types.VOID
        return node

    def visit_unary_expr(self, node: UnaryExprNode) -> Any:
        node.operand.accept(self)
        operand_type = getattr(node.operand, 'inferred_type', None)
        op = node.operator
        node.inferred_type = operand_type if op == '-' else Types.BOOL if op == '!' else (operand_type or Types.VOID)
        return node

    # 🔑 Вставь этот метод ВНУТРЬ класса SemanticAnalyzer
    def visit_call_expr(self, node: CallExprNode):
        func_name = node.callee.name
        func_decl = self.symbol_table.lookup(func_name)

        if not func_decl:
            self.error(f"undefined function '{func_name}'")
            return

        params = getattr(func_decl, 'parameters', [])
        args = node.arguments

        # 1. Проверка количества аргументов
        if len(args) != len(params):
            self.error(f"argument count mismatch: expected {len(params)}, got {len(args)}")
            return

        # 2. 🔍 Проверка типов аргументов
        for arg_node, param_node in zip(args, params):
            arg_type = self._infer_type(arg_node)
            param_type = getattr(param_node, 'param_type', None)

            if arg_type and param_type and arg_type != param_type:
                self.error(f"type mismatch in argument '{param_node.name}': expected {param_type}, got {arg_type}")
                break  # Останавливаемся на первой ошибке типа

    # 🔑 Вспомогательный метод для определения типа выражения
    def _infer_type(self, node):
        if isinstance(node, LiteralExprNode):
            # Пробуем разные возможные названия поля с типом
            for attr in ['literal_type', 'type_', 'value_type']:
                if hasattr(node, attr):
                    val = getattr(node, attr)
                    if val: return str(val).lower()
            # Фоллбэк по значению
            v = getattr(node, 'value', None)
            if isinstance(v, str): return 'string'
            if isinstance(v, bool): return 'bool'
            if isinstance(v, float): return 'float'
            if isinstance(v, int): return 'int'
            return 'unknown'

        if isinstance(node, IdentifierExprNode):
            sym = self.symbol_table.lookup(node.name)
            if sym:
                for attr in ['type_', 'param_type', 'return_type']:
                    if hasattr(sym, attr) and getattr(sym, attr):
                        return str(getattr(sym, attr)).lower()
            return 'unknown'

        if isinstance(node, BinaryExprNode):
            lt = self._infer_type(node.left)
            rt = self._infer_type(node.right)
            if lt == 'float' or rt == 'float': return 'float'
            if lt == 'int' or rt == 'int': return 'int'
            return 'bool'

        if isinstance(node, CallExprNode):
            return self.visit_call_expr(node) or 'unknown'

        return 'unknown'

    def visit_assignment_expr(self, node: AssignmentExprNode) -> Any:
        if self._pass_number == 2:
            # 1. Анализируем правую часть (значение)
            node.value.accept(self)
            value_type = getattr(node.value, 'inferred_type', None)

            # 2. Анализируем левую часть (цель присваивания: переменная или arr[i])
            node.target.accept(self)
            target_type = getattr(node.target, 'inferred_type', None)

            # 3. Сравниваем типы ТОЛЬКО если оба являются объектами Type
            if target_type and value_type and isinstance(target_type, Type) and isinstance(value_type, Type):
                if not value_type.is_compatible_with(target_type):
                    self.errors.add_error(SemanticError.type_mismatch(
                        expected=str(target_type),
                        actual=str(value_type),
                        line=node.line,
                        column=node.column,
                        file=self.filename,
                        context='assignment'
                    ))

            node.inferred_type = value_type
        return node

    def visit_param(self, node: ParamNode) -> Any:
        return node