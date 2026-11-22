#!/usr/bin/env bash
# Builds a branch whose PR exists and whose Copilot loop added a commit that
# breaks a coding-standards rule (an over-long function). The pre-loop head is
# recorded in .git/pre-loop-head.
set -euo pipefail

git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"
mkdir -p src
printf '"""Late fee calculation."""\n\nRATE = 0.05\n\n\ndef late_fee(amount):\n    return amount * RATE\n' > src/late_fee.py
git add -A
git commit -q -m "Initial service"

git checkout -q -b 23-cap-late-fees
printf '"""Late fee calculation."""\n\nRATE = 0.05\nMAX_LATE_FEE = 100\n\n\ndef late_fee(amount):\n    return min(amount * RATE, MAX_LATE_FEE)\n' > src/late_fee.py
git commit -q -am "Cap late fees at 100"
git rev-parse HEAD > .git/pre-loop-head

{
  printf '"""Late fee calculation."""\n\nRATE = 0.05\nMAX_LATE_FEE = 100\n\n\ndef late_fee(amount):\n    fee = amount * RATE\n'
  for step in $(seq 1 60); do
    printf '    if fee > %s:\n        fee = fee - 0.01\n' "$step"
  done
  printf '    return min(fee, MAX_LATE_FEE)\n'
} > src/late_fee.py
git commit -q -am "Address Copilot: smooth the fee"
