from typing import List, Optional, Any
from .tokens import Token, TokenType

KEYWORDS = {
    "if": TokenType.KW_IF, "else": TokenType.KW_ELSE, "while": TokenType.KW_WHILE,
    "for": TokenType.KW_FOR, "int": TokenType.KW_INT, "float": TokenType.KW_FLOAT,
    "bool": TokenType.KW_BOOL, "return": TokenType.KW_RETURN, "void": TokenType.KW_VOID,
    "struct": TokenType.KW_STRUCT, "fn": TokenType.KW_FN
}


class Scanner:
    def __init__(self, source: str):
        self.source = source
        self.tokens: List[Token] = []
        self.start = 0
        self.current = 0
        self.line = 1
        self.column = 1
        self.current_col = 1

    def is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def next_token(self) -> Token:
        while not self.is_at_end():
            self.start = self.current
            c = self._advance()

            if c == ' ' or c == '\t':
                continue
            elif c == '\n':
                self.line += 1
                self.current_col = 1
                continue
            elif c == '\r':
                if not self.is_at_end() and self.source[self.current] == '\n':
                    self._advance()
                self.line += 1
                self.current_col = 1
                continue

            elif c == '/':
                if self._match('/'):
                    while not self.is_at_end() and self.peek() != '\n':
                        self._advance()
                    continue
                elif self._match('*'):
                    while not self.is_at_end():
                        if self.peek() == '*' and self.peek_next() == '/':
                            self._advance()
                            self._advance()
                            break
                        if self.peek() == '\n':
                            self.line += 1
                            self.current_col = 1
                        self._advance()
                    continue
                else:
                    return self._make_token(TokenType.SLASH)

            elif c == '(':
                return self._make_token(TokenType.LPAREN)
            elif c == ')':
                return self._make_token(TokenType.RPAREN)
            elif c == '{':
                return self._make_token(TokenType.LBRACE)
            elif c == '}':
                return self._make_token(TokenType.RBRACE)
            elif c == ';':
                return self._make_token(TokenType.SEMICOLON)
            elif c == ',':
                return self._make_token(TokenType.COMMA)
            elif c == '+':
                return self._make_token(TokenType.PLUS)
            elif c == '-':
                return self._make_token(TokenType.MINUS)
            elif c == '*':
                return self._make_token(TokenType.STAR)
            elif c == '%':
                return self._make_token(TokenType.PERCENT)

            elif c == '=':
                return self._make_token(TokenType.EQ if self._match('=') else TokenType.ASSIGN)

            elif c == '!':
                if self._match('='):
                    return self._make_token(TokenType.NEQ)
                else:
                    return self._make_token(TokenType.NOT)

            elif c == '<':
                return self._make_token(TokenType.LTE if self._match('=') else TokenType.LT)
            elif c == '>':
                return self._make_token(TokenType.GTE if self._match('=') else TokenType.GT)

            elif c == '&':
                if self._match('&'):
                    return self._make_token(TokenType.AND)
                else:
                    self._error("Ожидался '&' после '&'")
                    return self._make_token(TokenType.ERROR)
            elif c == '|':
                if self._match('|'):
                    return self._make_token(TokenType.OR)
                else:
                    self._error("Ожидался '|' после '|'")
                    return self._make_token(TokenType.ERROR)

            elif c == '"':
                return self._string()

            elif c.isalpha() or c == '_':
                return self._identifier()

            elif c.isdigit():
                return self._number()

            else:
                self._error(f"Неожиданный символ: {c}")
                return self._make_token(TokenType.ERROR)

        return Token(TokenType.EOF, "", self.line, self.current_col)

    def peek_token(self) -> Token:
        return self.tokens[-1] if self.tokens else Token(TokenType.EOF, "", self.line, self.current_col)

    def scan_tokens(self) -> List[Token]:
        self.tokens = []

        if not self.is_at_end() and self.source[self.current] == '\ufeff':
            self._advance()
            self.start = self.current

        while True:
            token = self.next_token()
            self.tokens.append(token)
            if token.type == TokenType.EOF:
                break
        return self.tokens

    def _make_token(self, type: TokenType, value: Any = None) -> Token:
        text = self.source[self.start:self.current]
        col = self.start_col_save()
        return Token(type, text, self.line, col, value)

    def _string(self) -> Token:
        while not self.is_at_end() and self.peek() != '"':
            if self.peek() == '\n':
                self._error("Незавершенная строка (перенос строки внутри)")
                break

            if self.peek() == '\\':
                self._advance()
                if not self.is_at_end():
                    self._advance()
            else:
                self._advance()

        if self.is_at_end() and self.peek() != '"':
            self._error("Незавершенная строка (конец файла)")
        else:
            self._advance()

        lexeme = self.source[self.start:self.current]
        content = lexeme[1:-1] if len(lexeme) >= 2 else ""
        try:
            value = content.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')
        except:
            value = content

        return self._make_token(TokenType.STRING_LITERAL, value)

    def _identifier(self) -> Token:
        while not self.is_at_end() and (self.peek().isalnum() or self.peek() == '_'):
            self._advance()

        text = self.source[self.start:self.current]

        if text == 'true':
            return self._make_token(TokenType.BOOL_LITERAL, True)
        elif text == 'false':
            return self._make_token(TokenType.BOOL_LITERAL, False)
        else:
            token_type = KEYWORDS.get(text)
            if token_type is None:
                token_type = TokenType.IDENTIFIER
            return self._make_token(token_type)

    def _number(self) -> Token:
        while not self.is_at_end() and self.peek().isdigit():
            self._advance()

        if self.peek() == '.' and self.peek_next().isdigit():
            self._advance()
            while not self.is_at_end() and self.peek().isdigit():
                self._advance()

        value_str = self.source[self.start:self.current]
        if '.' in value_str:
            return self._make_token(TokenType.FLOAT_LITERAL, float(value_str))
        else:
            return self._make_token(TokenType.INT_LITERAL, int(value_str))

    def _advance(self) -> str:
        self.current += 1
        self.current_col += 1
        return self.source[self.current - 1]

    def _match(self, expected: str) -> bool:
        if self.is_at_end(): return False
        if self.source[self.current] != expected: return False
        self.current += 1
        self.current_col += 1
        return True

    def peek(self) -> str:
        if self.is_at_end(): return '\0'
        return self.source[self.current]

    def peek_next(self) -> str:
        if self.current + 1 >= len(self.source): return '\0'
        return self.source[self.current + 1]

    def _error(self, message: str):
        import sys
        sys.stderr.write(f"Error at line {self.line}, column {self.current_col}: {message}\n")
        sys.stderr.flush()

    def start_col_save(self) -> int:
        return self.current_col - (self.current - self.start)