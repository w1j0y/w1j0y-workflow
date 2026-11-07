# Phase 02.5: map classes
What: Map the evidence from phase 02 to vulnerability classes and knowledge files, and write the test plan as ledger rows.
Who writes: The repo author; maintenance proposes changes.
Who reads: The phase subagent that the orchestrator starts, tools/wiring_check.py (the trigger table) and the orchestrator for its gate.
Wired into: prompts/web/WEB_LOOP.md, prompts/reference/routing_and_handoff.md, prompts/reference/evidence_rules.md, prompts/reference/ledger_schema.md (one-way: schema owned by its own file), knowledge/INDEX.md (one-way: generated index), tools/ledger_gate.py (one-way: script)

Mode: planning. No exploitation, no requests that change state. Writes planning rows only.

## Before Step 1

1. You were started by `prompts/web/WEB_LOOP.md` with the seed preamble and five parameter lines. Obey AGENTS.md section 2.
2. Scope: write a scope decision line for any surface before you plan a request to it.

## Step 1: your bounded state

Run `python3 tools/ledger_gate.py packet --target [target] --phase 02.5`.

## Consult

Always open `knowledge/INDEX.md` (never the knowledge folder) and open at most the files whose index line matches the surface in front of you. Before any severity label, open the false-positive file named in the trigger table of `prompts/web/02_5-map-classes.md`. Also read `prompts/reference/ledger_schema.md` (blocks you write: Surfaces, Phase handoff), `prompts/reference/evidence_rules.md` and `prompts/reference/routing_and_handoff.md`. Open `memory/playbook/INDEX.md` and only the matching class file.

## Trigger table

Match the evidence you have against this table. Open the knowledge file on the same row, and no others unless the index line for another file also matches. The wiring check reads this table; keep every path exact; a file may appear on more than one row.

| Evidence | Knowledge file |
|---|---|
| A path, query or body field holds an id or name that refers to an object (order 101, user 7) | `knowledge/object_reference_checks.md` |
| Two responses must be compared, or a change must be shown as a difference from normal | `knowledge/baseline_and_differential.md` |
| Many different paths return 200 with the same page or size | `knowledge/spa_catch_all_200.md` |
| A candidate is about to receive a severity label or a status of confirmed | `knowledge/spa_catch_all_200.md` |

## Steps

1. For each surface with an input inventory, name the class it belongs to and the evidence that suggests it.
2. Open the knowledge file the trigger table names. If no row matches, use `knowledge/INDEX.md` to find a file; if none fits, record a gap in the target notes and leave the write-back for maintenance.
3. For each hypothesis write one ledger row in the Surfaces table: class, status untested, evidence (the path to the observation), next (the first request: baseline and control, then the variant).
4. Order by impact and by how cheap the control is. Mark a whole group of identical surfaces as one grouped skip row when they share a template and one has been tested.
5. Write a Phase handoff row: from 02.5, to 03, status OPEN, note naming the row ids. Set the consumed 02 to 02.5 row to CONSUMED.

## What this phase writes

The ledger (Surfaces planning rows, one handoff row) and target notes (append only). No evidence files, no requests.

## The gate it must pass

`python3 tools/ledger_gate.py check --target [target] --phase 02.5`. Required columns for 02.5 are in the schema. If a field does not apply, write `N/A - [reason]`.

## Refusals

Stop with BLOCKED if the scope file is missing or its rules are unconfirmed. Do not plan a request to a host that is not listed.

## ROUTING

`ROUTING: NEXT_PHASE=03` when at least one planned row is ready. `ROUTING: LOOP_BACK` when the plan needs more characterizing. `ROUTING: BLOCKED` when a condition outside the ledger stops the plan. `ROUTING: STOP` when no planned row is worth testing.

## Write-back

Append one cited fact to the single matching knowledge file if a lookup came up short (one section, four-part form, one source line). Then run `python3 tools/knowledge_index.py`. Do not create knowledge files during a run.
