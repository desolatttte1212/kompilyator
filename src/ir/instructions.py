from abc import ABC, abstractmethod
from typing import List, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto

from .operand import Operand, Temporary, Variable, Literal, Label, MemoryLocation


class InstructionType(Enum):
    # Arithmetic
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    MOD = auto()
    NEG = auto()

    # Logical (Bitwise)
    AND = auto()
    OR = auto()
    NOT = auto()
    XOR = auto()

    # Comparisons
    CMP_EQ = auto()
    CMP_NE = auto()
    CMP_LT = auto()
    CMP_LE = auto()
    CMP_GT = auto()
    CMP_GE = auto()

    # Memory
    LOAD = auto()
    STORE = auto()
    ALLOCA = auto()
    GEP = auto()

    # Control Flow (Low-level)
    JUMP = auto()
    JUMP_IF = auto()
    JUMP_IF_NOT = auto()
    LABEL = auto()

    # Functions
    CALL = auto()
    RETURN = auto()
    PARAM = auto()

    # Misc
    MOVE = auto()
    PHI = auto()

    #  Sprint 6: High-Level Control Flow & Short-Circuit
    IF_START = auto()
    IF_END = auto()
    WHILE_START = auto()
    WHILE_END = auto()
    LOGICAL_AND = auto()
    LOGICAL_OR = auto()


@dataclass
class Instruction(ABC):
    instruction_type: InstructionType = InstructionType.MOVE
    dest: Optional[Operand] = None
    comment: Optional[str] = None

    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def get_operands(self) -> List[Operand]:
        pass

    @abstractmethod
    def get_uses(self) -> List[Operand]:
        pass

    @abstractmethod
    def get_defs(self) -> List[Operand]:
        pass


@dataclass
class BinaryArithmeticInstr(Instruction):
    instruction_type: InstructionType = InstructionType.ADD
    dest: Optional[Operand] = None
    src1: Operand = field(default_factory=lambda: Temporary(0))
    src2: Operand = field(default_factory=lambda: Temporary(0))
    comment: Optional[str] = None

    def __str__(self) -> str:
        op_name = self.instruction_type.name
        comment = f"  # {self.comment}" if self.comment else ""
        return f"{self.dest} = {op_name} {self.src1}, {self.src2}{comment}"

    def get_operands(self) -> List[Operand]:
        return [self.dest, self.src1, self.src2] if self.dest else [self.src1, self.src2]

    def get_uses(self) -> List[Operand]:
        return [self.src1, self.src2]

    def get_defs(self) -> List[Operand]:
        return [self.dest] if self.dest else []


@dataclass
class UnaryArithmeticInstr(Instruction):
    instruction_type: InstructionType = InstructionType.NEG
    dest: Optional[Operand] = None
    src: Operand = field(default_factory=lambda: Temporary(0))
    comment: Optional[str] = None

    def __str__(self) -> str:
        op_name = self.instruction_type.name
        comment = f"  # {self.comment}" if self.comment else ""
        return f"{self.dest} = {op_name} {self.src}{comment}"

    def get_operands(self) -> List[Operand]:
        return [self.dest, self.src] if self.dest else [self.src]

    def get_uses(self) -> List[Operand]:
        return [self.src]

    def get_defs(self) -> List[Operand]:
        return [self.dest] if self.dest else []


@dataclass
class BinaryLogicalInstr(Instruction):
    instruction_type: InstructionType = InstructionType.AND
    dest: Optional[Operand] = None
    src1: Operand = field(default_factory=lambda: Temporary(0))
    src2: Operand = field(default_factory=lambda: Temporary(0))
    comment: Optional[str] = None

    def __str__(self) -> str:
        op_name = self.instruction_type.name
        comment = f"  # {self.comment}" if self.comment else ""
        return f"{self.dest} = {op_name} {self.src1}, {self.src2}{comment}"

    def get_operands(self) -> List[Operand]:
        return [self.dest, self.src1, self.src2] if self.dest else [self.src1, self.src2]

    def get_uses(self) -> List[Operand]:
        return [self.src1, self.src2]

    def get_defs(self) -> List[Operand]:
        return [self.dest] if self.dest else []


@dataclass
class UnaryLogicalInstr(Instruction):
    instruction_type: InstructionType = InstructionType.NOT
    dest: Optional[Operand] = None
    src: Operand = field(default_factory=lambda: Temporary(0))
    comment: Optional[str] = None

    def __str__(self) -> str:
        op_name = self.instruction_type.name
        comment = f"  # {self.comment}" if self.comment else ""
        return f"{self.dest} = {op_name} {self.src}{comment}"

    def get_operands(self) -> List[Operand]:
        return [self.dest, self.src] if self.dest else [self.src]

    def get_uses(self) -> List[Operand]:
        return [self.src]

    def get_defs(self) -> List[Operand]:
        return [self.dest] if self.dest else []


@dataclass
class ComparisonInstr(Instruction):
    instruction_type: InstructionType = InstructionType.CMP_EQ
    dest: Optional[Operand] = None
    src1: Operand = field(default_factory=lambda: Temporary(0))
    src2: Operand = field(default_factory=lambda: Temporary(0))
    comment: Optional[str] = None

    def __str__(self) -> str:
        op_name = self.instruction_type.name.replace('CMP_', '')
        comment = f"  # {self.comment}" if self.comment else ""
        return f"{self.dest} = {op_name} {self.src1}, {self.src2}{comment}"

    def get_operands(self) -> List[Operand]:
        return [self.dest, self.src1, self.src2] if self.dest else [self.src1, self.src2]

    def get_uses(self) -> List[Operand]:
        return [self.src1, self.src2]

    def get_defs(self) -> List[Operand]:
        return [self.dest] if self.dest else []


@dataclass
class LoadInstr(Instruction):
    instruction_type: InstructionType = InstructionType.LOAD
    dest: Optional[Operand] = None
    src: Operand = field(default_factory=lambda: MemoryLocation(Temporary(0)))
    comment: Optional[str] = None

    def __post_init__(self):
        if not isinstance(self.src, MemoryLocation):
            self.src = MemoryLocation(self.src)

    def __str__(self) -> str:
        comment = f"  # {self.comment}" if self.comment else ""
        return f"{self.dest} = LOAD {self.src}{comment}"

    def get_operands(self) -> List[Operand]:
        return [self.dest, self.src] if self.dest else [self.src]

    def get_uses(self) -> List[Operand]:
        return [self.src]

    def get_defs(self) -> List[Operand]:
        return [self.dest] if self.dest else []


@dataclass
class StoreInstr(Instruction):
    instruction_type: InstructionType = InstructionType.STORE
    dest: Optional[Operand] = None
    src: Operand = field(default_factory=lambda: Temporary(0))
    comment: Optional[str] = None

    def __post_init__(self):
        if self.dest and not isinstance(self.dest, MemoryLocation):
            self.dest = MemoryLocation(self.dest)

    def __str__(self) -> str:
        comment = f"  # {self.comment}" if self.comment else ""
        return f"STORE {self.dest}, {self.src}{comment}"

    def get_operands(self) -> List[Operand]:
        return [self.dest, self.src] if self.dest else [self.src]

    def get_uses(self) -> List[Operand]:
        return [self.dest, self.src] if self.dest else [self.src]

    def get_defs(self) -> List[Operand]:
        return []


@dataclass
class AllocaInstr(Instruction):
    instruction_type: InstructionType = InstructionType.ALLOCA
    dest: Optional[Operand] = None
    size: int = 4
    comment: Optional[str] = None

    def __str__(self) -> str:
        comment = f"  # {self.comment}" if self.comment else ""
        return f"{self.dest} = ALLOCA {self.size}{comment}"

    def get_operands(self) -> List[Operand]:
        return [self.dest] if self.dest else []

    def get_uses(self) -> List[Operand]:
        return []

    def get_defs(self) -> List[Operand]:
        return [self.dest] if self.dest else []


@dataclass
class GepInstr(Instruction):
    instruction_type: InstructionType = InstructionType.GEP
    dest: Optional[Operand] = None
    base: Operand = field(default_factory=lambda: Temporary(0))
    index: Operand = field(default_factory=lambda: Temporary(0))
    comment: Optional[str] = None

    def __str__(self) -> str:
        comment = f"  # {self.comment}" if self.comment else ""
        return f"{self.dest} = GEP {self.base}, {self.index}{comment}"

    def get_operands(self) -> List[Operand]:
        return [self.dest, self.base, self.index] if self.dest else [self.base, self.index]

    def get_uses(self) -> List[Operand]:
        return [self.base, self.index]

    def get_defs(self) -> List[Operand]:
        return [self.dest] if self.dest else []


@dataclass
class JumpInstr(Instruction):
    instruction_type: InstructionType = InstructionType.JUMP
    dest: Optional[Operand] = None
    target: Label = field(default_factory=lambda: Label("L0"))
    comment: Optional[str] = None

    def __str__(self) -> str:
        comment = f"  # {self.comment}" if self.comment else ""
        return f"JUMP {self.target}{comment}"

    def get_operands(self) -> List[Operand]:
        return [self.target]

    def get_uses(self) -> List[Operand]:
        return [self.target]

    def get_defs(self) -> List[Operand]:
        return []


@dataclass
class ConditionalJumpInstr(Instruction):
    instruction_type: InstructionType = InstructionType.JUMP_IF
    dest: Optional[Operand] = None
    condition: Operand = field(default_factory=lambda: Temporary(0))
    target: Label = field(default_factory=lambda: Label("L0"))
    comment: Optional[str] = None

    def __str__(self) -> str:
        op = "JUMP_IF" if self.instruction_type == InstructionType.JUMP_IF else "JUMP_IF_NOT"
        comment = f"  # {self.comment}" if self.comment else ""
        return f"{op} {self.condition}, {self.target}{comment}"

    def get_operands(self) -> List[Operand]:
        return [self.condition, self.target]

    def get_uses(self) -> List[Operand]:
        return [self.condition, self.target]

    def get_defs(self) -> List[Operand]:
        return []


@dataclass
class LabelInstr(Instruction):
    instruction_type: InstructionType = InstructionType.LABEL
    dest: Optional[Operand] = None
    label: Label = field(default_factory=lambda: Label("L0"))
    comment: Optional[str] = None

    def __str__(self) -> str:
        comment = f"  # {self.comment}" if self.comment else ""
        return f"{self.label}:{comment}"

    def get_operands(self) -> List[Operand]:
        return [self.label]

    def get_uses(self) -> List[Operand]:
        return [self.label]

    def get_defs(self) -> List[Operand]:
        return []


@dataclass
class CallInstr(Instruction):
    instruction_type: InstructionType = InstructionType.CALL
    dest: Optional[Operand] = None
    func_name: str = ""
    args: List[Operand] = field(default_factory=list)
    comment: Optional[str] = None

    def __str__(self) -> str:
        args_str = ", ".join(str(arg) for arg in self.args)
        comment = f"  # {self.comment}" if self.comment else ""
        if self.dest:
            return f"{self.dest} = CALL {self.func_name}({args_str}){comment}"
        else:
            return f"CALL {self.func_name}({args_str}){comment}"

    def get_operands(self) -> List[Operand]:
        result = [self.dest] if self.dest else []
        result.extend(self.args)
        return result

    def get_uses(self) -> List[Operand]:
        return self.args.copy()

    def get_defs(self) -> List[Operand]:
        return [self.dest] if self.dest else []


@dataclass
class ReturnInstr(Instruction):
    instruction_type: InstructionType = InstructionType.RETURN
    dest: Optional[Operand] = None
    value: Optional[Operand] = None
    comment: Optional[str] = None

    def __str__(self) -> str:
        comment = f"  # {self.comment}" if self.comment else ""
        if self.value:
            return f"RETURN {self.value}{comment}"
        else:
            return f"RETURN{comment}"

    def get_operands(self) -> List[Operand]:
        return [self.value] if self.value else []

    def get_uses(self) -> List[Operand]:
        return [self.value] if self.value else []

    def get_defs(self) -> List[Operand]:
        return []


@dataclass
class ParamInstr(Instruction):
    instruction_type: InstructionType = InstructionType.PARAM
    dest: Optional[Operand] = None
    index: int = 0
    value: Operand = field(default_factory=lambda: Temporary(0))
    comment: Optional[str] = None

    def __str__(self) -> str:
        comment = f"  # {self.comment}" if self.comment else ""
        return f"PARAM {self.index}, {self.value}{comment}"

    def get_operands(self) -> List[Operand]:
        return [self.value]

    def get_uses(self) -> List[Operand]:
        return [self.value]

    def get_defs(self) -> List[Operand]:
        return []


@dataclass
class MoveInstr(Instruction):
    instruction_type: InstructionType = InstructionType.MOVE
    dest: Optional[Operand] = None
    src: Operand = field(default_factory=lambda: Temporary(0))
    comment: Optional[str] = None

    def __str__(self) -> str:
        comment = f"  # {self.comment}" if self.comment else ""
        return f"{self.dest} = MOVE {self.src}{comment}"

    def get_operands(self) -> List[Operand]:
        return [self.dest, self.src] if self.dest else [self.src]

    def get_uses(self) -> List[Operand]:
        return [self.src]

    def get_defs(self) -> List[Operand]:
        return [self.dest] if self.dest else []


@dataclass
class PhiInstr(Instruction):
    instruction_type: InstructionType = InstructionType.PHI
    dest: Optional[Operand] = None
    sources: List[Tuple[Operand, Label]] = field(default_factory=list)
    comment: Optional[str] = None

    def __str__(self) -> str:
        sources_str = ", ".join(f"({val}, {blk})" for val, blk in self.sources)
        comment = f"  # {self.comment}" if self.comment else ""
        return f"{self.dest} = PHI {sources_str}{comment}"

    def get_operands(self) -> List[Operand]:
        result = [self.dest] if self.dest else []
        for val, blk in self.sources:
            result.append(val)
            result.append(blk)
        return result

    def get_uses(self) -> List[Operand]:
        return [val for val, _ in self.sources]

    def get_defs(self) -> List[Operand]:
        return [self.dest] if self.dest else []

    def add_source(self, value: Operand, block: Label):
        self.sources.append((value, block))

@dataclass
class IfStartInstr(Instruction):
    instruction_type: InstructionType = InstructionType.IF_START
    dest: Optional[Operand] = None
    condition: Operand = field(default_factory=lambda: Temporary(0))
    then_label: Label = field(default_factory=lambda: Label("L_then"))
    else_label: Optional[Label] = None
    merge_label: Label = field(default_factory=lambda: Label("L_merge"))
    comment: Optional[str] = None

    def __str__(self) -> str:
        return f"IF_START {self.condition} -> {self.then_label}"

    def get_operands(self) -> List[Operand]: return [self.condition]

    def get_uses(self) -> List[Operand]: return [self.condition]

    def get_defs(self) -> List[Operand]: return []


@dataclass
class IfEndInstr(Instruction):
    instruction_type: InstructionType = InstructionType.IF_END
    dest: Optional[Operand] = None
    else_label: Optional[Label] = None
    merge_label: Label = field(default_factory=lambda: Label("L_merge"))
    comment: Optional[str] = None

    def __str__(self) -> str: return "IF_END"

    def get_operands(self) -> List[Operand]: return []

    def get_uses(self) -> List[Operand]: return []

    def get_defs(self) -> List[Operand]: return []


@dataclass
class WhileStartInstr(Instruction):
    instruction_type: InstructionType = InstructionType.WHILE_START
    dest: Optional[Operand] = None
    condition: Operand = field(default_factory=lambda: Temporary(0))
    cond_label: Label = field(default_factory=lambda: Label("L_cond"))
    body_label: Label = field(default_factory=lambda: Label("L_body"))
    end_label: Label = field(default_factory=lambda: Label("L_end"))
    comment: Optional[str] = None

    def __str__(self) -> str: return f"WHILE_START {self.condition}"

    def get_operands(self) -> List[Operand]: return [self.condition]

    def get_uses(self) -> List[Operand]: return [self.condition]

    def get_defs(self) -> List[Operand]: return []


@dataclass
class WhileEndInstr(Instruction):
    instruction_type: InstructionType = InstructionType.WHILE_END
    dest: Optional[Operand] = None
    cond_label: Label = field(default_factory=lambda: Label("L_cond"))
    end_label: Label = field(default_factory=lambda: Label("L_end"))
    comment: Optional[str] = None

    def __str__(self) -> str: return "WHILE_END"

    def get_operands(self) -> List[Operand]: return []

    def get_uses(self) -> List[Operand]: return []

    def get_defs(self) -> List[Operand]: return []


@dataclass
class LogicalAndInstr(Instruction):
    instruction_type: InstructionType = InstructionType.LOGICAL_AND
    dest: Optional[Operand] = None
    left: Operand = field(default_factory=lambda: Temporary(0))
    right: Operand = field(default_factory=lambda: Temporary(0))
    false_label: Label = field(default_factory=lambda: Label("L_false"))
    end_label: Label = field(default_factory=lambda: Label("L_end"))
    comment: Optional[str] = None

    def __str__(self) -> str: return f"LOGICAL_AND {self.dest} = {self.left} && {self.right}"

    def get_operands(self) -> List[Operand]: return [self.dest, self.left, self.right]

    def get_uses(self) -> List[Operand]: return [self.left, self.right]

    def get_defs(self) -> List[Operand]: return [self.dest] if self.dest else []


@dataclass
class LogicalOrInstr(Instruction):
    instruction_type: InstructionType = InstructionType.LOGICAL_OR
    dest: Optional[Operand] = None
    left: Operand = field(default_factory=lambda: Temporary(0))
    right: Operand = field(default_factory=lambda: Temporary(0))
    true_label: Label = field(default_factory=lambda: Label("L_true"))
    end_label: Label = field(default_factory=lambda: Label("L_end"))
    comment: Optional[str] = None

    def __str__(self) -> str: return f"LOGICAL_OR {self.dest} = {self.left} || {self.right}"

    def get_operands(self) -> List[Operand]: return [self.dest, self.left, self.right]

    def get_uses(self) -> List[Operand]: return [self.left, self.right]

    def get_defs(self) -> List[Operand]: return [self.dest] if self.dest else []


class InstructionFactory:
    @staticmethod
    def add(dest: Operand, src1: Operand, src2: Operand, comment: str = None) -> BinaryArithmeticInstr:
        return BinaryArithmeticInstr(
            instruction_type=InstructionType.ADD, dest=dest, src1=src1, src2=src2, comment=comment
        )

    @staticmethod
    def sub(dest: Operand, src1: Operand, src2: Operand, comment: str = None) -> BinaryArithmeticInstr:
        return BinaryArithmeticInstr(
            instruction_type=InstructionType.SUB, dest=dest, src1=src1, src2=src2, comment=comment
        )

    @staticmethod
    def mul(dest: Operand, src1: Operand, src2: Operand, comment: str = None) -> BinaryArithmeticInstr:
        return BinaryArithmeticInstr(
            instruction_type=InstructionType.MUL, dest=dest, src1=src1, src2=src2, comment=comment
        )

    @staticmethod
    def div(dest: Operand, src1: Operand, src2: Operand, comment: str = None) -> BinaryArithmeticInstr:
        return BinaryArithmeticInstr(
            instruction_type=InstructionType.DIV, dest=dest, src1=src1, src2=src2, comment=comment
        )

    @staticmethod
    def mod(dest: Operand, src1: Operand, src2: Operand, comment: str = None) -> BinaryArithmeticInstr:
        return BinaryArithmeticInstr(
            instruction_type=InstructionType.MOD, dest=dest, src1=src1, src2=src2, comment=comment
        )

    @staticmethod
    def neg(dest: Operand, src: Operand, comment: str = None) -> UnaryArithmeticInstr:
        return UnaryArithmeticInstr(
            instruction_type=InstructionType.NEG, dest=dest, src=src, comment=comment
        )

    @staticmethod
    def and_op(dest: Operand, src1: Operand, src2: Operand, comment: str = None) -> BinaryLogicalInstr:
        return BinaryLogicalInstr(
            instruction_type=InstructionType.AND, dest=dest, src1=src1, src2=src2, comment=comment
        )

    @staticmethod
    def or_op(dest: Operand, src1: Operand, src2: Operand, comment: str = None) -> BinaryLogicalInstr:
        return BinaryLogicalInstr(
            instruction_type=InstructionType.OR, dest=dest, src1=src1, src2=src2, comment=comment
        )

    @staticmethod
    def not_op(dest: Operand, src: Operand, comment: str = None) -> UnaryLogicalInstr:
        return UnaryLogicalInstr(
            instruction_type=InstructionType.NOT, dest=dest, src=src, comment=comment
        )

    @staticmethod
    def cmp_eq(dest: Operand, src1: Operand, src2: Operand, comment: str = None) -> ComparisonInstr:
        return ComparisonInstr(
            instruction_type=InstructionType.CMP_EQ, dest=dest, src1=src1, src2=src2, comment=comment
        )

    @staticmethod
    def cmp_ne(dest: Operand, src1: Operand, src2: Operand, comment: str = None) -> ComparisonInstr:
        return ComparisonInstr(
            instruction_type=InstructionType.CMP_NE, dest=dest, src1=src1, src2=src2, comment=comment
        )

    @staticmethod
    def cmp_lt(dest: Operand, src1: Operand, src2: Operand, comment: str = None) -> ComparisonInstr:
        return ComparisonInstr(
            instruction_type=InstructionType.CMP_LT, dest=dest, src1=src1, src2=src2, comment=comment
        )

    @staticmethod
    def cmp_le(dest: Operand, src1: Operand, src2: Operand, comment: str = None) -> ComparisonInstr:
        return ComparisonInstr(
            instruction_type=InstructionType.CMP_LE, dest=dest, src1=src1, src2=src2, comment=comment
        )

    @staticmethod
    def cmp_gt(dest: Operand, src1: Operand, src2: Operand, comment: str = None) -> ComparisonInstr:
        return ComparisonInstr(
            instruction_type=InstructionType.CMP_GT, dest=dest, src1=src1, src2=src2, comment=comment
        )

    @staticmethod
    def cmp_ge(dest: Operand, src1: Operand, src2: Operand, comment: str = None) -> ComparisonInstr:
        return ComparisonInstr(
            instruction_type=InstructionType.CMP_GE, dest=dest, src1=src1, src2=src2, comment=comment
        )

    @staticmethod
    def load(dest: Operand, address: Operand, comment: str = None) -> LoadInstr:
        return LoadInstr(dest=dest, src=address, comment=comment)

    @staticmethod
    def store(address: Operand, src: Operand, comment: str = None) -> StoreInstr:
        return StoreInstr(dest=address, src=src, comment=comment)

    @staticmethod
    def alloca(dest: Operand, size: int = 4, comment: str = None) -> AllocaInstr:
        return AllocaInstr(dest=dest, size=size, comment=comment)

    @staticmethod
    def gep(dest: Operand, base: Operand, index: Operand, comment: str = None) -> GepInstr:
        return GepInstr(dest=dest, base=base, index=index, comment=comment)

    @staticmethod
    def jump(target: Label, comment: str = None) -> JumpInstr:
        return JumpInstr(target=target, comment=comment)

    @staticmethod
    def jump_if(condition: Operand, target: Label, comment: str = None) -> ConditionalJumpInstr:
        return ConditionalJumpInstr(
            instruction_type=InstructionType.JUMP_IF, condition=condition, target=target, comment=comment
        )

    @staticmethod
    def jump_if_not(condition: Operand, target: Label, comment: str = None) -> ConditionalJumpInstr:
        return ConditionalJumpInstr(
            instruction_type=InstructionType.JUMP_IF_NOT, condition=condition, target=target, comment=comment
        )

    @staticmethod
    def label(name: str, comment: str = None) -> LabelInstr:
        return LabelInstr(label=Label(name), comment=comment)

    @staticmethod
    def call(dest: Optional[Operand], func_name: str, args: List[Operand], comment: str = None) -> CallInstr:
        return CallInstr(dest=dest, func_name=func_name, args=args, comment=comment)

    @staticmethod
    def return_stmt(value: Optional[Operand] = None, comment: str = None) -> ReturnInstr:
        return ReturnInstr(value=value, comment=comment)

    @staticmethod
    def param(index: int, value: Operand, comment: str = None) -> ParamInstr:
        return ParamInstr(index=index, value=value, comment=comment)

    @staticmethod
    def move(dest: Operand, src: Operand, comment: str = None) -> MoveInstr:
        return MoveInstr(dest=dest, src=src, comment=comment)

    @staticmethod
    def phi(dest: Operand, sources: List[Tuple[Operand, Label]], comment: str = None) -> PhiInstr:
        return PhiInstr(dest=dest, sources=sources, comment=comment)

    @staticmethod
    def if_start(condition: Operand, then_label: Label, else_label: Optional[Label], merge_label: Label,
                 comment: str = None) -> IfStartInstr:
        return IfStartInstr(condition=condition, then_label=then_label, else_label=else_label, merge_label=merge_label,
                            comment=comment)

    @staticmethod
    def if_end(else_label: Optional[Label], merge_label: Label, comment: str = None) -> IfEndInstr:
        return IfEndInstr(else_label=else_label, merge_label=merge_label, comment=comment)

    @staticmethod
    def while_start(condition: Operand, cond_label: Label, body_label: Label, end_label: Label,
                    comment: str = None) -> WhileStartInstr:
        return WhileStartInstr(condition=condition, cond_label=cond_label, body_label=body_label, end_label=end_label,
                               comment=comment)

    @staticmethod
    def while_end(cond_label: Label, end_label: Label, comment: str = None) -> WhileEndInstr:
        return WhileEndInstr(cond_label=cond_label, end_label=end_label, comment=comment)

    @staticmethod
    def logical_and(dest: Operand, left: Operand, right: Operand, false_label: Label, end_label: Label,
                    comment: str = None) -> LogicalAndInstr:
        return LogicalAndInstr(dest=dest, left=left, right=right, false_label=false_label, end_label=end_label,
                               comment=comment)

    @staticmethod
    def logical_or(dest: Operand, left: Operand, right: Operand, true_label: Label, end_label: Label,
                   comment: str = None) -> LogicalOrInstr:
        return LogicalOrInstr(dest=dest, left=left, right=right, true_label=true_label, end_label=end_label,
                              comment=comment)


def is_terminator(instr: Instruction) -> bool:
    return instr.instruction_type in (
        InstructionType.JUMP,
        InstructionType.JUMP_IF,
        InstructionType.JUMP_IF_NOT,
        InstructionType.RETURN,
    )


def is_control_flow(instr: Instruction) -> bool:
    return instr.instruction_type in (
        InstructionType.JUMP,
        InstructionType.JUMP_IF,
        InstructionType.JUMP_IF_NOT,
        InstructionType.LABEL,
        InstructionType.IF_START,
        InstructionType.IF_END,
        InstructionType.WHILE_START,
        InstructionType.WHILE_END,
    )


def is_memory_op(instr: Instruction) -> bool:
    return instr.instruction_type in (
        InstructionType.LOAD,
        InstructionType.STORE,
        InstructionType.ALLOCA,
        InstructionType.GEP,
    )


def is_arithmetic_op(instr: Instruction) -> bool:
    return instr.instruction_type in (
        InstructionType.ADD, InstructionType.SUB, InstructionType.MUL,
        InstructionType.DIV, InstructionType.MOD, InstructionType.NEG,
    )


def is_logical_op(instr: Instruction) -> bool:
    return instr.instruction_type in (
        InstructionType.AND, InstructionType.OR, InstructionType.NOT, InstructionType.XOR,
        InstructionType.LOGICAL_AND, InstructionType.LOGICAL_OR,
    )


def is_comparison_op(instr: Instruction) -> bool:
    return instr.instruction_type in (
        InstructionType.CMP_EQ, InstructionType.CMP_NE,
        InstructionType.CMP_LT, InstructionType.CMP_LE,
        InstructionType.CMP_GT, InstructionType.CMP_GE,
    )

