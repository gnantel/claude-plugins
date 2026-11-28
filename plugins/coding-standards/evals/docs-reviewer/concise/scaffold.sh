#!/usr/bin/env bash
# Builds an application whose branch adds a README that follows the docs rule,
# including numbers that may stay: a minimum version, a timeout and a limit.
set -euo pipefail

git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"

cat > pyproject.toml <<'TOML'
[project]
name = "thumbnailer"
version = "0.1.0"
description = "Makes thumbnails for uploaded product photos."
requires-python = ">=3.12"
TOML
git add -A
git commit -q -m "Initial application"

git checkout -q -b add-readme
cat > README.md <<'MD'
# thumbnailer

Makes thumbnails for uploaded product photos, so shop pages load quickly.

## Use

Requires Python 3.12 or later. Set `PHOTO_BUCKET`, then run
`python -m thumbnailer`.

A photo that takes longer than 30 seconds is skipped, and the run stops after
5 skipped photos.

## Why thumbnails are made ahead of time

The CDN that serves shop pages can't resize images, so every size has to exist
before a page is published.
MD
git add -A
git commit -q -m "Add README"
