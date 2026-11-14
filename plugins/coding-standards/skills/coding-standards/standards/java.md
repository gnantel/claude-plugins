# Java Standards

Extends `general.md`. Tooling: Maven, Spotless with palantir-java-format,
Error Prone, JUnit 5.

## JV1. Class-level Javadoc as the file header (G6a)

Every top-level type has a class-level Javadoc stating its purpose.

```java
/** Calculates late fees for overdue invoices according to the account's plan. */
public final class LateFeeCalculator {
```

Javadoc on methods and fields follows G6b: only for the public API of a
library. In applications, do not add it.

## JV2. Method length (G3)

Hard max 50 lines per method, including lambdas inside it. Long methods are
usually orchestrators with inlined steps (G2): extract each step into a
private method with a clear name.

## JV3. Predicates (G7)

Extract to small `private boolean isX(...)` / `hasX` / `canX` methods,
including stream `filter` lambdas.

```java
// Bad
if (invoice.getStatus() == Status.OPEN && invoice.getDueDate().isBefore(today) && !account.isExempt()) {

// Good
if (isChargeable(invoice, account)) {
```

```java
invoices.stream().filter(this::isChargeable)
```

## JV4. Tests (G8, G9)

- Tests live under `src/test/java`, mirroring the production package.
  No test classes, fixtures or helpers under `src/main`.
- No `@VisibleForTesting`.
- Do not widen visibility for tests: `private` → package-private, `protected`
  or `public` only so a test in the same package can reach it is a violation.
  Test through the public API.
- No test-only constructors, setters or flags. Use constructor injection with
  interfaces, a `Clock` for time and real collaborators or test doubles that
  implement the interface.

## Spring Boot

Spring Boot conventions live in the separate `spring-boot` plugin, enabled
per project.
