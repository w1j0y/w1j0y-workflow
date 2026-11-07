# Phase 02: characterize
What: Walk the application as a user, record how each surface works and what inputs it takes, and hand off to the mapping phase.
Who writes: The repo author; maintenance proposes changes.
Who reads: The phase subagent that the orchestrator starts, and the orchestrator for its gate.
Wired into: prompts/web/WEB_LOOP.md, prompts/reference/routing_and_handoff.md, prompts/reference/evidence_rules.md, prompts/reference/ledger_schema.md (one-way: schema owned by its own file), knowledge/INDEX.md (one-way: generated index), tools/ledger_gate.py (one-way: script)

Mode: triage extended with the browser. Observation only: no submit, purchase, upload, settings change, consent or message send.

## Before Step 1

1. You were started by `prompts/web/WEB_LOOP.md` with the seed preamble and five parameter lines. Obey AGENTS.md section 2.
2. The entry gate has already passed. If a tool you need (Burp, Chrome) is not loaded, load it with the tool search step; treat it as unavailable only if a loaded call fails.
3. Scope: the active scope file is the only list of hosts. Write a scope decision line (host, protocol and port, covering rule quoted, IN or OUT) before the first request to any surface.

## Step 1: your bounded state

Run `python3 tools/ledger_gate.py packet --target [target] --phase 02`. It prints the open rows for this phase. Work from those rows and from `recon_output/[target]/target_notes.md`.

## Consult

Always open `knowledge/INDEX.md` (never the knowledge folder) and open at most the files whose index line matches the surface in front of you. Before any severity label, open the false-positive file named in the trigger table of `prompts/web/02_5-map-classes.md`. Also read `prompts/reference/ledger_schema.md` (blocks you write: Surfaces, Phase handoff), `prompts/reference/evidence_rules.md` and `prompts/reference/routing_and_handoff.md`. Open `memory/playbook/INDEX.md` and only the matching class file.

## Steps

1. Load the Burp and Chrome tool sets if not loaded. Look at the human's open tabs first; use a tab that is already on an in-scope host, or open a new one.
2. For each open Surfaces row, walk the workflow in the browser as tester-a: what the page does, what requests it makes, which fields take input. Prefer text-reading tools; take a screenshot only to confirm and save it under the target's evidence folder.
3. Passive Burp check: read the recorded proxy history for the host with a Host header regex (not a URL pattern) and a small count, and compare an observed request with what the browser showed. "Reached end of items" is a result about your query.
4. Build the input inventory per surface: path parts, query fields, body fields, headers, cookies, ids and what they refer to. Record in the target notes under a business logic heading (once per target).
5. Note which roles exist and which objects belong to which account (tester-a, tester-b). Do not log in as anyone else.
6. Update each row: class, status (untested if only observed, no-signal if nothing to test, blocked if stopped), evidence path, next.
7. Write one Phase handoff row: from 02, to 02.5, status OPEN, note naming surfaces with an input inventory. Set the consumed 01 to 02 row to CONSUMED.

## What this phase writes

The ledger (Surfaces rows updated, handoff rows), target notes (append only), evidence files (redacted screenshots and text). No state-changing request.

## The gate it must pass

`python3 tools/ledger_gate.py check --target [target] --phase 02`. Rows you changed must have the columns the schema requires for phase 02, and a status from the schema vocabulary. If a field truly does not apply, write `N/A - [reason]`.

The orchestrator runs this check after you finish, and a passing check deletes the snapshot, so do not run `check` yourself; the orchestrator's run would then have nothing to compare with. Before you end, reread every row you changed against the required columns in the schema.

## Refusals

Stop and use the BLOCKED line if: the scope file is missing or its rules are unconfirmed, a host is not listed, a step would change state without approval, or a hook denies a call and you cannot change the call to fit the scope. Do not route around a hook.

Browser clicks that navigate inside a page are not visible to the hook. Stay on the workflow you recorded and re-check the address bar host after any redirect; if it is out of scope, stop and say so.

## ROUTING

`ROUTING: NEXT_PHASE=02.5` when at least one surface has an inventory. `ROUTING: LOOP_BACK` when a handoff row sends you back to 01. `ROUTING: BLOCKED` when the app cannot be reached in scope.

## Write-back

If a lookup came up short, append one cited fact to the single matching knowledge file (one section, four-part form, one source line, same session), then run `python3 tools/knowledge_index.py`. Do not create knowledge files during a run. Details: AGENTS.md section 5.
