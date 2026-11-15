#!/usr/bin/env bash
# Adds an order-cancellation handler with no metrics, and a metric labelled by
# customer ID, to the shared service.
set -euo pipefail

git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"
mkdir -p .claude orders
cat > .claude/operational.md <<'EOF'
# Operational conventions

- Metrics: prometheus_client, Prometheus naming (`snake_case`, `_total` for counters, `_seconds` for durations).
- Logging: structlog with key-value fields; every log has `order_id` where one exists.
- Resilience: tenacity for retries; every HTTP call through `httpx` has an explicit timeout.
- Personal data: never log email addresses or names.
EOF
printf '[project]\nname = "orders"\nversion = "0.1.0"\n' > pyproject.toml
printf '"""Order service."""\n' > orders/__init__.py
git add -A
git commit -q -m "Initial service"
git checkout -q -b change
cat > orders/cancellation.py <<'EOF'
"""Cancels orders that haven't shipped yet."""

from prometheus_client import Counter

ORDERS_VIEWED_TOTAL = Counter("orders_viewed_total", "Orders viewed", ["customer_id"])


def view_order(order, customer_id):
    ORDERS_VIEWED_TOTAL.labels(customer_id=customer_id).inc()
    return order


def cancel_order(order, payments):
    if order.shipped:
        raise ValueError("Shipped orders can't be cancelled")
    payments.refund(order.payment_id)
    order.status = "cancelled"
    return order
EOF
git add -A
git commit -q -m "Add order cancellation"
