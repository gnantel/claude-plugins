# Python Standards

Extends `general.md`. Tooling: `uv`, `ruff` (format + lint), `pyright`, `pytest`.

## PY1. Module docstring as the file header (G6a)

Every module starts with a module docstring stating its purpose.

```python
"""Parses bank CSV exports into Transaction records."""
```

Function and class docstrings follow G6b: only for the public API of a
library. In applications, do not add them.

## PY2. Function length (G3)

Hard max 50 lines per function or method, including nested functions.

## PY3. Predicates (G7)

Extract to small functions or properties named as questions.

```python
# Bad
if order.status == Status.OPEN and order.due_date < today and not order.on_hold:
    escalate(order)

# Good
def is_overdue(order: Order, today: date) -> bool:
    return order.status == Status.OPEN and order.due_date < today and not order.on_hold

if is_overdue(order, today):
    escalate(order)
```

Same for comprehension filters: `[o for o in orders if is_overdue(o, today)]`.

## PY4. Type hints are part of clear naming

Annotate function signatures. A precise type often removes the urge to
comment (`dict[CustomerId, list[Invoice]]` says what `data` would not).

## PY5. Tests (G8, G9)

- Tests live under `tests/`, mirroring the package layout, never inside the
  package modules.
- Test helpers and fixtures live in `tests/` (`conftest.py`, helper modules).
- Do not add `_for_testing` functions, `if TESTING` branches or test-only
  parameters to production code.
- Test through public functions. Making a `_private` function public just to
  test it is not allowed; test it through the public function that uses it,
  or extract it into its own module where it is legitimately public.
- Use dependency injection (pass a clock, client or repository in) rather than
  `monkeypatch`-ing internals when the design allows it.

## PY6. Private by default with a leading underscore (G14)

- Module-level functions, classes and constants that no other module imports
  start with `_`. Methods and attributes that only their class uses start
  with `_` too.
- A name without `_` is part of the module's surface: another module imports
  it, or it is an entry point such as `main`.
- Never drop the `_` so a test can import the helper (G9, PY5).
