# Finding: tester-b can read tester-a item 101
What: Example finding used only by the gate tests.
Who writes: the test fixtures.
Who reads: tools/tests/test_ledger_gate.py
Wired into: none: fixture

Request GET /api/items/101 as tester-b returns the record owned by tester-a. Control: item 102 returns 403.
