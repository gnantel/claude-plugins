# coding-standards

Personal coding style standards for Java, Python, Rust and TypeScript.

## Install

```
/plugin marketplace add gnantel/claude-plugins
/plugin install coding-standards@personal
```

| Path | Purpose |
|---|---|
| `skills/coding-standards/standards/` | The rules: `general.md` plus one file per language |
| `skills/coding-standards/SKILL.md` | Loads the standards before Claude writes code |
| `skills/pre-pr/SKILL.md` | `/coding-standards:pre-pr`: runs every enabled review plugin's reviewers in parallel |
| `skills/issues/` | Issue-first work: find or create the change's leaf issue, split work into sub-issues, with a helper script |
| `skills/copilot-review-loop/` | `/coding-standards:copilot-review-loop`: addresses Copilot's PR review round after round until it has no new comments |
| `agents/*-reviewer.md` | Reviewers (Sonnet): structure, naming, comments, test separation, organization, scope |
| `hooks/` | Blocks PR creation by Claude until the current commit has passed `/pre-pr` |
| `summary.md` | Short version to import into `~/.claude/CLAUDE.md` |

## Use

- Writing code: the `coding-standards` skill loads automatically.
- Before a PR: runs automatically. When Claude creates a PR (`gh pr create`
  or a GitHub MCP `create_pull_request` tool), the hook blocks it until the
  current commit has been reviewed. Claude then runs the review, resolves the
  findings with you, and retries. You can also run it yourself:
  `/coding-standards:pre-pr` (optionally a base branch and `--fix`).
- After the PR is created: the Copilot review loop starts automatically. It
  waits for Copilot's review, fixes relevant comments or replies with why
  not, pushes, and repeats until Copilot's review of the latest commit has no
  new comments (at most 5 rounds). It never acts on comments from people.
- The reviewed commit is recorded in `.git/coding-standards-reviewed`
  (per worktree). Any new commit needs a fresh review.
- Scope: every change starts from a leaf issue, and each PR closes exactly
  one (`Closes #<n>`). `/pre-pr` refuses a branch without one, and the scope
  reviewer checks the diff against the issue and its comments. Rules:
  `skills/coding-standards/standards/pull-requests.md`.
- PRs you create yourself outside Claude (GitHub web UI, `gh` in your own
  terminal) are not covered by the hook.
