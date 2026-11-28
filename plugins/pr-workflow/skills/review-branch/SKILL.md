---
name: review-branch
description: Review the current branch locally against its leaf issue with every enabled review plugin's narrow reviewer agents in parallel, report consolidated findings, fix the ones the user approves and record the review. Never creates a pull request. Use when the user asks to review a branch or check it against the standards, at any time, with or without a PR, or when the pr-workflow hook blocks pull request creation.
argument-hint: "[base-branch] [--fix]"
---

# Review Branch

Review this branch's changes locally, so nothing reaches review or CI that
the standards would flag. It works on a branch with or without a PR and
never creates one: that is the `submit-pr` skill's job.

Arguments: `$ARGUMENTS`

## 1. Work out what changed

- Base: the first argument if one is given. Otherwise, if the branch has a
  PR, its actual base: `git merge-base HEAD origin/<baseRefName>` from
  `gh pr view --json baseRefName`, so a stacked PR is judged only on its
  own changes. Otherwise `git merge-base HEAD origin/main`, falling back to
  `main` then `master`. If the branch is meant to stack on another branch
  and has no PR yet, ask the user for the base instead of guessing.
- Changed files: `git diff --name-only <base>` plus uncommitted changes
  (`git status --porcelain`). Keep source files (`.java`, `.py`, `.rs`,
  `.ts`, `.tsx`) and configuration or manifest files (`.yaml`, `.yml`,
  `.toml`, `.properties`, `pom.xml`, `package.json`), which operational
  reviewers need. Ignore generated files, lockfiles and vendored code.
- If no source or configuration file changed, run only
  `pr-workflow:scope-reviewer` in step 3, since scope creep happens in
  any kind of change, then continue as usual and record the review in
  step 7.
- **Issue:** find the leaf issue this branch implements with
  `python3 ${CLAUDE_PLUGIN_ROOT}/skills/issues/scripts/issues.py for-branch`
  (or the issue the user names). When the user gives the issue's text
  because the repository isn't on GitHub, use that text as the issue and
  look nothing up. Otherwise stop and tell the user if there is none,
  if it is closed, or if it has sub-issues (`is_leaf: false`): every PR
  implements exactly one open leaf issue (rule PR1). Offer to create or
  split the issue with the `issues` skill. Stopping means no review of any
  kind: give no assessment of the changes yourself either, not even a quick
  or informal one, since there is no scope to judge them against.
- **Existing PR:** if the branch already has a PR based on the default
  branch, its `gh pr view --json closingIssuesReferences` must be exactly
  that issue. If the link is missing, add `Closes #<n>` to the description
  with `gh pr edit` before continuing; if it names a different issue, stop
  and ask the user. Stacked PRs are exempt (see step 7).

## 2. Find the reviewers

The reviewers are **every** agent type available to you whose name matches
`<plugin>:<name>-reviewer`, from any plugin. Being available means the
plugin is enabled for this project, so run them all; do not skip a reviewer
because its plugin is not `pr-workflow`, and do not decide yourself
whether a project needs it. Each reviewer knows where its own plugin's rules
are and ignores files outside its scope.

List the reviewers you found before launching them.

## 3. Run the reviewers in parallel

Launch every reviewer from step 2 **in one message**, so they run in
parallel. Give each one the same prompt: the base ref, the issue number
from step 1 (with the full issue text when the user gave it, and the
instruction to look nothing up), and the list of changed files with their
languages. Reviewers ignore files outside their own scope.
`pr-workflow:scope-reviewer` gets every changed file instead, including documentation and untracked files
(`git ls-files --others --exclude-standard`), since scope creep can be in
any file.

When `pr-workflow:scope-reviewer` flags changes outside the issue, the
fix is never to delete the work: after confirming with the user, open a new
issue for it (rule PR3) and move it to its own branch and PR.

## 4. Consolidate

- Merge all outputs. Remove duplicates (the same line flagged by two
  reviewers: keep the more specific finding).
- Drop any finding that contradicts the standards' own exceptions (for
  example a two-clause null guard under G7, or interfaces under G9).
- Group by file, ordered by line. Count findings per rule ID.

Report in this shape:

```
## Branch review: <n> findings in <m> files

### <file>
- [G2] :42 - <problem>
  Fix: <fix>

### Summary
G2: 3 · G6: 5 · G9: 1
```

If there are no findings, say the branch is clean.

## 5. Fix

- With `--fix`: apply every fix, then run the project's format, lint and
  test commands (`just fmt`, `just lint`, `just test` if a justfile exists;
  otherwise the project's own tooling) and report the results.
- Before the first amend or squash of a branch that is already pushed
  (here or in step 7), fetch it and check that its remote tip is an
  ancestor of `HEAD` (`git merge-base --is-ancestor <remote tip> HEAD`).
  If not, stop and ask the user to sync: a later lease push would discard
  the commits the remote has and `HEAD` lacks. Note that tip; before each
  later rewrite only check that the remote is still at it, since your own
  rewrites make it a non-ancestor.
- Fold every fix into the branch's single commit with
  `git commit --amend` (rule PR6) instead of adding a commit, and update the
  message if a fix changes what the commit does. A branch that already has
  a person's involvement in its PR (a review, a comment or a review thread
  they started) is the exception: fixes there are new commits.
  So is a branch with no commit of its own yet (`git rev-list --count
  <base>..HEAD` is 0): commit normally, since amending would rewrite the
  base. So is a stacked branch deliberately split into several commits:
  its fixes are new commits, as before.
- Without `--fix`: ask the user which findings to fix (all, by rule ID, or
  none) before changing anything.

## 6. Feed back into the standards

If the same rule was flagged three or more times, tell the user. That rule
is either worth turning into a lint/ast-grep check or worth sharpening in
the standards, and it is worth mentioning which.

## 7. Record the review

First make the branch one commit (rule PR6). Count the branch's commits
with `git rev-list --count <fork-point>..HEAD`, where the fork point is
`git merge-base HEAD <base>` (a base given as an argument is a branch tip,
which may have moved on since the branch forked). If there is more than one
and no person has been involved in the PR (as above), squash them into one
curated commit:

```bash
git reset --soft <fork-point> && git commit
```

Its message describes the whole change, in the repository's commit style,
and ends with `Closes #<n>` (before any trailers). Skip this for a stacked branch that is deliberately
split into several commits, or whose PR a person has been involved in. A
branch that already has exactly one commit has nothing to squash, but
check that its message describes the whole change and carries `Closes #<n>`,
and amend it if not (under the same exceptions).

A hook blocks pull request creation until the current commit is recorded as
reviewed. Record it only once every finding is either fixed or explicitly
declined by the user, and all fixes are committed (the PR is built from
commits, so a reviewed HEAD with uncommitted fixes would be meaningless):

```bash
git rev-parse HEAD > "$(git rev-parse --path-format=absolute --git-path pr-workflow-reviewed)"
```

This command is how the review is recorded, and nothing else writes the
marker. Run it on its own, before the command that creates the PR: the hook
checks the marker before a command runs, so a single command that records
the review and creates the PR is blocked.

Any later commit or amend changes HEAD, so record only after the last
amend. Before the next PR, review again and record it through this step;
never just update the marker to the new HEAD.

## 8. Report the outcome

End with the issue, the findings raised, which were fixed (with commits) and
which the user declined, and that the review is recorded for this commit.
If the review was triggered by a blocked PR creation, point the user to
`pr-workflow:submit-pr`, which creates the PR and carries it through
Copilot's review.
