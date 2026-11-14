# spring-boot

Spring Boot conventions for Java services. Enable it per project; its
reviewer joins `/coding-standards:pre-pr` automatically.

## Install

```
/plugin marketplace add gnantel/claude-plugins
/plugin install spring-boot@personal
```

| Path | Purpose |
|---|---|
| `skills/spring-boot/standards/general.md` | The rules (SB1–SB6) |
| `skills/spring-boot/SKILL.md` | Loads the rules before Claude writes Spring code |
| `agents/spring-reviewer.md` | Configuration per package, Settings and YAML defaults, constructor injection, visibility |

The rules assume the `@YamlPropertySource` annotation from my Spring
utilities, which loads a YAML file as a default property source.
