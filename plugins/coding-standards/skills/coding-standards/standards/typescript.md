# TypeScript Standards

Extends `general.md`. Tooling: `pnpm`, Biome (format + lint),
`tsc --noEmit`, `vitest`.

## TS1. File header comment (G6a)

Every source file starts with a short block comment stating its purpose.

```ts
/** Builds the checkout summary shown before payment. */
```

TSDoc on exported items follows G6b: only for the public API of a library
package. In applications, do not add it.

## TS2. Function length (G3)

Hard max 50 lines per function or method. This includes React components:
a long component is an orchestrator (G2) and should delegate to smaller
components and hooks.

## TS3. Predicates (G7)

Extract to small `isX` / `hasX` / `canX` functions, including `.filter()` and
`.find()` callbacks and JSX conditionals.

```ts
// Bad
{user && user.plan !== "free" && !user.trialExpired && <ExportButton />}

// Good
{canExport(user) && <ExportButton />}
```

## TS4. Tests (G8, G9)

- Tests live in separate `*.test.ts` files (beside the module or under a
  `tests/` directory: follow the project's existing convention). Never put
  test code in a production module.
- Do not `export` a function only so a test can import it. Test through the
  module's real exports, or move the logic into its own module where exporting
  it is legitimate.
- No test-only parameters, flags or `process.env.NODE_ENV === "test"`
  branches in production code.
- Prefer injecting dependencies (pass a client, clock or store) over
  `vi.mock` of internal modules when the design allows it.
