from enum import Enum, auto
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field
from .type_system import Type, PrimitiveType, StructType, FunctionType, Parameter, Types

class SymbolKind(Enum):
    VARIABLE = auto()
    PARAMETER = auto()
    FUNCTION = auto()
    STRUCT = auto()
    FIELD = auto()


@dataclass
class Symbol:
    name: str
    kind: SymbolKind
    type_: Type
    line: int
    column: int

    return_type: Optional[Type] = None
    parameters: List[Parameter] = field(default_factory=list)
    is_defined: bool = False

    fields: Dict[str, 'Symbol'] = field(default_factory=dict)

    is_mutable: bool = True

    def __post_init__(self):
        if self.kind == SymbolKind.FUNCTION:
            if self.return_type is None:
                raise ValueError(f"Function '{self.name}' must have return_type")

    def __str__(self) -> str:
        if self.kind == SymbolKind.FUNCTION:
            params = ', '.join(str(p) for p in self.parameters)
            return f"fn {self.name}({params}) -> {self.return_type}"
        elif self.kind == SymbolKind.STRUCT:
            fields = ', '.join(f"{k}: {v.type_}" for k, v in self.fields.items())
            return f"struct {self.name} {{ {fields} }}"
        else:
            return f"{self.kind.name.lower()} {self.name}: {self.type_}"

    def __repr__(self) -> str:
        return f"Symbol('{self.name}', kind={self.kind.name}, type={self.type_})"

@dataclass
class Scope:
    name: str
    parent: Optional['Scope'] = None
    depth: int = 0
    symbols: Dict[str, Symbol] = field(default_factory=dict)

    def insert(self, symbol: Symbol) -> bool:
        if symbol.name in self.symbols:
            return False
        self.symbols[symbol.name] = symbol
        return True

    def lookup(self, name: str) -> Optional[Symbol]:
        return self.symbols.get(name)

    def __str__(self) -> str:
        return f"Scope('{self.name}', depth={self.depth}, symbols={list(self.symbols.keys())})"


class SymbolTable:
    def __init__(self):
        self._global_scope = Scope(name='global', depth=0)
        self._current_scope: Scope = self._global_scope
        self._scope_stack: List[Scope] = [self._global_scope]

    def enter_scope(self, name: str = "") -> Scope:
        new_depth = self._current_scope.depth + 1
        new_scope = Scope(
            name=name or f"scope_{new_depth}",
            parent=self._current_scope,
            depth=new_depth
        )
        self._scope_stack.append(new_scope)
        self._current_scope = new_scope
        return new_scope

    def exit_scope(self) -> Scope:
        if self._current_scope == self._global_scope:
            raise RuntimeError("Cannot exit global scope")

        self._scope_stack.pop()
        self._current_scope = self._scope_stack[-1]
        return self._current_scope

    def insert(self, name: str, symbol: Symbol) -> bool:
        return self._current_scope.insert(symbol)

    def lookup(self, name: str) -> Optional[Symbol]:
        scope = self._current_scope
        while scope is not None:
            symbol = scope.lookup(name)
            if symbol is not None:
                return symbol
            scope = scope.parent
        return None

    def lookup_local(self, name: str) -> Optional[Symbol]:
        return self._current_scope.lookup(name)

    @property
    def current_scope(self) -> Scope:
        return self._current_scope

    @property
    def global_scope(self) -> Scope:
        return self._global_scope

    @property
    def depth(self) -> int:
        return self._current_scope.depth

    def is_global_scope(self) -> bool:
        return self._current_scope == self._global_scope

    def get_scope_chain(self) -> List[Scope]:
        chain = []
        scope = self._current_scope
        while scope is not None:
            chain.append(scope)
            scope = scope.parent
        return chain

    def dump(self, indent: str = "") -> str:
        lines = []

        def dump_scope(scope: Scope, prefix: str):
            lines.append(f"{prefix}{scope.name} (depth={scope.depth}):")
            for name, symbol in scope.symbols.items():
                lines.append(f"{prefix}  - {symbol}")
                if symbol.kind == SymbolKind.STRUCT and symbol.fields:
                    for field_name, field_symbol in symbol.fields.items():
                        lines.append(f"{prefix}    . {field_symbol}")

        for scope in reversed(self.get_scope_chain()):
            dump_scope(scope, indent)

        return "\n".join(lines)

    def to_dict(self) -> dict:
        result = {}

        for scope in reversed(self.get_scope_chain()):
            scope_data = {}
            for name, symbol in scope.symbols.items():
                symbol_data = {
                    'name': symbol.name,
                    'kind': symbol.kind.name,
                    'type': str(symbol.type_),
                    'line': symbol.line,
                    'column': symbol.column,
                    'mutable': symbol.is_mutable,
                }

                if symbol.kind == SymbolKind.FUNCTION:
                    symbol_data['return_type'] = str(symbol.return_type)
                    symbol_data['parameters'] = [
                        {'name': p.name, 'type': str(p.type_)}
                        for p in symbol.parameters
                    ]
                    symbol_data['is_defined'] = symbol.is_defined

                if symbol.kind == SymbolKind.STRUCT:
                    symbol_data['fields'] = {
                        k: str(v.type_) for k, v in symbol.fields.items()
                    }

                scope_data[name] = symbol_data

            result[scope.name] = scope_data

        return result

    def insert_variable(self, name: str, type_: Type, line: int, column: int,
                        mutable: bool = True) -> bool:
        symbol = Symbol(
            name=name,
            kind=SymbolKind.VARIABLE,
            type_=type_,
            line=line,
            column=column,
            is_mutable=mutable
        )
        return self.insert(name, symbol)

    def insert_parameter(self, name: str, type_: Type, line: int, column: int) -> bool:
        symbol = Symbol(
            name=name,
            kind=SymbolKind.PARAMETER,
            type_=type_,
            line=line,
            column=column
        )
        return self.insert(name, symbol)

    def insert_function(self, name: str, return_type: Type,
                        parameters: List[Parameter], line: int, column: int,
                        is_defined: bool = False) -> bool:
        symbol = Symbol(
            name=name,
            kind=SymbolKind.FUNCTION,
            type_=FunctionType(return_type=return_type,
                               param_types=[p.type_ for p in parameters],
                               param_names=[p.name for p in parameters]),
            line=line,
            column=column,
            return_type=return_type,
            parameters=parameters,
            is_defined=is_defined
        )
        return self.insert(name, symbol)

    def insert_struct(self, name: str, line: int, column: int) -> bool:
        symbol = Symbol(
            name=name,
            kind=SymbolKind.STRUCT,
            type_=StructType(name=name),
            line=line,
            column=column
        )
        return self.insert(name, symbol)

    def add_struct_field(self, struct_name: str, field_name: str,
                         field_type: Type, line: int, column: int) -> bool:
        symbol = self.lookup(struct_name)
        if symbol is None or symbol.kind != SymbolKind.STRUCT:
            return False

        if field_name in symbol.fields:
            return False

        field_symbol = Symbol(
            name=field_name,
            kind=SymbolKind.FIELD,
            type_=field_type,
            line=line,
            column=column
        )
        symbol.fields[field_name] = field_symbol
        symbol.type_.fields[field_name] = field_type
        return True

    def mark_function_defined(self, name: str) -> bool:
        symbol = self._global_scope.lookup(name)
        if symbol is None or symbol.kind != SymbolKind.FUNCTION:
            return False
        symbol.is_defined = True
        return True

class ScopeGuard:
    def __init__(self, symbol_table: SymbolTable, scope_name: str = ""):
        self.symbol_table = symbol_table
        self.scope_name = scope_name
        self.entered_scope: Optional[Scope] = None

    def __enter__(self) -> Scope:
        self.entered_scope = self.symbol_table.enter_scope(self.scope_name)
        return self.entered_scope

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.symbol_table.exit_scope()
        return False