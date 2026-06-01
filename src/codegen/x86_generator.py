import sys
from typing import List, Optional
from ..ir.basic_block import IRProgram, IRFunction, BasicBlock
from ..ir.instructions import InstructionType
from ..ir.operand import Temporary, Variable, Literal, MemoryLocation, Label
from .abi import INTEGER_PARAM_REGISTERS, Register
from .stack_frame import StackFrame
from .label_manager import LabelManager
from .control_flow import ControlFlowGenerator
from .logical_ops import LogicalOpsGenerator


class X86Generator:
    # 🚨 64-битные регистры для Windows x64 ABI
    REG_DST = 'rax'
    REG_SRC = 'rdx'
    REG_DIV = 'rcx'

    def __init__(self, ir_program: IRProgram):
        self.ir = ir_program
        self.output: List[str] = []
        self.current_frame: Optional[StackFrame] = None

        self.label_manager = LabelManager()
        self.cf_gen = ControlFlowGenerator(self.label_manager)
        self.logic_gen = LogicalOpsGenerator(self.label_manager)

    def _extract_temps(self, op, temps_set):
        """Рекурсивно собирает все Temporary из операнда, включая вложенные в MemoryLocation"""
        if op is None:
            return
        if isinstance(op, Temporary):
            temps_set.add(op.id)
        elif isinstance(op, MemoryLocation):
            # Рекурсивно проверяем базу и смещение
            base = getattr(op, 'address', None) or getattr(op, 'base', None)
            self._extract_temps(base, temps_set)
            offset = getattr(op, 'offset', None)
            if isinstance(offset, Temporary):
                temps_set.add(offset.id)
        elif isinstance(op, (list, tuple)):
            for item in op:
                self._extract_temps(item, temps_set)
        elif hasattr(op, 'get_operands'):
            for operand in op.get_operands():
                self._extract_temps(operand, temps_set)

    def generate(self) -> str:
        # ЖЁСТКИЙ СПИСОК: эти функции НИКОГДА не генерируются как код
        EXTERN_WHITELIST = {"ExitProcess", "exit", "malloc", "free", "printf", "puts"}

        called_externs = set()
        for func in self.ir.functions.values():
            for block in func.blocks:
                for instr in block.instructions:
                    if instr.instruction_type.name == "CALL":
                        fname = getattr(instr, 'func_name', '')
                        if fname in EXTERN_WHITELIST:
                            called_externs.add(fname)

        self.output = ["section .text"]
        for name in sorted(called_externs):
            self.output.append(f"extern {name}")
        self.output.append("global main")
        self.output.append("")

        for func in self.ir.functions.values():
            if func.name in EXTERN_WHITELIST:
                continue
            self._generate_function(func)
            self.output.append("")

        return "\n".join(self.output)

    def _generate_function(self, func):
        self.output.append(f"{func.name}:")
        self.current_frame = StackFrame(func.name, len(func.parameters))

        # 1. Выделяем локальные переменные
        for name, (_, size) in func.local_vars.items():
            self.current_frame.allocate_local(name, size)

        # 2. 🔍 ПРЕДСКАН: Находим ВСЕ временные переменные (рекурсивно!)
        all_temps = set()
        for block in func.blocks:
            for instr in block.instructions:
                for attr in ['dest', 'src', 'src1', 'src2', 'value', 'condition', 'base', 'index']:
                    if hasattr(instr, attr):
                        val = getattr(instr, attr)
                        if val:
                            self._extract_temps(val, all_temps)
                if hasattr(instr, 'args'):
                    for arg in instr.args:
                        self._extract_temps(arg, all_temps)

        # 3. Выделяем слоты для всех найденных temps (8 байт для указателей!)
        for tid in all_temps:
            if tid not in self.current_frame.temp_offsets:
                self.current_frame.allocate_temp(tid, 8)

        # 4. Теперь finalize() посчитает корректный размер
        stack_sz = self.current_frame.finalize()

        # Минимальный размер для Shadow Space + выравнивание по 16 байт
        if stack_sz < 32:
            stack_sz = 32
        stack_sz = (stack_sz + 15) // 16 * 16

        # Пролог
        self.output.append("    push rbp")
        self.output.append("    mov rbp, rsp")
        if stack_sz > 0:
            self.output.append(f"    sub rsp, {stack_sz}")
        self.output.append("")

        # Тело функции
        for block in func.blocks:
            self._generate_block(block)

        # Эпилог
        self.output.append(f"    .{func.name}_exit:")
        if stack_sz > 0:
            self.output.append(f"    add rsp, {stack_sz}")
        self.output.append("    pop rbp")
        self.output.append("    ret")

    def _generate_block(self, block: BasicBlock):
        if block.instructions:
            self.output.append(f"    ; Block: {block.label.name}")

            if not block.label.name.endswith("_entry"):
                asm_label = self.label_manager.format_label(block.label.name)
                self.output.append(f"{asm_label}:")

            for instr in block.instructions:
                self._emit_instruction(instr)
            self.output.append("")

    def _emit_instruction(self, instr):
        # 🐛 ОТЛАДКА: Печатаем каждую инструкцию
        if self.current_frame and self.current_frame.func_name == "main":
            print(f"  [DEBUG] Processing: {instr.instruction_type.name} | dest={instr.dest} | comment={instr.comment}",
                  file=sys.stderr)

        itype = instr.instruction_type
        comment = f"  ; {instr.comment}" if instr.comment else ""
        # ... остальной код ...

        if itype == InstructionType.ADD:
            self._emit_binop("add", instr, comment)
        elif itype == InstructionType.SUB:
            self._emit_binop("sub", instr, comment)
        elif itype == InstructionType.MUL:
            self._emit_binop("imul", instr, comment)
        elif itype == InstructionType.DIV:
            self._emit_binop("idiv", instr, comment)
        elif itype == InstructionType.MOD:
            self._emit_binop("mod", instr, comment)
        elif itype == InstructionType.GEP:
            self._emit_gep(instr, comment)
        elif itype == InstructionType.AND:
            self._emit_binop("and", instr, comment)
        elif itype == InstructionType.OR:
            self._emit_binop("or", instr, comment)
        elif itype == InstructionType.NOT:
            self._emit_not(instr, comment)
        elif itype == InstructionType.NEG:
            self._emit_neg(instr, comment)
        elif itype == InstructionType.CMP_EQ:
            self._emit_cmp("e", instr, comment)
        elif itype == InstructionType.CMP_NE:
            self._emit_cmp("ne", instr, comment)
        elif itype == InstructionType.CMP_LT:
            self._emit_cmp("l", instr, comment)
        elif itype == InstructionType.CMP_LE:
            self._emit_cmp("le", instr, comment)
        elif itype == InstructionType.CMP_GT:
            self._emit_cmp("g", instr, comment)
        elif itype == InstructionType.CMP_GE:
            self._emit_cmp("ge", instr, comment)
        elif itype == InstructionType.LOAD:
            self._emit_load(instr, comment)
        elif itype == InstructionType.STORE:
            self._emit_store(instr, comment)
        elif itype == InstructionType.RETURN:
            self._emit_return(instr, comment)
        elif itype == InstructionType.CALL:
            self._emit_call(instr, comment)
        elif itype == InstructionType.JUMP:
            self._emit_jump(instr.target, comment, cond="jmp")
        elif itype == InstructionType.JUMP_IF:
            self._emit_jump_if(instr, comment, invert=False)
        elif itype == InstructionType.JUMP_IF_NOT:
            self._emit_jump_if(instr, comment, invert=True)
        elif itype == InstructionType.IF_START:
            self._emit_if_start(instr, comment)
        elif itype == InstructionType.IF_END:
            self._emit_if_end(instr, comment)
        elif itype == InstructionType.WHILE_START:
            self._emit_while_start(instr, comment)
        elif itype == InstructionType.WHILE_END:
            self._emit_while_end(instr, comment)
        elif itype == InstructionType.LOGICAL_AND:
            self._emit_logical_and(instr, comment)
        elif itype == InstructionType.LOGICAL_OR:
            self._emit_logical_or(instr, comment)
        elif itype == InstructionType.MOVE:
            self._emit_move_instr(instr, comment)
        elif itype in (InstructionType.ALLOCA, InstructionType.PARAM, InstructionType.PHI):
            pass
        else:
            self.output.append(f"    ; TODO: {itype.name} not implemented{comment}")

    def _emit_gep(self, instr, comment: str):
        base = self._resolve_operand(instr.base)
        index = self._resolve_operand(instr.index)
        dest = self._resolve_operand(instr.dest)

        self._load_to_reg(base, self.REG_DST)
        self._load_to_reg(index, self.REG_SRC)
        self.output.append(f"    imul {self.REG_SRC}, 4")
        self.output.append(f"    add {self.REG_DST}, {self.REG_SRC}{comment}")

        if self._is_mem(dest):
            self.output.append(f"    mov {dest}, {self.REG_DST}")
        elif dest != self.REG_DST:
            self.output.append(f"    mov {dest}, {self.REG_DST}")

    def _is_mem(self, op_str: str) -> bool:
        return '[' in op_str

    def _load_to_reg(self, op_str: str, reg: str):
        if op_str == reg:
            return
        self.output.append(f"    mov {reg}, {op_str}")

    def _emit_binop(self, op: str, instr, comment: str):
        src1 = self._resolve_operand(instr.src1)
        src2 = self._resolve_operand(instr.src2)
        dest = self._resolve_operand(instr.dest)

        self._load_to_reg(src1, self.REG_DST)

        if op in ("idiv", "mod"):
            self.output.append(f"    cqo")
            self._load_to_reg(src2, self.REG_DIV)
            self.output.append(f"    idiv {self.REG_DIV}{comment}")
            if op == "mod":
                self.output.append(f"    mov {self.REG_DST}, rdx")
        else:
            if src2 != self.REG_DST:
                self._load_to_reg(src2, self.REG_SRC)
            else:
                self.output.append(f"    mov {self.REG_SRC}, {self.REG_DST}")
            if op == "imul":
                self.output.append(f"    imul {self.REG_DST}, {self.REG_SRC}{comment}")
            else:
                self.output.append(f"    {op} {self.REG_DST}, {self.REG_SRC}{comment}")

        if self._is_mem(dest):
            self.output.append(f"    mov {dest}, {self.REG_DST}")
        elif dest != self.REG_DST:
            self.output.append(f"    mov {dest}, {self.REG_DST}")

    def _emit_neg(self, instr, comment: str):
        src = self._resolve_operand(instr.src)
        dest = self._resolve_operand(instr.dest)
        self._load_to_reg(src, self.REG_DST)
        self.output.append(f"    neg {self.REG_DST}{comment}")
        if self._is_mem(dest):
            self.output.append(f"    mov {dest}, {self.REG_DST}")
        elif dest != self.REG_DST:
            self.output.append(f"    mov {dest}, {self.REG_DST}")

    def _emit_not(self, instr, comment: str):
        src = self._resolve_operand(instr.src)
        dest = self._resolve_operand(instr.dest)
        self._load_to_reg(src, self.REG_DST)
        self.output.append(f"    xor {self.REG_DST}, -1{comment}")
        if self._is_mem(dest):
            self.output.append(f"    mov {dest}, {self.REG_DST}")
        elif dest != self.REG_DST:
            self.output.append(f"    mov {dest}, {self.REG_DST}")

    def _emit_cmp(self, suffix: str, instr, comment: str):
        src1 = self._resolve_operand(instr.src1)
        src2 = self._resolve_operand(instr.src2)
        dest = self._resolve_operand(instr.dest)
        self._load_to_reg(src1, self.REG_DST)
        if src2 != self.REG_DST:
            self._load_to_reg(src2, self.REG_SRC)
        else:
            self.output.append(f"    mov {self.REG_SRC}, {self.REG_DST}")
        self.output.append(f"    cmp {self.REG_DST}, {self.REG_SRC}{comment}")
        self.output.append(f"    set{suffix} al")
        self.output.append(f"    movzx eax, al")
        if self._is_mem(dest):
            self.output.append(f"    mov {dest}, eax")
        elif dest != "eax":
            self.output.append(f"    mov {dest}, eax")

    def _emit_store(self, instr, comment: str):
        dest = instr.dest
        src = instr.src

        if isinstance(dest, MemoryLocation):
            base = getattr(dest, 'address', None) or getattr(dest, 'base', None)
            if isinstance(base, Variable):
                offset = self.current_frame.get_offset(base.name)
                dest_str = f"[rbp{offset:+d}]"
                src_str = self._resolve_operand(src)
                self._load_to_reg(src_str, self.REG_DST)
                self.output.append(f"    mov {dest_str}, {self.REG_DST}{comment}")
                return

            base_str = self._resolve_operand(base)
            addr_reg = "r8"
            val_reg = "eax"

            self.output.append(f"    mov {addr_reg}, {base_str}")
            offset = getattr(dest, 'offset', 0)
            if offset != 0:
                self.output.append(f"    add {addr_reg}, {offset}")

            src_str = self._resolve_operand(src)
            if src_str.startswith("["):
                self.output.append(f"    mov {val_reg}, {src_str}")
            else:
                self.output.append(f"    mov {val_reg}, {src_str}")

            self.output.append(f"    mov [{addr_reg}], {val_reg}{comment}")
            return

        dest_str = self._resolve_operand(dest)
        src_str = self._resolve_operand(src)
        self._load_to_reg(src_str, self.REG_DST)
        self.output.append(f"    mov {dest_str}, {self.REG_DST}{comment}")

    def _emit_load(self, instr, comment: str):
        dest = instr.dest
        src = instr.src

        if isinstance(src, MemoryLocation):
            base = getattr(src, 'address', None) or getattr(src, 'base', None)
            if isinstance(base, Variable):
                offset = self.current_frame.get_offset(base.name)
                src_str = f"[rbp{offset:+d}]"
                dest_str = self._resolve_operand(dest)
                self._load_to_reg(src_str, self.REG_DST)
                if self._is_mem(dest_str):
                    self.output.append(f"    mov {dest_str}, {self.REG_DST}{comment}")
                elif dest_str != self.REG_DST:
                    self.output.append(f"    mov {dest_str}, {self.REG_DST}{comment}")
                return

            base_str = self._resolve_operand(base)
            addr_reg = "r8"
            val_reg = "eax"

            self.output.append(f"    mov {addr_reg}, {base_str}")
            offset = getattr(src, 'offset', 0)
            if offset != 0:
                self.output.append(f"    add {addr_reg}, {offset}")

            self.output.append(f"    mov {val_reg}, [{addr_reg}]")

            dest_str = self._resolve_operand(dest)
            if dest_str.startswith("["):
                self.output.append(f"    mov {dest_str}, {val_reg}{comment}")
            else:
                self.output.append(f"    mov {dest_str}, {val_reg}{comment}")
            return

        dest_str = self._resolve_operand(dest)
        src_str = self._resolve_operand(src)
        self._load_to_reg(src_str, self.REG_DST)
        if self._is_mem(dest_str):
            self.output.append(f"    mov {dest_str}, {self.REG_DST}{comment}")
        elif dest_str != self.REG_DST:
            self.output.append(f"    mov {dest_str}, {self.REG_DST}{comment}")

    def _emit_return(self, instr, comment: str):
        if instr.value:
            val = self._resolve_operand(instr.value)
            self._load_to_reg(val, "eax")
            if comment:
                self.output[-1] += comment
        self._emit_jump(f"{self.current_frame.func_name}_exit", cond="jmp")

    def _emit_call(self, instr, comment: str):
        func_name = instr.func_name
        WIN_ARG_REGS = ["rcx", "rdx", "r8", "r9"]
        arg_regs = WIN_ARG_REGS[:len(instr.args)]

        for reg, arg in zip(arg_regs, instr.args):
            arg_asm = self._resolve_operand(arg)
            self._load_to_reg(arg_asm, reg)

        if func_name in ("printf", "scanf"):
            self.output.append("    xor eax, eax")

        self.output.append(f"    call {func_name}{comment}")

        if instr.dest:
            dest_asm = self._resolve_operand(instr.dest)
            if self._is_mem(dest_asm):
                self.output.append(f"    mov {dest_asm}, rax")
            elif dest_asm != "rax":
                self.output.append(f"    mov {dest_asm}, rax")

    def _emit_jump(self, target, comment: str = "", cond: str = "jmp"):
        asm_target = self.label_manager.format_label(target)
        self.output.append(f"    {cond} {asm_target}{comment}")

    def _emit_jump_if(self, instr, comment: str, invert: bool):
        cond_asm = self._resolve_operand(instr.condition)
        if self._is_mem(cond_asm):
            self.output.append(f"    mov {self.REG_DST}, {cond_asm}")
            self.output.append(f"    test {self.REG_DST}, {self.REG_DST}")
        else:
            self.output.append(f"    test {cond_asm}, {cond_asm}")
        target = instr.target
        cond = "jz" if not invert else "jnz"
        self._emit_jump(target, comment, cond=cond)

    def _emit_if_start(self, instr, comment: str):
        cond_reg = self._resolve_operand(instr.condition)
        if self._is_mem(cond_reg):
            self.output.append(f"    mov {self.REG_DST}, {cond_reg}")
            cond_reg = self.REG_DST
        then_start = instr.then_label
        then_end = instr.merge_label
        else_start = getattr(instr, 'else_label', None)
        self.label_manager.enter_conditional()
        self.output.append(f"    test {cond_reg}, {cond_reg}")
        if else_start:
            else_label = self.label_manager.format_label(else_start)
            self.output.append(f"    jz {else_label}")
        else:
            merge_label = self.label_manager.format_label(then_end)
            self.output.append(f"    jz {merge_label}")
        then_label = self.label_manager.format_label(then_start)
        self.output.append(f"{then_label}:")
        if comment:
            self.output[-1] += comment

    def _emit_if_end(self, instr, comment: str):
        then_end = instr.merge_label
        else_start = getattr(instr, 'else_label', None)
        if else_start:
            merge_label = self.label_manager.format_label(then_end)
            self.output.append(f"    jmp {merge_label}")
            else_label = self.label_manager.format_label(else_start)
            self.output.append(f"{else_label}:")
            self.output.append(f"{merge_label}:")
        else:
            merge_label = self.label_manager.format_label(then_end)
            self.output.append(f"{merge_label}:")
        self.label_manager.exit_conditional()
        if comment:
            self.output[-1] += comment

    def _emit_while_start(self, instr, comment: str):
        cond_reg = self._resolve_operand(instr.condition)
        if self._is_mem(cond_reg):
            self.output.append(f"    mov {self.REG_DST}, {cond_reg}")
            cond_reg = self.REG_DST
        cond_label = instr.cond_label
        body_label = instr.body_label
        end_label = instr.end_label
        self.label_manager.enter_loop()
        cond_asm = self.label_manager.format_label(cond_label)
        self.output.append(f"{cond_asm}:")
        self.output.append(f"    test {cond_reg}, {cond_reg}")
        end_asm = self.label_manager.format_label(end_label)
        self.output.append(f"    jz {end_asm}")
        body_asm = self.label_manager.format_label(body_label)
        self.output.append(f"{body_asm}:")
        if comment:
            self.output[-1] += comment

    def _emit_while_end(self, instr, comment: str):
        cond_label = instr.cond_label
        end_label = instr.end_label
        cond_asm = self.label_manager.format_label(cond_label)
        self.output.append(f"    jmp {cond_asm}")
        end_asm = self.label_manager.format_label(end_label)
        self.output.append(f"{end_asm}:")
        self.label_manager.exit_loop()
        if comment:
            self.output[-1] += comment

    def _emit_logical_and(self, instr, comment: str):
        left_reg = self._resolve_operand(instr.left)
        right_reg = self._resolve_operand(instr.right)
        dest_reg = self._resolve_operand(instr.dest)
        false_label = instr.false_label
        end_label = instr.end_label
        if self._is_mem(left_reg):
            self.output.append(f"    mov {self.REG_DST}, {left_reg}")
            left_reg = self.REG_DST
        self.output.append(f"    test {left_reg}, {left_reg}")
        false_asm = self.label_manager.format_label(false_label)
        self.output.append(f"    jz {false_asm}  ; Short-circuit AND")
        if self._is_mem(right_reg):
            self.output.append(f"    mov {self.REG_DST}, {right_reg}")
            right_reg = self.REG_DST
        self.output.append(f"    test {right_reg}, {right_reg}")
        self.output.append(f"    jz {false_asm}")
        self.output.append(f"    mov {dest_reg}, 1")
        end_asm = self.label_manager.format_label(end_label)
        self.output.append(f"    jmp {end_asm}")
        self.output.append(f"{false_asm}:")
        self.output.append(f"    mov {dest_reg}, 0")
        self.output.append(f"{end_asm}:")
        if comment:
            self.output[-1] += comment

    def _emit_logical_or(self, instr, comment: str):
        left_reg = self._resolve_operand(instr.left)
        right_reg = self._resolve_operand(instr.right)
        dest_reg = self._resolve_operand(instr.dest)
        true_label = instr.true_label
        end_label = instr.end_label
        if self._is_mem(left_reg):
            self.output.append(f"    mov {self.REG_DST}, {left_reg}")
            left_reg = self.REG_DST
        self.output.append(f"    test {left_reg}, {left_reg}")
        true_asm = self.label_manager.format_label(true_label)
        self.output.append(f"    jnz {true_asm}  ; Short-circuit OR")
        if self._is_mem(right_reg):
            self.output.append(f"    mov {self.REG_DST}, {right_reg}")
            right_reg = self.REG_DST
        self.output.append(f"    test {right_reg}, {right_reg}")
        self.output.append(f"    jnz {true_asm}")
        self.output.append(f"    mov {dest_reg}, 0")
        end_asm = self.label_manager.format_label(end_label)
        self.output.append(f"    jmp {end_asm}")
        self.output.append(f"{true_asm}:")
        self.output.append(f"    mov {dest_reg}, 1")
        self.output.append(f"{end_asm}:")
        if comment:
            self.output[-1] += comment

    def _emit_move_instr(self, instr, comment: str):
        src = self._resolve_operand(instr.src)
        dest = self._resolve_operand(instr.dest)
        if self._is_mem(dest) and self._is_mem(src):
            self.output.append(f"    mov {self.REG_DST}, {src}")
            self.output.append(f"    mov {dest}, {self.REG_DST}{comment}")
        else:
            if self._is_mem(dest) and isinstance(instr.src, Literal):
                self.output.append(f"    mov dword {dest}, {src}{comment}")
            else:
                self.output.append(f"    mov {dest}, {src}{comment}")

    def _resolve_operand(self, op) -> str:
        if op is None:
            return "0"
        if isinstance(op, Temporary):
            tname = f"t{op.id}"
            # Временная переменная должна быть уже выделена в предскане
            if op.id not in self.current_frame.temp_offsets:
                self.current_frame.allocate_temp(op.id, 8)
            off = self.current_frame.get_temp_offset(op.id)
            return f"[rbp{off:+d}]"
        elif isinstance(op, Variable):
            off = self.current_frame.get_offset(op.name)
            if off is not None:
                return f"[rbp{off:+d}]"
            return f"[{op.name}]"
        elif isinstance(op, Literal):
            return str(int(op.value) if isinstance(op.value, bool) else op.value)
        elif isinstance(op, MemoryLocation):
            addr_op = getattr(op, 'address', None) or getattr(op, 'base', None)
            if addr_op is None:
                return "[0]"
            base = self._resolve_operand(addr_op)
            base_inner = base.strip('[]')
            offset = getattr(op, 'offset', 0)
            if offset == 0:
                return f"[{base_inner}]"
            return f"[{base_inner} + {offset}]"
        elif isinstance(op, Label):
            return str(op.name)
        return str(op)

    def save_to_file(self, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.generate())