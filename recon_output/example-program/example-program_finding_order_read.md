# Finding: order read across accounts

What: The finding file the ledger validation row points at: the class, the steps to repeat, baseline, control, variant, delta, impact and evidence.
Who writes: the test phase prompt.
Who reads: the finding validation prompt and tools/ledger_gate.py.
Wired into: recon_output/example-program/coverage_ledger.md, reports/example-program/example-finding/REPORT.md (one-way: reference only)

## Class
Authorization check on an order page: does the page confirm that the order belongs to the signed-in account?

## What was done
Invented sample data on a .test host, two test accounts, four requests, all recorded in the evidence file.
1. As tester-a, order 101 (tester-a's own) was requested: 200, owner tester-a (baseline).
2. As tester-a, order 999999 was requested: 404 (control), so the page can say no.
3. As tester-a, order 102 (tester-b's) was requested with the same session: 200, owner tester-b (variant).
4. As tester-b, order 102 was requested: 200, same items (read-back).

## Baseline, control, variant and delta
- Baseline: 200, owner tester-a.
- Control: 404.
- Variant: 200, owner tester-b, shown to tester-a's session.
- Delta: the page did not check ownership. The read-back confirms the data is tester-b's and not a catch-all page.

## Impact
tester-a was shown tester-b's order details (items and address). Only the two test accounts were used.

## Evidence
reports/example-program/example-finding/evidence/order_read_redacted.txt
