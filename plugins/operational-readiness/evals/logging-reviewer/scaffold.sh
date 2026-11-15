#!/usr/bin/env bash
# Adds an order-confirmation step that logs by interpolating personal data, next
# to a structured log call that follows the conventions.
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
cat > orders/confirmation.py <<'EOF'
"""Confirms orders and emails the customer."""

import structlog

log = structlog.get_logger()


def confirm_order(order, mailer):
    mailer.send(order.customer_email, "Your order is confirmed")
    log.info(f"Sent confirmation for order {order.id} to {order.customer_email}")
    order.status = "confirmed"
    log.info("order confirmed", order_id=order.id)
    return order
EOF
git add -A
git commit -q -m "Add order confirmation"
