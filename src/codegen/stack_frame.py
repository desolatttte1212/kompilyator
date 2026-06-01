
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class StackFrame:
    func_name: str
    param_count: int = 0

    param_offsets: Dict[int, int] = field(default_factory=dict)
    local_offsets: Dict[str, int] = field(default_factory=dict)
    temp_offsets: Dict[int, int] = field(default_factory=dict)

    param_names: Dict[str, int] = field(default_factory=dict)

    _next_offset: int = -8
    _stack_size: int = 0

    def __post_init__(self):
        if self.param_offsets is None:
            self.param_offsets = {}
        if self.local_offsets is None:
            self.local_offsets = {}
        if self.temp_offsets is None:
            self.temp_offsets = {}
        if self.param_names is None:
            self.param_names = {}

    def allocate_param(self, index: int, name: Optional[str] = None) -> int:
        if index not in self.param_offsets:
            self.param_offsets[index] = self._next_offset
            self._next_offset -= 8
        if name:
            self.param_names[name] = index
        return self.param_offsets[index]

    def allocate_local(self, name: str, size: int = 8) -> int:
        if name not in self.local_offsets:
            aligned_size = ((size + 7) // 8) * 8
            self.local_offsets[name] = self._next_offset
            self._next_offset -= aligned_size
        return self.local_offsets[name]

    def allocate_temp(self, temp_id: int, size: int = 8) -> int:
        if temp_id not in self.temp_offsets:
            aligned_size = ((size + 7) // 8) * 8
            self.temp_offsets[temp_id] = self._next_offset
            self._next_offset -= aligned_size
        return self.temp_offsets[temp_id]

    def get_offset(self, name: str) -> Optional[int]:
        if name in self.local_offsets:
            return self.local_offsets[name]
        if name in self.param_names:
            param_idx = self.param_names[name]
            return self.param_offsets.get(param_idx)
        return None

    def get_temp_offset(self, temp_id: int) -> int:
        return self.temp_offsets[temp_id]

    def finalize(self) -> int:
        raw_size = -self._next_offset
        aligned = ((raw_size + 15) // 16) * 16
        self._stack_size = aligned
        return aligned

    @property
    def stack_size(self) -> int:
        return self._stack_size

    @property
    def prologue(self) -> str:
        lines = [
            "    push rbp",
            "    mov rbp, rsp",
        ]
        if self._stack_size > 0:
            lines.append(f"    sub rsp, {self._stack_size}")
        return "\n".join(lines)

    @property
    def epilogue(self) -> str:
        lines = []
        if self._stack_size > 0:
            lines.append(f"    mov rsp, rbp")
        lines.extend([
            "    pop rbp",
            "    ret"
        ])
        return "\n".join(lines)