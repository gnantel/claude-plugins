#!/usr/bin/env bash
# Builds a Python application whose feature branch adds a 60-line function and a
# three-clause condition, next to a simple two-clause null guard.
set -euo pipefail

git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"
printf '[project]\nname = "billing"\nversion = "0.1.0"\n' > pyproject.toml
mkdir -p billing
printf '"""Billing application."""\n' > billing/__init__.py
git add -A
git commit -q -m "Initial application"

git checkout -q -b add-invoice-rendering
{
  printf '"""Renders invoices as plain text for printing."""\n\n\n'
  printf 'def render_invoice(invoice, customer) -> str:\n'
  printf '    lines = []\n'
  for field in number date due_date currency status reference purchase_order terms notes \
               customer_name customer_email customer_phone billing_street billing_city \
               billing_postcode billing_country shipping_street shipping_city shipping_postcode \
               shipping_country subtotal discount tax_rate tax_amount shipping_cost total \
               amount_paid balance payment_method bank_account sort_code iban swift \
               late_fee_rate grace_days account_manager region cost_centre project \
               contract approval_code approver department budget_line \
               created_by created_at updated_by updated_at source channel campaign \
               segment tier; do
    printf '    lines.append(f"%s: {invoice.%s}")\n' "$field" "$field"
  done
  printf '    if customer.is_overseas and customer.vat_number and not customer.vat_exempt:\n'
  printf '        lines.append(f"Reverse charge VAT: {customer.vat_number}")\n'
  printf '    if customer is not None and customer.notes:\n'
  printf '        lines.append(customer.notes)\n'
  printf '    return "\\n".join(lines)\n'
} > billing/invoice_text.py
git add -A
git commit -q -m "Add invoice rendering"
