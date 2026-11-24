#!/usr/bin/env bash
# Builds a Python application whose branch adds a module with unmarked helpers
# only that module uses, a helper stripped of its `_` for a test, and a public
# function another feature really imports.
set -euo pipefail

git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"
printf '[project]\nname = "billing"\nversion = "0.1.0"\n' > pyproject.toml
mkdir -p billing/invoices billing/reports tests
printf '"""Billing application."""\n' > billing/__init__.py
printf '"""Invoices."""\n' > billing/invoices/__init__.py
printf '"""Reports."""\n' > billing/reports/__init__.py
printf '"""Issues invoices."""\n\n\ndef issue_invoice(customer, amount_cents):\n    return {"customer": customer, "amount_cents": amount_cents}\n' > billing/invoices/issuing.py
printf '"""Applies a discount to an invoice total."""\n\n\ndef discounted_total(amount_cents, percent):\n    return amount_cents - _discount_cents(amount_cents, percent)\n\n\ndef _discount_cents(amount_cents, percent):\n    return amount_cents * percent // 100\n' > billing/invoices/discounts.py
printf 'from billing.invoices.discounts import discounted_total\n\n\ndef test_discounted_total():\n    assert discounted_total(1000, 10) == 900\n' > tests/test_discounts.py
git add -A
git commit -q -m "Initial application"

git checkout -q -b receipts
cat > billing/invoices/receipts.py <<'PY'
"""Renders invoice receipts as text."""


def render_receipt(invoice):
    return format_header(invoice) + "\n" + format_total(invoice)


def format_header(invoice):
    return f"Receipt for {invoice['customer']}"


def format_total(invoice):
    return f"Total: {invoice['amount_cents'] / 100:.2f}"
PY
printf '"""Applies a discount to an invoice total."""\n\n\ndef discounted_total(amount_cents, percent):\n    return amount_cents - discount_cents(amount_cents, percent)\n\n\ndef discount_cents(amount_cents, percent):\n    return amount_cents * percent // 100\n' > billing/invoices/discounts.py
printf 'from billing.invoices.discounts import discount_cents, discounted_total\n\n\ndef test_discounted_total():\n    assert discounted_total(1000, 10) == 900\n\n\ndef test_discount_cents():\n    assert discount_cents(1000, 10) == 100\n' > tests/test_discounts.py
printf '"""Invoices."""\n\nfrom billing.invoices.receipts import render_receipt\n\n__all__ = ["render_receipt"]\n' > billing/invoices/__init__.py
cat > billing/reports/monthly.py <<'PY'
"""Monthly revenue report."""

from billing.invoices import render_receipt


def revenue_report(invoices):
    return "\n".join(render_receipt(invoice) for invoice in invoices)
PY
git add -A
git commit -q -m "Render receipts"
