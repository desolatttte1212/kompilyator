from typing import List, Optional, Any
from ..lexer.scanner import Scanner
from ..lexer.tokens import Token, TokenType
from .ast_nodes import (
    ASTNode, ProgramNode, DeclarationNode, StatementNode, ExpressionNode,
    FunctionDeclNode, StructDeclNode, ParamNode, VarDeclStmtNode,
    BlockStmtNode, ExprStmtNode, IfStmtNode, WhileStmtNode, ForStmtNode,
    ReturnStmtNode, LiteralExprNode, IdentifierExprNode, BinaryExprNode,
    UnaryExprNode, CallExprNode, AssignmentExprNode, IndexExprNode, ASTVisitor
)


class ParseError(Exception):
    def __init__(self, message: str, line: int, column: int):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"[{line}:{column}] {message}")


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0
        self.errors: List[ParseError] = []
        self.max_errors = 10

    def parse(self) -> ProgramNode:
        try:
            return self.parse_program()
        except ParseError as e:
            self.errors.append(e)
            raise

    def parse_program(self) -> ProgramNode:
        line = self.peek().line if not self.is_at_end() else 1
        column = self.peek().column if not self.is_at_end() else 1
        declarations = []
        while not self.is_at_end() and self.peek().type != TokenType.EOF:
            try:
                decl = self.parse_declaration()
                if decl:
                    declarations.append(decl)
            except ParseError:
                self.synchronize()
        return ProgramNode(declarations=declarations, line=line, column=column)

    def parse_extern_decl(self) -> Optional[FunctionDeclNode]:
        extern_token = self.previous()

        if not self.match(TokenType.KW_FN):
            raise self.error("Expected 'fn' after 'extern'")

        name_token = self.consume(TokenType.IDENTIFIER, "Expected function name")
        self.consume(TokenType.LPAREN, "Expected '(' after function name")

        parameters = []
        if not self.check(TokenType.RPAREN):
            parameters = self.parse_parameters()

        self.consume(TokenType.RPAREN, "Expected ')' after parameters")

        return_type = "void"
        if self.match(TokenType.ASSIGN):
            type_token = self.consume(
                TokenType.KW_INT, TokenType.KW_FLOAT, TokenType.KW_BOOL,
                TokenType.KW_VOID, TokenType.IDENTIFIER,
                "Expected return type"
            )
            return_type = type_token.lexeme

        self.consume(TokenType.SEMICOLON, "Expected ';' after extern declaration")

        return FunctionDeclNode(
            return_type=return_type,
            name=name_token.lexeme,
            parameters=parameters,
            body=None,
            line=extern_token.line,
            column=extern_token.column,
            is_extern=True
        )

    def parse_declaration(self) -> Optional[DeclarationNode]:
        try:
            if self.match(TokenType.KW_FN):
                return self.parse_function_decl()
            elif self.match(TokenType.KW_EXTERN):  # 🆕 Новая ветка для extern
                return self.parse_extern_decl()
            elif self.match(TokenType.KW_STRUCT):
                return self.parse_struct_decl()
            elif self.match(TokenType.KW_INT, TokenType.KW_FLOAT, TokenType.KW_BOOL,
                            TokenType.KW_VOID, TokenType.IDENTIFIER):
                return self.parse_var_or_function()
            else:
                raise self.error("Expected declaration")
        except ParseError:
            self.synchronize()
            return None

    def parse_var_or_function(self) -> Optional[DeclarationNode]:
        self.previous()
        type_token = self.advance()
        var_type = type_token.lexeme

        if self.check(TokenType.IDENTIFIER):
            name_token = self.advance()
            name = name_token.lexeme

            if self.match(TokenType.LPAREN):
                self.previous()
                self.previous()
                return self.parse_function_decl()
            else:
                return self.finish_var_decl(var_type, name, name_token.line, name_token.column)

        raise self.error("Expected identifier after type")

    def parse_function_decl(self) -> FunctionDeclNode:
        fn_token = self.previous()
        name_token = self.consume(TokenType.IDENTIFIER, "Expected function name")
        self.consume(TokenType.LPAREN, "Expected '(' after function name")

        parameters = []
        if not self.check(TokenType.RPAREN):
            parameters = self.parse_parameters()

        self.consume(TokenType.RPAREN, "Expected ')' after parameters")

        return_type = "void"
        if self.match(TokenType.ASSIGN):
            type_token = self.consume(
                TokenType.KW_INT, TokenType.KW_FLOAT, TokenType.KW_BOOL,
                TokenType.KW_VOID, TokenType.IDENTIFIER,
                "Expected return type"
            )
            return_type = type_token.lexeme

        self.consume(TokenType.LBRACE, "Expected '{' after function signature")
        body = self.parse_block()

        return FunctionDeclNode(
            return_type=return_type,
            name=name_token.lexeme,
            parameters=parameters,
            body=body,
            line=fn_token.line,
            column=fn_token.column
        )

    def parse_parameters(self) -> List[ParamNode]:
        params = []
        while not self.check(TokenType.RPAREN):
            if self.match(TokenType.ELLIPSIS):
                break

            type_token = self.consume(
                TokenType.KW_INT, TokenType.KW_FLOAT, TokenType.KW_BOOL,
                TokenType.IDENTIFIER,
                "Expected parameter type"
            )
            name_token = self.consume(TokenType.IDENTIFIER, "Expected parameter name")
            params.append(ParamNode(
                param_type=type_token.lexeme,
                name=name_token.lexeme,
                line=type_token.line,
                column=type_token.column
            ))
            if not self.match(TokenType.COMMA):
                break
        return params

    def parse_struct_decl(self) -> StructDeclNode:
        struct_token = self.previous()
        name_token = self.consume(TokenType.IDENTIFIER, "Expected struct name")
        self.consume(TokenType.LBRACE, "Expected '{' after struct name")

        fields = []
        while not self.check(TokenType.RBRACE) and not self.is_at_end():
            try:
                field = self.parse_var_decl()
                if field:
                    fields.append(field)
            except ParseError:
                self.synchronize()

        self.consume(TokenType.RBRACE, "Expected '}' after struct fields")

        return StructDeclNode(
            name=name_token.lexeme,
            fields=fields,
            line=struct_token.line,
            column=struct_token.column
        )

    def finish_var_decl(self, var_type: str, name: str, line: int, column: int) -> VarDeclStmtNode:
        array_size = None
        if self.match(TokenType.LBRACKET):  # '['
            if self.check(TokenType.INT_LITERAL):
                size_token = self.advance()
                array_size = int(size_token.lexeme)
            else:
                raise self.error("Array size must be a constant integer")

            self.consume(TokenType.RBRACKET, "Expected ']'")

        initializer = None
        if self.match(TokenType.ASSIGN):
            initializer = self.parse_initializer()

        self.consume(TokenType.SEMICOLON, "Expected ';' after variable declaration")

        if array_size is not None:
            var_type = f"{var_type}[{array_size}]"

        return VarDeclStmtNode(
            var_type=var_type,
            name=name,
            initializer=initializer,
            line=line,
            column=column
        )

    def parse_initializer(self) -> Optional[ExpressionNode]:
        if self.match(TokenType.LBRACE):  # '{'
            elements = []
            while not self.check(TokenType.RBRACE):
                elements.append(self.parse_expression())
                if self.match(TokenType.COMMA):
                    if self.check(TokenType.RBRACE):
                        break
            self.consume(TokenType.RBRACE, "Expected '}' after initializer list")

            if elements:
                return elements[0]
            return LiteralExprNode(value=0, literal_type='int', line=self.previous().line,
                                   column=self.previous().column)
        else:
            return self.parse_expression()

    def parse_var_decl(self) -> Optional[VarDeclStmtNode]:
        try:
            type_token = self.consume(
                TokenType.KW_INT, TokenType.KW_FLOAT, TokenType.KW_BOOL,
                TokenType.IDENTIFIER,
                "Expected type"
            )
            name_token = self.consume(TokenType.IDENTIFIER, "Expected variable name")
            return self.finish_var_decl(type_token.lexeme, name_token.lexeme,
                                        type_token.line, type_token.column)
        except ParseError:
            self.synchronize()
            return None

    def parse_statement(self) -> Optional[StatementNode]:
        try:
            if self.match(TokenType.LBRACE):
                return self.parse_block()
            elif self.match(TokenType.KW_IF):
                return self.parse_if_stmt()
            elif self.match(TokenType.KW_WHILE):
                return self.parse_while_stmt()
            elif self.match(TokenType.KW_FOR):
                return self.parse_for_stmt()
            elif self.match(TokenType.KW_RETURN):
                return self.parse_return_stmt()
            elif self.check(TokenType.KW_INT, TokenType.KW_FLOAT, TokenType.KW_BOOL,
                            TokenType.IDENTIFIER):
                if self.is_var_declaration():
                    return self.parse_var_decl()
                else:
                    return self.parse_expr_stmt()
            elif self.match(TokenType.SEMICOLON):
                return ExprStmtNode(
                    expression=LiteralExprNode(value=None, literal_type='null',
                                               line=self.previous().line,
                                               column=self.previous().column),
                    line=self.previous().line,
                    column=self.previous().column
                )
            else:
                return self.parse_expr_stmt()
        except ParseError:
            self.synchronize()
            return None

    def is_var_declaration(self) -> bool:
        saved = self.current
        if self.check(TokenType.KW_INT, TokenType.KW_FLOAT, TokenType.KW_BOOL, TokenType.IDENTIFIER):
            self.advance()
            if self.check(TokenType.IDENTIFIER):
                self.advance()
                if self.check(TokenType.ASSIGN, TokenType.SEMICOLON, TokenType.LBRACKET):
                    self.current = saved
                    return True
        self.current = saved
        return False

    def parse_block(self) -> BlockStmtNode:
        brace_token = self.previous()
        statements = []
        while not self.check(TokenType.RBRACE) and not self.is_at_end():
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        self.consume(TokenType.RBRACE, "Expected '}' after block")
        return BlockStmtNode(statements=statements, line=brace_token.line, column=brace_token.column)

    def parse_if_stmt(self) -> IfStmtNode:
        if_token = self.previous()
        self.consume(TokenType.LPAREN, "Expected '(' after 'if'")
        condition = self.parse_expression()
        self.consume(TokenType.RPAREN, "Expected ')' after condition")
        then_branch = self.parse_statement()
        else_branch = None
        if self.match(TokenType.KW_ELSE):
            else_branch = self.parse_statement()
        return IfStmtNode(condition=condition, then_branch=then_branch,
                          else_branch=else_branch, line=if_token.line, column=if_token.column)

    def parse_while_stmt(self) -> WhileStmtNode:
        while_token = self.previous()
        self.consume(TokenType.LPAREN, "Expected '(' after 'while'")
        condition = self.parse_expression()
        self.consume(TokenType.RPAREN, "Expected ')' after condition")
        body = self.parse_statement()
        return WhileStmtNode(condition=condition, body=body,
                             line=while_token.line, column=while_token.column)

    def parse_for_stmt(self) -> ForStmtNode:
        for_token = self.previous()
        self.consume(TokenType.LPAREN, "Expected '(' after 'for'")
        init = None
        if not self.check(TokenType.SEMICOLON):
            if self.check(TokenType.KW_INT, TokenType.KW_FLOAT, TokenType.KW_BOOL, TokenType.IDENTIFIER):
                if self.is_var_declaration():
                    init = self.parse_var_decl()
                else:
                    init = self.parse_expr_stmt()
            else:
                init = self.parse_expr_stmt()
        self.consume(TokenType.SEMICOLON, "Expected ';' after loop init")
        condition = None
        if not self.check(TokenType.SEMICOLON):
            condition = self.parse_expression()
        self.consume(TokenType.SEMICOLON, "Expected ';' after loop condition")
        update = None
        if not self.check(TokenType.RPAREN):
            update = self.parse_expression()
        self.consume(TokenType.RPAREN, "Expected ')' after loop update")
        body = self.parse_statement()
        return ForStmtNode(init=init, condition=condition, update=update, body=body,
                           line=for_token.line, column=for_token.column)

    def parse_return_stmt(self) -> ReturnStmtNode:
        return_token = self.previous()
        value = None
        if not self.check(TokenType.SEMICOLON):
            value = self.parse_expression()
        self.consume(TokenType.SEMICOLON, "Expected ';' after return value")
        return ReturnStmtNode(value=value, line=return_token.line, column=return_token.column)

    def parse_expr_stmt(self) -> ExprStmtNode:
        expr = self.parse_expression()
        self.consume(TokenType.SEMICOLON, "Expected ';' after expression")
        return ExprStmtNode(expression=expr, line=expr.line, column=expr.column)

    def parse_expression(self) -> ExpressionNode:
        return self.parse_assignment()

    def parse_assignment(self) -> ExpressionNode:
        expr = self.parse_logical_or()
        if self.match(TokenType.ASSIGN):
            operator = self.previous().lexeme
            value = self.parse_assignment()
            expr = AssignmentExprNode(target=expr, operator=operator, value=value,
                                      line=expr.line, column=expr.column)
        return expr

    def parse_logical_or(self) -> ExpressionNode:
        expr = self.parse_logical_and()
        while self.match(TokenType.OR):
            operator = self.previous().lexeme
            right = self.parse_logical_and()
            expr = BinaryExprNode(left=expr, operator=operator, right=right,
                                  line=expr.line, column=expr.column)
        return expr

    def parse_logical_and(self) -> ExpressionNode:
        expr = self.parse_equality()
        while self.match(TokenType.AND):
            operator = self.previous().lexeme
            right = self.parse_equality()
            expr = BinaryExprNode(left=expr, operator=operator, right=right,
                                  line=expr.line, column=expr.column)
        return expr

    def parse_equality(self) -> ExpressionNode:
        expr = self.parse_relational()
        while self.match(TokenType.EQ, TokenType.NEQ):
            operator = self.previous().lexeme
            right = self.parse_relational()
            expr = BinaryExprNode(left=expr, operator=operator, right=right,
                                  line=expr.line, column=expr.column)
        return expr

    def parse_relational(self) -> ExpressionNode:
        expr = self.parse_additive()
        while self.match(TokenType.LT, TokenType.LTE, TokenType.GT, TokenType.GTE):
            operator = self.previous().lexeme
            right = self.parse_additive()
            expr = BinaryExprNode(left=expr, operator=operator, right=right,
                                  line=expr.line, column=expr.column)
        return expr

    def parse_additive(self) -> ExpressionNode:
        expr = self.parse_multiplicative()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            operator = self.previous().lexeme
            right = self.parse_multiplicative()
            expr = BinaryExprNode(left=expr, operator=operator, right=right,
                                  line=expr.line, column=expr.column)
        return expr

    def parse_multiplicative(self) -> ExpressionNode:
        expr = self.parse_unary()
        while self.match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            operator = self.previous().lexeme
            right = self.parse_unary()
            expr = BinaryExprNode(left=expr, operator=operator, right=right,
                                  line=expr.line, column=expr.column)
        return expr

    def parse_unary(self) -> ExpressionNode:
        if self.match(TokenType.MINUS, TokenType.NOT):
            operator = self.previous().lexeme
            right = self.parse_unary()
            return UnaryExprNode(operator=operator, operand=right,
                                 line=self.previous().line, column=self.previous().column)
        return self.parse_postfix()

    def parse_postfix(self) -> ExpressionNode:
        expr = self.parse_primary()

        while True:
            if self.match(TokenType.LPAREN):
                expr = self.finish_call(expr)
            elif self.match(TokenType.LBRACKET):
                index = self.parse_expression()
                self.consume(TokenType.RBRACKET, "Expected ']' after index")
                expr = IndexExprNode(array=expr, index=index,
                                     line=expr.line, column=expr.column)
            else:
                break

        return expr

    def finish_call(self, callee: ExpressionNode) -> CallExprNode:
        arguments = []
        if not self.check(TokenType.RPAREN):
            while True:
                arguments.append(self.parse_expression())
                if not self.match(TokenType.COMMA):
                    break
        self.consume(TokenType.RPAREN, "Expected ')' after arguments")
        callee_node = callee if isinstance(callee, IdentifierExprNode) else \
            IdentifierExprNode(name="unknown", line=callee.line, column=callee.column)
        return CallExprNode(callee=callee_node, arguments=arguments,
                            line=callee.line, column=callee.column)

    def parse_primary(self) -> ExpressionNode:
        if self.match(TokenType.BOOL_LITERAL):
            token = self.previous()
            value = token.value if token.value is not None else (token.lexeme == 'true')
            return LiteralExprNode(value=value, literal_type='bool',
                                   line=token.line, column=token.column)
        if self.match(TokenType.INT_LITERAL):
            token = self.previous()
            value = int(token.lexeme) if token.value is None else token.value
            return LiteralExprNode(value=value, literal_type='int',
                                   line=token.line, column=token.column)
        if self.match(TokenType.FLOAT_LITERAL):
            token = self.previous()
            value = float(token.lexeme) if token.value is None else token.value
            return LiteralExprNode(value=value, literal_type='float',
                                   line=token.line, column=token.column)
        if self.match(TokenType.STRING_LITERAL):
            token = self.previous()
            value = token.lexeme[1:-1] if token.value is None else token.value
            return LiteralExprNode(value=value, literal_type='string',
                                   line=token.line, column=token.column)
        if self.match(TokenType.IDENTIFIER):
            token = self.previous()
            return IdentifierExprNode(name=token.lexeme, line=token.line, column=token.column)
        if self.match(TokenType.LPAREN):
            expr = self.parse_expression()
            self.consume(TokenType.RPAREN, "Expected ')' after expression")
            return expr
        raise self.error("Expected expression")

    def match(self, *types: TokenType) -> bool:
        for type in types:
            if self.check(type):
                self.advance()
                return True
        return False

    def check(self, *types: TokenType) -> bool:
        if self.is_at_end():
            return False
        return self.peek().type in types

    def advance(self) -> Token:
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def is_at_end(self) -> bool:
        return self.peek().type == TokenType.EOF

    def peek(self) -> Token:
        return self.tokens[self.current]

    def previous(self) -> Token:
        return self.tokens[self.current - 1]

    def consume(self, *types: TokenType, message: str = "Unexpected token") -> Token:
        for type in types:
            if self.check(type):
                return self.advance()
        raise self.error(message)

    def error(self, message: str) -> ParseError:
        token = self.peek()
        if len(self.errors) >= self.max_errors:
            raise ParseError("Too many errors, parsing aborted", token.line, token.column)
        error = ParseError(message, token.line, token.column)
        self.errors.append(error)
        return error

    def synchronize(self):
        self.advance()
        while not self.is_at_end():
            if self.peek().type == TokenType.SEMICOLON:
                self.advance()
                return
            if self.peek().type in [
                TokenType.KW_FN, TokenType.KW_STRUCT, TokenType.KW_IF,
                TokenType.KW_WHILE, TokenType.KW_FOR, TokenType.KW_RETURN,
                TokenType.LBRACE, TokenType.RBRACE
            ]:
                return
            self.advance()

    def get_errors(self) -> List[ParseError]:
        return self.errors

    def has_errors(self) -> bool:
        return len(self.errors) > 0