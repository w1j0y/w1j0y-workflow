# Template: ledger gate

What: The contract any ledger_gate.py must keep, so it can be regenerated from the viewer's own schema.
Who writes: the repo author.
Who reads: tools/_GENERATE_GATE.md and whoever regenerates tools/ledger_gate.py.
Wired into: tools/_GENERATE_GATE.md, tools/ledger_gate.py, prompts/reference/ledger_schema.md

## Header block
The generated file starts with the four-line box as comments, then a docstring with the subcommands and exit codes.

## Subcommands
- snapshot --target T --phase P: record the ledger rows and finding files now. For phase 01 with no ledger, write an empty snapshot so the first cycle can start.
- check --target T --phase P: compare to the snapshot. Rows new or changed since then must have the required columns for the phase non-blank, a status from the schema, and handoff rows a status. Every finding file new or changed since then needs a Finding Validation row naming it. Delete the snapshot on pass.
- packet --target T --phase P: print only the open rows, capped at the schema's row cap.
- submittable --target T --report-dir D: REPORT.md exists, the ledger holds at least one Finding Validation row with the ready verdict (rows are not matched to the report folder by name, because the report folder and the finding file may use different slugs), and the target's own scope file (targets/T/scope.json, never session state) is read for the ai_use rule: refuse when it is prohibited or restricted, and when it is disclosure_required the report must hold a line starting with AI disclosure:. A missing scope file is a refusal.
- --root [dir] on every subcommand; default is the repo root.

## Contract
1. Read prompts/reference/ledger_schema.md at runtime: parse the fenced json block. Statuses, phases, columns, required fields and the row cap come only from it.
2. Exit 0 pass, 2 usage or missing file, 3 refusal.
3. Refusal text on stderr: "GATE FAIL: phase P for target 'T' -- N row(s) incomplete:" then one "  - " line per row.
4. Pass text on stdout starts with "GATE PASS:".

## Tests
Good and bad fixtures as real files under tools/tests/fixtures/good and fixtures/bad. One test per rule. A meta test that changes the schema and shows the gate follows it. A meta test that flips a good fixture to its bad twin and requires exit 3.

## Wire it in
Name the gate in each phase prompt that calls it. Run the wiring check.
