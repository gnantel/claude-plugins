# coding-standards

Personal coding style standards for Java, Python, Rust and TypeScript, with
five narrow reviewers that join `/pr-workflow:pre-pr`.

## Install

```
/plugin marketplace add gnantel/claude-plugins
/plugin install coding-standards@personal
```

| Path | Purpose |
|---|---|
| `skills/coding-standards/standards/` | The rules: `general.md` plus one file per language |
| `skills/coding-standards/SKILL.md` | Loads the standards before Claude writes code |
| `agents/*-reviewer.md` | Reviewers (Sonnet): structure, naming, comments, test separation, organization |
| `summary.md` | Short version to import into `~/.claude/CLAUDE.md` |

## Use

- Writing code: the `coding-standards` skill loads automatically.
- Reviewing: the reviewers run as part of `/pr-workflow:pre-pr`, which comes
  from the [pr-workflow](../pr-workflow) plugin. Install it too for the issue,
  PR and review workflow.
