# rewind-py

A time-travel debugger for Python. Run a program once, then drag a slider backwards through
its history and ask questions like "when did this variable become `None`?".

## Status

Early scaffold. Done so far:

- `rewind.record()` records every executed line of a function's source file, with a `repr`
  snapshot of locals and the call depth, using PEP 669 `sys.monitoring`.
- `Trace.when_changed()` and `Trace.first_step_where()` answer simple history queries.

## Planned milestones

1. Full recording: calls, returns, exceptions and assignments, stored compactly on disk
   (deltas instead of full snapshots).
2. Reverse step / reverse continue / reverse step-out over a recorded trace.
3. History queries: watch an expression across the whole run, find the last write to a name.
4. Debug Adapter Protocol server so an editor can drive it.
5. Local web page with a timeline slider showing the source line and variables.

## Success bar

Reverse-stepping 200 programs matches the forward run at every step, a 10-million-line trace
loads in under 5 seconds, and recording slows programs down by at most 10×.

## Development

Requires Python 3.12+.

```bash
pip install -e .[dev]
pytest
```
