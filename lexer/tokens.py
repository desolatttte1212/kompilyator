from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional


class TokenType(Enum):
    # Literals (LANG-4)
    INT_LITERAL = auto()
    FLOAT_LITERAL = auto()
    STRING_LITERAL = auto()
    BOOL_LITERAL = auto()

    # Identifiers & Keywords (LANG-2, LANG-3)
    IDENTIFIER = auto()
    KW_IF = auto()
    KW_ELSE = auto()
    KW_WHILE = auto()
    KW_FOR = auto()
    KW_INT = auto()
    KW_FLOAT = auto()
    KW_BOOL = auto()
    KW_RETURN = auto()
    KW_VOID = auto()
    KW_STRUCT = auto()
    KW_FN = auto()

    # Operators (LANG-5)
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()

    EQ = auto()  # ==
    NEQ = auto()  # !=
    LT = auto()  # <
    LTE = auto()  # <=
    GT = auto()  # >
    GTE = auto()  # >=

    AND = auto()  # &&
    OR = auto()  # ||
    NOT = auto()  # !
    ASSIGN = auto()  # =

    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    SEMICOLON = auto()
    COMMA = auto()

    # Special
    EOF = auto()
    ERROR = auto()


@dataclass
class Token:
    type: TokenType
    lexeme: str
    line: int
    column: int
    value: Any = None

    def __str__(self):
        if self.value is not None:
            return f"{self.line}:{self.column} {self.type.name} \"{self.lexeme}\" {self.value}"
        return f"{self.line}:{self.column} {self.type.name} \"{self.lexeme}\""