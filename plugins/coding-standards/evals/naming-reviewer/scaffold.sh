#!/usr/bin/env bash
# Builds a Python application whose feature branch adds vague names and a
# wrapper that adds no clarity, next to a conventional loop index.
set -euo pipefail

git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"
printf '[project]\nname = "shop"\nversion = "0.1.0"\n' > pyproject.toml
mkdir -p shop
printf '"""Shop application."""\n' > shop/__init__.py
git add -A
git commit -q -m "Initial application"

git checkout -q -b add-order-totals
cat > shop/order_totals.py <<'EOF'
"""Totals the prices of the items in an order."""


def process(data: list[dict]) -> int:
    res = 0
    for i in range(len(data)):
        res += price_of(data[i])
    return res


def price_of(item: dict) -> int:
    return get_price(item)


def get_price(item: dict) -> int:
    return item["unit_price_cents"] * item["quantity"]
EOF
git add -A
git commit -q -m "Add order totals"
