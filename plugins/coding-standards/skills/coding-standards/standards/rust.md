# Rust Standards

Extends `general.md`. Tooling: `cargo`, `rustfmt`, `clippy`, `cargo test`
(or `cargo nextest`), toolchain pinned with `rust-toolchain.toml`.

## RS1. `//!` file header (G6a)

Every source file starts with an inner doc comment stating the module's
purpose.

```rust
//! Resolves wiktionary page redirects into canonical entry titles.
```

`///` doc comments on items follow G6b: only on the public API of a library
crate. In binaries and internal modules, do not add them.

## RS2. Function length (G3)

Hard max 100 lines, allowed because large `match` expressions are idiomatic.
A long function that is *not* mostly a `match` should stay near 50. Long
`match` arms are themselves candidates for extraction: each arm should
ideally be a single call or expression.

```rust
// Good
match command {
    Command::Add(item) => add_item(&mut store, item),
    Command::Remove(id) => remove_item(&mut store, id),
    Command::List => print_items(&store),
}
```

## RS3. Predicates (G7)

Extract to small `fn is_*` / `fn has_*` / `fn can_*` functions or methods,
including multi-clause match guards and `filter` closures.

```rust
// Bad
if token.kind == Kind::Ident && !token.text.is_empty() && token.text.chars().all(char::is_alphanumeric) {

// Good
if is_plain_identifier(&token) {
```

## RS4. Tests live in a separate file (G8)

Unit tests do **not** go inline in the implementation file. The
implementation file only declares the test module:

```rust
// src/browser/commands.rs
#[cfg(test)]
#[path = "commands_tests.rs"]
mod tests;
```

- A leaf module `foo.rs` keeps its tests in a sibling `foo_tests.rs`, loaded
  with `#[path]` as above, so the tests sit next to the code in the same
  feature directory.
- A `mod.rs` (or `lib.rs`/`main.rs`) declares `mod tests;` and keeps its
  tests in a sibling `tests.rs`, or a `tests/` directory when they need
  several files.
- As a child module, the test module can `use super::*;` and reach private
  items, so no visibility changes are ever needed.
- Integration tests that use only the public API go in the crate's `tests/`
  directory.
- An inline `#[cfg(test)] mod tests { ... }` with a body is a violation.

## RS5. No test-only code in implementation (G9)

- `#[cfg(test)]` appears in production files only on test module
  declarations (`mod tests;`, `mod foo_tests;`). Never on functions, impls, fields or branches.
- Do not widen visibility (`pub`, `pub(crate)`, `pub(super)`) for tests; the
  child test module already sees private items.
- Test doubles come from traits: depend on a trait and implement it in the
  test module.

## RS6. No `pub` unless used outside the module (G14)

- Items, fields and methods start private. Add `pub(super)` or `pub(crate)`
  when other modules of the crate use them, and `pub` only for what other
  crates use. Prefer the narrower form.
- Never widen an item so a test can reach it (G9, RS5).
