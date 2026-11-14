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
- **Features expose a small surface.** Keep a feature's internals private to
  it (package-private in Java, private modules or `pub(crate)` re-exports in
  Rust, unexported in TypeScript, `_`-prefixed in Python), and have other
  features use only what it deliberately exposes.
- **Framework-imposed locations are the exception.** Where a framework
  requires a layout (Maven's `src/test/java`, a web framework's routes
  directory), follow it, and keep feature grouping inside it: tests mirror
  the feature packages.
