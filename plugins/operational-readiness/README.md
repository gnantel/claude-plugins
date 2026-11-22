# operational-readiness

Operational review pack for services. Enable it per project; its reviewers
join `/pr-workflow:review-branch` automatically.

## Install

```
/plugin marketplace add gnantel/claude-plugins
/plugin install operational-readiness@personal
```

| Path | Purpose |
|---|---|
| `skills/operational-readiness/standards/general.md` | The rules: metrics (OM), logging (OL), resilience (OR) |
| `skills/operational-readiness/SKILL.md` | Loads the rules before Claude writes service code |
| `agents/metrics-reviewer.md` | Metrics added, updated and removed with behavior; label cardinality; naming |
| `agents/logging-reviewer.md` | Structured logging, significant events, levels, error context, no secrets |
| `agents/resilience-reviewer.md` | Timeouts, safe retries, failure paths, circuit breaking on external calls |

Each project describes its own tools in `.claude/operational.md`, for example:

```markdown
# Operational conventions

- Metrics: Micrometer, Prometheus naming (`snake_case`, `_total`, `_seconds`).
- Logging: SLF4J + Logback JSON encoder; every log has `request_id`.
- Resilience: resilience4j; default retry 3 attempts, exponential backoff.
- Personal data: never log emails or names.
```
