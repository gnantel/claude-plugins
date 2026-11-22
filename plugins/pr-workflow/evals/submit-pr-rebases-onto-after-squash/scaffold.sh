#!/usr/bin/env bash
# Builds a stacked branch whose parent branch was squash-merged into
# origin/main. The parent's old tip is recorded in .git/parent-old-tip.
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

git checkout -q -b 40-cap-late-fees
printf 'RATE = 0.05\nMAX_LATE_FEE = 100\n' > fees.py
git commit -q -am "Cap late fees at 100"
git rev-parse HEAD > .git/parent-old-tip
git push -q origin 40-cap-late-fees

git checkout -q -b 41-report-late-fees
printf 'def report(fee):\n    return f"late fee: {fee}"\n' > report.py
git add -A
git commit -q -m "Report late fees"
git push -q origin 41-report-late-fees

git checkout -q main
git merge -q --squash 40-cap-late-fees
git commit -q -m "Cap late fees at 100 (#40)"
git push -q origin main
git checkout -q 41-report-late-fees
