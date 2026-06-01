from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field


class Type(ABC):

    @abstractmethod
    def is_compatible_with(self, other: 'Type') -> bool:
        pass

    @abstractmethod
    def __eq__(self, other) -> bool:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass


class PrimitiveType(Type):

    _instances: Dict[str, 'PrimitiveType'] = {}

    def __new__(cls, name: str):
        if name not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[name] = instance
        return cls._instances[name]

    def __init__(self, name: str):
        if hasattr(self, '_initialized'):
            return
        self._name = name
        self._initialized = True

    @property
    def name(self) -> str:
        return self._name

    @property
    def size(self) -> int:
        """Размер типа в байтах."""
        sizes = {'int': 4, 'float': 8, 'bool': 4, 'void': 0, 'string': 8}
        return sizes.get(self._name, 4)

    def is_compatible_with(self, other: Type) -> bool:
        if not isinstance(other, PrimitiveType):
            return False
        if self._name == other._name:
            return True
        if self._name == 'float' and other._name == 'int':
            return True
        return False

    def can_be_assigned_from(self, other: Type) -> bool:
        return other.is_compatible_with(self)

    def __eq__(self, other) -> bool:
        if not isinstance(other, PrimitiveType):
            return False
        return self._name == other._name

    def __hash__(self) -> int:
        return hash(('PrimitiveType', self._name))

    def __str__(self) -> str:
        return self._name

    def __repr__(self) -> str:
        return f"PrimitiveType('{self._name}')"


class Types:

    INT = PrimitiveType('int')
    FLOAT = PrimitiveType('float')
    BOOL = PrimitiveType('bool')
    VOID = PrimitiveType('void')
    STRING = PrimitiveType('string')

    @classmethod
    def from_name(cls, name: str) -> Optional[PrimitiveType]:
        types_map = {
            'int': cls.INT,
            'float': cls.FLOAT,
            'bool': cls.BOOL,
            'void': cls.VOID,
            'string': cls.STRING,
        }
        return types_map.get(name)

    @classmethod
    def is_primitive(cls, name: str) -> bool:
        return name in ['int', 'float', 'bool', 'void', 'string']


@dataclass
class StructType(Type):
    name: str
    fields: Dict[str, Type] = field(default_factory=dict)
    line: int = 1
    column: int = 1

    def is_compatible_with(self, other: Type) -> bool:
        if not isinstance(other, StructType):
            return False
        return self.name == other.name

    def __eq__(self, other) -> bool:
        if not isinstance(other, StructType):
            return False
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(('StructType', self.name))

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"StructType('{self.name}', fields={list(self.fields.keys())})"

    def has_field(self, field_name: str) -> bool:
        return field_name in self.fields

    def get_field_type(self, field_name: str) -> Optional[Type]:
        return self.fields.get(field_name)

    def add_field(self, name: str, type_: Type, line: int = 1, column: int = 1) -> bool:
        if name in self.fields:
            return False
        self.fields[name] = type_
        return True


@dataclass
class PointerType(Type):
    """Тип указателя. Массивы при использовании распадаются в этот тип."""
    element_type: Type

    def is_compatible_with(self, other: Type) -> bool:
        if not isinstance(other, PointerType):
            return False
        return self.element_type == other.element_type

    def __eq__(self, other) -> bool:
        if not isinstance(other, PointerType):
            return False
        return self.element_type == other.element_type

    def __hash__(self) -> int:
        return hash(('PointerType', self.element_type))

    def __str__(self) -> str:
        return f"{self.element_type}*"

    def __repr__(self) -> str:
        return f"PointerType({self.element_type})"

    @property
    def size(self) -> int:
        return 8  # 64-bit pointer


@dataclass
class ArrayType(Type):
    """Внутренний тип массива с известным размером. При использовании распадается в PointerType."""
    element_type: Type
    size: int

    def is_compatible_with(self, other: Type) -> bool:
        if isinstance(other, ArrayType):
            return self.element_type == other.element_type and self.size == other.size
        if isinstance(other, PointerType):
            return self.element_type == other.element_type
        return False

    def __eq__(self, other) -> bool:
        if not isinstance(other, ArrayType):
            return False
        return self.element_type == other.element_type and self.size == other.size

    def __hash__(self) -> int:
        return hash(('ArrayType', self.element_type, self.size))

    def __str__(self) -> str:
        return f"{self.element_type}[{self.size}]"

    def __repr__(self) -> str:
        return f"ArrayType({self.element_type}, {self.size})"

    @property
    def total_size(self) -> int:
        elem_size = getattr(self.element_type, 'size', 4)
        return self.size * elem_size

    def decay(self) -> PointerType:
        return PointerType(self.element_type)


@dataclass
class Parameter:
    name: str
    type_: Type
    line: int = 1
    column: int = 1

    def __str__(self) -> str:
        return f"{self.name}: {self.type_}"

    def __repr__(self) -> str:
        return f"Parameter('{self.name}', type={self.type_})"


@dataclass
class FunctionType(Type):
    return_type: Type
    param_types: List[Type] = field(default_factory=list)
    param_names: List[str] = field(default_factory=list)

    def is_compatible_with(self, other: Type) -> bool:
        if not isinstance(other, FunctionType):
            return False
        if not self.return_type.is_compatible_with(other.return_type):
            return False
        if len(self.param_types) != len(other.param_types):
            return False
        for self_param, other_param in zip(self.param_types, other.param_types):
            if not self_param.is_compatible_with(other_param):
                return False
        return True

    def __eq__(self, other) -> bool:
        if not isinstance(other, FunctionType):
            return False
        if self.return_type != other.return_type:
            return False
        if len(self.param_types) != len(other.param_types):
            return False
        for s, o in zip(self.param_types, other.param_types):
            if s != o:
                return False
        return True

    def __hash__(self) -> int:
        return hash((
            'FunctionType',
            self.return_type,
            tuple(self.param_types)
        ))

    def __str__(self) -> str:
        params = ', '.join(
            f"{name}: {type_}"
            for name, type_ in zip(self.param_names, self.param_types)
        )
        return f"({params}) -> {self.return_type}"

    def __repr__(self) -> str:
        return f"FunctionType(return={self.return_type}, params={self.param_types})"

    def check_call(self, arg_types: List[Type]) -> Tuple[bool, Optional[str]]:
        if len(arg_types) != len(self.param_types):
            return False, f"expected {len(self.param_types)} arguments, got {len(arg_types)}"
        for i, (arg_type, param_type) in enumerate(zip(arg_types, self.param_types)):
            if not arg_type.is_compatible_with(param_type):
                param_name = self.param_names[i] if i < len(self.param_names) else f"arg{i + 1}"
                return False, f"argument {i + 1} ('{param_name}'): expected {param_type}, got {arg_type}"
        return True, None


def get_common_type(t1: Type, t2: Type) -> Optional[Type]:
    if t1 == t2:
        return t1

    if isinstance(t1, PrimitiveType) and isinstance(t2, PrimitiveType):
        if (t1.name == 'int' and t2.name == 'float') or \
                (t1.name == 'float' and t2.name == 'int'):
            return Types.FLOAT

    return None


def is_numeric_type(type_: Type) -> bool:
    return isinstance(type_, PrimitiveType) and type_.name in ('int', 'float')


def is_boolean_type(type_: Type) -> bool:
    return isinstance(type_, PrimitiveType) and type_.name == 'bool'


def is_void_type(type_: Type) -> bool:
    return isinstance(type_, PrimitiveType) and type_.name == 'void'


def type_to_keyword(type_: Type) -> Optional[str]:
    if isinstance(type_, PrimitiveType):
        return type_.name
    elif isinstance(type_, StructType):
        return type_.name
    return None