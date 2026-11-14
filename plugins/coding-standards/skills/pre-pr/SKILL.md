---
name: pre-pr
description: Review the current branch with every enabled review plugin's narrow reviewer agents in parallel (coding standards always; others such as operational-readiness when the project enables them), then report consolidated findings and offer to fix them. Use when the user asks for a pre-PR or standards review, or when the coding-standards hook blocks pull request creation.
argument-hint: "[base-branch] [--fix]"
---

# Pre-PR Review

Review this branch's changes before a PR is opened, so nothing reaches
review or CI that the standards would flag.

Arguments: `$ARGUMENTS`

## 1. Work out what changed

- Base: the first argument if one is given, otherwise
  `git merge-base HEAD origin/main`, falling back to `main` then `master`.
- Changed files: `git diff --name-only <base>` plus uncommitted changes
  (`git status --porcelain`). Keep source files (`.java`, `.py`, `.rs`,
  `.ts`, `.tsx`) and configuration or manifest files (`.yaml`, `.yml`,
  `.toml`, `.properties`, `pom.xml`, `package.json`), which operational
  reviewers need. Ignore generated files, lockfiles and vendored code.
- If nothing relevant changed, say so, record the review (step 7) and stop.

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
parallel. Give each one the same prompt: the base ref and the list of
changed files with their languages. Reviewers ignore files outside their own
scope.

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
PR again once the review is recorded.
