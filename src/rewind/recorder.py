"""Record every executed line of chosen Python code with a snapshot of its local variables.

Uses PEP 669 ``sys.monitoring`` (Python 3.12+), which has much lower overhead than ``sys.settrace``.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from types import CodeType
from typing import Any, Callable

TOOL_ID = sys.monitoring.DEBUGGER_ID
_E = sys.monitoring.events


@dataclass(frozen=True)
class Step:
    index: int
    filename: str
    lineno: int
    function: str
    depth: int
    locals: dict[str, str]  # repr() of each local at the moment the line is about to run


@dataclass
class Trace:
    steps: list[Step] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.steps)

    def lines(self) -> list[int]:
        return [s.lineno for s in self.steps]

    def when_changed(self, name: str) -> list[tuple[int, str | None]]:
        """Every step at which local ``name`` took a new value, as (step index, repr)."""
        changes, last = [], object()
        for s in self.steps:
            value = s.locals.get(name)
            if value != last:
                changes.append((s.index, value))
                last = value
        return changes

    def first_step_where(self, name: str, value_repr: str) -> Step | None:
        """Answer 'when did this variable become X?' (e.g. ``value_repr='None'``)."""
        return next((s for s in self.steps if s.locals.get(name) == value_repr), None)


def _safe_repr(value: Any, limit: int = 200) -> str:
    try:
        text = repr(value)
    except Exception as exc:  # a broken __repr__ must not kill the recording
        text = f"<repr failed: {type(exc).__name__}>"
    return text if len(text) <= limit else text[: limit - 3] + "..."


class Recorder:
    """Records lines from code objects whose filename passes ``include``."""

    def __init__(self, include: Callable[[str], bool]):
        self.include = include
        self.trace = Trace()
        self._depth = 0

    def _wanted(self, code: CodeType) -> bool:
        return self.include(code.co_filename)

    def _on_start(self, code: CodeType, offset: int):
        if not self._wanted(code):
            return sys.monitoring.DISABLE
        self._depth += 1

    def _on_return(self, code: CodeType, offset: int, retval: Any):
        if not self._wanted(code):
            return sys.monitoring.DISABLE
        self._depth -= 1

    def _on_line(self, code: CodeType, lineno: int):
        if not self._wanted(code):
            return sys.monitoring.DISABLE
        frame = sys._getframe(1)
        snapshot = {k: _safe_repr(v) for k, v in frame.f_locals.items()}
        self.trace.steps.append(
            Step(len(self.trace.steps), code.co_filename, lineno, code.co_qualname, self._depth, snapshot)
        )

    def __enter__(self) -> "Recorder":
        mon = sys.monitoring
        mon.use_tool_id(TOOL_ID, "rewind")
        mon.register_callback(TOOL_ID, _E.LINE, self._on_line)
        mon.register_callback(TOOL_ID, _E.PY_START, self._on_start)
        mon.register_callback(TOOL_ID, _E.PY_RETURN, self._on_return)
        mon.set_events(TOOL_ID, _E.LINE | _E.PY_START | _E.PY_RETURN)
        return self

    def __exit__(self, *exc) -> None:
        mon = sys.monitoring
        mon.set_events(TOOL_ID, 0)
        for event in (_E.LINE, _E.PY_START, _E.PY_RETURN):
            mon.register_callback(TOOL_ID, event, None)
        mon.free_tool_id(TOOL_ID)
        mon.restart_events()


def record(func: Callable[..., Any], *args: Any, **kwargs: Any) -> tuple[Any, Trace]:
    """Run ``func`` and record every line executed in the file that defines it."""
    target = func.__code__.co_filename
    with Recorder(lambda filename: filename == target) as rec:
        result = func(*args, **kwargs)
    return result, rec.trace
