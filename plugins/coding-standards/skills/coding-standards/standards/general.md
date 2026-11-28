# General Coding Standards

These rules apply to every language. Language files (`python.md`, `rust.md`,
`typescript.md`, `java.md`) add specifics and override thresholds where stated.

Formatting and lint are delegated to each project's standard tooling. These
rules cover what tooling cannot judge. Each rule has an ID so reviews can cite it.

## Thresholds

| | Java | Python | TypeScript | Rust |
|---|---|---|---|---|
| Function/method hard max | 50 lines | 50 lines | 50 lines | 100 lines |
| File: refactoring target | 300 lines | 300 lines | 300 lines | 300 lines |

The hard max is a ceiling, not a target. Most functions should be far shorter.
Rust gets more room only because large `match` expressions are idiomatic; a long
Rust function that is *not* mostly a `match` is held to the same spirit as 50.

---

## G1. Many short functions with clear names

Prefer many very short functions over a few long ones. A function's name should
say exactly what it does, so the reader rarely needs to look inside.

**Why:** Short, well-named functions make code read like a description of
intent, and they make each piece easy to understand, change and test.

**Watch out for:** over-extraction. A wrapper that only renames a single obvious
call, or a name vaguer than the code it hides (`handle`, `process`, `doStuff`),
makes things worse. Extraction is only good when the name adds clarity.

## G2. Orchestrators read like a script

When a function must do several things, it becomes an orchestrator: it decides
and delegates, and each step lives in its own function. The orchestrator should
read cleanly top to bottom: "if this, call that; else if this, call that".

Bad:
```
function importOrders(file):
    rows = []
    for line in readLines(file):
        if line.trim() == "" or line.startsWith("#"):
            continue
        parts = line.split(",")
        rows.append(Order(parts[0], parseMoney(parts[1]), parseDate(parts[2])))
    for order in rows:
        if order.total > 0 and order.date <= today():
            db.insert(order)
        else:
            log.warn("skipping", order)
```

Good:
```
function importOrders(file):
    orders = parseOrders(file)
    for order in orders:
        if isImportable(order):
            save(order)
        else:
            reportSkipped(order)
```

An orchestrator should contain almost no low-level detail (string handling,
index math, raw I/O). If it does, that detail belongs in a step function.

## G3. Function length

Functions over the language's hard max (see Thresholds) must be broken up.
Anything approaching it should be questioned: it is usually an orchestrator
with its steps inlined (see G2).

## G4. File length signals too many concepts

A file over 300 lines is a refactoring target. A long file is usually doing
more than one thing. Find the separate concepts inside it and give each its
own file/module/class. Do not split arbitrarily (`utils2`, `part_b`) just to
hit the number; split along concepts.

## G5. Clear variable names

Names say what a value *is* in domain terms: `unpaidInvoices`, not `list2`,
`data`, `tmp` or `res`. Single-letter names are fine only for tiny scopes with
a conventional meaning (loop index `i`, coordinates `x`/`y`, a lambda's sole
parameter). Avoid abbreviations unless they are universal in the domain.

## G6. Comments almost never

If you feel a comment is needed, first make the code clearer: rename, extract
a well-named function, introduce an explaining variable. Comments are for
truly exceptional cases, typically a *why* that code cannot express: a
workaround for an external bug, a non-obvious constraint, a surprising
performance decision.

Never acceptable:
- Comments restating what the code does (`// increment counter`).
- Section-divider comments inside a function (`// --- validate ---`): those
  sections should be functions.
- Commented-out code.
- Comments explaining an unclear name instead of fixing the name.

Bad:
```
// check if user can access the report
if user.role == ADMIN or (user.team == report.team and not user.suspended):
```

Good:
```
if canAccess(user, report):
```

### G6a. File header comment (required)

Every source file starts with a short comment stating its purpose: what this
file/module/class is for, in one to three sentences. The language files say
where it goes. It describes the concept, not the implementation, and should
stay true as the code evolves.

### G6b. API documentation for libraries only

Doc comments on public API items (Javadoc, Python docstrings, Rust `///`,
TSDoc) are acceptable **only in libraries** meant to be consumed by others.
In applications, names and types are the documentation.

## G7. Extract long or compound predicates

Conditions that take effort to read are extracted into tiny, well-named
predicate functions (`isExpired`, `hasOverdueInvoices`, `canRetry`).

This is a judgment call, not a mechanical rule:
- **Extract** when the reader has to stop and decode the condition, when it
  mixes several concepts, or when it has three or more clauses.
- **Fine to leave inline:** a simple two-clause guard where both parts are
  obvious, such as a null/None check plus one property test
  (`x is not None and x.isActive`).
- If the same condition appears twice, always extract it.

Applies to `if`, `while`, ternaries, match guards and filter lambdas alike.

## G8. Tests are separate from implementation

Test code lives in separate files from production code. Production files
contain no test functions, test modules, fixtures or test helpers. See the
language file for where tests go.

## G9. Never modify implementation just for testability

There is always a way to test without adding test-specific code to the
implementation.

Not acceptable:
- Widening visibility (public, protected, package-private, `pub`, `pub(crate)`,
  exporting) only so a test can reach something.
- Test-only annotations or markers in production code (`@VisibleForTesting`,
  `#[cfg(test)]` outside the test module declaration, `if TESTING`).
- Test-only constructors, setters, flags, hooks or branches.

Acceptable, because it is good design rather than a test hack:
- Depending on an interface/trait/protocol instead of a concrete type.
- Injecting collaborators, a clock, a random source or configuration.
- Splitting a class or module so each part can be tested through its public
  surface.

If something is hard to test, that is a design signal: restructure so the
behavior is reachable through a real public surface, then test that.

## G10. Organize code by feature, not by layer

Group code by the feature or domain concept it serves, not by its technical
role. Everything one feature needs (entry points, logic, persistence,
configuration, settings and their tests) lives together in that feature's
directory, package or module.

Bad:
```
src/
  controllers/   invoice_controller, customer_controller
  services/      invoice_service, customer_service
  repositories/  invoice_repository, customer_repository
  models/        invoice, customer
  utils/
```

Good:
```
src/
  invoices/      routes, invoice, late_fees, invoice_store, tests
  customers/     routes, customer, customer_store, tests
  money/         (shared concept used by several features)
```

- **Top-level directories are features**, never layers. Directory or package
  names like `controllers`, `services`, `repositories`, `models`, `dto`,
  `handlers`, `middleware`, `routes`, `utils`, `helpers` or `common` at the
  top level are violations.
- **Inside a feature, split by sub-concept.** A large feature may have
  sub-modules, including a role-named one when it is a coherent part of that
  feature (for example `viewer/renderer/`).
- **Code used by one feature lives in that feature.** Only code shared by
  several features moves out, into a module named for the concept it
  represents (`money`, `clock`, `http_client`), never into a `utils` or
  `common` grab bag.
- **Features expose a small surface.** Judge exposure at the feature's
  boundary, not per file: files inside a feature may expose things to each
  other as the language requires. Other features use only the feature's
  deliberate entry point:
  - Java: package-private by default; `public` only for what other
    packages use.
  - Rust: private modules, with what other features need re-exported from
    the feature's `mod.rs`.
  - TypeScript: other features import only from the feature's `index.ts`,
    which exports only what they use. Exports between files of the same
    feature are fine.
  - Python: other features import only what the feature's `__init__.py`
    exposes; `_`-prefixed names stay internal.
- **Framework-imposed locations are the exception.** Where a framework
  requires a layout (Maven's `src/test/java`, a web framework's routes
  directory), follow it, and keep feature grouping inside it: tests mirror
  the feature packages.

## G11. Write idiomatic code

Use each language the way its experienced users do: its standard library,
established idioms and conventions, rather than patterns carried over from
another language. When unsure, work out what the idiomatic way is before
writing the code, and follow the idioms already used in the project.

Examples:
- Java: records for data carriers, streams where they read better than
  loops, `Optional` as a return type, try-with-resources.
- Python: comprehensions, context managers, `pathlib`, dataclasses,
  iterating directly instead of over indices.
- Rust: iterators over index loops, `?` for error propagation, `Option` and
  `Result` combinators, pattern matching, ownership instead of cloning.
- TypeScript: optional chaining and nullish coalescing, discriminated
  unions, `const` and immutable updates, `async`/`await` over raw promises.

**Precedence:** the explicit rules in these standards win where an idiom
conflicts with them. For example, Rust tests stay in separate files (RS4)
even though inline test modules are idiomatic, and Python functions get no
docstrings in applications (G6b).

## G13. Order code top-down in call order (the stepdown rule)

A file reads like a narrative: the public API comes first, and each public
function or method is followed by the private helpers it calls, in the order it
calls them, depth first.

- Public functions appear in the order a caller uses them: the order of the
  entry-point dispatch, or the main flow, when there is one.
- A second public function goes after the first one's whole helper tree,
  never between the first one and its helpers. It is followed by those of its
  own helpers that are not already above it.
- A helper called by several functions goes after its first caller, so a
  helper two public functions share stays under the first one.
- **Exception:** a private utility used in many places in the same file goes
  at the bottom.
- Constants, types, imports and fields stay where the language expects them,
  at the top. In Java that means fields and constructors first, then each
  public method followed by its private helpers, rather than all public
  methods grouped together.
- Entry points the language puts at the bottom, such as Python's
  `if __name__ == "__main__":` block, stay there.

**Why:** the reader meets the high-level intent first and follows the calls
downward, and never has to hunt for a helper far from where it is used.

Bad (helpers in the opposite order from the calls, far from the caller):

```python
def _format_total(order): ...
def _format_header(order): ...

def render_receipt(order):
    return _format_header(order) + _format_total(order)

def render_summary(order): ...
```

Bad (the second public function sits between the first one and its helpers):

```python
def render_receipt(order):
    return _format_header(order) + _format_total(order)

def render_summary(order):
    return _format_header(order) + _format_count(order)

def _format_header(order): ...
def _format_total(order): ...
def _format_count(order): ...
```

Good (two public functions that share `_format_header`; the shared helper
stays under its first caller, and `render_summary` follows the whole
`render_receipt` tree):

```python
def render_receipt(order):
    return _format_header(order) + _format_total(order)

def _format_header(order): ...
def _format_total(order): ...

def render_summary(order):
    return _format_header(order) + _format_count(order)

def _format_count(order): ...
```

## G14. Narrowest visibility by default

A function, method, type or constant that is not used outside its module or
class is private: through the language's construct, or through its convention
where the language has none. Widen visibility only when something outside
really uses the item, and only as far as that user needs.

**Why:** a small surface keeps a feature's entry points obvious (G10), and
the reader and G13 can tell which functions are entry points and which are
helpers.

- Check who uses an item with a search before making it public or leaving it
  unmarked.
- Tests do not count as users (G9): test through the public surface, and
  never widen an item, or strip its private marker, so a test can reach it.
- The language files give each language's form: `private` in Java, a leading
  `_` in Python, no `pub` in Rust, no `export` in TypeScript.

Bad (`format_header` is only called inside this module, yet looks like an
entry point):

```python
def render_receipt(order):
    return format_header(order) + _format_total(order)

def format_header(order): ...
```

Good:

```python
def render_receipt(order):
    return _format_header(order) + _format_total(order)

def _format_header(order): ...
```

## G15. Don't duplicate logic that already exists

Before writing a function, type or behaviour, search for one that already
does the job: in the repository, in the language's standard library and in
the project's dependencies (G11). Search for what the code does, not only
for the name you would give it.

Not acceptable:
- Reimplementing a function, type or behaviour that already exists in the
  repository, under the same name or another one, written the same way or
  differently.
- Hand-rolling what the standard library or a dependency the project already
  has provides.
- Two features growing the same logic separately.

**Why:** copies drift apart. A fix or rule change made in one misses the
others, and the reader cannot tell whether their differences are deliberate.

To fix it, use what exists. When two features need the same logic, follow
G10: the feature that owns the concept exposes it through its small surface,
or the logic becomes a feature of its own, named for its concept. Never move
it into a `utils` or `common` grab bag.

**Not duplication:** code that looks alike but expresses different rules,
which can change independently. Two fees that are each a capped percentage
are two business rules; merging them couples things that only happen to look
alike today. Likewise, don't replace code with an existing function that
behaves differently in a case the caller can hit.

Bad (`format_amount` in `money/` already does this, and `Counter` counts):

```python
def _render_price(minor_units):
    whole, fraction = divmod(minor_units, 100)
    return "$" + f"{whole:,}" + "." + str(fraction).zfill(2)

def _tally_statuses(orders):
    tally = {}
    for order in orders:
        if order.status not in tally:
            tally[order.status] = 0
        tally[order.status] += 1
    return tally
```

Good (call `format_amount(order.total_cents)` where `_render_price` was
needed):

```python
from collections import Counter

from shop.money import format_amount

def _tally_statuses(orders):
    return Counter(order.status for order in orders)
```
