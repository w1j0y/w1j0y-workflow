# Phase 01: triage
What: Rank the surfaces found by recon, create the coverage ledger and the target notes, and hand off to phase 02.
Who writes: The repo author; maintenance proposes changes.
Who reads: The phase subagent that the orchestrator starts, and the orchestrator for its gate.
Wired into: prompts/web/WEB_LOOP.md, prompts/reference/routing_and_handoff.md, prompts/reference/evidence_rules.md, prompts/reference/ledger_schema.md (one-way: schema owned by its own file), knowledge/INDEX.md (one-way: generated index), tools/ledger_gate.py (one-way: script)

Mode: triage. Read-only. GET, HEAD and OPTIONS requests only, and no form submission.

## Before Step 1

1. You were started by `prompts/web/WEB_LOOP.md` with the seed preamble and five parameter lines. Obey AGENTS.md section 2.
2. The entry gate has already passed. If a tool you need (Burp, Chrome) is not loaded, load it with the tool search step; treat it as unavailable only if a loaded call fails.
3. Scope: the active scope file is the only list of hosts. Write a scope decision line (host, protocol and port, covering rule quoted, IN or OUT) before the first request to any surface.

## Step 1: your bounded state

Run `python3 tools/ledger_gate.py packet --target [target] --phase 01`. It prints the open rows for this phase. Work from those rows and from `recon_output/[target]/target_notes.md`.

## Consult

Always open `knowledge/INDEX.md` (never the knowledge folder) and open at most the files whose index line matches the surface in front of you. Before any severity label, open the false-positive file named in the trigger table of `prompts/web/02_5-map-classes.md`. Also read `prompts/reference/ledger_schema.md` (blocks you write: Surfaces, Phase handoff), `prompts/reference/evidence_rules.md` and `prompts/reference/routing_and_handoff.md`. Open `memory/playbook/INDEX.md` and only the matching class file.

## Steps

1. Read `targets/[target]/scope.json`, including the rules block. Note the header, the rate and the automation and AI-use rules in the target notes.
2. Read the newest run folder under `recon_output/[target]/` (subdomains, probe results, archive URLs). Do not rerun recon.
3. Keep only hosts the scope file lists. Anything else is OUT: write one line saying so and move on.
4. If the ledger does not exist, create it with the three tables from the schema (Surfaces, Phase handoff, Finding Validation). If a target notes file does not exist, create it with a first line naming the target and date.
5. Check whether the target has a notes file in `memory/targets/[target]/`. If it does not, create it from the example shape and register nothing else.
6. Rank surfaces by how much a flaw would matter and how little is known: logins, account objects with ids, file or export features, APIs. One Surfaces row per surface: id, surface, class (your best guess), status untested, evidence (a path to the recon line), next.
7. Check the duplicate list: read earlier report folders for this target, and the program's known issues in the guidelines file. Mark a surface skip with a reason if it is a known duplicate.
8. Write one Phase handoff row: from 01, to 02, status OPEN, note naming the surface ids.

## What this phase writes

The ledger (Surfaces rows, one Phase handoff row), the target notes (append only), the memory target file if missing. No inbox summary. No requests are sent beyond reading files.

## The gate it must pass

`python3 tools/ledger_gate.py check --target [target] --phase 01`. Rows you changed must have the columns the schema requires for phase 01, and a status from the schema vocabulary. If a field truly does not apply, write `N/A - [reason]`.

## Refusals

Stop and use the BLOCKED line if: the scope file is missing or its rules are unconfirmed, a host is not listed, a step would change state without approval, or a hook denies a call and you cannot change the call to fit the scope. Do not route around a hook.

## ROUTING

`ROUTING: NEXT_PHASE=02` when at least one surface is untested and in scope. `ROUTING: STOP` when nothing in scope remains.

## Write-back

If a lookup came up short, append one cited fact to the single matching knowledge file (one section, four-part form, one source line, same session), then run `python3 tools/knowledge_index.py`. Do not create knowledge files during a run. Details: AGENTS.md section 5.
