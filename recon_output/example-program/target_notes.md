# Target notes: example-program

What: Free-form notes about the example program, appended by phases and read at the start of each phase.
Who writes: the phase prompts (append only) and the human.
Who reads: every phase prompt; tools/ledger_to_inbox.py extracts new lines from it.
Wired into: recon_output/example-program/coverage_ledger.md (one-way: reference only), memory/targets/example-program/example-program.md

## Notes
- 2026-01-01 shop.example-shop.test is a single-page app; unknown paths return 200 with the app shell (catch-all).
- 2026-01-01 Test accounts: tester-a (buyer), tester-b (buyer). Order ids 101 belongs to tester-a, 102 to tester-b.
- 2026-01-01 The program asks for the X-Research header on every request and at most 60 requests per minute.
