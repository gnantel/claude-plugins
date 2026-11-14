---
name: pre-pr
description: Review the current branch against its leaf issue with every enabled review plugin's narrow reviewer agents in parallel (coding standards always; others such as operational-readiness when the project enables them), then report consolidated findings and offer to fix them. Use when the user asks for a pre-PR or standards review, or when the coding-standards hook blocks pull request creation.
argument-hint: "[base-branch] [--fix]"
---

# Pre-PR Review

Review this branch's changes before a PR is opened, so nothing reaches
review or CI that the standards would flag.

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
  `coding-standards:scope-reviewer` in step 3, since scope creep happens in
  any kind of change, then continue as usual: record the review in step 7,
  retry the PR creation if it was blocked, and continue with step 8.
- **Issue:** find the leaf issue this branch implements with
  `python3 ${CLAUDE_PLUGIN_ROOT}/skills/issues/scripts/issues.py for-branch`
  (or the issue the user names). Stop and tell the user if there is none,
  if it is closed, or if it has sub-issues (`is_leaf: false`): every PR
  implements exactly one open leaf issue (rule PR1). Offer to create or
  split the issue with the `issues` skill.
- **Existing PR:** if the branch already has a PR based on the default
  branch, its `gh pr view --json closingIssuesReferences` must be exactly
  that issue. If the link is missing, add `Closes #<n>` to the description
  with `gh pr edit` before continuing; if it names a different issue, stop
  and ask the user. Stacked PRs are exempt (see step 7).

## 2. Find the reviewers

The reviewers are **every** agent type available to you whose name matches
`<plugin>:<name>-reviewer`, from any plugin. Being available means the
plugin is enabled for this project, so run them all; do not skip a reviewer
because its plugin is not `coding-standards`, and do not decide yourself
whether a project needs it. Each reviewer knows where its own plugin's rules
are and ignores files outside its scope.

List the reviewers you found before launching them.

## 3. Run the reviewers in parallel

Launch every reviewer from step 2 **in one message**, so they run in
parallel. Give each one the same prompt: the base ref, the issue number
from step 1, and the list of changed files with their languages. Reviewers
ignore files outside their own scope. `coding-standards:scope-reviewer` gets
every changed file instead, including documentation and untracked files
(`git ls-files --others --exclude-standard`), since scope creep can be in
any file.

When `coding-standards:scope-reviewer` flags changes outside the issue, the
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
## Pre-PR review: <n> findings in <m> files

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
- Without `--fix`: ask the user which findings to fix (all, by rule ID, or
  none) before changing anything.

## 6. Feed back into the standards

If the same rule was flagged three or more times, tell the user. That rule
is either worth turning into a lint/ast-grep check or worth sharpening in
the standards, and it is worth mentioning which.

## 7. Record the review

A hook blocks pull request creation until the current commit is recorded as
reviewed. Record it only once every finding is either fixed or explicitly
declined by the user, and all fixes are committed (the PR is built from
commits, so a reviewed HEAD with uncommitted fixes would be meaningless):

```bash
git rev-parse HEAD > "$(git rev-parse --path-format=absolute --git-path coding-standards-reviewed)"
```

Any later commit changes HEAD, so the branch needs a fresh review before the
next PR. If this review was triggered by a blocked PR creation, create the
PR again once the review is recorded. The PR description must include
`Closes #<n>` for the issue from step 1. After creating the PR, confirm the
link with `gh pr view --json closingIssuesReferences` (exactly that one
issue), and fix the description with `gh pr edit` if it doesn't match.

A stacked PR (based on another feature branch, not the default branch) is
the exception: GitHub ignores closing keywords there, so the link stays
empty. Its issue comes from the branch name (`<issue-id>-<description>`).
Confirm the link once the PR is retargeted to the default branch.

## 8. Start the Copilot review loop

Once the PR exists, run the `coding-standards:copilot-review-loop` skill on
it, so Copilot's automatic review is addressed without the user having to
ask.
