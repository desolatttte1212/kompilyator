from typing import Any, Optional
from .ast_nodes import (
    ASTNode, ProgramNode, FunctionDeclNode, StructDeclNode, ParamNode,
    VarDeclStmtNode, BlockStmtNode, ExprStmtNode, IfStmtNode, WhileStmtNode,
    ForStmtNode, ReturnStmtNode, LiteralExprNode, IdentifierExprNode,
    BinaryExprNode, UnaryExprNode, CallExprNode, AssignmentExprNode,
    IndexExprNode, ASTVisitor
)
import json


class PrettyPrinter(ASTVisitor):
    def __init__(self):
        self.indent_level = 0
        self.output = []

    def _indent(self):
        return "  " * self.indent_level

    def _add(self, text: str):
        self.output.append(f"{self._indent()}{text}")

    def print(self, node: ASTNode) -> str:
        self.output = []
        node.accept(self)
        return "\n".join(self.output)

    def visit_program(self, node: ProgramNode) -> Any:
        self._add("Program:")
        self.indent_level += 1
        for decl in node.declarations:
            decl.accept(self)
        self.indent_level -= 1
        return node

    def visit_function_decl(self, node: FunctionDeclNode) -> Any:
        self._add(f"FunctionDecl: {node.name}() -> {node.return_type}")
        self.indent_level += 1
        if node.parameters:
            self._add("Parameters:")
            self.indent_level += 1
            for p in node.parameters:
                p.accept(self)
            self.indent_level -= 1
        node.body.accept(self)
        self.indent_level -= 1
        return node

    def visit_struct_decl(self, node: StructDeclNode) -> Any:
        self._add(f"StructDecl: {node.name}")
        self.indent_level += 1
        for f in node.fields:
            f.accept(self)
        self.indent_level -= 1
        return node

    def visit_param(self, node: ParamNode) -> Any:
        self._add(f"Param: {node.name}: {node.param_type}")
        return node

    def visit_var_decl_stmt(self, node: VarDeclStmtNode) -> Any:
        init = " = <expr>" if node.initializer else ""
        self._add(f"VarDecl: {node.var_type} {node.name}{init}")
        if node.initializer:
            self.indent_level += 1
            node.initializer.accept(self)
            self.indent_level -= 1
        return node

    def visit_block_stmt(self, node: BlockStmtNode) -> Any:
        self._add("Block:")
        self.indent_level += 1
        for stmt in node.statements:
            stmt.accept(self)
        self.indent_level -= 1
        return node

    def visit_expr_stmt(self, node: ExprStmtNode) -> Any:
        self._add("ExprStmt:")
        self.indent_level += 1
        node.expression.accept(self)
        self.indent_level -= 1
        return node

    def visit_if_stmt(self, node: IfStmtNode) -> Any:
        self._add("IfStmt:")
        self.indent_level += 1
        self._add("condition:")
        self.indent_level += 1
        node.condition.accept(self)
        self.indent_level -= 1
        self._add("then:")
        node.then_branch.accept(self)
        if node.else_branch:
            self._add("else:")
            node.else_branch.accept(self)
        self.indent_level -= 1
        return node

    def visit_while_stmt(self, node: WhileStmtNode) -> Any:
        self._add("WhileStmt:")
        self.indent_level += 1
        self._add("condition:")
        node.condition.accept(self)
        self._add("body:")
        node.body.accept(self)
        self.indent_level -= 1
        return node

    def visit_for_stmt(self, node: ForStmtNode) -> Any:
        self._add("ForStmt:")
        self.indent_level += 1
        self._add("init:")
        node.init.accept(self) if node.init else self._add("None")
        self._add("condition:")
        node.condition.accept(self) if node.condition else self._add("None")
        self._add("update:")
        node.update.accept(self) if node.update else self._add("None")
        self._add("body:")
        node.body.accept(self)
        self.indent_level -= 1
        return node

    def visit_return_stmt(self, node: ReturnStmtNode) -> Any:
        self._add("ReturnStmt:")
        if node.value:
            self.indent_level += 1
            node.value.accept(self)
            self.indent_level -= 1
        return node

    def visit_literal_expr(self, node: LiteralExprNode) -> Any:
        self._add(f"Literal({node.literal_type}): {node.value}")
        return node

    def visit_identifier_expr(self, node: IdentifierExprNode) -> Any:
        self._add(f"Identifier: {node.name}")
        return node

    def visit_index_expr(self, node: IndexExprNode) -> Any:
        self._add("IndexExpr:")
        self.indent_level += 1
        self._add("array:")
        node.array.accept(self)
        self._add("index:")
        node.index.accept(self)
        self.indent_level -= 1
        return node

    def visit_binary_expr(self, node: BinaryExprNode) -> Any:
        self._add(f"BinaryExpr: {node.operator}")
        self.indent_level += 1
        node.left.accept(self)
        node.right.accept(self)
        self.indent_level -= 1
        return node

    def visit_unary_expr(self, node: UnaryExprNode) -> Any:
        self._add(f"UnaryExpr: {node.operator}")
        self.indent_level += 1
        node.operand.accept(self)
        self.indent_level -= 1
        return node

    def visit_call_expr(self, node: CallExprNode) -> Any:
        self._add(f"CallExpr: {node.callee.name}()")
        self.indent_level += 1
        for arg in node.arguments:
            arg.accept(self)
        self.indent_level -= 1
        return node

    def visit_assignment_expr(self, node: AssignmentExprNode) -> Any:
        self._add("AssignmentExpr:")
        self.indent_level += 1
        self._add("target:")
        node.target.accept(self)
        self._add("value:")
        node.value.accept(self)
        self.indent_level -= 1
        return node


class DotVisitor(ASTVisitor):
    def __init__(self):
        self.dot = ['digraph AST {', '  rankdir=TB;', '  node [shape=box, style=filled, fillcolor=lightblue];']
        self.node_id = 0

    def _new_id(self) -> int:
        self.node_id += 1
        return self.node_id

    def _add_node(self, nid: int, label: str):
        safe_label = label.replace('"', '\\"').replace('\n', '\\n')
        self.dot.append(f'  n{nid} [label="{safe_label}"];')

    def _add_edge(self, src: int, dst: int):
        self.dot.append(f'  n{src} -> n{dst};')

    def generate(self, node: ASTNode) -> str:
        node.accept(self)
        self.dot.append('}')
        return '\n'.join(self.dot)

    def visit_program(self, node: ProgramNode) -> Any:
        nid = self._new_id()
        self._add_node(nid, "Program")
        for decl in node.declarations:
            child_id = decl.accept(self)
            self._add_edge(nid, child_id)
        return nid

    def visit_function_decl(self, node: FunctionDeclNode) -> Any:
        nid = self._new_id()
        self._add_node(nid, f"fn {node.name}() -> {node.return_type}")
        for p in node.parameters:
            pid = p.accept(self)
            self._add_edge(nid, pid)
        bid = node.body.accept(self)
        self._add_edge(nid, bid)
        return nid

    def visit_struct_decl(self, node: StructDeclNode) -> Any:
        nid = self._new_id()
        self._add_node(nid, f"struct {node.name}")
        for f in node.fields:
            fid = f.accept(self)
            self._add_edge(nid, fid)
        return nid

    def visit_param(self, node: ParamNode) -> Any:
        nid = self._new_id()
        self._add_node(nid, f"param {node.name}: {node.param_type}")
        return nid

    def visit_var_decl_stmt(self, node: VarDeclStmtNode) -> Any:
        nid = self._new_id()
        self._add_node(nid, f"var {node.name}: {node.var_type}")
        if node.initializer:
            iid = node.initializer.accept(self)
            self._add_edge(nid, iid)
        return nid

    def visit_block_stmt(self, node: BlockStmtNode) -> Any:
        nid = self._new_id()
        self._add_node(nid, "Block")
        for stmt in node.statements:
            sid = stmt.accept(self)
            self._add_edge(nid, sid)
        return nid

    def visit_expr_stmt(self, node: ExprStmtNode) -> Any:
        nid = self._new_id()
        self._add_node(nid, "ExprStmt")
        eid = node.expression.accept(self)
        self._add_edge(nid, eid)
        return nid

    def visit_if_stmt(self, node: IfStmtNode) -> Any:
        nid = self._new_id()
        self._add_node(nid, "If")
        cid = node.condition.accept(self)
        self._add_edge(nid, cid)
        tid = node.then_branch.accept(self)
        self._add_edge(nid, tid)
        if node.else_branch:
            eid = node.else_branch.accept(self)
            self._add_edge(nid, eid)
        return nid

    def visit_while_stmt(self, node: WhileStmtNode) -> Any:
        nid = self._new_id()
        self._add_node(nid, "While")
        cid = node.condition.accept(self)
        self._add_edge(nid, cid)
        bid = node.body.accept(self)
        self._add_edge(nid, bid)
        return nid

    def visit_for_stmt(self, node: ForStmtNode) -> Any:
        nid = self._new_id()
        self._add_node(nid, "For")
        if node.init:
            iid = node.init.accept(self)
            self._add_edge(nid, iid)
        if node.condition:
            cid = node.condition.accept(self)
            self._add_edge(nid, cid)
        if node.update:
            uid = node.update.accept(self)
            self._add_edge(nid, uid)
        bid = node.body.accept(self)
        self._add_edge(nid, bid)
        return nid

    def visit_return_stmt(self, node: ReturnStmtNode) -> Any:
        nid = self._new_id()
        self._add_node(nid, "Return")
        if node.value:
            vid = node.value.accept(self)
            self._add_edge(nid, vid)
        return nid

    def visit_literal_expr(self, node: LiteralExprNode) -> Any:
        nid = self._new_id()
        self._add_node(nid, f"Lit({node.literal_type}): {node.value}")
        return nid

    def visit_identifier_expr(self, node: IdentifierExprNode) -> Any:
        nid = self._new_id()
        self._add_node(nid, f"Id: {node.name}")
        return nid

    def visit_index_expr(self, node: IndexExprNode) -> Any:
        nid = self._new_id()
        self._add_node(nid, "IndexExpr []")
        aid = node.array.accept(self)
        self._add_edge(nid, aid)
        iid = node.index.accept(self)
        self._add_edge(nid, iid)
        return nid

    def visit_binary_expr(self, node: BinaryExprNode) -> Any:
        nid = self._new_id()
        self._add_node(nid, f"Op: {node.operator}")
        lid = node.left.accept(self)
        self._add_edge(nid, lid)
        rid = node.right.accept(self)
        self._add_edge(nid, rid)
        return nid

    def visit_unary_expr(self, node: UnaryExprNode) -> Any:
        nid = self._new_id()
        self._add_node(nid, f"Op: {node.operator}")
        oid = node.operand.accept(self)
        self._add_edge(nid, oid)
        return nid

    def visit_call_expr(self, node: CallExprNode) -> Any:
        nid = self._new_id()
        self._add_node(nid, f"Call: {node.callee.name}")
        for arg in node.arguments:
            aid = arg.accept(self)
            self._add_edge(nid, aid)
        return nid

    def visit_assignment_expr(self, node: AssignmentExprNode) -> Any:
        nid = self._new_id()
        self._add_node(nid, "Assign =")
        tid = node.target.accept(self)
        self._add_edge(nid, tid)
        vid = node.value.accept(self)
        self._add_edge(nid, vid)
        return nid


class JsonVisitor(ASTVisitor):
    def to_json(self, node: ASTNode) -> str:
        data = node.accept(self)
        return json.dumps(data, indent=2, ensure_ascii=False)

    def visit_program(self, node: ProgramNode) -> Any:
        return {
            'type': 'Program',
            'declarations': [d.accept(self) for d in node.declarations]
        }

    def visit_function_decl(self, node: FunctionDeclNode) -> Any:
        return {
            'type': 'FunctionDecl',
            'name': node.name,
            'return_type': node.return_type,
            'parameters': [p.accept(self) for p in node.parameters],
            'body': node.body.accept(self)
        }

    def visit_struct_decl(self, node: StructDeclNode) -> Any:
        return {
            'type': 'StructDecl',
            'name': node.name,
            'fields': [f.accept(self) for f in node.fields]
        }

    def visit_param(self, node: ParamNode) -> Any:
        return {'type': 'Param', 'name': node.name, 'param_type': node.param_type}

    def visit_var_decl_stmt(self, node: VarDeclStmtNode) -> Any:
        return {
            'type': 'VarDeclStmt',
            'var_type': node.var_type,
            'name': node.name,
            'initializer': node.initializer.accept(self) if node.initializer else None
        }

    def visit_block_stmt(self, node: BlockStmtNode) -> Any:
        return {
            'type': 'BlockStmt',
            'statements': [s.accept(self) for s in node.statements]
        }

    def visit_expr_stmt(self, node: ExprStmtNode) -> Any:
        return {'type': 'ExprStmt', 'expression': node.expression.accept(self)}

    def visit_if_stmt(self, node: IfStmtNode) -> Any:
        return {
            'type': 'IfStmt',
            'condition': node.condition.accept(self),
            'then_branch': node.then_branch.accept(self),
            'else_branch': node.else_branch.accept(self) if node.else_branch else None
        }

    def visit_while_stmt(self, node: WhileStmtNode) -> Any:
        return {
            'type': 'WhileStmt',
            'condition': node.condition.accept(self),
            'body': node.body.accept(self)
        }

    def visit_for_stmt(self, node: ForStmtNode) -> Any:
        return {
            'type': 'ForStmt',
            'init': node.init.accept(self) if node.init else None,
            'condition': node.condition.accept(self) if node.condition else None,
            'update': node.update.accept(self) if node.update else None,
            'body': node.body.accept(self)
        }

    def visit_return_stmt(self, node: ReturnStmtNode) -> Any:
        return {
            'type': 'ReturnStmt',
            'value': node.value.accept(self) if node.value else None
        }

    def visit_literal_expr(self, node: LiteralExprNode) -> Any:
        return {'type': 'Literal', 'literal_type': node.literal_type, 'value': node.value}

    def visit_identifier_expr(self, node: IdentifierExprNode) -> Any:
        return {'type': 'Identifier', 'name': node.name}

    # 🆕 Новый метод для индексации массивов
    def visit_index_expr(self, node: IndexExprNode) -> Any:
        return {
            'type': 'IndexExpr',
            'array': node.array.accept(self),
            'index': node.index.accept(self)
        }

    def visit_binary_expr(self, node: BinaryExprNode) -> Any:
        return {
            'type': 'BinaryExpr',
            'operator': node.operator,
            'left': node.left.accept(self),
            'right': node.right.accept(self)
        }

    def visit_unary_expr(self, node: UnaryExprNode) -> Any:
        return {
            'type': 'UnaryExpr',
            'operator': node.operator,
            'operand': node.operand.accept(self)
        }

    def visit_call_expr(self, node: CallExprNode) -> Any:
        return {
            'type': 'CallExpr',
            'callee': node.callee.accept(self),
            'arguments': [a.accept(self) for a in node.arguments]
        }

    def visit_assignment_expr(self, node: AssignmentExprNode) -> Any:
        return {
            'type': 'AssignmentExpr',
            'target': node.target.accept(self),
            'value': node.value.accept(self)
        }