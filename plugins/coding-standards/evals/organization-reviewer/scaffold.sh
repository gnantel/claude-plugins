#!/usr/bin/env bash
# Builds a feature-organized Python application whose branch adds a top-level
# layer folder and a utils grab bag, next to a sub-concept folder inside a feature.
set -euo pipefail

git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"
printf '[project]\nname = "billing"\nversion = "0.1.0"\n' > pyproject.toml
mkdir -p billing/invoices billing/customers
printf '"""Billing application."""\n' > billing/__init__.py
printf '"""Invoices: issuing, numbering and late fees."""\n' > billing/invoices/__init__.py
printf '"""Customers and their accounts."""\n' > billing/customers/__init__.py
printf '"""Issues invoices."""\n\n\ndef issue_invoice(customer, amount_cents):\n    return {"customer": customer, "amount_cents": amount_cents}\n' > billing/invoices/issuing.py
git add -A
git commit -q -m "Initial feature-organized application"

git checkout -q -b email-invoices
mkdir -p billing/services billing/utils billing/invoices/rendering
printf '"""Sends invoice emails."""\n\n\ndef send_invoice_email(invoice, mailer):\n    mailer.send(invoice["customer"], "Your invoice")\n' > billing/services/invoice_email_service.py
printf '"""Assorted helpers."""\n\n\ndef format_cents(amount_cents):\n    return f"{amount_cents / 100:.2f}"\n' > billing/utils/helpers.py
printf '"""Renders invoices as HTML for emails."""\n\n\ndef render_html(invoice):\n    return f"<p>{invoice[\"amount_cents\"]}</p>"\n' > billing/invoices/rendering/html.py
printf '"""Rendering invoices for different outputs."""\n' > billing/invoices/rendering/__init__.py
git add -A
git commit -q -m "Email invoices"
