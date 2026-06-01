from typing import List, Optional, Dict, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto

from .operand import Label, Temporary, Variable, Literal, MemoryLocation, Operand
from .instructions import Instruction, InstructionType, LabelInstr, JumpInstr, ConditionalJumpInstr, ReturnInstr, \
    is_terminator

class BlockType(Enum):
    ENTRY = auto()
    NORMAL = auto()
    EXIT = auto()
    LOOP_HEADER = auto()
    LOOP_BODY = auto()
    JOIN = auto()


@dataclass
class BasicBlock:
    label: Label
    block_type: BlockType = BlockType.NORMAL
    instructions: List[Instruction] = field(default_factory=list)

    predecessors: List['BasicBlock'] = field(default_factory=list)
    successors: List['BasicBlock'] = field(default_factory=list)

    parent_function: Optional['IRFunction'] = None
    source_line: Optional[int] = None

    def __post_init__(self):
        if isinstance(self.label, str):
            self.label = Label(self.label)

    def add_instruction(self, instr: Instruction):
        if self.instructions and is_terminator(self.instructions[-1]):
            raise ValueError(
                f"Cannot add instruction after terminator in block {self.label}. "
                f"Current terminator: {self.instructions[-1]}"
            )

        self.instructions.append(instr)

    def add_instructions(self, instrs: List[Instruction]):
        for instr in instrs:
            self.add_instruction(instr)

    def get_terminator(self) -> Optional[Instruction]:
        if self.instructions and is_terminator(self.instructions[-1]):
            return self.instructions[-1]
        return None

    def has_terminator(self) -> bool:
        return self.get_terminator() is not None

    def is_empty(self) -> bool:
        return len(self.instructions) == 0

    def get_successors(self) -> List['BasicBlock']:
        terminator = self.get_terminator()
        successors = []

        if terminator:
            if isinstance(terminator, JumpInstr):
                target_label = terminator.target
                if self.parent_function:
                    target_block = self.parent_function.get_block(target_label)
                    if target_block:
                        successors.append(target_block)

            elif isinstance(terminator, ConditionalJumpInstr):
                target_label = terminator.target
                if self.parent_function:
                    target_block = self.parent_function.get_block(target_label)
                    if target_block:
                        successors.append(target_block)

                    current_index = self.parent_function.get_block_index(self)
                    if current_index is not None and current_index + 1 < len(self.parent_function.blocks):
                        fallthrough_block = self.parent_function.blocks[current_index + 1]
                        successors.append(fallthrough_block)

            elif isinstance(terminator, ReturnInstr):
                pass
        else:
            if self.parent_function:
                current_index = self.parent_function.get_block_index(self)
                if current_index is not None and current_index + 1 < len(self.parent_function.blocks):
                    fallthrough_block = self.parent_function.blocks[current_index + 1]
                    successors.append(fallthrough_block)

        return successors

    def get_predecessors(self) -> List['BasicBlock']:
        return self.predecessors.copy()

    def add_predecessor(self, block: 'BasicBlock'):
        if block not in self.predecessors:
            self.predecessors.append(block)

    def add_successor(self, block: 'BasicBlock'):
        if block not in self.successors:
            self.successors.append(block)

    def __str__(self) -> str:
        lines = []
        lines.append(f"{self.label}:  # {self.block_type.name}")

        for instr in self.instructions:
            lines.append(f"  {instr}")

        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"BasicBlock({self.label}, {len(self.instructions)} instructions)"

    def __hash__(self) -> int:
        return hash(('BasicBlock', self.label))

    def __eq__(self, other) -> bool:
        return isinstance(other, BasicBlock) and self.label == other.label

@dataclass
class IRFunction:
    name: str
    return_type: str
    parameters: List[Tuple[str, str]] = field(default_factory=list)
    blocks: List[BasicBlock] = field(default_factory=list)

    variable_map: Dict[str, Operand] = field(default_factory=dict)

    local_vars: Dict[str, Tuple[Operand, int]] = field(default_factory=dict)

    _temp_counter: int = 0
    _label_counter: int = 0

    parent_program: Optional['IRProgram'] = None

    def __post_init__(self):
        if not self.blocks:
            entry_block = BasicBlock(
                label=Label(f"{self.name}_entry"),
                block_type=BlockType.ENTRY,
                parent_function=self
            )
            self.blocks.append(entry_block)

    @property
    def entry_block(self) -> BasicBlock:
        if self.blocks:
            return self.blocks[0]
        entry_block = BasicBlock(
            label=Label(f"{self.name}_entry"),
            block_type=BlockType.ENTRY,
            parent_function=self
        )
        self.blocks.append(entry_block)
        return entry_block

    @property
    def exit_blocks(self) -> List[BasicBlock]:
        return [
            block for block in self.blocks
            if block.get_terminator() and isinstance(block.get_terminator(), ReturnInstr)
        ]

    def get_block(self, label: Label) -> Optional[BasicBlock]:
        if isinstance(label, str):
            label = Label(label)

        for block in self.blocks:
            if block.label == label:
                return block
        return None

    def get_block_index(self, block: BasicBlock) -> Optional[int]:
        for i, b in enumerate(self.blocks):
            if b == block:
                return i
        return None

    def create_block(self, label: str = None, block_type: BlockType = BlockType.NORMAL) -> BasicBlock:
        if label is None:
            label = f"L{self._label_counter}"
            self._label_counter += 1

        block = BasicBlock(
            label=Label(label) if isinstance(label, str) else label,
            block_type=block_type,
            parent_function=self
        )

        self.blocks.append(block)
        return block

    def create_temporary(self) -> Temporary:
        temp = Temporary(self._temp_counter)
        self._temp_counter += 1
        return temp

    def reset_counters(self):
        self._temp_counter = 0
        self._label_counter = 0

    def map_variable(self, name: str, operand: Operand, size: int = 4):
        self.variable_map[name] = operand
        self.local_vars[name] = (operand, size)

    def get_variable_operand(self, name: str) -> Optional[Operand]:
        return self.variable_map.get(name)

    def link_blocks(self):
        for block in self.blocks:
            block.predecessors.clear()
            block.successors.clear()

        for block in self.blocks:
            successors = block.get_successors()
            for succ in successors:
                block.add_successor(succ)
                succ.add_predecessor(block)

    def __str__(self) -> str:
        lines = []
        params = ", ".join(f"{name}: {type_}" for name, type_ in self.parameters)
        lines.append(f"function {self.name}: {self.return_type} ({params})")

        for block in self.blocks:
            lines.append(str(block))
            lines.append("")

        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"IRFunction('{self.name}', {len(self.blocks)} blocks)"

@dataclass
class IRProgram:
    functions: Dict[str, IRFunction] = field(default_factory=dict)
    globals: Dict[str, Operand] = field(default_factory=dict)

    def add_function(self, func: IRFunction):
        func.parent_program = self
        self.functions[func.name] = func

    def get_function(self, name: str) -> Optional[IRFunction]:
        return self.functions.get(name)

    def has_function(self, name: str) -> bool:
        return name in self.functions

    def add_global(self, name: str, operand: Operand):
        self.globals[name] = operand

    def get_global(self, name: str) -> Optional[Operand]:
        return self.globals.get(name)

    def __str__(self) -> str:
        lines = []
        lines.append("# IR Program")
        lines.append("")

        if self.globals:
            lines.append("# Global variables")
            for name, operand in self.globals.items():
                lines.append(f".global {name} = {operand}")
            lines.append("")

        for name, func in self.functions.items():
            lines.append(str(func))
            lines.append("")

        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"IRProgram({len(self.functions)} functions)"

def get_dominators(function: IRFunction) -> Dict[BasicBlock, Set[BasicBlock]]:
    if not function.blocks:
        return {}

    entry = function.entry_block
    all_blocks = set(function.blocks)

    dominators = {block: all_blocks.copy() for block in function.blocks}
    dominators[entry] = {entry}

    changed = True
    while changed:
        changed = False
        for block in function.blocks:
            if block == entry:
                continue

            preds = block.get_predecessors()
            if preds:
                new_dom = set.intersection(*[dominators[pred] for pred in preds])
                new_dom.add(block)
            else:
                new_dom = {block}

            if new_dom != dominators[block]:
                dominators[block] = new_dom
                changed = True

    return dominators


def get_loops(function: IRFunction) -> List[Tuple[BasicBlock, BasicBlock]]:
    loops = []
    dominators = get_dominators(function)

    for block in function.blocks:
        for succ in block.get_successors():
            if succ in dominators.get(block, set()):
                loops.append((succ, block))
    return loops


def is_reachable(function: IRFunction, block: BasicBlock) -> bool:
    visited = set()
    stack = [function.entry_block]

    while stack:
        current = stack.pop()
        if current == block:
            return True
        if current in visited:
            continue
        visited.add(current)
        stack.extend(current.get_successors())

    return False


def get_reachable_blocks(function: IRFunction) -> Set[BasicBlock]:
    visited = set()
    stack = [function.entry_block]

    while stack:
        current = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        stack.extend(current.get_successors())

    return visited