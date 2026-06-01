from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from .operand import Operand, Temporary, Variable, Literal, Label, MemoryLocation
from .instructions import Instruction, InstructionType, is_terminator, is_control_flow, is_memory_op
from .basic_block import BasicBlock, BlockType, IRFunction, IRProgram

class IRPrinter:
    def __init__(self, show_comments: bool = True, show_empty_blocks: bool = False):
        self.show_comments = show_comments
        self.show_empty_blocks = show_empty_blocks

    def print_program(self, program: IRProgram) -> str:
        lines = []
        lines.append("# IR Program")
        lines.append("")

        if program.globals:
            lines.append("# Global variables")
            for name, operand in program.globals.items():
                lines.append(f".global {name} = {operand}")
            lines.append("")

        for name, func in program.functions.items():
            lines.append(self.print_function(func))
            lines.append("")

        return "\n".join(lines)

    def print_function(self, func: IRFunction) -> str:
        lines = []

        params = ", ".join(f"{name}: {type_}" for name, type_ in func.parameters)
        lines.append(f"function {func.name}: {func.return_type} ({params})")

        for block in func.blocks:
            block_str = self.print_block(block)
            if block_str:
                lines.append(block_str)

        return "\n".join(lines)

    def print_block(self, block: BasicBlock) -> str:
        if block.is_empty() and not self.show_empty_blocks:
            if block.block_type != BlockType.JOIN or not block.predecessors:
                return ""

        lines = []

        block_type_str = f"  # {block.block_type.name}" if block.block_type != BlockType.NORMAL else ""
        lines.append(f"{block.label}:{block_type_str}")

        for instr in block.instructions:
            instr_str = str(instr)

            lines.append(f"  {instr_str}")

        return "\n".join(lines)

    def print_to_file(self, program: IRProgram, filepath: str):
        output = self.print_program(program)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(output)

class CFGDotPrinter:
    BLOCK_COLORS = {
        BlockType.ENTRY: "#90EE90",
        BlockType.NORMAL: "#FFFFFF",
        BlockType.EXIT: "#FFB6C1",
        BlockType.LOOP_HEADER: "#87CEEB",
        BlockType.LOOP_BODY: "#E0FFFF",
        BlockType.JOIN: "#DDA0DD",
    }

    def __init__(self, show_comments: bool = False, rankdir: str = "TB", fontname: str = "Courier"):
        self.show_comments = show_comments
        self.rankdir = rankdir
        self.fontname = fontname

    def generate_program(self, program: IRProgram) -> str:
        lines = []
        lines.append("digraph IR_Program {")
        lines.append(f"  rankdir={self.rankdir};")
        lines.append(f"  fontname=\"{self.fontname}\";")
        lines.append("  node [shape=box, fontname=\"Courier\", fontsize=10];")
        lines.append("  edge [fontname=\"Courier\"];")
        lines.append("")

        for func_name, func in program.functions.items():
            lines.append(self.generate_function(func))
            lines.append("")

        lines.append("}")
        return "\n".join(lines)

    def generate_function(self, func: IRFunction) -> str:
        lines = []
        lines.append(f"  subgraph cluster_{func.name} {{")
        lines.append(
            f"    label=\"Function: {func.name}\\n{func.return_type} ({', '.join(p[0] for p in func.parameters)})\";")
        lines.append("    style=rounded;")
        lines.append("    color=black;")
        lines.append("")

        for block in func.blocks:
            node_str = self._create_block_node(func.name, block)
            lines.append(f"    {node_str}")

        lines.append("")

        for block in func.blocks:
            edges = self._create_block_edges(func.name, block)
            lines.extend(f"    {edge}" for edge in edges)

        lines.append("  }")
        return "\n".join(lines)

    def _create_block_node(self, func_name: str, block: BasicBlock) -> str:
        color = self.BLOCK_COLORS.get(block.block_type, "#FFFFFF")

        content_lines = []
        content_lines.append(block.label.name)
        content_lines.append(f"[{block.block_type.name}]")

        for instr in block.instructions:
            instr_text = str(instr)

            if not self.show_comments and "#" in instr_text:
                instr_text = instr_text.split("#")[0].strip()

            if len(instr_text) > 60:
                instr_text = instr_text[:57] + "..."

            instr_text = instr_text.replace('"', '\\"')

            content_lines.append(instr_text)

        content = "\\n".join(content_lines)

        node_id = self._node_id(func_name, block)
        return f'{node_id} [label="{content}", style=filled, fillcolor="{color}"];'

    def _create_block_edges(self, func_name: str, block: BasicBlock) -> List[str]:
        edges = []
        from_id = self._node_id(func_name, block)

        for succ in block.successors:
            to_id = self._node_id(func_name, succ)

            terminator = block.get_terminator()
            edge_label = ""
            edge_color = "black"

            if terminator:
                from .instructions import ConditionalJumpInstr
                if isinstance(terminator, ConditionalJumpInstr):
                    if succ == block.successors[0]:
                        edge_label = "true"
                        edge_color = "green"
                    else:
                        edge_label = "false"
                        edge_color = "red"

            edge_attrs = []
            if edge_label:
                edge_attrs.append(f'label="{edge_label}"')
            if edge_color != "black":
                edge_attrs.append(f'color="{edge_color}"')

            attr_str = f" [{', '.join(edge_attrs)}]" if edge_attrs else ""
            edges.append(f"{from_id} -> {to_id}{attr_str};")

        return edges

    def _node_id(self, func_name: str, block: BasicBlock) -> str:
        safe_label = block.label.name.replace(":", "_").replace("-", "_")
        return f"{func_name}_{safe_label}"

    def generate_to_file(self, program: IRProgram, filepath: str):
        output = self.generate_program(program)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(output)

class IRJsonPrinter:
    def __init__(self, indent: int = 2):
        self.indent = indent

    def program_to_dict(self, program: IRProgram) -> dict:
        return {
            "type": "IRProgram",
            "globals": {
                name: self._operand_to_dict(operand)
                for name, operand in program.globals.items()
            },
            "functions": {
                name: self.function_to_dict(func)
                for name, func in program.functions.items()
            }
        }

    def function_to_dict(self, func: IRFunction) -> dict:
        return {
            "type": "IRFunction",
            "name": func.name,
            "return_type": func.return_type,
            "parameters": [
                {"name": name, "type": type_}
                for name, type_ in func.parameters
            ],
            "blocks": [
                self.block_to_dict(block)
                for block in func.blocks
            ],
            "variable_map": {
                name: self._operand_to_dict(operand)
                for name, operand in func.variable_map.items()
            }
        }

    def block_to_dict(self, block: BasicBlock) -> dict:
        return {
            "type": "BasicBlock",
            "label": block.label.name,
            "block_type": block.block_type.name,
            "instructions": [
                self.instruction_to_dict(instr)
                for instr in block.instructions
            ],
            "predecessors": [b.label.name for b in block.predecessors],
            "successors": [b.label.name for b in block.successors]
        }

    def instruction_to_dict(self, instr: Instruction) -> dict:
        return {
            "type": instr.instruction_type.name,
            "dest": self._operand_to_dict(instr.dest) if instr.dest else None,
            "operands": [
                self._operand_to_dict(op)
                for op in instr.get_operands()
            ],
            "comment": instr.comment
        }

    def _operand_to_dict(self, operand: Optional[Operand]) -> Optional[dict]:
        if operand is None:
            return None

        if isinstance(operand, Temporary):
            return {"type": "Temporary", "id": operand.id, "value": str(operand)}
        elif isinstance(operand, Variable):
            return {"type": "Variable", "name": operand.name, "value": str(operand)}
        elif isinstance(operand, Literal):
            return {"type": "Literal", "value": operand.value, "str": str(operand)}
        elif isinstance(operand, Label):
            return {"type": "Label", "name": operand.name, "value": str(operand)}
        elif isinstance(operand, MemoryLocation):
            return {
                "type": "MemoryLocation",
                "address": self._operand_to_dict(operand.address),
                "offset": operand.offset,
                "value": str(operand)
            }
        else:
            return {"type": "Unknown", "value": str(operand)}

    def to_json(self, program: IRProgram) -> str:
        import json
        data = self.program_to_dict(program)
        return json.dumps(data, indent=self.indent, ensure_ascii=False)

    def write_to_file(self, program: IRProgram, filepath: str):
        output = self.to_json(program)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(output)

def print_ir(program: IRProgram, show_comments: bool = True) -> str:
    printer = IRPrinter(show_comments=show_comments)
    return printer.print_program(program)


def generate_cfg_dot(program: IRProgram, show_comments: bool = False) -> str:
    printer = CFGDotPrinter(show_comments=show_comments)
    return printer.generate_program(program)


def ir_to_json(program: IRProgram, indent: int = 2) -> str:
    printer = IRJsonPrinter(indent=indent)
    return printer.to_json(program)