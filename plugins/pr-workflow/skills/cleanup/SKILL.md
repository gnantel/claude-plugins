---
name: cleanup
description: Remove local branches whose pull request merged, together with their clean worktrees. Use right after `git fetch origin` when starting work, or when local branches and worktrees have piled up.
argument-hint: "[--dry-run]"
---

# Cleanup

Run `python3 ${CLAUDE_SKILL_DIR}/scripts/cleanup.py [--dry-run]` from any
worktree of the repository. It runs `git fetch --prune origin`, then looks at
every local branch except the default one. Squash merges defeat
`git branch --merged`, so it asks GitHub (`gh`) about each branch's PRs.

A branch is deleted, after removing the worktree that has it checked out,
only when all of these hold:

- its PR is merged and the local head equals the PR's final head, so no
  commit is unpushed;
- no PR for it is open;
- its worktree has no uncommitted or untracked changes;
- it is not the current worktree's branch, nor checked out in the main
  worktree.

Every other branch is kept and reported with the reason, including branches
whose PR was closed without merging and branches with no PR. Nothing is
forced: if git refuses to remove a worktree (for example a locked one), the
branch is kept and the reason is reported.

`--dry-run` only reports what would be removed. It still fetches.

The checks guard against losing your own work, not against a hostile
repository.
