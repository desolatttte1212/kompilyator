

from typing import List
from ..ir.basic_block import IRProgram, IRFunction
from ..ir.instructions import IROpcode, IRInstruction


def collect_extern_declarations(program: IRProgram) -> List[str]:
    externs = set()
    for func in program.functions:
        for block in func.blocks:
            for instr in block.instructions:
                if instr.opcode == IROpcode.CALL and instr.args:
                    callee = instr.args[0]
                    if hasattr(callee, 'name') and callee.name not in program.functions:
                        externs.add(callee.name)
    return [f"extern {name}" for name in sorted(externs)]


def emit_variadic_preamble(output: List[str], is_variadic: bool) -> None:
    if is_variadic:
        output.append("    xor eax, eax")