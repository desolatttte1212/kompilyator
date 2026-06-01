from abc import ABC, abstractmethod
from typing import Optional, Union
from dataclasses import dataclass, field

class Operand(ABC):
    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def __eq__(self, other) -> bool:
        pass

    @abstractmethod
    def __hash__(self) -> int:
        pass


@dataclass(frozen=True)
class Temporary(Operand):
    id: int

    def __str__(self) -> str:
        return f"t{self.id}"

    def __repr__(self) -> str:
        return f"Temporary({self.id})"

    def __eq__(self, other) -> bool:
        return isinstance(other, Temporary) and self.id == other.id

    def __hash__(self) -> int:
        return hash(('Temporary', self.id))


@dataclass(frozen=True)
class Variable(Operand):
    name: str
    type_name: Optional[str] = None
    offset: Optional[int] = None

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Variable('{self.name}')"

    def __eq__(self, other) -> bool:
        return isinstance(other, Variable) and self.name == other.name

    def __hash__(self) -> int:
        return hash(('Variable', self.name))


@dataclass(frozen=True)
class Literal(Operand):
    value: Union[int, float, bool, str]

    def __str__(self) -> str:
        if isinstance(self.value, bool):
            return 'true' if self.value else 'false'
        elif isinstance(self.value, str):
            return f'"{self.value}"'
        else:
            return str(self.value)

    def __repr__(self) -> str:
        return f"Literal({repr(self.value)})"

    def __eq__(self, other) -> bool:
        return isinstance(other, Literal) and self.value == other.value

    def __hash__(self) -> int:
        return hash(('Literal', self.value))


@dataclass(frozen=True)
class Label(Operand):
    name: str

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Label('{self.name}')"

    def __eq__(self, other) -> bool:
        return isinstance(other, Label) and self.name == other.name

    def __hash__(self) -> int:
        return hash(('Label', self.name))


@dataclass(frozen=True)
class MemoryLocation(Operand):
    address: Operand
    offset: int = 0

    def __str__(self) -> str:
        if self.offset == 0:
            return f"[{self.address}]"
        elif self.offset > 0:
            return f"[{self.address}+{self.offset}]"
        else:
            return f"[{self.address}{self.offset}]"

    def __repr__(self) -> str:
        return f"MemoryLocation({repr(self.address)}, offset={self.offset})"

    def __eq__(self, other) -> bool:
        return (isinstance(other, MemoryLocation) and
                self.address == other.address and
                self.offset == other.offset)

    def __hash__(self) -> int:
        return hash(('MemoryLocation', self.address, self.offset))

class OperandFactory:
    _temp_counter = 0

    @classmethod
    def new_temporary(cls) -> Temporary:
        temp = Temporary(cls._temp_counter)
        cls._temp_counter += 1
        return temp

    @classmethod
    def reset_temp_counter(cls):
        cls._temp_counter = 0

    @classmethod
    def variable(cls, name: str, type_name: Optional[str] = None) -> Variable:
        return Variable(name=name, type_name=type_name)

    @classmethod
    def literal(cls, value: Union[int, float, bool, str]) -> Literal:
        return Literal(value=value)

    @classmethod
    def label(cls, name: str) -> Label:
        return Label(name=name)

    @classmethod
    def memory(cls, address: Operand, offset: int = 0) -> MemoryLocation:
        return MemoryLocation(address=address, offset=offset)

    @classmethod
    def from_value(cls, value) -> Operand:
        if isinstance(value, Operand):
            return value
        elif isinstance(value, (int, float, bool, str)):
            return cls.literal(value)
        else:
            raise ValueError(f"Cannot create operand from {type(value)}: {value}")

def is_immediate(operand: Operand) -> bool:
    return isinstance(operand, Literal)


def is_temporary(operand: Operand) -> bool:
    return isinstance(operand, Temporary)


def is_variable(operand: Operand) -> bool:
    return isinstance(operand, Variable)


def is_memory(operand: Operand) -> bool:
    return isinstance(operand, MemoryLocation)


def is_label(operand: Operand) -> bool:
    return isinstance(operand, Label)