from enum import Enum, auto
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


class SemanticErrorType(Enum):
    UNDECLARED_IDENTIFIER = auto()
    DUPLICATE_DECLARATION = auto()
    USE_BEFORE_DECLARATION = auto()

    TYPE_MISMATCH = auto()
    INVALID_TYPE = auto()
    INCOMPATIBLE_TYPES = auto()

    FUNCTION_NOT_FOUND = auto()
    ARG_COUNT_MISMATCH = auto()
    ARG_TYPE_MISMATCH = auto()
    INVALID_RETURN_TYPE = auto()
    MISSING_RETURN = auto()

    INVALID_OPERATOR = auto()
    INVALID_CONDITION_TYPE = auto()
    INVALID_ASSIGNMENT_TARGET = auto()

    OUT_OF_SCOPE = auto()
    SHADOWING_WARNING = auto()

    UNKNOWN_FIELD = auto()
    DUPLICATE_FIELD = auto()
    INVALID_STRUCT_USAGE = auto()

ERROR_TEMPLATES: Dict[SemanticErrorType, str] = {
    SemanticErrorType.UNDECLARED_IDENTIFIER:
        "undeclared identifier '{name}'",

    SemanticErrorType.DUPLICATE_DECLARATION:
        "duplicate declaration of '{name}' in same scope",

    SemanticErrorType.USE_BEFORE_DECLARATION:
        "variable '{name}' used before declaration",

    SemanticErrorType.TYPE_MISMATCH:
        "type mismatch: expected {expected}, got {actual}",

    SemanticErrorType.INVALID_TYPE:
        "invalid type '{type_name}'",

    SemanticErrorType.INCOMPATIBLE_TYPES:
        "incompatible types in operation: {type1} and {type2}",

    SemanticErrorType.FUNCTION_NOT_FOUND:
        "function '{name}' not found",

    SemanticErrorType.ARG_COUNT_MISMATCH:
        "argument count mismatch: expected {expected}, got {actual}",

    SemanticErrorType.ARG_TYPE_MISMATCH:
        "argument type mismatch for parameter '{param}': expected {expected}, got {actual}",

    SemanticErrorType.INVALID_RETURN_TYPE:
        "return type mismatch: expected {expected}, got {actual}",

    SemanticErrorType.MISSING_RETURN:
        "function '{name}' missing return statement",

    SemanticErrorType.INVALID_OPERATOR:
        "invalid operator '{op}' for types {type1} and {type2}",

    SemanticErrorType.INVALID_CONDITION_TYPE:
        "condition must be bool, got {actual}",

    SemanticErrorType.INVALID_ASSIGNMENT_TARGET:
        "invalid assignment target: '{name}' is not mutable",

    SemanticErrorType.OUT_OF_SCOPE:
        "'{name}' is out of scope",

    SemanticErrorType.SHADOWING_WARNING:
        "'{name}' shadows declaration in outer scope",

    SemanticErrorType.UNKNOWN_FIELD:
        "unknown field '{field}' in struct '{struct}'",

    SemanticErrorType.DUPLICATE_FIELD:
        "duplicate field '{field}' in struct '{struct}'",

    SemanticErrorType.INVALID_STRUCT_USAGE:
        "invalid usage of struct '{name}'",
}

@dataclass
class SemanticError:
    error_type: SemanticErrorType
    message: str
    line: int
    column: int
    file: str = ""
    context: str = ""
    expected: Optional[str] = None
    actual: Optional[str] = None
    suggestion: Optional[str] = None
    name: Optional[str] = None

    def __post_init__(self):
        if '{name}' in self.message and self.name:
            self.message = self.message.replace('{name}', self.name)
        if '{expected}' in self.message and self.expected:
            self.message = self.message.replace('{expected}', self.expected)
        if '{actual}' in self.message and self.actual:
            self.message = self.message.replace('{actual}', self.actual)
        if '{type1}' in self.message and self.expected:
            self.message = self.message.replace('{type1}', self.expected)
        if '{type2}' in self.message and self.actual:
            self.message = self.message.replace('{type2}', self.actual)
        if '{op}' in self.message:
            self.message = self.message.replace('{op}', self.actual or '?')
        if '{field}' in self.message and self.name:
            self.message = self.message.replace('{field}', self.name)
        if '{struct}' in self.message and self.context:
            self.message = self.message.replace('{struct}', self.context)
        if '{param}' in self.message and self.name:
            self.message = self.message.replace('{param}', self.name)
        if '{type_name}' in self.message and self.actual:
            self.message = self.message.replace('{type_name}', self.actual)

    def __str__(self) -> str:
        parts = []

        parts.append(f"semantic error: {self.message}")

        if self.file:
            parts.append(f"  --> {self.file}:{self.line}:{self.column}")
        else:
            parts.append(f"  --> line {self.line}:{self.column}")

        if self.context:
            parts.append(f"   | in {self.context}")

        if self.expected and self.actual:
            parts.append(f"   = expected: {self.expected}")
            parts.append(f"   = found: {self.actual}")
        elif self.expected:
            parts.append(f"   = expected: {self.expected}")
        elif self.actual:
            parts.append(f"   = found: {self.actual}")

        if self.suggestion:
            parts.append(f"   = hint: {self.suggestion}")

        return "\n".join(parts)

    def to_dict(self) -> dict:
        return {
            'error_type': self.error_type.name,
            'message': self.message,
            'line': self.line,
            'column': self.column,
            'file': self.file,
            'context': self.context,
            'expected': self.expected,
            'actual': self.actual,
            'suggestion': self.suggestion,
        }

    @classmethod
    def undeclared(cls, name: str, line: int, column: int,
                   file: str = "", context: str = "",
                   suggestion: Optional[str] = None) -> 'SemanticError':
        return cls(
            error_type=SemanticErrorType.UNDECLARED_IDENTIFIER,
            message=ERROR_TEMPLATES[SemanticErrorType.UNDECLARED_IDENTIFIER],
            line=line, column=column, file=file, context=context,
            name=name, suggestion=suggestion
        )

    @classmethod
    def duplicate(cls, name: str, line: int, column: int,
                  file: str = "", context: str = "") -> 'SemanticError':
        return cls(
            error_type=SemanticErrorType.DUPLICATE_DECLARATION,
            message=ERROR_TEMPLATES[SemanticErrorType.DUPLICATE_DECLARATION],
            line=line, column=column, file=file, context=context,
            name=name
        )

    @classmethod
    def type_mismatch(cls, expected: str, actual: str,
                      line: int, column: int, file: str = "",
                      context: str = "", suggestion: Optional[str] = None) -> 'SemanticError':
        return cls(
            error_type=SemanticErrorType.TYPE_MISMATCH,
            message=ERROR_TEMPLATES[SemanticErrorType.TYPE_MISMATCH],
            line=line, column=column, file=file, context=context,
            expected=expected, actual=actual, suggestion=suggestion
        )

    @classmethod
    def arg_count_mismatch(cls, expected: int, actual: int,
                           line: int, column: int, file: str = "",
                           context: str = "") -> 'SemanticError':
        return cls(
            error_type=SemanticErrorType.ARG_COUNT_MISMATCH,
            message=ERROR_TEMPLATES[SemanticErrorType.ARG_COUNT_MISMATCH],
            line=line, column=column, file=file, context=context,
            expected=str(expected), actual=str(actual)
        )

    @classmethod
    def arg_type_mismatch(cls, param: str, expected: str, actual: str,
                          line: int, column: int, file: str = "",
                          context: str = "") -> 'SemanticError':
        return cls(
            error_type=SemanticErrorType.ARG_TYPE_MISMATCH,
            message=ERROR_TEMPLATES[SemanticErrorType.ARG_TYPE_MISMATCH],
            line=line, column=column, file=file, context=context,
            name=param, expected=expected, actual=actual
        )

    @classmethod
    def invalid_return_type(cls, expected: str, actual: str,
                            line: int, column: int, file: str = "",
                            context: str = "") -> 'SemanticError':
        return cls(
            error_type=SemanticErrorType.INVALID_RETURN_TYPE,
            message=ERROR_TEMPLATES[SemanticErrorType.INVALID_RETURN_TYPE],
            line=line, column=column, file=file, context=context,
            expected=expected, actual=actual
        )

    @classmethod
    def invalid_condition(cls, actual: str, line: int, column: int,
                          file: str = "", context: str = "") -> 'SemanticError':
        return cls(
            error_type=SemanticErrorType.INVALID_CONDITION_TYPE,
            message=ERROR_TEMPLATES[SemanticErrorType.INVALID_CONDITION_TYPE],
            line=line, column=column, file=file, context=context,
            actual=actual
        )

    @classmethod
    def invalid_operator(cls, op: str, type1: str, type2: str,
                         line: int, column: int, file: str = "",
                         context: str = "") -> 'SemanticError':
        return cls(
            error_type=SemanticErrorType.INVALID_OPERATOR,
            message=ERROR_TEMPLATES[SemanticErrorType.INVALID_OPERATOR],
            line=line, column=column, file=file, context=context,
            expected=type1, actual=type2
        )

    @classmethod
    def unknown_field(cls, field: str, struct: str,
                      line: int, column: int, file: str = "",
                      context: str = "") -> 'SemanticError':
        return cls(
            error_type=SemanticErrorType.UNKNOWN_FIELD,
            message=ERROR_TEMPLATES[SemanticErrorType.UNKNOWN_FIELD],
            line=line, column=column, file=file, context=context,
            name=field
        )

class ErrorCollector:

    def __init__(self, max_errors: int = 100):
        self._errors: List[SemanticError] = []
        self._max_errors = max_errors
        self._warnings: List[SemanticError] = []

    def add_error(self, error: SemanticError) -> None:
        if len(self._errors) >= self._max_errors:
            return

        self._errors.append(error)

    def add_warning(self, error: SemanticError) -> None:
        self._warnings.append(error)

    def has_errors(self) -> bool:
        return len(self._errors) > 0

    def has_warnings(self) -> bool:
        return len(self._warnings) > 0

    @property
    def errors(self) -> List[SemanticError]:
        return self._errors.copy()

    @property
    def warnings(self) -> List[SemanticError]:
        return self._warnings.copy()

    @property
    def error_count(self) -> int:
        return len(self._errors)

    @property
    def warning_count(self) -> int:
        return len(self._warnings)

    def clear(self) -> None:
        self._errors.clear()
        self._warnings.clear()

    def __str__(self) -> str:
        if not self._errors and not self._warnings:
            return "No errors or warnings."

        lines = []

        if self._errors:
            lines.append(f"=== {len(self._errors)} Error(s) ===")
            for i, error in enumerate(self._errors, 1):
                lines.append(f"\n[{i}] {error}")

        if self._warnings:
            lines.append(f"\n=== {len(self._warnings)} Warning(s) ===")
            for i, warning in enumerate(self._warnings, 1):
                lines.append(f"\n[{i}] {warning}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            'errors': [e.to_dict() for e in self._errors],
            'warnings': [w.to_dict() for w in self._warnings],
            'error_count': len(self._errors),
            'warning_count': len(self._warnings),
        }

    def print_report(self, file: str = "") -> None:
        import sys

        if not self._errors and not self._warnings:
            print("[SUCCESS] No semantic errors found.")
            return

        if self._errors:
            print(f"\n[ERROR] Semantic analysis failed with {len(self._errors)} error(s):",
                  file=sys.stderr)
            for error in self._errors:
                print(f"\n{error}", file=sys.stderr)

        if self._warnings:
            print(f"\n[WARNING] {len(self._warnings)} warning(s):", file=sys.stderr)
            for warning in self._warnings:
                print(f"\n{warning}", file=sys.stderr)

        print(f"\n--- Summary: {len(self._errors)} errors, {len(self._warnings)} warnings ---",
              file=sys.stderr)

def format_type_name(type_obj) -> str:
    if type_obj is None:
        return "void"
    if isinstance(type_obj, str):
        return type_obj
    if hasattr(type_obj, '__str__'):
        return str(type_obj)
    return repr(type_obj)


def suggest_similar_names(name: str, available_names: List[str],
                          max_suggestions: int = 3) -> Optional[str]:
    def levenshtein_distance(s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    similar = []
    for available in available_names:
        distance = levenshtein_distance(name.lower(), available.lower())
        if distance <= 2 and distance > 0:
            similar.append((distance, available))

    if not similar:
        return None

    similar.sort(key=lambda x: x[0])
    suggestions = [name for _, name in similar[:max_suggestions]]

    if len(suggestions) == 1:
        return f"did you mean '{suggestions[0]}'?"
    else:
        quoted_suggestions = ["'" + s + "'" for s in suggestions]
        suggestions_str = ', '.join(quoted_suggestions)
        return f"did you mean one of: {suggestions_str}?"