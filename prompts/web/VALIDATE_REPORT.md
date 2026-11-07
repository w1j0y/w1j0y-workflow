# Report validation
What: A fresh reader audits a drafted report as a triager would and appends one round to the report audit file until it is ready to submit.
Who writes: The repo author; maintenance proposes changes.
Who reads: The report-audit subagent that the orchestrator starts.
Wired into: prompts/web/WEB_LOOP.md, prompts/reference/routing_and_handoff.md, prompts/reference/evidence_rules.md, prompts/reference/ledger_schema.md (one-way: schema owned by its own file), knowledge/INDEX.md (one-way: generated index), tools/ledger_gate.py (one-way: script)

Mode: review. Read-only except for the audit file. Send no requests.

Context: an authorized program, invented sample data on .test hosts. You audit a report that already exists. No request is sent and no exploit payload is written or run.

## Before Step 1

You are a fresh reader: you did not test or write this. You were given a report folder `reports/[target]/[slug]/`. Obey AGENTS.md section 2.

## Step 1: read

Read `REPORT.md`, the evidence folder it names, the finding file, and `targets/[target]/guidelines.txt`. Run `python3 tools/ledger_gate.py packet --target [target] --phase 03` only if you need the ledger rows.

## Consult

Always open `knowledge/INDEX.md` (never the knowledge folder) and open at most the files whose index line matches the surface in front of you. Before any severity label, open the false-positive file named in the trigger table of `prompts/web/02_5-map-classes.md`. Also read `prompts/reference/ledger_schema.md` (blocks you write: Finding Validation), `prompts/reference/evidence_rules.md` and `prompts/reference/routing_and_handoff.md`. Open `memory/playbook/INDEX.md` and only the matching class file.

## Checks

1. Title and summary say what is wrong, in one sentence each, without hype.
2. Steps to repeat can be followed by a stranger using only the report, with the two test accounts named.
3. Impact is concrete: who can do what to whose data. No severity words that the evidence does not carry.
4. Every claim has an evidence path that exists, and every evidence file is redacted (no token, cookie or credential). Run `python3 tools/secret_scan.py` over the report folder.
5. No out-of-scope class, no duplicate shape from the guidelines, no program rule broken in the steps (rate, header, automation).
6. If the program's AI-use rule is disclosure_required, the report has a line starting with `AI disclosure:`. If AI use is prohibited or restricted, stop with BLOCKED.
7. The verdict row for this finding is VALID_READY_TO_REPORT.

## Output

Append a round to `reports/[target]/[slug]/REPORT_AUDIT.md`: round number, date, a table of problems (line, why it matters, fix), and a decision. Do not edit REPORT.md; the drafting session does.

## ROUTING

`ROUTING: SUBMIT` when there are no problems left. `ROUTING: REVISE` when there are. After SUBMIT the orchestrator runs `python3 tools/ledger_gate.py submittable --target [target] --report-dir reports/[target]/[slug]`.

## Write-back

Nothing is appended to knowledge by this prompt.
