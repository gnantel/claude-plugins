---
name: coding-standards
description: The user's personal coding standards for Java, Python, Rust and TypeScript - short well-named functions, orchestrator methods, length limits, near-zero comments with a required file header, extracted predicates, tests kept separate and no test-only code in implementations. Use before writing, modifying or refactoring code in any of these languages, and when reviewing code against the user's standards.
---

# Coding Standards

The full standards are in the `standards/` directory next to this file:

- `standards/general.md`: rules for every language, thresholds and rule IDs.
- `standards/python.md`, `standards/rust.md`, `standards/typescript.md`,
  `standards/java.md`: language specifics.

Before writing or changing code, read `general.md` and the file for the
language you are working in. Apply the rules as you write, not afterwards.

The ones most often missed:

1. **G2/G3:** split work into many short, well-named functions. Orchestrators
   only decide and delegate. Hard max 50 lines (Rust 100).
2. **G6:** don't write comments; make the code clearer instead. The one
   required comment is the file header (G6a).
3. **G7:** extract hard-to-read or compound conditions into named predicates.
4. **G8/G9:** tests in separate files (Rust: `foo_tests.rs` beside `foo.rs`
   via `#[path]`, `tests.rs` beside a `mod.rs`). Never widen visibility or
   add test-only code for testability.
5. **G10:** organize by feature, never by layer. Put new code in the
   feature it belongs to; no top-level `services/`, `models/` or `utils/`.
6. **G11:** write idiomatic code for the language; when unsure, work out the
   idiomatic way first. The explicit rules above win over idiom.
7. **G13:** order code top-down in call order: public functions in the
   order a caller uses them, each followed by the private helpers it calls
   that aren't already above it, depth first. A second public function goes
   after the first one's whole helper tree. A utility used all over the file
   goes at the bottom.

When you finish a change, check your own diff against these rules before
reporting it done. For a full review, the user runs `/pr-workflow:review-branch`.
