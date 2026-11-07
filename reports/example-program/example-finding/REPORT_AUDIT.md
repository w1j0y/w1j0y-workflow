# Report audit: order read across accounts

What: The checklist result for the example report before it was submitted.
Who writes: the report validation prompt.
Who reads: the human before submitting; tools/ledger_gate.py reads the ledger, not this file.
Wired into: reports/example-program/example-finding/REPORT.md, recon_output/example-program/coverage_ledger.md (one-way: reference only)

## Round 1

Date: 2026-01-02
Reader: a fresh report-audit reader (prompts/web/VALIDATE_REPORT.md), read-only, no requests sent.

Checks that passed: both accounts are test accounts the tester created; baseline, control and variant are in the steps; the read-back is from the owner account; evidence is redacted and says which session each request used; header and rate rules followed; the AI disclosure line is present (the program requires it); the severity label matches the evidence (a read of order details).

| Line | Problem | Why it matters | Fix |
|---|---|---|---|
| none | none | none | none |

Decision: no problems left.

ROUTING: SUBMIT
