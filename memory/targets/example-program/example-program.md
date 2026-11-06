# Target file: example-program

What: Curated memory about the example program: what works, what is blocked, who the test accounts are.
Who writes: tools/digest_inbox.sh appends target notes; the human curates.
Who reads: every phase prompt at the start of work on this target.
Wired into: recon_output/example-program/target_notes.md, memory/target-registry.json

## Facts
- Platform: invented example program, hosts under example-shop.test.
- Test accounts: tester-a and tester-b (both buyers). Orders 101 and 102 belong to them.
- Rules: at most 60 requests per minute, header X-Research: tester-a on every request, AI disclosure line in reports.

## What worked
- Object reference check on /orders/[id] (see reports/example-program/example-finding/REPORT.md).

## Dead ends
- /static/missing-page returns 200 for any path (catch-all).
