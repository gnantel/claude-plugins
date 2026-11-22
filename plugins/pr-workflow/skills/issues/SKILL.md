---
name: issues
description: Issue-first work - every change starts from a leaf GitHub issue written before the work, and each pull request closes exactly one leaf issue. Use before starting any change (find or open its issue, split it into sub-issues if it needs several PRs), when new work comes up while a PR is open, and when recording follow-ups or scope decisions.
---

# Issues

Helper: `python3 ${CLAUDE_SKILL_DIR}/scripts/issues.py <command>` (prints JSON,
needs gh 2.104 or later for sub-issues):

| Command | Does |
|---|---|
| `show <n>` | The issue's body, comments (each marked `trusted` when written by the repository's owner, a member or a collaborator), state, parent, sub-issues and `is_leaf` |
| `for-branch` | The issue the current branch implements: its PR's closing issue (refused if it's in another repository), or the `<issue-id>-` branch name, marked `stacked` when the PR isn't based on the default branch |
| `create --title <t> --body-file <path> [--parent <n>] [--label <l>]` | Creates an issue, as a sub-issue if `--parent` is given |
| `link <parent> <child>` | Makes an existing issue a sub-issue |

## Before starting a change

1. Find its issue, or create one from the user's request **before** writing
   code. The body has `## Scope` (the purpose, one or two sentences), `## Out
   of scope` (related work left for other issues) and `## Done when`.
2. If it needs more than one PR, it is a parent: split it into sub-issues,
   one per PR, and work on a leaf. Only leaves get PRs.
3. Branch from the default branch, named `<issue-id>-<description>` (for
   example `6-issue-linked-prs`).

## While working

- **New work that comes up** (a new request, a problem noticed in passing)
  becomes a new issue, with `--parent` when it belongs to a larger goal. It
  does not go into the current branch unless the user explicitly says so.
- **Scope decisions made during discussion** go on the issue as a comment,
  so the issue stays the true record of what the PR should contain.
- **Follow-ups** are new issues, not notes in a PR description.

## Opening the PR

The description includes `Closes #<n>` for exactly one leaf issue.
