#!/usr/bin/env bash
# Builds an empty repository; the issue under test is in the prompt.
set -euo pipefail

git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"
printf '# Billing\n\nBilling service.\n' > README.md
git add -A
git commit -q -m "Initial service"
