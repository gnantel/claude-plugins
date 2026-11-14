# Spring Boot Standards

Extends the coding-standards `java.md` and G10 (organize by feature): each
feature package is self-contained, with its own beans, configuration,
settings and defaults. Each rule has an ID so reviews can cite it.

## SB1. One `@Configuration` class per package with beans

Every package that contains bean classes has exactly one `@Configuration`
class, which wires that package's beans.

- It is named after the package's concept and ends in `Configuration`: for
  `com.example.**.resources`, `ResourceConfiguration` or
  `ResourcesConfiguration`. The application's root package uses the
  application's name (`WiktionaryImporterConfiguration`).
- A nested `static` `@Configuration` class is fine for grouping something
  inside it, such as an extra YAML property source.
- Configuration for a package never lives in another package.

## SB2. Beans are plain classes wired by `@Bean` methods

Bean classes are plain Java classes with no Spring stereotype annotations.
The package's `@Configuration` creates them in `@Bean` methods.

Bad:
```java
@Service
public class LateFeeCalculator { ... }
```

Good:
```java
@Configuration
@EnableConfigurationProperties(LateFeeSettings.class)
@YamlPropertySource("classpath:com/example/billing/fees/late-fee.defaults.yaml")
class LateFeeConfiguration {
    private final LateFeeSettings settings;

    LateFeeConfiguration(LateFeeSettings settings) {
        this.settings = settings;
    }

    @Bean
    LateFeeCalculator lateFeeCalculator(Clock clock) {
        return new LateFeeCalculator(settings.rate(), settings.cap(), clock);
    }
}
```

No `@Component`, `@Service` or `@Repository` on bean classes, and no
component scanning that relies on them.

**Exception: web controllers.** Spring MVC only recognizes handler types
annotated `@Controller` (or `@RestController`), so controllers keep that
annotation, as do `@ControllerAdvice` classes. They are discovered by
component scanning, so they are **not** also registered with a `@Bean`
method (that would create a second instance). Everything else still
applies: they live in their feature package, use constructor injection
(SB5) and are package-private where Spring allows (SB6).

## SB3. Settings are records ending in `Settings`

- Configuration properties are bound to `record`s named `*Settings`,
  annotated `@ConfigurationProperties("<prefix>")`.
- Nested groups of properties are their own `*Settings` records.
- The package's `@Configuration` enables them with
  `@EnableConfigurationProperties(...)` and passes values from them into the
  beans it creates. Beans receive plain values or their own settings record,
  never the whole `Environment`.
- No `@Value`: every property goes through a `*Settings` record.
- A settings record documents its properties in its class-level Javadoc
  (the G6a header), not with `@param` tags. Settings records are the
  configuration surface, so this is the one place where documenting each
  field is expected, even in applications.

```java
/**
 * Settings for the late-fee calculation.
 * <ul>
 *   <li>{@code rate}: fraction of the invoice amount charged per period</li>
 *   <li>{@code cap}: maximum fee per invoice, in cents</li>
 * </ul>
 */
@ConfigurationProperties("billing.late-fee")
record LateFeeSettings(double rate, long cap) {
}
```

## SB4. Every Settings record has YAML defaults beside it

- Defaults for a feature's settings live in `<concept>.defaults.yaml` in the
  same package directory as the record, under `src/main/java`
  (`import.defaults.yaml` beside `ImportSettings`, `template.defaults.yaml`
  beside `TemplateSettings`). File names are lowercase, hyphenated.
- The package's `@Configuration` loads it with
  `@YamlPropertySource("classpath:<package/path>/<concept>.defaults.yaml")`,
  the YAML property source annotation from the user's Spring utilities.
- Every property of the record has a default there. A property that must be
  supplied by the deployment appears commented out (`# file:`), so the file
  still lists every property.
- The Maven build includes `**/*.yaml` from `src/main/java` as resources.

## SB5. Constructor injection only

- Dependencies are injected through the constructor, in `@Configuration`
  classes and bean classes alike. No `@Autowired` on fields or setters, and
  no `@Autowired` on constructors (a single constructor needs none).
- Test classes are the only exception, and only those that start a Spring
  context:
  - **Unit tests** construct the class under test directly with `new`,
    passing its dependencies. No Spring context, no `@Autowired`.
  - **Configuration wiring tests** load a feature's `@Configuration`
    (`@SpringJUnitConfig`, `@ContextConfiguration` or `@SpringBootTest`) to
    check its beans are wired correctly. They may use `@Autowired` fields,
    since JUnit creates the test instance.
- `@Autowired` anywhere under `src/main` is a violation.

## SB6. Package-private by default

In line with G10's small feature surface: `@Configuration` classes, their
constructors and `@Bean` methods, `*Settings` records and bean classes used
only inside the feature are package-private. Make something `public` only
when another feature uses it.
