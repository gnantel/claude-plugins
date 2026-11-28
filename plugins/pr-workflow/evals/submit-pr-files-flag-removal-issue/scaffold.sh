#!/usr/bin/env bash
# Builds a service with one existing OpenFeature flag and two branches. One
# adds a new flag. The other only has look-alikes: a new use of the existing
# flag and a new configuration setting.
set -euo pipefail

git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"
mkdir -p .claude billing
cat > .claude/operational.md <<'DOC'
# Operations

## Feature flags

Flags go through OpenFeature, read once per request into `FlagSnapshot` in
`billing/flags.py`. Names are `kebab-case`. Remove a flag once it has been
fully on for 21 days.
DOC
cat > billing/flags.py <<'PY'
"""The feature flags of one billing request, read once."""

from dataclasses import dataclass

from openfeature import api


@dataclass(frozen=True)
class FlagSnapshot:
    new_invoice_email: bool


def read_flags() -> FlagSnapshot:
    client = api.get_client()
    return FlagSnapshot(
        new_invoice_email=client.get_boolean_value("new-invoice-email", False),
    )
PY
cat > billing/late_fee.py <<'PY'
"""Late fee calculation."""

RATE = 0.05


def late_fee(amount):
    return amount * RATE
PY
cat > billing/email.py <<'PY'
"""Invoice email text."""


def subject(invoice_number, flags):
    if flags.new_invoice_email:
        return f"Your invoice {invoice_number} is ready"
    return f"Invoice {invoice_number}"


def footer(lines, flags):
    return "\n".join(lines)
PY
git add -A
git commit -q -m "Initial billing service"
git update-ref refs/remotes/origin/main main

git checkout -q -b 7-shorter-email-footer
cat > billing/email.py <<'PY'
"""Invoice email text."""

import os

MAX_FOOTER_LINES = int(os.environ.get("MAX_FOOTER_LINES", "5"))


def subject(invoice_number, flags):
    if flags.new_invoice_email:
        return f"Your invoice {invoice_number} is ready"
    return f"Invoice {invoice_number}"


def footer(lines, flags):
    if flags.new_invoice_email:
        return _short_footer(lines)
    return "\n".join(lines)


def _short_footer(lines):
    return "\n".join(lines[:MAX_FOOTER_LINES])
PY
git commit -q -am "Shorten the new invoice email's footer

Closes #7"

git checkout -q -b 6-tiered-late-fees main
sed -i 's/    new_invoice_email: bool/&\n    tiered_late_fees: bool/' billing/flags.py
sed -i 's/        new_invoice_email=.*/&\n        tiered_late_fees=client.get_boolean_value(TIERED_LATE_FEES, False),/' billing/flags.py
sed -i 's/^from openfeature import api/&\n\nTIERED_LATE_FEES = "tiered-late-fees"/' billing/flags.py
cat > billing/late_fee.py <<'PY'
"""Late fee calculation."""

RATE = 0.05
HIGH_RATE = 0.08
HIGH_AMOUNT = 1000


def late_fee(amount, flags):
    if flags.tiered_late_fees:
        return _tiered_fee(amount)
    return _flat_fee(amount)


def _tiered_fee(amount):
    return amount * (HIGH_RATE if amount > HIGH_AMOUNT else RATE)


def _flat_fee(amount):
    return amount * RATE
PY
git commit -q -am "Charge tiered late fees behind a flag

Closes #6"
