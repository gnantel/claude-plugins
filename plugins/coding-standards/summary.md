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
- Write idiomatic code for each language (its standard library and
  established idioms); when unsure, work out the idiomatic way first. These
  explicit rules win where an idiom conflicts with them.

## Pull requests

Full rules: `standards/pull-requests.md` in the coding-standards skill.

- Every change starts from a leaf GitHub issue written before the work
  (scope, out of scope, done when); use the `issues` skill. Work needing
  several PRs is a parent issue split into sub-issues first.
- One PR closes exactly one leaf issue (`Closes #<n>`). In scope: the
  issue, fixes to its own changes within that scope, and minimal
  supporting changes.
- Anything else that comes up while a PR is open, including a new request
  from the user, becomes a new issue and its own branch and PR, unless the
  user explicitly says to include it. Never add it to the branch that
  happens to be checked out.
- Problems noticed in passing and follow-ups become issues. Scope decisions
  made in discussion go on the issue as a comment.
