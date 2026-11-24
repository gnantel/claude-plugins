#!/usr/bin/env bash
# Adds a shipping-quote step with an untraced outbound call and an operation
# that drops its trace context in a thread hand-off, next to a correctly
# traced call that follows the conventions.
set -euo pipefail

git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"
mkdir -p .claude shipping
cat > .claude/operational.md <<'EOF2'
# Operational conventions

- Metrics: prometheus_client, Prometheus naming (`snake_case`, `_total` for counters, `_seconds` for durations).
- Logging: structlog with key-value fields.
- Resilience: every HTTP call through `httpx` has an explicit timeout.
- Tracing: OpenTelemetry (`opentelemetry-api`). Outbound HTTP is not auto-instrumented: wrap each call in a span and name it after the operation.
- Personal data: never log email addresses or names.
EOF2
printf '[project]\nname = "shipping"\nversion = "0.1.0"\n' > pyproject.toml
printf '"""Shipping service."""\n' > shipping/__init__.py
git add -A
git commit -q -m "Initial service"
git checkout -q -b change
cat > shipping/quotes.py <<'EOF2'
"""Fetches shipping quotes from carriers."""

from concurrent.futures import ThreadPoolExecutor

import httpx
from opentelemetry import trace
from opentelemetry.propagate import inject

tracer = trace.get_tracer(__name__)
pool = ThreadPoolExecutor(max_workers=4)


def fetch_carrier_quote(carrier_url, parcel):
    response = httpx.post(carrier_url, json=parcel, timeout=2.0)
    response.raise_for_status()
    return response.json()


def fetch_all_quotes(carrier_urls, parcel):
    with tracer.start_as_current_span("fetch all quotes"):
        futures = [pool.submit(fetch_carrier_quote, url, parcel) for url in carrier_urls]
        return [future.result() for future in futures]


def fetch_tracking(tracking_url, tracking_id):
    with tracer.start_as_current_span("fetch tracking"):
        trace.get_current_span().set_attribute("shipping.tracking_id", tracking_id)
        headers = {}
        inject(headers)
        response = httpx.get(tracking_url, params={"id": tracking_id}, headers=headers, timeout=2.0)
        response.raise_for_status()
        return response.json()
EOF2
git add -A
git commit -q -m "Add shipping quotes"
