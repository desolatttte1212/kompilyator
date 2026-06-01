
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class LabelContext:
    prefix: str
    counter: int = 0
    parent: Optional['LabelContext'] = None

    def new_label(self, suffix: str = "") -> str:
        label = f"{self.prefix}_{self.counter}"
        if suffix:
            label = f"{label}_{suffix}"
        self.counter += 1
        return label


class LabelManager:
    def __init__(self):
        self._contexts: List[LabelContext] = []
        self._push_context("func")

    def _push_context(self, prefix: str):
        ctx = LabelContext(prefix=prefix, parent=self._contexts[-1] if self._contexts else None)
        self._contexts.append(ctx)

    def _pop_context(self):
        if len(self._contexts) > 1:
            self._contexts.pop()

    def new_label(self, kind: str) -> str:
        ctx = self._contexts[-1]
        return ctx.new_label(kind)

    def enter_function(self, func_name: str):
        self._push_context(f"{func_name}")

    def exit_function(self):
        self._pop_context()

    def enter_conditional(self):
        self._push_context("if")

    def exit_conditional(self):
        self._pop_context()

    def enter_loop(self):
        self._push_context("loop")

    def exit_loop(self):
        self._pop_context()

    def format_label(self, name) -> str:
        if hasattr(name, 'name'):
            label_str = name.name
        else:
            label_str = str(name)

        return f".{label_str}" if not label_str.startswith('.') else label_str