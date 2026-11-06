# Coverage ledger: example-program
## Surfaces
| id | surface | class | status | evidence | next |
|---|---|---|---|---|---|
| s1 | GET /api/items/101 | object-reference | candidate | baseline 200, tester-b read tester-a record 101 | validate |
| s2 | GET /api/items/102 | object-reference | no-signal | control and variant identical | none |

## Phase handoff
| id | from | to | status | note |
|---|---|---|---|---|
| h1 | 03 | FINDING_VALIDATION | OPEN | finding for item 101 |

## Finding Validation
| id | finding_file | verdict | reason |
|---|---|---|---|

