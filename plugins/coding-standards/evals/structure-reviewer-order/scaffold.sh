#!/usr/bin/env bash
# Builds a Python application whose feature branch adds a module with a helper placed
# far above its caller, and a private utility used all over the file placed at the bottom.
set -euo pipefail

git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"
printf '[project]\nname = "reports"\nversion = "0.1.0"\n' > pyproject.toml
mkdir -p reports
printf '"""Reporting application."""\n' > reports/__init__.py
git add -A
git commit -q -m "Initial application"

git checkout -q -b add-sales-report
cat > reports/sales_report.py <<'PY'
"""Builds the weekly sales report text."""


def _total_line(sales) -> str:
    return _money_line("Total", sum(sale.amount for sale in sales))


def _title_line(week: int) -> str:
    return f"Sales report, week {week}"


def _tax_line(sales) -> str:
    return _money_line("Tax", sum(sale.tax for sale in sales))


def _discount_line(sales) -> str:
    return _money_line("Discounts", sum(sale.discount for sale in sales))


def _shipping_line(sales) -> str:
    return _money_line("Shipping", sum(sale.shipping for sale in sales))


def _refund_line(sales) -> str:
    return _money_line("Refunds", sum(sale.refund for sale in sales))


def build_report(week: int, sales) -> str:
    lines = [
        _title_line(week),
        _total_line(sales),
        _tax_line(sales),
        _discount_line(sales),
        _shipping_line(sales),
        _refund_line(sales),
    ]
    return "\n".join(lines)


def _money_line(label: str, amount: float) -> str:
    return f"{label}: {amount:.2f}"
PY
git add -A
git commit -q -m "Add sales report"
