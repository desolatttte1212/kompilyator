
from typing import List, Tuple
from .label_manager import LabelManager


class LogicalOpsGenerator:

    def __init__(self, label_manager: LabelManager):
        self.labels = label_manager
        self.output: List[str] = []

    def generate_and(self, left_reg: str, right_reg: str,
                     dest_reg: str, labels: Tuple[str, str]) -> str:
        lines = []

        lines.append(f"    test {left_reg}, {left_reg}")
        false_label = self.labels.format_label(labels[0])
        lines.append(f"    jz {false_label}  ; Short-circuit AND")

        lines.append(f"    test {right_reg}, {right_reg}")
        lines.append(f"    jz {false_label}")

        lines.append(f"    mov {dest_reg}, 1")
        end_label = self.labels.format_label(labels[1])
        lines.append(f"    jmp {end_label}")

        lines.append(f"{false_label}:")
        lines.append(f"    mov {dest_reg}, 0")
        lines.append(f"{end_label}:")

        return "\n".join(lines)

    def generate_or(self, left_reg: str, right_reg: str,
                    dest_reg: str, labels: Tuple[str, str]) -> str:
        lines = []

        lines.append(f"    test {left_reg}, {left_reg}")
        true_label = self.labels.format_label(labels[0])
        lines.append(f"    jnz {true_label}  ; Short-circuit OR")

        lines.append(f"    test {right_reg}, {right_reg}")
        lines.append(f"    jnz {true_label}")

        lines.append(f"    mov {dest_reg}, 0")
        end_label = self.labels.format_label(labels[1])
        lines.append(f"    jmp {end_label}")

        lines.append(f"{true_label}:")
        lines.append(f"    mov {dest_reg}, 1")
        lines.append(f"{end_label}:")

        return "\n".join(lines)

    def generate_not(self, src_reg: str, dest_reg: str) -> str:
        return f"    xor {dest_reg}, 1  ; Logical NOT"

    def generate_bool_test(self, reg: str) -> str:
        return "\n".join([
            f"    test {reg}, {reg}",
            f"    setnz al",
            f"    movzx {reg}, al"
        ])