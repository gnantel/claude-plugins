#!/usr/bin/env bash
# Builds a branch for issue #6 with two commits on main, as a session leaves it
# when it committed the test separately while working. No review is recorded.
set -euo pipefail

git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"
mkdir -p src
printf '"""Late fee calculation."""\n\nRATE = 0.05\n\n\ndef late_fee(amount):\n    return amount * RATE\n' > src/late_fee.py
git add -A
git commit -q -m "Initial service"

git checkout -q -b 6-cap-late-fees
printf '"""Late fee calculation."""\n\nRATE = 0.05\nMAX_LATE_FEE = 100\n\n\ndef late_fee(amount):\n    return min(amount * RATE, MAX_LATE_FEE)\n' > src/late_fee.py
git commit -q -am "Cap late fees at 100"
mkdir -p tests
printf '"""Tests for the late fee cap."""\n\nfrom src.late_fee import late_fee\n\n\ndef test_late_fee_is_capped_at_100():\n    assert late_fee(10000) == 100\n' > tests/test_late_fee.py
git add -A
git commit -q -m "Test the late fee cap"
