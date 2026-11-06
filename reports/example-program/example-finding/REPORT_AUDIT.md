# Report audit: order read across accounts

What: The checklist result for the example report before it was submitted.
Who writes: the report validation prompt.
Who reads: the human before submitting; tools/ledger_gate.py reads the ledger, not this file.
Wired into: reports/example-program/example-finding/REPORT.md, recon_output/example-program/coverage_ledger.md (one-way: reference only)

| Check | Result |
|---|---|
| Both accounts are test accounts the tester created | pass |
| Baseline, control and variant are all in the steps | pass |
| Read-back done from the owner account | pass |
| Evidence is redacted | pass |
| Rate and header rules followed | pass |
| AI disclosure line present (program requires it) | pass |
| Severity label matches evidence (read of order details) | pass |

Verdict: ready to submit after the human reads it once.
