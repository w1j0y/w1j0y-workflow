# Coverage ledger: example-program
## Surfaces
| id | surface | class | status | evidence | next |
|---|---|---|---|---|---|
| s1 | GET /api/items/101 | object-reference | maybe | baseline 200 | validate |

## Phase handoff
| id | from | to | status | note |
|---|---|---|---|---|
| h1 | 03 | FINDING_VALIDATION | OPEN | finding for item 101 |

## Finding Validation
| id | finding_file | verdict | reason |
|---|---|---|---|
| f1 | example-program_finding_item_read.md | VALID_READY_TO_REPORT | read-back confirmed with tester-b |
