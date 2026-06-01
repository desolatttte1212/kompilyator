from typing import List, Dict, Set, Optional, Any
from .instructions import (
    Instruction, InstructionType, InstructionFactory,
    Literal, Temporary
)
from .basic_block import IRProgram, IRFunction, BasicBlock
from .operand import Operand


class OptimizationPipeline:
    def __init__(self, ir_program: IRProgram):
        self.program = ir_program
        self.stats = {
            "constant_folds": 0,
            "constant_propagations": 0,
            "peephole_rules": 0,
            "dead_code_removed": 0
        }

    def run(self) -> IRProgram:
        self._constant_folding()
        self._constant_propagation()
        self._peephole_optimization()
        self._dead_code_elimination()
        return self.program

    def get_report(self) -> str:
        return (
            f"Optimization Report:\n"
            f"  Constant Folds: {self.stats['constant_folds']}\n"
            f"  Constant Propagations: {self.stats['constant_propagations']}\n"
            f"  Peephole Rules Applied: {self.stats['peephole_rules']}\n"
            f"  Dead Instructions Removed: {self.stats['dead_code_removed']}"
        )

    def _constant_folding(self):
        for func in self.program.functions.values():
            for block in func.blocks:
                new_instructions = []
                for instr in block.instructions:
                    folded = self._try_fold(instr)
                    if folded:
                        new_instructions.append(folded)
                        self.stats["constant_folds"] += 1
                    else:
                        new_instructions.append(instr)
                block.instructions = new_instructions

    def _try_fold(self, instr: Instruction) -> Optional[Instruction]:
        itype = instr.instruction_type
        dest = instr.dest
        if not dest or not isinstance(dest, Temporary):
            return None

        src1 = getattr(instr, "src1", None)
        src2 = getattr(instr, "src2", None)
        src = getattr(instr, "src", None)
        condition = getattr(instr, "condition", None)

        if itype in (InstructionType.ADD, InstructionType.SUB, InstructionType.MUL, InstructionType.DIV, InstructionType.MOD):
            if isinstance(src1, Literal) and isinstance(src2, Literal):
                v1, v2 = src1.value, src2.value
                res = None
                try:
                    if itype == InstructionType.ADD: res = v1 + v2
                    elif itype == InstructionType.SUB: res = v1 - v2
                    elif itype == InstructionType.MUL: res = v1 * v2
                    elif itype == InstructionType.DIV and v2 != 0: res = v1 // v2
                    elif itype == InstructionType.MOD and v2 != 0: res = v1 % v2
                except Exception:
                    pass
                if res is not None:
                    return InstructionFactory.move(dest, Literal(res), comment="folded")

        elif itype in (InstructionType.AND, InstructionType.OR):
            if isinstance(src1, Literal) and isinstance(src2, Literal):
                v1, v2 = bool(src1.value), bool(src2.value)
                res = (v1 and v2) if itype == InstructionType.AND else (v1 or v2)
                return InstructionFactory.move(dest, Literal(1 if res else 0), comment="folded")

        elif itype == InstructionType.NOT:
            if isinstance(src, Literal):
                res = not bool(src.value)
                return InstructionFactory.move(dest, Literal(1 if res else 0), comment="folded")

        elif itype == InstructionType.NEG:
            if isinstance(src, Literal):
                return InstructionFactory.move(dest, Literal(-src.value), comment="folded")

        elif itype in (InstructionType.CMP_EQ, InstructionType.CMP_NE,
                       InstructionType.CMP_LT, InstructionType.CMP_LE,
                       InstructionType.CMP_GT, InstructionType.CMP_GE):
            if isinstance(src1, Literal) and isinstance(src2, Literal):
                v1, v2 = src1.value, src2.value
                res = False
                if itype == InstructionType.CMP_EQ: res = v1 == v2
                elif itype == InstructionType.CMP_NE: res = v1 != v2
                elif itype == InstructionType.CMP_LT: res = v1 < v2
                elif itype == InstructionType.CMP_LE: res = v1 <= v2
                elif itype == InstructionType.CMP_GT: res = v1 > v2
                elif itype == InstructionType.CMP_GE: res = v1 >= v2
                return InstructionFactory.move(dest, Literal(1 if res else 0), comment="folded")

        return None
    def _constant_propagation(self):
        for func in self.program.functions.values():
            for block in func.blocks:
                const_map: Dict[int, Literal] = {}
                new_instructions = []
                
                for instr in block.instructions:
                    self._replace_consts_in_instr(instr, const_map)

                    dest = instr.dest
                    if dest and isinstance(dest, Temporary):
                        src = getattr(instr, "src", None)
                        src1 = getattr(instr, "src1", None)

                        if instr.instruction_type == InstructionType.MOVE and isinstance(src, Literal):
                            const_map[dest.id] = src
                        elif instr.instruction_type in (InstructionType.ADD, InstructionType.MUL) and \
                             isinstance(src1, Literal) and isinstance(getattr(instr, "src2", None), Literal):
                            pass 
                        else:
                            if isinstance(src, Literal):
                                const_map[dest.id] = src
                            elif isinstance(src1, Literal) and instr.instruction_type == InstructionType.MOVE:
                                const_map[dest.id] = src1

                    new_instructions.append(instr)
                
                block.instructions = new_instructions

    def _replace_consts_in_instr(self, instr: Instruction, const_map: Dict[int, Literal]):
        def replace_if_known(op: Operand) -> Operand:
            if isinstance(op, Temporary) and op.id in const_map:
                self.stats["constant_propagations"] += 1
                return const_map[op.id]
            return op

        if hasattr(instr, "src"):
            instr.src = replace_if_known(instr.src)
        if hasattr(instr, "src1"):
            instr.src1 = replace_if_known(instr.src1)
        if hasattr(instr, "src2"):
            instr.src2 = replace_if_known(instr.src2)
        if hasattr(instr, "condition"):
            instr.condition = replace_if_known(instr.condition)
        if hasattr(instr, "value"):
            instr.value = replace_if_known(instr.value)

    def _peephole_optimization(self):
        for func in self.program.functions.values():
            for block in func.blocks:
                new_instructions = []
                i = 0
                insns = block.instructions
                
                while i < len(insns):
                    curr = insns[i]
                    replaced = False

                    if curr.instruction_type == InstructionType.MOVE:
                        src = getattr(curr, "src", None)
                        dest = curr.dest
                        if isinstance(src, Temporary) and isinstance(dest, Temporary) and src.id == dest.id:
                            self.stats["peephole_rules"] += 1
                            replaced = True

                    elif curr.instruction_type in (InstructionType.ADD, InstructionType.SUB, InstructionType.MUL):
                        src1 = getattr(curr, "src1", None)
                        src2 = getattr(curr, "src2", None)
                        dest = curr.dest
                        zero = isinstance(src2, Literal) and src2.value == 0
                        one = isinstance(src2, Literal) and src2.value == 1
                        
                        if curr.instruction_type == InstructionType.ADD and zero:
                            new_instructions.append(InstructionFactory.move(dest, src1, comment="peephole: +0"))
                            self.stats["peephole_rules"] += 1
                            replaced = True
                        elif curr.instruction_type == InstructionType.SUB and zero:
                            new_instructions.append(InstructionFactory.move(dest, src1, comment="peephole: -0"))
                            self.stats["peephole_rules"] += 1
                            replaced = True
                        elif curr.instruction_type == InstructionType.MUL and one:
                            new_instructions.append(InstructionFactory.move(dest, src1, comment="peephole: *1"))
                            self.stats["peephole_rules"] += 1
                            replaced = True

                    if not replaced:
                        new_instructions.append(curr)
                    i += 1
                
                block.instructions = new_instructions

    def _dead_code_elimination(self):
        for func in self.program.functions.values():
            for block in func.blocks:
                cleaned = []
                terminator_found = False
                for instr in block.instructions:
                    if terminator_found:
                        self.stats["dead_code_removed"] += 1
                        continue
                    cleaned.append(instr)
                    if instr.instruction_type in (InstructionType.JUMP, InstructionType.JUMP_IF, 
                                                  InstructionType.JUMP_IF_NOT, InstructionType.RETURN):
                        terminator_found = True
                block.instructions = cleaned

                live_temps: Set[int] = set()
                final_instructions = []

                for instr in reversed(block.instructions):
                    uses = self._get_uses(instr)
                    defs = self._get_defs(instr)

                    has_side_effects = instr.instruction_type in (
                        InstructionType.CALL, InstructionType.STORE, InstructionType.RETURN,
                        InstructionType.JUMP, InstructionType.JUMP_IF, InstructionType.JUMP_IF_NOT,
                        InstructionType.LABEL, InstructionType.PHI, InstructionType.ALLOCA, InstructionType.PARAM
                    )
                    
                    dest = instr.dest
                    is_dead_def = (
                        dest and isinstance(dest, Temporary) and 
                        dest.id not in live_temps and 
                        not has_side_effects
                    )
                    
                    if is_dead_def:
                        self.stats["dead_code_removed"] += 1
                    else:
                        final_instructions.append(instr)

                    live_temps.update(uses)
                    live_temps.difference_update(defs)

                block.instructions = list(reversed(final_instructions))

    def _get_uses(self, instr: Instruction) -> Set[int]:
        uses = set()
        for op in instr.get_uses():
            if isinstance(op, Temporary):
                uses.add(op.id)
        return uses

    def _get_defs(self, instr: Instruction) -> Set[int]:
        defs = set()
        for op in instr.get_defs():
            if isinstance(op, Temporary):
                defs.add(op.id)
        return defs