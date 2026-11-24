#!/usr/bin/env bash
# Builds a checkout repo whose change mixes one correct feature gate with flag-usage flaws.
set -euo pipefail

git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"
mkdir -p .claude checkout
cat > .claude/operational.md <<'EOF2'
# Operational conventions

- Feature flags: OpenFeature through `checkout.flags`. `snapshot_for_request()` reads all flags once, resilient to flag service outages, and returns a `FlagSnapshot` to pass down. Flag names are `checkout.<change>` in kebab-case. Never import a vendor SDK.
- Configuration: permanent per-environment settings live in `checkout/settings.py`.
- Metrics: prometheus_client, Prometheus naming.
EOF2
printf '[project]\nname = "checkout"\nversion = "0.1.0"\n' > pyproject.toml
printf '"""Checkout service."""\n' > checkout/__init__.py
cat > checkout/flags.py <<'EOF2'
"""Resilient OpenFeature access: one snapshot of flags per request."""

from dataclasses import dataclass

from openfeature import api


@dataclass(frozen=True)
class FlagSnapshot:
    values: dict

    def enabled(self, name):
        return self.values.get(name, False)

    def value(self, name, default):
        return self.values.get(name, default)


def snapshot_for_request():
    client = api.get_client()
    return FlagSnapshot({
        "checkout.new-tax-engine": client.get_boolean_value("checkout.new-tax-engine", False),
        "checkout.max-order-total": client.get_integer_value("checkout.max-order-total", 1000),
    })
EOF2
git add -A
git commit -q -m "Initial service"
git checkout -q -b change
cat > checkout/payments.py <<'EOF2'
"""Charging and pricing for an order."""

import launchdarkly_server_sdk
from openfeature import api
from prometheus_client import Counter

from checkout.flags import FlagSnapshot, snapshot_for_request

launchdarkly_client = launchdarkly_server_sdk.get()
tax_engine_runs = Counter("checkout_tax_engine_runs_total", "Orders priced, by tax engine", ["engine"])


def price_and_checkout_order(order, card):
    flag_snapshot = snapshot_for_request()
    discounted_order = apply_discount(order)
    total = price_order(discounted_order, flag_snapshot)
    receipt = charge_order_within_limit({**discounted_order, "total": total}, card, flag_snapshot)
    return {**receipt, "summary": summarize_order(discounted_order)}


def apply_discount(order):
    if api.get_client().get_boolean_value("checkout.loyalty-discount", False):
        order["subtotal"] *= 0.95
    return order


def price_order(order, flag_snapshot: FlagSnapshot):
    if flag_snapshot.enabled("checkout.new-tax-engine"):
        return price_with_new_tax_engine(order)
    return price_with_old_tax_engine(order)


def price_with_new_tax_engine(order):
    tax_engine_runs.labels(engine="new").inc()
    return order["subtotal"] * 1.14


def price_with_old_tax_engine(order):
    tax_engine_runs.labels(engine="old").inc()
    return order["subtotal"] * 1.15


def charge_order_within_limit(order, card, flag_snapshot: FlagSnapshot):
    if order["total"] > flag_snapshot.value("checkout.max-order-total", 1000):
        raise ValueError("order total above the maximum")
    return charge_order_in_installments(order, card)


def charge_order_in_installments(order, card):
    return {"order": order["id"], "installments": 3, "card": card["token"]}


def summarize_order(order):
    total = order["subtotal"]
    if api.get_client().get_boolean_value("checkout.loyalty-discount", False):
        total *= 0.95
    return {"id": order["id"], "total": total}


def show_loyalty_banner(user_id):
    return launchdarkly_client.variation("checkout.loyalty-banner", user_id, False)
EOF2
mkdir -p tests
cat > tests/test_pricing.py <<'EOF2'
"""Tests for pricing behind the new tax engine flag."""

import pytest

from checkout.flags import FlagSnapshot
from checkout.payments import price_order


def test_old_tax_engine_when_flag_off():
    assert price_order({"subtotal": 100}, FlagSnapshot({})) == pytest.approx(115)


def test_new_tax_engine_when_flag_on():
    snapshot = FlagSnapshot({"checkout.new-tax-engine": True})
    assert price_order({"subtotal": 100}, snapshot) == pytest.approx(114)
EOF2
git add -A
git commit -q -m "Add installments, limits and loyalty discount"
