#!/usr/bin/env bash
# Builds a Python application whose feature branch breaks the comment rules in
# ways generic advice would accept (a missing file header, a function docstring
# in an application), next to a comment that rightly explains a workaround.
set -euo pipefail

git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"

cat > pyproject.toml <<'EOF'
[project]
name = "visit-counter"
version = "0.1.0"
description = "Web application that counts page visits."
EOF
mkdir -p counter
cat > counter/__init__.py <<'EOF'
"""Counts visits to the site's pages."""
EOF
git add -A
git commit -q -m "Initial application"

git checkout -q -b add-visit-counting
cat > counter/visits.py <<'EOF'
import time

VENDOR_RATE_LIMIT_PAUSE_SECONDS = 0.2


def record_visit(visits_by_page: dict[str, int], page: str) -> None:
    """Record one visit to the given page.

    Args:
        visits_by_page: Visit counts keyed by page path.
        page: The page that was visited.
    """
    # increment the visit count for the page
    visits_by_page[page] = visits_by_page.get(page, 0) + 1


def report_visits(visits_by_page: dict[str, int], send) -> None:
    for page, count in visits_by_page.items():
        send(page, count)
        # The analytics vendor drops requests sent faster than five per second
        # (their bug #4412, no fix planned), so pace the calls.
        time.sleep(VENDOR_RATE_LIMIT_PAUSE_SECONDS)
EOF
git add -A
git commit -q -m "Add visit counting"
