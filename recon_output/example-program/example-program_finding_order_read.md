# Finding: order read across accounts

What: The finding file the ledger validation row points at: the class, the steps to repeat, baseline, control, variant, delta, impact and evidence.
Who writes: the test phase prompt.
Who reads: the finding validation prompt and tools/ledger_gate.py.
Wired into: recon_output/example-program/coverage_ledger.md, reports/example-program/example-finding/REPORT.md (one-way: reference only)

## Class
Object reference: the server does not check that an order belongs to the caller.

## Steps to repeat
1. As tester-a, request tester-a's own order 101. Save request and response (baseline).
2. As tester-a, request an order that does not exist, 999999. It returns 404 (control).
3. As tester-a, with the same session, request order 102, which belongs to tester-b. Only the id changes (variant).
4. As tester-b, request order 102 (read-back).

## Baseline, control, variant and delta
- Baseline: 200, order 101, owner tester-a.
- Control: 404, so the surface can say no and the 200 below is not a catch-all.
- Variant: 200, order 102, owner tester-b, to tester-a's session.
- Delta: tester-a received tester-b's order. The read-back from tester-b shows the same items.

## Impact
tester-a can read tester-b's order details (items and address) by changing the id in /orders/[id]; any buyer could read any other buyer's orders by iterating ids.

## Evidence
reports/example-program/example-finding/evidence/order_read_redacted.txt
