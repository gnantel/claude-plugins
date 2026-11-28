#!/usr/bin/env bash
# Builds an application whose branch documents its sync feature by putting the
# code into words, next to purpose, usage and a decision the code doesn't show.
set -euo pipefail

git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"

printf '# contact-sync\n' > README.md
git add -A
git commit -q -m "Initial application"

git checkout -q -b add-sync
mkdir -p sync
printf '"""Copies CRM contacts into the shared address book."""\n' > sync/__init__.py
cat > sync/fetch.py <<'PY'
"""Reads contacts from the CRM."""


def fetch_contacts(crm):
    return [contact for contact in crm.contacts() if contact.email]
PY
cat > sync/merge.py <<'PY'
"""Works out which address book entries to write."""


def changed_contacts(contacts, address_book):
    return [c for c in contacts if address_book.get(c.email) != c]
PY
cat > sync/job.py <<'PY'
"""Runs one sync."""

from sync.fetch import fetch_contacts
from sync.merge import changed_contacts


def run_sync(crm, address_book):
    for contact in changed_contacts(fetch_contacts(crm), address_book):
        address_book[contact.email] = contact
PY
cat > README.md <<'MD'
# contact-sync

Keeps the shared address book up to date with the CRM, so support sees current
contact details.

## Use

Run `python -m sync`.

## How it works

- `sync/fetch.py` has `fetch_contacts`, which calls `crm.contacts()` and keeps
  only the contacts that have an email address.
- `sync/merge.py` has `changed_contacts`, which looks up each contact in the
  address book by email and keeps the ones that differ.
- `sync/job.py` has `run_sync`, which first calls `fetch_contacts`, passes the
  result to `changed_contacts`, then loops over what it returns and writes each
  contact into the address book under its email.

## Deletions

Contacts are never deleted from the address book, because the billing system
reads the same one and keeps invoicing former customers.
MD
git add -A
git commit -q -m "Add contact sync"
