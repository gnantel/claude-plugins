#!/usr/bin/env bash
# Builds a repository whose branch has no issue: no PR, no GitHub remote, and a
# branch name that doesn't start with an issue number.
set -euo pipefail

git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"
mkdir -p src
printf '"""Late fee calculation."""\n\nRATE = 0.05\n\n\ndef late_fee(amount):\n    return amount * RATE\n' > src/late_fee.py
git add -A
git commit -q -m "Initial service"

git checkout -q -b cap-late-fees
printf '"""Late fee calculation."""\n\nRATE = 0.05\nMAX_LATE_FEE = 100\n\n\ndef late_fee(amount):\n    return min(amount * RATE, MAX_LATE_FEE)\n' > src/late_fee.py
git commit -q -am "Cap late fees at 100"
