#!/usr/bin/env bash
# Adds a payment capture that calls an external API with no timeout and retries
# a non-idempotent POST without an idempotency key.
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
cat > orders/payment_capture.py <<'EOF'
"""Captures payment for confirmed orders."""

import httpx
from tenacity import retry, stop_after_attempt


@retry(stop=stop_after_attempt(5))
def capture_payment(order):
    response = httpx.post("https://payments.example.com/captures",
                          json={"payment_id": order.payment_id, "amount_cents": order.total_cents})
    response.raise_for_status()
    return response.json()["capture_id"]
EOF
git add -A
git commit -q -m "Add payment capture"
