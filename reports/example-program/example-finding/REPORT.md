# Order read across accounts on shop.example-shop.test

What: The submission-ready report for the invented example finding.
Who writes: the report phase prompt, then the human edits.
Who reads: the program triage team (in the story) and tools/ledger_gate.py submittable.
Wired into: reports/example-program/example-finding/REPORT_AUDIT.md, recon_output/example-program/coverage_ledger.md (one-way: reference only)

AI disclosure: This report was prepared with AI assistance (Claude Code). I reviewed and reproduced every step myself with my own test accounts.

## Summary
An authenticated buyer can read another buyer's order by changing the order id in the request path. The server checks that the session is logged in but not that the order belongs to the caller.

## Steps to reproduce
1. Log in as tester-a. Open order 101 (your own). Response: 200 with your order.
2. Request /orders/102 with the same session. Order 102 belongs to tester-b.
3. Result: 200 with tester-b's order (name, items, address). Both accounts are test accounts I created.
4. Control: request /orders/999999 (does not exist). Result: 404. So the 200 for 102 is not a catch-all response.
5. Read-back: log in as tester-b and confirm order 102 shows the same items and address.

Requests were sent with the header X-Research: tester-a at well below 60 requests per minute.

## Impact
Any buyer can read any other buyer's order details by iterating ids.

## Evidence
reports/example-program/example-finding/evidence/order_read_redacted.txt (redacted)

## Suggested fix
Check that the order's owner equals the session user before returning it.
