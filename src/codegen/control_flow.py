
from typing import List, Optional, Tuple
from .label_manager import LabelManager


class ControlFlowGenerator:

    def __init__(self, label_manager: LabelManager):
        self.labels = label_manager
        self.output: List[str] = []

    def generate_if(self, cond_reg: str, then_labels: Tuple[str, str],
                    else_labels: Optional[Tuple[str, str]] = None) -> str:
        lines = []

        lines.append(f"    test {cond_reg}, {cond_reg}")

        if else_labels:
            else_start = self.labels.format_label(else_labels[0])
            lines.append(f"    jz {else_start}")
        else:
            then_end = self.labels.format_label(then_labels[1])
            lines.append(f"    jz {then_end}")

        then_start = self.labels.format_label(then_labels[0])
        lines.append(f"{then_start}:")

        return "\n".join(lines)

    def generate_if_else_join(self, then_labels: Tuple[str, str],
                              else_labels: Tuple[str, str]) -> str:
        lines = []

        merge_label = self.labels.format_label(then_labels[1])
        lines.append(f"    jmp {merge_label}")

        else_start = self.labels.format_label(else_labels[0])
        lines.append(f"{else_start}:")
        lines.append(f"{merge_label}:")

        return "\n".join(lines)

    def generate_while(self, cond_reg: str, loop_labels: Tuple[str, str, str]) -> str:
        lines = []

        cond_label = self.labels.format_label(loop_labels[0])
        lines.append(f"{cond_label}:")

        lines.append(f"    test {cond_reg}, {cond_reg}")
        end_label = self.labels.format_label(loop_labels[2])
        lines.append(f"    jz {end_label}")

        body_label = self.labels.format_label(loop_labels[1])
        lines.append(f"{body_label}:")

        return "\n".join(lines)

    def generate_while_end(self, loop_labels: Tuple[str, str, str]) -> str:
        lines = []

        cond_label = self.labels.format_label(loop_labels[0])
        lines.append(f"    jmp {cond_label}")

        end_label = self.labels.format_label(loop_labels[2])
        lines.append(f"{end_label}:")

        return "\n".join(lines)

    def generate_for(self, init_code: str, cond_reg: str, update_code: str,
                     loop_labels: Tuple[str, str, str]) -> str:
        lines = []

        if init_code:
            lines.append(f"    ; For init")
            lines.append(f"    {init_code}")

        lines.append(self.generate_while(cond_reg, loop_labels))

        return "\n".join(lines)

    def generate_for_update(self, update_code: str, loop_labels: Tuple[str, str, str]) -> str:
        lines = []

        if update_code:
            lines.append(f"    ; For update")
            lines.append(f"    {update_code}")

        cond_label = self.labels.format_label(loop_labels[0])
        lines.append(f"    jmp {cond_label}")

        end_label = self.labels.format_label(loop_labels[2])
        lines.append(f"{end_label}:")

        return "\n".join(lines)