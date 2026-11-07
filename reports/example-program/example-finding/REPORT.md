# Order read across accounts on shop.example-shop.test

What: The submission-ready report for the invented example finding.
Who writes: the report phase prompt, then the human edits.
Who reads: the program triage team (in the story) and tools/ledger_gate.py submittable.
Wired into: reports/example-program/example-finding/REPORT_AUDIT.md, recon_output/example-program/coverage_ledger.md (one-way: reference only)

AI disclosure: This report was prepared with AI assistance (Claude Code). I reviewed and reproduced every step myself with my own test accounts.

## Summary
GET /orders/[id] on shop.example-shop.test returns another buyer's order to a logged-in buyer, because the server checks the session but not that the order belongs to the caller.

## Steps to reproduce
1. As tester-a, send GET /orders/101 to shop.example-shop.test with the header X-Research: tester-a. Response: 200, owner tester-a (baseline).
2. As tester-a, with the same session, send GET /orders/999999. Response: 404 (control), so the surface can answer no and the next 200 is not a catch-all response.
3. As tester-a, with the same session, send GET /orders/102. Order 102 belongs to tester-b. Response: 200 with owner tester-b, items and address (variant). Both accounts are test accounts I created.
4. Read-back: as tester-b, with tester-b's session, send GET /orders/102. Response: 200 with the same items and address.

Requests were sent with the header X-Research: tester-a at well below 60 requests per minute.

## Impact
tester-a can read tester-b's order 102 (owner, items, address) by changing the id in GET /orders/[id]. Only the two test accounts were used.

## Evidence
reports/example-program/example-finding/evidence/order_read_redacted.txt (redacted; each request says which account's session it used)

## Suggested fix
Check that the order's owner equals the session user before returning it.
