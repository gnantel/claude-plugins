#!/usr/bin/env bash
# Builds a branch whose base (origin/main) moved on with a different change to the
# same lines, so the PR conflicts. origin is a local bare repository.
set -euo pipefail

git init -q --bare ../origin.git
git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"
git remote add origin ../origin.git
printf 'RATE = 0.05\n' > fees.py
git add -A
git commit -q -m "Initial fees"
git push -q origin main

git checkout -q -b 31-cap-late-fees
printf 'RATE = 0.05\nMAX_LATE_FEE = 100\n' > fees.py
git commit -q -am "Cap late fees at 100"
git push -q origin 31-cap-late-fees

git checkout -q main
printf 'RATE = 0.05\nGRACE_DAYS = 5\n' > fees.py
git commit -q -am "Add a grace period"
git push -q origin main
git checkout -q 31-cap-late-fees
