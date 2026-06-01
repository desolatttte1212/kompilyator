import sys
from typing import List, Optional, Dict, Set
from ..parser.ast_nodes import (
    ASTNode, ProgramNode, FunctionDeclNode, StructDeclNode, ParamNode,
    VarDeclStmtNode, BlockStmtNode, ExprStmtNode, IfStmtNode, WhileStmtNode,
    ForStmtNode, ReturnStmtNode, LiteralExprNode, IdentifierExprNode,
    BinaryExprNode, UnaryExprNode, CallExprNode, AssignmentExprNode,
    ASTVisitor
)


class SemanticChecker(ASTVisitor):
    def __init__(self, symbol_table: Optional[Dict] = None):
        self.symbol_table = symbol_table or {}
        self.errors: List[str] = []
        self.current_return_type: Optional[str] = None
        self.scope_stack: List[Set[str]] = [set()]  # Отслеживание локальных переменных

    def error(self, msg: str):
        """Выводит ошибку в stderr в формате, который ожидает тестовый раннер."""
        print(f"semantic error: {msg}", file=sys.stderr)
        self.errors.append(msg)

    def enter_scope(self):
        self.scope_stack.append(set())

    def exit_scope(self):
        self.scope_stack.pop()

    def declare_in_scope(self, name: str):
        if name in self.scope_stack[-1]:
            self.error(f"duplicate declaration of '{name}' in same scope")
        else:
            self.scope_stack[-1].add(name)

    def _get_expr_type(self, node: ASTNode) -> str:
        """Определяет тип выражения для сравнения с параметрами/присваиваниями."""
        if isinstance(node, LiteralExprNode):
            return node.literal_type  # "int", "string", "bool", "float"

        if isinstance(node, IdentifierExprNode):
            sym = self.symbol_table.get(node.name)
            if sym:
                return sym.type_ if hasattr(sym, 'type_') else sym.get('type', 'unknown')
            return "unknown"

        if isinstance(node, BinaryExprNode):
            lt = self._get_expr_type(node.left)
            rt = self._get_expr_type(node.right)
            if lt in ("int", "float") and rt in ("int", "float"):
                return "float" if "float" in (lt, rt) else "int"
            if lt == "string" or rt == "string":
                return "string"
            return "bool"  # Результаты сравнений

        if isinstance(node, UnaryExprNode):
            if node.operator == "!":
                return "bool"
            return self._get_expr_type(node.operand)

        if isinstance(node, CallExprNode):
            return self.visit_call_expr(node) or "unknown"

        return "unknown"

    def visit_program(self, node: ProgramNode):
        self.enter_scope()
        for decl in node.declarations:
            decl.accept(self)
        self.exit_scope()
        return not bool(self.errors)

    def visit_function_decl(self, node: FunctionDeclNode):
        self.declare_in_scope(node.name)
        self.symbol_table[node.name] = node

        self.enter_scope()
        for param in node.parameters:
            self.declare_in_scope(param.name)
            self.symbol_table[param.name] = param

        old_ret = self.current_return_type
        self.current_return_type = node.return_type
        node.body.accept(self)
        self.current_return_type = old_ret

        self.exit_scope()

    def visit_struct_decl(self, node: StructDeclNode):
        self.declare_in_scope(node.name)
        self.symbol_table[node.name] = node

    def visit_var_decl_stmt(self, node: VarDeclStmtNode):
        self.declare_in_scope(node.name)
        self.symbol_table[node.name] = type('Sym', (), {'type_': node.var_type})()

        if node.initializer:
            init_type = self._get_expr_type(node.initializer)
            if init_type != "unknown" and node.var_type != "unknown":
                if init_type != node.var_type:
                    self.error(
                        f"type mismatch in initialization of '{node.name}': expected {node.var_type}, got {init_type}")

    def visit_block_stmt(self, node: BlockStmtNode):
        self.enter_scope()
        for stmt in node.statements:
            stmt.accept(self)
        self.exit_scope()

    def visit_expr_stmt(self, node: ExprStmtNode):
        node.expression.accept(self)

    def visit_if_stmt(self, node: IfStmtNode):
        cond_type = self._get_expr_type(node.condition)
        if cond_type != "bool":
            self.error(f"condition must be bool, got {cond_type}")

        self.enter_scope()
        node.then_branch.accept(self)
        self.exit_scope()

        if node.else_branch:
            self.enter_scope()
            node.else_branch.accept(self)
            self.exit_scope()

    def visit_while_stmt(self, node: WhileStmtNode):
        cond_type = self._get_expr_type(node.condition)
        if cond_type != "bool":
            self.error(f"condition must be bool, got {cond_type}")

        self.enter_scope()
        node.body.accept(self)
        self.exit_scope()

    def visit_for_stmt(self, node: ForStmtNode):
        self.enter_scope()
        if node.init: node.init.accept(self)
        if node.condition:
            cond_type = self._get_expr_type(node.condition)
            if cond_type != "bool":
                self.error(f"condition must be bool, got {cond_type}")
        if node.update: node.update.accept(self)
        node.body.accept(self)
        self.exit_scope()

    def visit_return_stmt(self, node: ReturnStmtNode):
        if self.current_return_type == "void":
            if node.value:
                self.error("void function should not return a value")
        else:
            if not node.value:
                self.error(f"function expected to return {self.current_return_type}, but returns nothing")
            else:
                ret_type = self._get_expr_type(node.value)
                if ret_type != self.current_return_type:
                    self.error(f"type mismatch in return: expected {self.current_return_type}, got {ret_type}")

    def visit_literal_expr(self, node: LiteralExprNode):
        pass

    def visit_identifier_expr(self, node: IdentifierExprNode):
        if node.name not in self.symbol_table:
            self.error(f"undeclared identifier '{node.name}'")

    def visit_binary_expr(self, node: BinaryExprNode):
        node.left.accept(self)
        node.right.accept(self)
        lt = self._get_expr_type(node.left)
        rt = self._get_expr_type(node.right)
        if node.operator in ('+', '-', '*', '/', '%') and lt not in ("int", "float"):
            self.error(f"arithmetic operation on non-numeric type: {lt}")

    def visit_unary_expr(self, node: UnaryExprNode):
        node.operand.accept(self)

    # 🔑 ИСПРАВЛЕНИЕ: Строгая проверка типов аргументов при вызове функции
    def visit_call_expr(self, node: CallExprNode) -> Optional[str]:
        func_name = node.callee.name
        func_decl = self.symbol_table.get(func_name)

        if not func_decl or not isinstance(func_decl, FunctionDeclNode):
            self.error(f"undefined function '{func_name}'")
            return "void"

        params = func_decl.parameters
        args = node.arguments

        if len(args) != len(params):
            self.error(f"argument count mismatch for '{func_name}': expected {len(params)}, got {len(args)}")
            return func_decl.return_type

        for i, (arg, param) in enumerate(zip(args, params)):
            arg_type = self._get_expr_type(arg)
            param_type = param.param_type

            if arg_type != param_type:
                param_name = param.name
                self.error(
                    f"type mismatch in argument '{param_name}' of '{func_name}': "
                    f"expected {param_type}, got {arg_type}"
                )
                break  # Останавливаемся на первой несовпадающей паре

        return func_decl.return_type

    def visit_assignment_expr(self, node: AssignmentExprNode):
        target_type = "unknown"
        if isinstance(node.target, IdentifierExprNode):
            sym = self.symbol_table.get(node.target.name)
            if sym:
                target_type = getattr(sym, 'type_', sym.get('type', 'unknown') if isinstance(sym, dict) else 'unknown')
            else:
                self.error(f"undeclared identifier '{node.target.name}'")

        value_type = self._get_expr_type(node.value)
        if target_type != "unknown" and value_type != "unknown" and target_type != value_type:
            self.error(f"type mismatch in assignment: expected {target_type}, got {value_type}")

    def check(self, ast: ProgramNode) -> bool:
        """Точка входа для семантического анализа."""
        self.errors = []
        self.scope_stack = [set()]
        ast.accept(self)
        return len(self.errors) == 0