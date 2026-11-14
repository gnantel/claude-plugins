---
name: spring-boot
description: The user's Spring Boot conventions - one Configuration class per feature package wiring plain bean classes with @Bean methods, Settings records with a .defaults.yaml beside them loaded by @YamlPropertySource, constructor injection only, package-private by default. Use before writing or changing Spring Boot code, and when reviewing it.
---

# Spring Boot Conventions

The rules are in `standards/general.md` next to this file (rule IDs SB1–SB6).
They extend the coding-standards Java rules and G10 (organize by feature).

The ones most often missed:

1. **SB1/SB2:** each package with beans has one `<Concept>Configuration`
   class that creates them with `@Bean` methods. No `@Component`/`@Service`;
   only web controllers keep `@RestController` (and get no `@Bean`).
2. **SB3/SB4:** properties bind to `*Settings` records with a
   `<concept>.defaults.yaml` beside them in `src/main/java`, loaded with
   `@YamlPropertySource`. No `@Value`. Document the properties in the
   record's class-level Javadoc, not `@param`.
3. **SB5:** constructor injection only. `@Autowired` only in configuration
   wiring tests, never in `src/main` or plain unit tests.
4. **SB6:** package-private unless another feature needs it.
