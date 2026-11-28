# pr-workflow

Issue-first pull request workflow: leaf issues, the `/review-branch` review, the
`/submit-pr` flow, a scope reviewer, a hook that requires the review before PR
creation, and the Copilot review loop.

## Install

```
/plugin marketplace add gnantel/claude-plugins
/plugin install pr-workflow@personal
```

| Path | Purpose |
|---|---|
| `skills/review-branch/SKILL.md` | `/pr-workflow:review-branch`: runs every enabled review plugin's reviewers in parallel; never creates a PR |
| `skills/submit-pr/SKILL.md` | `/pr-workflow:submit-pr`: review, create the PR, Copilot loop, re-review of the loop's commits, a removal issue for each new feature flag, then report it ready for human review |
| `skills/issues/` | Issue-first work: find or create the change's leaf issue, split work into sub-issues, brief child sessions, with a helper script |
| `skills/cleanup/` | `/pr-workflow:cleanup [--dry-run]`: removes local branches whose PR merged, and their clean worktrees; keeps and explains everything else |
| `skills/copilot-review-loop/` | `/pr-workflow:copilot-review-loop`: addresses Copilot's PR review round after round until it has no new comments |
| `agents/scope-reviewer.md` | Reviewer (Sonnet): the diff must serve the branch's one leaf issue |
| `standards/pull-requests.md` | The pull request rules |
| `hooks/` | Blocks PR creation by Claude until the current commit has passed `/review-branch` |
| `summary.md` | Short version to import into `~/.claude/CLAUDE.md` |

## Use

- Before a PR: runs automatically. When Claude creates a PR (the GitHub CLI
  or a GitHub MCP `create_pull_request` tool), the hook blocks it until the
  current commit has been reviewed. Claude then runs the review, resolves the
  findings with you, and retries. You can run the review yourself at any
  time, with or without a PR: `/pr-workflow:review-branch` (optionally a base
  branch and `--fix`).
- Start to finish: `/pr-workflow:submit-pr` runs the review, creates the PR
  with `Closes #<n>`, runs the Copilot loop, reviews again any commits the
  loop added, files a removal issue for each feature flag the branch adds,
  and reports the PR ready for human review, with what was raised, fixed and
  declined.
- Flag removal: each new flag gets an issue labelled `flag-removal`, with
  fields automation can read, linked from the PR (rule PR7). How long a flag
  stays fully on before removal comes from the project's
  `.claude/operational.md`, for example
  `Remove a flag once it has been fully on for 30 days.`
- The Copilot review loop (inside `submit-pr`, or run it yourself). It
  waits for Copilot's review, fixes relevant comments or replies with why
  not, pushes, and repeats until Copilot's review of the latest commit has no
  new comments (at most 5 rounds). It never acts on comments from people.
- The reviewed commit is recorded in `.git/pr-workflow-reviewed`
  (per worktree). Any new commit needs a fresh review.
- Scope: every change starts from a leaf issue, and each PR closes exactly
  one (`Closes #<n>`). `/review-branch` refuses a branch without one, and the scope
  reviewer checks the diff against the issue and its comments. Rules:
  `standards/pull-requests.md`.
- PRs you create yourself outside Claude (GitHub web UI, the GitHub CLI in
  your own terminal) are not covered by the hook.
