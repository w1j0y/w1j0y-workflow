# Finding validation
What: A fresh reader decides whether one finding is real, using only the finding file and its evidence, and writes one verdict row.
Who writes: The repo author; maintenance proposes changes.
Who reads: The phase subagent that the orchestrator starts, and the orchestrator for its gate.
Wired into: prompts/web/WEB_LOOP.md, prompts/reference/routing_and_handoff.md, prompts/reference/evidence_rules.md, prompts/reference/ledger_schema.md (one-way: schema owned by its own file), knowledge/INDEX.md (one-way: generated index), tools/ledger_gate.py (one-way: script)

Mode: review. Read-only except for one ledger row. Send no requests.

## Before Step 1

1. You were started by `prompts/web/WEB_LOOP.md` with the seed preamble and five parameter lines. Obey AGENTS.md section 2.
2. The entry gate has already passed. If a tool you need (Burp, Chrome) is not loaded, load it with the tool search step; treat it as unavailable only if a loaded call fails.
3. Scope: the active scope file is the only list of hosts. Write a scope decision line (host, protocol and port, covering rule quoted, IN or OUT) before the first request to any surface.

## Step 1: your bounded state

Run `python3 tools/ledger_gate.py packet --target [target] --phase 03`. It prints the open rows for this phase. Work from those rows and from `recon_output/[target]/target_notes.md`.

## Consult

Always open `knowledge/INDEX.md` (never the knowledge folder) and open at most the files whose index line matches the surface in front of you. Before any severity label, open the false-positive file named in the trigger table of `prompts/web/02_5-map-classes.md`. Also read `prompts/reference/ledger_schema.md` (blocks you write: Finding Validation), `prompts/reference/evidence_rules.md` and `prompts/reference/routing_and_handoff.md`. Open `memory/playbook/INDEX.md` and only the matching class file.

## Steps

1. You were given one finding file path. Read it, then read only the evidence files it names and the scope and guideline files. Do not read the testing session or the target notes.
2. Check each claim has a path that exists and that the evidence shows it. A claim with no path is unsupported.
3. Check the control worked, the variant produced a delta, and for a write there is a read-back.
4. Check the impact sentence: who can do what to whose data. Check the scope: the host is listed and no out-of-scope vulnerability class applies. Check the guidelines for a known duplicate shape.
5. Open the false-positive file from the trigger table in `prompts/web/02_5-map-classes.md` and check the finding is not explained by it.
6. Write the verdict: VALID_READY_TO_REPORT, VALID_NEEDS_MORE_WORK or NOT_VALID, with a reason of one or two sentences naming what is missing, if anything.
7. Add one row to the Finding Validation table: id, finding_file (the repo-relative path), verdict, reason.

## What this phase writes

One row in the Finding Validation table of the ledger. Nothing else.

## The gate it must pass

`python3 tools/ledger_gate.py check --target [target] --phase 03`. Rows you changed must have the columns the schema requires for phase 03, and a status from the schema vocabulary. If a field truly does not apply, write `N/A - [reason]`.

The orchestrator runs this check after you finish, and a passing check deletes the snapshot, so do not run `check` yourself; the orchestrator's run would then have nothing to compare with. Before you end, reread every row you changed against the required columns in the schema.

## Refusals

Stop and use the BLOCKED line if: the scope file is missing or its rules are unconfirmed, a host is not listed, a step would change state without approval, or a hook denies a call and you cannot change the call to fit the scope. Do not route around a hook.

The loop does not draft the report. A READY verdict means a report is owed to the human.

## ROUTING

`ROUTING: VALIDATED` once the row is written. `ROUTING: BLOCKED` if the finding file or its evidence cannot be read.

## Write-back

If a lookup came up short, append one cited fact to the single matching knowledge file (one section, four-part form, one source line, same session), then run `python3 tools/knowledge_index.py`. Do not create knowledge files during a run. Details: AGENTS.md section 5.
