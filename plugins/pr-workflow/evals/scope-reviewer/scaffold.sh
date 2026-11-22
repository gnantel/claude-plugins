#!/usr/bin/env bash
# Builds a repository whose branch implements a late-fee cap but also carries an
# unrelated rename and a deployment document.
set -euo pipefail

git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"
mkdir -p src/fees src/reports
printf '"""Late fee calculation."""\n\nRATE = 0.05\n\n\ndef late_fee(amount):\n    return amount * RATE\n' > src/fees/late_fee.py
printf '"""Monthly report rendering."""\n\n\ndef render(rows):\n    return "\\n".join(str(r) for r in rows)\n' > src/reports/monthly.py
printf '# Billing\n\nBilling service.\n' > README.md
git add -A
git commit -q -m "Initial service"

git checkout -q -b 6-cap-late-fees
printf '"""Late fee calculation."""\n\nRATE = 0.05\nMAX_LATE_FEE = 100\n\n\ndef late_fee(amount):\n    return min(amount * RATE, MAX_LATE_FEE)\n' > src/fees/late_fee.py
git commit -q -am "Cap late fees at 100"
printf '"""Monthly report rendering."""\n\n\ndef render_monthly_report(report_rows):\n    return "\\n".join(str(row) for row in report_rows)\n' > src/reports/monthly.py
git commit -q -am "Tidy up report naming"
printf '# Billing\n\nBilling service.\n\n## Deployment\n\nDeploy with `just deploy` to staging first.\n' > README.md
git commit -q -am "Document deployment"
