#!/usr/bin/env bash
# Builds a Python application whose branch rewrites an existing money formatter
# under another name and hand-rolls a standard-library count, next to a capped
# percentage that looks like an existing one but is a different business rule.
set -euo pipefail

git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"
printf '[project]\nname = "shop"\nversion = "0.1.0"\nrequires-python = ">=3.12"\ndependencies = []\n' > pyproject.toml
mkdir -p shop/money shop/invoices shop/orders
printf '"""Shop application."""\n' > shop/__init__.py
printf '"""Orders."""\n' > shop/orders/__init__.py
cat > shop/money/__init__.py <<'PY'
"""Money amounts, held as integer cents."""

from shop.money.formatting import format_amount

__all__ = ["format_amount"]
PY
cat > shop/money/formatting.py <<'PY'
"""Shows money amounts to people."""


def format_amount(cents):
    return f"${cents // 100:,}.{cents % 100:02d}"
PY
cat > shop/invoices/__init__.py <<'PY'
"""Invoices and their late fees."""

from shop.invoices.late_fees import late_fee_cents

__all__ = ["late_fee_cents"]
PY
cat > shop/invoices/late_fees.py <<'PY'
"""The fee charged on an overdue invoice, set by the payment terms."""

_LATE_FEE_PERCENT = 2
_LATE_FEE_CAP_CENTS = 5_000


def late_fee_cents(overdue_cents):
    return min(overdue_cents * _LATE_FEE_PERCENT // 100, _LATE_FEE_CAP_CENTS)
PY
git add -A
git commit -q -m "Initial application"

git checkout -q -b receipts-and-loyalty
mkdir -p shop/receipts shop/loyalty
printf '"""Customer receipts."""\n\nfrom shop.receipts.receipt import render_receipt\n\n__all__ = ["render_receipt"]\n' > shop/receipts/__init__.py
cat > shop/receipts/receipt.py <<'PY'
"""Renders an order's receipt as text."""


def render_receipt(order):
    lines = [f"{line.name}: {_render_price(line.price_cents)}" for line in order.lines]
    lines.append(f"Total: {_render_price(order.total_cents)}")
    return "\n".join(lines)


def _render_price(minor_units):
    whole, fraction = divmod(minor_units, 100)
    return "$" + f"{whole:,}" + "." + str(fraction).zfill(2)
PY
cat > shop/orders/status_report.py <<'PY'
"""Reports how many orders are in each status."""


def status_report(orders):
    tally = _tally_statuses(orders)
    return "\n".join(f"{status}: {tally[status]}" for status in sorted(tally))


def _tally_statuses(orders):
    tally = {}
    for order in orders:
        if order.status not in tally:
            tally[order.status] = 0
        tally[order.status] += 1
    return tally
PY
printf '"""Loyalty rewards."""\n\nfrom shop.loyalty.credit import loyalty_credit_cents\n\n__all__ = ["loyalty_credit_cents"]\n' > shop/loyalty/__init__.py
cat > shop/loyalty/credit.py <<'PY'
"""The store credit a loyalty member earns on a purchase, set by marketing."""

_CREDIT_PERCENT = 5
_CREDIT_CAP_CENTS = 2_000


def loyalty_credit_cents(purchase_cents):
    return min(purchase_cents * _CREDIT_PERCENT // 100, _CREDIT_CAP_CENTS)
PY
git add -A
git commit -q -m "Receipts, status report and loyalty credit"
