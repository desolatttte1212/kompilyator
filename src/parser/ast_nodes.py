from abc import ABC, abstractmethod
from typing import List, Optional, Any
from dataclasses import dataclass

class ASTNode(ABC):
    def __init__(self, line: int = 1, column: int = 1):
        self.line = line
        self.column = column

    @abstractmethod
    def accept(self, visitor: 'ASTVisitor') -> Any:
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        pass


class ExpressionNode(ASTNode):
    pass


class StatementNode(ASTNode):
    pass


class DeclarationNode(ASTNode):
    pass

@dataclass
class LiteralExprNode(ExpressionNode):
    value: Any
    literal_type: str
    line: int = 1
    column: int = 1

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_literal_expr(self)

    def to_dict(self) -> dict:
        return {
            'type': 'LiteralExpr',
            'value': self.value,
            'literal_type': self.literal_type,
            'line': self.line,
            'column': self.column
        }


@dataclass
class IdentifierExprNode(ExpressionNode):
    name: str
    line: int = 1
    column: int = 1

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_identifier_expr(self)

    def to_dict(self) -> dict:
        return {
            'type': 'IdentifierExpr',
            'name': self.name,
            'line': self.line,
            'column': self.column
        }


@dataclass
class IndexExprNode(ExpressionNode):
    array: ExpressionNode
    index: ExpressionNode
    line: int = 1
    column: int = 1

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_index_expr(self)

    def to_dict(self) -> dict:
        return {
            'type': 'IndexExpr',
            'array': self.array.to_dict(),
            'index': self.index.to_dict(),
            'line': self.line,
            'column': self.column
        }


@dataclass
class BinaryExprNode(ExpressionNode):
    left: ExpressionNode
    operator: str
    right: ExpressionNode
    line: int = 1
    column: int = 1

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_binary_expr(self)

    def to_dict(self) -> dict:
        return {
            'type': 'BinaryExpr',
            'operator': self.operator,
            'left': self.left.to_dict(),
            'right': self.right.to_dict(),
            'line': self.line,
            'column': self.column
        }


@dataclass
class UnaryExprNode(ExpressionNode):
    operator: str
    operand: ExpressionNode
    line: int = 1
    column: int = 1

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_unary_expr(self)

    def to_dict(self) -> dict:
        return {
            'type': 'UnaryExpr',
            'operator': self.operator,
            'operand': self.operand.to_dict(),
            'line': self.line,
            'column': self.column
        }


@dataclass
class CallExprNode(ExpressionNode):
    callee: IdentifierExprNode
    arguments: List[ExpressionNode]
    line: int = 1
    column: int = 1

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_call_expr(self)

    def to_dict(self) -> dict:
        return {
            'type': 'CallExpr',
            'callee': self.callee.to_dict(),
            'arguments': [arg.to_dict() for arg in self.arguments],
            'line': self.line,
            'column': self.column
        }


@dataclass
class AssignmentExprNode(ExpressionNode):
    target: ExpressionNode
    operator: str
    value: ExpressionNode
    line: int = 1
    column: int = 1

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_assignment_expr(self)

    def to_dict(self) -> dict:
        return {
            'type': 'AssignmentExpr',
            'target': self.target.to_dict(),
            'operator': self.operator,
            'value': self.value.to_dict(),
            'line': self.line,
            'column': self.column
        }


@dataclass
class BlockStmtNode(StatementNode):
    statements: List[StatementNode]
    line: int = 1
    column: int = 1

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_block_stmt(self)

    def to_dict(self) -> dict:
        return {
            'type': 'BlockStmt',
            'statements': [stmt.to_dict() for stmt in self.statements],
            'line': self.line,
            'column': self.column
        }


@dataclass
class ExprStmtNode(StatementNode):
    expression: ExpressionNode
    line: int = 1
    column: int = 1

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_expr_stmt(self)

    def to_dict(self) -> dict:
        return {
            'type': 'ExprStmt',
            'expression': self.expression.to_dict(),
            'line': self.line,
            'column': self.column
        }


@dataclass
class IfStmtNode(StatementNode):
    condition: ExpressionNode
    then_branch: StatementNode
    else_branch: Optional[StatementNode] = None
    line: int = 1
    column: int = 1

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_if_stmt(self)

    def to_dict(self) -> dict:
        result = {
            'type': 'IfStmt',
            'condition': self.condition.to_dict(),
            'then_branch': self.then_branch.to_dict(),
            'line': self.line,
            'column': self.column
        }
        if self.else_branch:
            result['else_branch'] = self.else_branch.to_dict()
        return result


@dataclass
class WhileStmtNode(StatementNode):
    condition: ExpressionNode
    body: StatementNode
    line: int = 1
    column: int = 1

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_while_stmt(self)

    def to_dict(self) -> dict:
        return {
            'type': 'WhileStmt',
            'condition': self.condition.to_dict(),
            'body': self.body.to_dict(),
            'line': self.line,
            'column': self.column
        }


@dataclass
class ForStmtNode(StatementNode):
    init: Optional[ExpressionNode]
    condition: Optional[ExpressionNode]
    update: Optional[ExpressionNode]
    body: StatementNode
    line: int = 1
    column: int = 1

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_for_stmt(self)

    def to_dict(self) -> dict:
        return {
            'type': 'ForStmt',
            'init': self.init.to_dict() if self.init else None,
            'condition': self.condition.to_dict() if self.condition else None,
            'update': self.update.to_dict() if self.update else None,
            'body': self.body.to_dict(),
            'line': self.line,
            'column': self.column
        }


@dataclass
class ReturnStmtNode(StatementNode):
    value: Optional[ExpressionNode]
    line: int = 1
    column: int = 1

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_return_stmt(self)

    def to_dict(self) -> dict:
        return {
            'type': 'ReturnStmt',
            'value': self.value.to_dict() if self.value else None,
            'line': self.line,
            'column': self.column
        }


@dataclass
class VarDeclStmtNode(StatementNode):
    var_type: str
    name: str
    initializer: Optional[ExpressionNode]
    line: int = 1
    column: int = 1

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_var_decl_stmt(self)

    def to_dict(self) -> dict:
        return {
            'type': 'VarDeclStmt',
            'var_type': self.var_type,
            'name': self.name,
            'initializer': self.initializer.to_dict() if self.initializer else None,
            'line': self.line,
            'column': self.column
        }

@dataclass
class ParamNode(ASTNode):
    param_type: str
    name: str
    line: int = 1
    column: int = 1

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_param(self)

    def to_dict(self) -> dict:
        return {
            'type': 'Param',
            'param_type': self.param_type,
            'name': self.name,
            'line': self.line,
            'column': self.column
        }


@dataclass
class FunctionDeclNode(DeclarationNode):
    return_type: str
    name: str
    parameters: List[ParamNode]
    body: Optional[BlockStmtNode]
    line: int = 1
    column: int = 1
    is_extern: bool = False

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_function_decl(self)

    def to_dict(self) -> dict:
        return {
            'type': 'FunctionDecl',
            'return_type': self.return_type,
            'name': self.name,
            'parameters': [p.to_dict() for p in self.parameters],
            'body': self.body.to_dict() if self.body else None,
            'is_extern': self.is_extern,
            'line': self.line,
            'column': self.column
        }

@dataclass
class StructDeclNode(DeclarationNode):
    name: str
    fields: List[VarDeclStmtNode]
    line: int = 1
    column: int = 1

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_struct_decl(self)

    def to_dict(self) -> dict:
        return {
            'type': 'StructDecl',
            'name': self.name,
            'fields': [f.to_dict() for f in self.fields],
            'line': self.line,
            'column': self.column
        }


@dataclass
class ProgramNode(ASTNode):
    declarations: List[DeclarationNode]
    line: int = 1
    column: int = 1

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_program(self)

    def to_dict(self) -> dict:
        return {
            'type': 'Program',
            'declarations': [d.to_dict() for d in self.declarations],
            'line': self.line,
            'column': self.column
        }


class ASTVisitor(ABC):
    @abstractmethod
    def visit_program(self, node: ProgramNode) -> Any: pass

    @abstractmethod
    def visit_function_decl(self, node: FunctionDeclNode) -> Any: pass

    @abstractmethod
    def visit_struct_decl(self, node: StructDeclNode) -> Any: pass

    @abstractmethod
    def visit_var_decl_stmt(self, node: VarDeclStmtNode) -> Any: pass

    @abstractmethod
    def visit_block_stmt(self, node: BlockStmtNode) -> Any: pass

    @abstractmethod
    def visit_expr_stmt(self, node: ExprStmtNode) -> Any: pass

    @abstractmethod
    def visit_if_stmt(self, node: IfStmtNode) -> Any: pass

    @abstractmethod
    def visit_while_stmt(self, node: WhileStmtNode) -> Any: pass

    @abstractmethod
    def visit_for_stmt(self, node: ForStmtNode) -> Any: pass

    @abstractmethod
    def visit_return_stmt(self, node: ReturnStmtNode) -> Any: pass

    @abstractmethod
    def visit_literal_expr(self, node: LiteralExprNode) -> Any: pass

    @abstractmethod
    def visit_identifier_expr(self, node: IdentifierExprNode) -> Any: pass

    @abstractmethod
    def visit_index_expr(self, node: IndexExprNode) -> Any: pass

    @abstractmethod
    def visit_binary_expr(self, node: BinaryExprNode) -> Any: pass

    @abstractmethod
    def visit_unary_expr(self, node: UnaryExprNode) -> Any: pass

    @abstractmethod
    def visit_call_expr(self, node: CallExprNode) -> Any: pass

    @abstractmethod
    def visit_assignment_expr(self, node: AssignmentExprNode) -> Any: pass

    @abstractmethod
    def visit_param(self, node: ParamNode) -> Any: pass