#!/usr/bin/env bash
# Builds an application whose branch turns its README into a changelog, next to
# a behaviour described with the word "previous" and an old line, already on
# main, that the branch doesn't touch.
set -euo pipefail

git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"

cat > README.md <<'MD'
# Report importer

Imports supplier reports into the warehouse. The importer now accepts gzipped
files.

## Use

Run `python -m importer <file>`.
MD
mkdir -p importer
printf '"""Imports supplier reports."""\n' > importer/__init__.py
git add -A
git commit -q -m "Initial application"

git checkout -q -b csv-reports
cat >> README.md <<'MD'

## Output

Reports are now written as CSV (previously they were JSON).

A failed upload retries the previous request once before the run stops.

## Recent changes

- Added CSV output.
- Renamed the `--out` flag to `--output`.
- Fixed a crash on empty files.
MD
git add -A
git commit -q -m "CSV output"
