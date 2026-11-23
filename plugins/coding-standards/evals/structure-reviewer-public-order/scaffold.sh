#!/usr/bin/env bash
# Builds a Python application whose feature branch adds a module with two public functions
# that share a helper, the second public function placed between the first and its helpers.
set -euo pipefail

git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"
printf '[project]\nname = "receipts"\nversion = "0.1.0"\n' > pyproject.toml
mkdir -p receipts
printf '"""Receipts application."""\n' > receipts/__init__.py
git add -A
git commit -q -m "Initial application"

git checkout -q -b add-receipt-rendering
cat > receipts/rendering.py <<'PY'
"""Renders order receipts and summaries as text."""


def render_receipt(order) -> str:
    return "\n".join([_header_line(order), _total_line(order)])


def render_summary(order) -> str:
    return "\n".join([_header_line(order), _count_line(order)])


def _header_line(order) -> str:
    return f"Order {order.number}"


def _total_line(order) -> str:
    return f"Total: {order.total:.2f}"


def _count_line(order) -> str:
    return f"Items: {len(order.items)}"
PY
git add -A
git commit -q -m "Add receipt rendering"
