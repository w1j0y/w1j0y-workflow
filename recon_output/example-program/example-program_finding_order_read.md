# Finding: order read across accounts

What: The finding file the ledger validation row points at, in short form.
Who writes: the test phase prompt.
Who reads: the finding validation prompt and tools/ledger_gate.py.
Wired into: recon_output/example-program/coverage_ledger.md, reports/example-program/example-finding/REPORT.md (one-way: reference only)

## Summary
tester-a can read order 102 (owned by tester-b) by changing the id in /orders/[id].

## Evidence
reports/example-program/example-finding/evidence/order_read_redacted.txt
