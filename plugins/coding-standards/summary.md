# Coding standards (summary)

Full rules: the `coding-standards` skill from the coding-standards plugin.
Load it before writing or changing Java, Python, Rust or TypeScript code.

- Many very short functions with clear names. Multi-step functions are
  orchestrators that only decide and delegate; each step is its own function.
- Hard max function length: 50 lines (Rust 100). Files over 300 lines are
  refactoring targets: split by concept.
- Clear, domain-specific variable names. No `data`, `tmp`, `res`.
- Comments almost never: make the code clearer instead. Every file starts
  with a short purpose comment. API doc comments only in libraries.
- Extract hard-to-read or compound conditions into named predicates.
- Organize code by feature, never by layer (no top-level `services/`,
  `controllers/`, `models/`, `utils/`). A feature keeps its own code,
  config and tests together and exposes a small surface.
- Tests live in separate files (Rust: `#[cfg(test)] #[path = "foo_tests.rs"]
  mod tests;` beside `foo.rs`; `tests.rs` beside a `mod.rs`). Never widen visibility or add test-only code for
  testability; interfaces/traits and injection are fine.
- Order code top-down in call order: public functions in the order a
  caller uses them, each followed by the private helpers it calls that
  aren't already above it, depth first (the second public function goes
  after the first one's whole helper tree); a private utility used all
  over the file goes at the bottom.
- Write idiomatic code for each language (its standard library and
  established idioms); when unsure, work out the idiomatic way first. These
  explicit rules win where an idiom conflicts with them.
- Narrowest visibility by default: private unless used outside the module
  or class, through the construct (`private`, no `pub`, no `export`) or the
  convention (Python's leading `_`). Tests are not users.
- Don't duplicate logic: before writing it, search the repository, the
  standard library and existing dependencies for what it does, not just its
  name. Share between features through one feature's small surface or a
  concept-named feature, never a `utils` grab bag. Look-alike code with
  different rules is not duplication.
