# Phase 03: test
What: Test one planned hypothesis at a time with baseline, control, variant and read-back, and record the outcome with evidence.
Who writes: The repo author; maintenance proposes changes.
Who reads: The phase subagent that the orchestrator starts, and the orchestrator for its gate.
Wired into: prompts/web/WEB_LOOP.md, prompts/reference/routing_and_handoff.md, prompts/reference/evidence_rules.md, prompts/reference/ledger_schema.md (one-way: schema owned by its own file), knowledge/INDEX.md (one-way: generated index), tools/ledger_gate.py (one-way: script)

Mode: test. A request that changes state needs explicit human approval in this session first. Cross-user checks use only tester-a and tester-b.

## Before Step 1

1. You were started by `prompts/web/WEB_LOOP.md` with the seed preamble and five parameter lines. Obey AGENTS.md section 2.
2. The entry gate has already passed. If a tool you need (Burp, Chrome) is not loaded, load it with the tool search step; treat it as unavailable only if a loaded call fails.
3. Scope: the active scope file is the only list of hosts. Write a scope decision line (host, protocol and port, covering rule quoted, IN or OUT) before the first request to any surface.

## Step 1: your bounded state

Run `python3 tools/ledger_gate.py packet --target [target] --phase 03`. It prints the open rows for this phase. Work from those rows and from `recon_output/[target]/target_notes.md`.

## Consult

Always open `knowledge/INDEX.md` (never the knowledge folder) and open at most the files whose index line matches the surface in front of you. Before any severity label, open the false-positive file named in the trigger table of `prompts/web/02_5-map-classes.md`. Also read `prompts/reference/ledger_schema.md` (blocks you write: Surfaces, Phase handoff, Finding Validation (you write none; a confirmed finding file makes the gate ask for a validation row)), `prompts/reference/evidence_rules.md` and `prompts/reference/routing_and_handoff.md`. Open `memory/playbook/INDEX.md` and only the matching class file.

## Steps

1. Take one planned row. Re-check the scope decision line for its host.
2. Baseline: save the normal request and response. Control: a request that must work, with your own object. Variant: change exactly one thing. Delta: write the difference.
3. Send requests with Burp (`send_http1_request` or `send_http2_request`) or drive the browser. Every request carries the identification header and stays under the rate limit; the hook will deny a call that does not.
4. For a write: send a separate read request afterwards (read-back) and compare with the baseline read. A 200 on the write alone is not proof.
5. Before you set a status, open the false-positive file from the trigger table. Check the delta is not a catch-all page, a cached response or a shared object.
6. Apply the confirmation bar in `prompts/reference/evidence_rules.md`. Statuses: confirmed (bar met), rejected (the application answered and the protection held), blocked (stopped before an answer), needs-depth (a clear signal needs more work), candidate (odd, not proven), no-signal.
7. Save evidence under the target's evidence folder, run `python3 tools/redact.py` over any text before saving, and put the path in the evidence column.
8. If the status is confirmed, create `recon_output/[target]/[target]_finding_[slug].md` with: the class, the steps to repeat, the baseline, control, variant and delta, the impact in one sentence with the two accounts named, and the evidence paths. Check duplicates first.
9. Before leaving a confirmed row: write the anti-pattern check (is this the known false-positive shape?), the complexity (how many steps) and the impact (who can do what to whose data).
10. Set the consumed 02.5 to 03 handoff row to CONSUMED. Write an OPEN row (to 02) for any surface that needs more characterizing.

## What this phase writes

The ledger (Surfaces rows updated, handoff rows), finding files (only for confirmed rows), evidence files (redacted), target notes (append only).

## The gate it must pass

`python3 tools/ledger_gate.py check --target [target] --phase 03`. Rows you changed must have the columns the schema requires for phase 03, and a status from the schema vocabulary. If a field truly does not apply, write `N/A - [reason]`.

The orchestrator runs this check after you finish, and a passing check deletes the snapshot, so do not run `check` yourself; the orchestrator's run would then have nothing to compare with. Before you end, reread every row you changed against the required columns in the schema.

## Refusals

Stop and use the BLOCKED line if: the scope file is missing or its rules are unconfirmed, a host is not listed, a step would change state without approval, or a hook denies a call and you cannot change the call to fit the scope. Do not route around a hook.

Intercept toggles, repeater and intruder handoff, and any setting change in Burp are staged by the human, not by you. Mutating browser actions and cross-user steps need approval first.

## ROUTING

`ROUTING: STOP` when no planned row remains. `ROUTING: LOOP_BACK` when a handoff row names an earlier phase. `ROUTING: BLOCKED` when scope, a rule or a tool stops the work.

## Write-back

If a lookup came up short, append one cited fact to the single matching knowledge file (one section, four-part form, one source line, same session), then run `python3 tools/knowledge_index.py`. Do not create knowledge files during a run. Details: AGENTS.md section 5.
