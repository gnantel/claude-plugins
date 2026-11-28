# coding-standards

Personal coding style standards for Java, Python, Rust and TypeScript, with
narrow style reviewers that join `/pr-workflow:review-branch`.

## Install

```
/plugin marketplace add gnantel/claude-plugins
/plugin install coding-standards@personal
```

| Path | Purpose |
|---|---|
| `skills/coding-standards/standards/` | The rules: `general.md` plus one file per language |
| `skills/coding-standards/SKILL.md` | Loads the standards before Claude writes code |
| `agents/*-reviewer.md` | Style reviewers (Sonnet), each checking a narrow set of rule IDs |
| `summary.md` | Short version to import into `~/.claude/CLAUDE.md` |

## Reviewers

| Reviewer | Checks |
|---|---|
| `comments-reviewer` | Comments, file headers and API docs |
| `duplication-reviewer` | Logic that already exists in the repository, the standard library or a dependency |
| `naming-reviewer` | Function names, extraction quality and variable names |
| `organization-reviewer` | Feature-based organization and narrow visibility |
| `structure-reviewer` | Orchestrators, function and file length, predicates and call order |
| `test-separation-reviewer` | Separate tests and no test-only code in implementations |

## Use

- Writing code: the `coding-standards` skill loads automatically.
- Reviewing: the reviewers run as part of `/pr-workflow:review-branch`, which comes
  from the [pr-workflow](../pr-workflow) plugin. Install it too for the issue,
  PR and review workflow.
