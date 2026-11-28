#!/usr/bin/env bash
# Builds a plugin repository whose branch hard-codes counts of growing lists in
# its README and in manifest and skill descriptions, and pins a tool version,
# next to numbers that may stay: a minimum version, a limit and a version field.
set -euo pipefail

git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"

mkdir -p .claude-plugin agents skills/lint
printf '# review-kit\n\nCode reviewers for pull requests.\n' > README.md
printf '{\n  "name": "review-kit",\n  "version": "1.2.0",\n  "description": "Code reviewers for pull requests."\n}\n' > .claude-plugin/plugin.json
git add -A
git commit -q -m "Initial plugin"

git checkout -q -b add-reviewers
for concern in naming comments tests security; do
  printf -- '---\nname: %s-reviewer\ndescription: Reviews changed code for %s.\n---\n\nReport findings only.\n' "$concern" "$concern" > "agents/$concern-reviewer.md"
done
cat > README.md <<'MD'
# review-kit

Code reviewers for pull requests. The plugin ships four reviewers, which run
in parallel.

## Use

Install Python 3.11 or later and ruff 0.6.9, then run `/lint`. A review stops
after 3 failed attempts.
MD
printf '{\n  "name": "review-kit",\n  "version": "1.3.0",\n  "description": "Four code reviewers for pull requests."\n}\n' > .claude-plugin/plugin.json
cat > skills/lint/SKILL.md <<'MD'
---
name: lint
description: Checks changed Python files against our 12 lint rules. Use before opening a pull request.
---

# Lint

Run `ruff check` on the changed files and report what it finds.
MD
git add -A
git commit -q -m "Add reviewers and the lint skill"
