"""
IR (Intermediate Representation) package for MiniCompiler.

Sprint 4: Промежуточное представление и генерация кода.
"""

from .operand import (
    Operand, Temporary, Variable, Literal, Label, MemoryLocation,
    OperandFactory, is_immediate, is_temporary, is_variable, is_memory, is_label
)

from .instructions import (
    Instruction, InstructionType,
    BinaryArithmeticInstr, UnaryArithmeticInstr,
    BinaryLogicalInstr, UnaryLogicalInstr,
    ComparisonInstr,
    LoadInstr, StoreInstr, AllocaInstr, GepInstr,
    JumpInstr, ConditionalJumpInstr, LabelInstr,
    CallInstr, ReturnInstr, ParamInstr,
    MoveInstr, PhiInstr,
    InstructionFactory,
    is_terminator, is_control_flow, is_memory_op, is_arithmetic_op, is_logical_op, is_comparison_op
)

from .basic_block import (
    BasicBlock, BlockType,
    IRFunction, IRProgram,
    get_dominators, get_loops, is_reachable, get_reachable_blocks
)

from .generator import IRGenerator, GenerationContext

from .printer import (
    IRPrinter, CFGDotPrinter, IRJsonPrinter,
    print_ir, generate_cfg_dot, ir_to_json
)

__all__ = [
    # Operands
    'Operand', 'Temporary', 'Variable', 'Literal', 'Label', 'MemoryLocation',
    'OperandFactory', 'is_immediate', 'is_temporary', 'is_variable', 'is_memory', 'is_label',

    # Instructions
    'Instruction', 'InstructionType',
    'BinaryArithmeticInstr', 'UnaryArithmeticInstr',
    'BinaryLogicalInstr', 'UnaryLogicalInstr',
    'ComparisonInstr',
    'LoadInstr', 'StoreInstr', 'AllocaInstr', 'GepInstr',
    'JumpInstr', 'ConditionalJumpInstr', 'LabelInstr',
    'CallInstr', 'ReturnInstr', 'ParamInstr',
    'MoveInstr', 'PhiInstr',
    'InstructionFactory',
    'is_terminator', 'is_control_flow', 'is_memory_op', 'is_arithmetic_op', 'is_logical_op', 'is_comparison_op',

    # Basic Blocks & CFG
    'BasicBlock', 'BlockType',
    'IRFunction', 'IRProgram',
    'get_dominators', 'get_loops', 'is_reachable', 'get_reachable_blocks',

    # Generator
    'IRGenerator', 'GenerationContext',

    # Printers
    'IRPrinter', 'CFGDotPrinter', 'IRJsonPrinter',
    'print_ir', 'generate_cfg_dot', 'ir_to_json',
]