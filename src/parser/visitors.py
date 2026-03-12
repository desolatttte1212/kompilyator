from typing import List, Optional
from .ast_nodes import (
    ASTNode, ProgramNode, FunctionDeclNode, StructDeclNode, ParamNode,
    VarDeclStmtNode, BlockStmtNode, ExprStmtNode, IfStmtNode, WhileStmtNode,
    ForStmtNode, ReturnStmtNode, LiteralExprNode, IdentifierExprNode,
    BinaryExprNode, UnaryExprNode, CallExprNode, AssignmentExprNode,
    ASTVisitor
)
import json

class PrettyPrinter(ASTVisitor):

    def __init__(self):
        self.indent_level = 0
        self.output = []

    def _indent(self) -> str:
        return "  " * self.indent_level

    def _line(self, text: str, node: ASTNode):
        self.output.append(f"{self._indent()}{text} [line {node.line}]")

    def _line_no_node(self, text: str):
        self.output.append(f"{self._indent()}{text}")

    def visit_program(self, node: ProgramNode) -> str:
        self._line_no_node("Program:")
        self.indent_level += 1
        for decl in node.declarations:
            decl.accept(self)
        self.indent_level -= 1
        return "\n".join(self.output)

    def visit_function_decl(self, node: FunctionDeclNode) -> str:
        self._line(f"FunctionDecl: {node.name} -> {node.return_type}", node)
        self.indent_level += 1
        self._line_no_node(f"Parameters: [{', '.join(p.name for p in node.parameters)}]")
        self._line_no_node("Body:")
        self.indent_level += 1
        node.body.accept(self)
        self.indent_level -= 2
        return "\n".join(self.output)

    def visit_struct_decl(self, node: StructDeclNode) -> str:
        self._line(f"StructDecl: {node.name}", node)
        self.indent_level += 1
        for field in node.fields:
            field.accept(self)
        self.indent_level -= 1
        return "\n".join(self.output)

    def visit_var_decl_stmt(self, node: VarDeclStmtNode) -> str:
        init = f" = {self._expr_to_string(node.initializer)}" if node.initializer else ""
        self._line(f"VarDecl: {node.var_type} {node.name}{init}", node)
        return "\n".join(self.output)

    def visit_block_stmt(self, node: BlockStmtNode) -> str:
        self._line("Block:", node)
        self.indent_level += 1
        for stmt in node.statements:
            stmt.accept(self)
        self.indent_level -= 1
        return "\n".join(self.output)

    def visit_expr_stmt(self, node: ExprStmtNode) -> str:
        self._line(f"Expr: {self._expr_to_string(node.expression)}", node)
        return "\n".join(self.output)

    def visit_if_stmt(self, node: IfStmtNode) -> str:
        self._line(f"If: {self._expr_to_string(node.condition)}", node)
        self.indent_level += 1
        self._line_no_node("Then:")
        self.indent_level += 1
        node.then_branch.accept(self)
        self.indent_level -= 2
        if node.else_branch:
            self._line_no_node("Else:")
            self.indent_level += 1
            node.else_branch.accept(self)
            self.indent_level -= 1
        return "\n".join(self.output)

    def visit_while_stmt(self, node: WhileStmtNode) -> str:
        self._line(f"While: {self._expr_to_string(node.condition)}", node)
        self.indent_level += 1
        node.body.accept(self)
        self.indent_level -= 1
        return "\n".join(self.output)

    def visit_for_stmt(self, node: ForStmtNode) -> str:
        init = self._expr_to_string(node.init) if node.init else ""
        cond = self._expr_to_string(node.condition) if node.condition else ""
        update = self._expr_to_string(node.update) if node.update else ""
        self._line(f"For: ({init}; {cond}; {update})", node)
        self.indent_level += 1
        node.body.accept(self)
        self.indent_level -= 1
        return "\n".join(self.output)

    def visit_return_stmt(self, node: ReturnStmtNode) -> str:
        value = self._expr_to_string(node.value) if node.value else ""
        self._line(f"Return: {value}", node)
        return "\n".join(self.output)

    def visit_literal_expr(self, node: LiteralExprNode) -> str:
        self._line(f"Literal: {node.value} ({node.literal_type})", node)
        return "\n".join(self.output)

    def visit_identifier_expr(self, node: IdentifierExprNode) -> str:
        self._line(f"Identifier: {node.name}", node)
        return "\n".join(self.output)

    def visit_binary_expr(self, node: BinaryExprNode) -> str:
        self._line(f"Binary: {node.operator}", node)
        self.indent_level += 1
        self._line_no_node("Left:")
        self.indent_level += 1
        node.left.accept(self)
        self.indent_level -= 2
        self._line_no_node("Right:")
        self.indent_level += 1
        node.right.accept(self)
        self.indent_level -= 2
        return "\n".join(self.output)

    def visit_unary_expr(self, node: UnaryExprNode) -> str:
        self._line(f"Unary: {node.operator}", node)
        self.indent_level += 1
        node.operand.accept(self)
        self.indent_level -= 1
        return "\n".join(self.output)

    def visit_call_expr(self, node: CallExprNode) -> str:
        args = ", ".join(self._expr_to_string(arg) for arg in node.arguments)
        self._line(f"Call: {node.callee.name}({args})", node)
        return "\n".join(self.output)

    def visit_assignment_expr(self, node: AssignmentExprNode) -> str:
        self._line(f"Assignment: {node.operator}", node)
        self.indent_level += 1
        self._line_no_node("Target:")
        self.indent_level += 1
        node.target.accept(self)
        self.indent_level -= 2
        self._line_no_node("Value:")
        self.indent_level += 1
        node.value.accept(self)
        self.indent_level -= 2
        return "\n".join(self.output)

    def visit_param(self, node: ParamNode) -> str:
        self._line_no_node(f"Param: {node.param_type} {node.name}")
        return "\n".join(self.output)

    def _expr_to_string(self, expr: Optional[ASTNode]) -> str:
        if expr is None:
            return ""
        if isinstance(expr, LiteralExprNode):
            return str(expr.value)
        elif isinstance(expr, IdentifierExprNode):
            return expr.name
        elif isinstance(expr, BinaryExprNode):
            return f"({self._expr_to_string(expr.left)} {expr.operator} {self._expr_to_string(expr.right)})"
        elif isinstance(expr, UnaryExprNode):
            return f"({expr.operator}{self._expr_to_string(expr.operand)})"
        elif isinstance(expr, CallExprNode):
            args = ", ".join(self._expr_to_string(arg) for arg in expr.arguments)
            return f"{expr.callee.name}({args})"
        elif isinstance(expr, AssignmentExprNode):
            return f"({self._expr_to_string(expr.target)} {expr.operator} {self._expr_to_string(expr.value)})"
        return "<expr>"

    def print(self, node: ASTNode) -> str:
        self.output = []
        self.indent_level = 0
        node.accept(self)
        return "\n".join(self.output)

class DotVisitor(ASTVisitor):

    def __init__(self):
        self.nodes = []
        self.edges = []
        self.node_id = 0
        self.parent_stack = []

    def _new_id(self) -> str:
        self.node_id += 1
        return f"n{self.node_id}"

    def _color_for_type(self, node_type: str) -> str:
        colors = {
            'Program': 'lightblue',
            'FunctionDecl': 'lightgreen',
            'StructDecl': 'lightyellow',
            'VarDeclStmt': 'lightcoral',
            'BlockStmt': 'lightgray',
            'IfStmt': 'orange',
            'WhileStmt': 'pink',
            'ForStmt': 'purple',
            'ReturnStmt': 'cyan',
            'BinaryExpr': 'wheat',
            'UnaryExpr': 'beige',
            'LiteralExpr': 'lightblue',
            'IdentifierExpr': 'lightblue',
            'CallExpr': 'lavender',
            'AssignmentExpr': 'peachpuff'
        }
        return colors.get(node_type, 'white')

    def _add_node(self, label: str, node: ASTNode) -> str:
        node_id = self._new_id()
        color = self._color_for_type(node.__class__.__name__.replace('Node', ''))
        safe_label = label.replace('"', '\\"').replace('\n', '\\n')
        self.nodes.append(
            f'  {node_id} [label="{safe_label}\\n[line {node.line}]", '
            f'style=filled, fillcolor="{color}"];'
        )
        if self.parent_stack:
            self.edges.append(f'  {self.parent_stack[-1]} -> {node_id};')
        return node_id

    def visit_program(self, node: ProgramNode) -> str:
        node_id = self._add_node("Program", node)
        self.parent_stack.append(node_id)
        for decl in node.declarations:
            decl.accept(self)
        self.parent_stack.pop()
        return self._generate_dot()

    def visit_function_decl(self, node: FunctionDeclNode) -> str:
        label = f"FunctionDecl\\n{node.name} -> {node.return_type}".replace("{name}", node.name)
        node_id = self._add_node(label, node)
        self.parent_stack.append(node_id)
        for param in node.parameters:
            param.accept(self)
        node.body.accept(self)
        self.parent_stack.pop()
        return self._generate_dot()

    def visit_struct_decl(self, node: StructDeclNode) -> str:
        node_id = self._add_node(f"StructDecl\\n{node.name}", node)
        self.parent_stack.append(node_id)
        for field in node.fields:
            field.accept(self)
        self.parent_stack.pop()
        return self._generate_dot()

    def visit_var_decl_stmt(self, node: VarDeclStmtNode) -> str:
        label = f"VarDecl\\n{node.var_type} {node.name}"
        node_id = self._add_node(label, node)
        if node.initializer:
            self.parent_stack.append(node_id)
            node.initializer.accept(self)
            self.parent_stack.pop()
        return self._generate_dot()

    def visit_block_stmt(self, node: BlockStmtNode) -> str:
        node_id = self._add_node("Block", node)
        self.parent_stack.append(node_id)
        for stmt in node.statements:
            stmt.accept(self)
        self.parent_stack.pop()
        return self._generate_dot()

    def visit_expr_stmt(self, node: ExprStmtNode) -> str:
        node_id = self._add_node("ExprStmt", node)
        self.parent_stack.append(node_id)
        node.expression.accept(self)
        self.parent_stack.pop()
        return self._generate_dot()

    def visit_if_stmt(self, node: IfStmtNode) -> str:
        node_id = self._add_node("IfStmt", node)
        self.parent_stack.append(node_id)
        node.condition.accept(self)
        self.parent_stack.pop()

        self.parent_stack.append(node_id)
        self._add_node("Then", node.then_branch)
        node.then_branch.accept(self)
        self.parent_stack.pop()

        if node.else_branch:
            self.parent_stack.append(node_id)
            self._add_node("Else", node.else_branch)
            node.else_branch.accept(self)
            self.parent_stack.pop()

        return self._generate_dot()

    def visit_while_stmt(self, node: WhileStmtNode) -> str:
        node_id = self._add_node("WhileStmt", node)
        self.parent_stack.append(node_id)
        node.condition.accept(self)
        node.body.accept(self)
        self.parent_stack.pop()
        return self._generate_dot()

    def visit_for_stmt(self, node: ForStmtNode) -> str:
        node_id = self._add_node("ForStmt", node)
        self.parent_stack.append(node_id)
        if node.init:
            node.init.accept(self)
        if node.condition:
            node.condition.accept(self)
        if node.update:
            node.update.accept(self)
        node.body.accept(self)
        self.parent_stack.pop()
        return self._generate_dot()

    def visit_return_stmt(self, node: ReturnStmtNode) -> str:
        node_id = self._add_node("ReturnStmt", node)
        if node.value:
            self.parent_stack.append(node_id)
            node.value.accept(self)
            self.parent_stack.pop()
        return self._generate_dot()

    def visit_literal_expr(self, node: LiteralExprNode) -> str:
        self._add_node(f"Literal\\n{node.value}", node)
        return self._generate_dot()

    def visit_identifier_expr(self, node: IdentifierExprNode) -> str:
        self._add_node(f"Identifier\\n{node.name}", node)
        return self._generate_dot()

    def visit_binary_expr(self, node: BinaryExprNode) -> str:
        node_id = self._add_node(f"Binary\\n{node.operator}", node)
        self.parent_stack.append(node_id)
        node.left.accept(self)
        node.right.accept(self)
        self.parent_stack.pop()
        return self._generate_dot()

    def visit_unary_expr(self, node: UnaryExprNode) -> str:
        node_id = self._add_node(f"Unary\\n{node.operator}", node)
        self.parent_stack.append(node_id)
        node.operand.accept(self)
        self.parent_stack.pop()
        return self._generate_dot()

    def visit_call_expr(self, node: CallExprNode) -> str:
        node_id = self._add_node(f"Call\\n{node.callee.name}", node)
        self.parent_stack.append(node_id)
        for arg in node.arguments:
            arg.accept(self)
        self.parent_stack.pop()
        return self._generate_dot()

    def visit_assignment_expr(self, node: AssignmentExprNode) -> str:
        node_id = self._add_node(f"Assignment\\n{node.operator}", node)
        self.parent_stack.append(node_id)
        node.target.accept(self)
        node.value.accept(self)
        self.parent_stack.pop()
        return self._generate_dot()

    def visit_param(self, node: ParamNode) -> str:
        self._add_node(f"Param\\n{node.param_type} {node.name}", node)
        return self._generate_dot()

    def _generate_dot(self) -> str:
        lines = ['digraph AST {']
        lines.append('  rankdir=TB;')
        lines.append('  node [shape=box];')
        lines.extend(self.nodes)
        lines.extend(self.edges)
        lines.append('}')
        return "\n".join(lines)

    def generate(self, node: ASTNode) -> str:
        """Generate DOT string from AST."""
        self.nodes = []
        self.edges = []
        self.node_id = 0
        self.parent_stack = []
        node.accept(self)
        return self._generate_dot()

class JsonVisitor(ASTVisitor):

    def visit_program(self, node: ProgramNode) -> dict:
        return node.to_dict()

    def visit_function_decl(self, node: FunctionDeclNode) -> dict:
        return node.to_dict()

    def visit_struct_decl(self, node: StructDeclNode) -> dict:
        return node.to_dict()

    def visit_var_decl_stmt(self, node: VarDeclStmtNode) -> dict:
        return node.to_dict()

    def visit_block_stmt(self, node: BlockStmtNode) -> dict:
        return node.to_dict()

    def visit_expr_stmt(self, node: ExprStmtNode) -> dict:
        return node.to_dict()

    def visit_if_stmt(self, node: IfStmtNode) -> dict:
        return node.to_dict()

    def visit_while_stmt(self, node: WhileStmtNode) -> dict:
        return node.to_dict()

    def visit_for_stmt(self, node: ForStmtNode) -> dict:
        return node.to_dict()

    def visit_return_stmt(self, node: ReturnStmtNode) -> dict:
        return node.to_dict()

    def visit_literal_expr(self, node: LiteralExprNode) -> dict:
        return node.to_dict()

    def visit_identifier_expr(self, node: IdentifierExprNode) -> dict:
        return node.to_dict()

    def visit_binary_expr(self, node: BinaryExprNode) -> dict:
        return node.to_dict()

    def visit_unary_expr(self, node: UnaryExprNode) -> dict:
        return node.to_dict()

    def visit_call_expr(self, node: CallExprNode) -> dict:
        return node.to_dict()

    def visit_assignment_expr(self, node: AssignmentExprNode) -> dict:
        return node.to_dict()

    def visit_param(self, node: ParamNode) -> dict:
        return node.to_dict()

    def to_json(self, node: ASTNode, indent: int = 2) -> str:
        data = node.accept(self)
        return json.dumps(data, indent=indent)