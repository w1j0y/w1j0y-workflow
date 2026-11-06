# Coverage ledger: example-program

What: The one ledger for the example program: surfaces, phase handoffs and finding validation.
Who writes: the phase prompts, one row at a time, checked by tools/ledger_gate.py.
Who reads: tools/ledger_gate.py, tools/ledger_to_inbox.py, the next phase prompt.
Wired into: tools/ledger_gate.py (one-way: reference only), prompts/reference/ledger_schema.md (one-way: reference only)

## Surfaces

| id | surface | class | status | evidence | next |
|---|---|---|---|---|---|
| S-001 | shop.example-shop.test /orders/[id] | object reference | confirmed | reports/example-program/example-finding/evidence/order_read_redacted.txt | report written |
| S-002 | shop.example-shop.test /api/profile | object reference | no-signal | reports/example-program/example-finding/evidence/order_read_redacted.txt | none |
| S-003 | shop.example-shop.test /static/missing-page | spa catch-all | rejected | non-reportable/example-program/spa-catch-all-closed.md | none |
| S-004 | api.example-shop.test | object reference | untested | none yet | enumerate in the next cycle |

## Phase handoff

| id | from | to | status | note |
|---|---|---|---|---|
| H-001 | 01 | 02 | CONSUMED | ranked surfaces S-001 to S-004 |
| H-002 | 02 | 02.5 | CONSUMED | input inventory for S-001 and S-002 |
| H-003 | 03 | 02 | OPEN | S-004 needs characterizing |

## Finding Validation

| id | finding_file | verdict | reason |
|---|---|---|---|
| FV-001 | recon_output/example-program/example-program_finding_order_read.md | VALID_READY_TO_REPORT | tester-a read order 102 owned by tester-b; control and read-back done |
