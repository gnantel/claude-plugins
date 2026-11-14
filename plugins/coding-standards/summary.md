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
- Tests live in separate files (Rust: `#[cfg(test)] mod tests;` with tests in
  `<module>/tests.rs`). Never widen visibility or add test-only code for
  testability; interfaces/traits and injection are fine.
