# Web loop: the orchestrator
What: The orchestrator prompt: runs phases 01, 02, 02.5 and 03 in fresh subagents, each behind a gate, then validation, summary and closeout.
Who writes: The repo author; maintenance proposes changes.
Who reads: The human pastes the activation line; the orchestrating Claude Code session follows it.
Wired into: AGENTS.md, prompts/README.md, prompts/web/01-triage.md, prompts/web/02-characterize.md, prompts/web/02_5-map-classes.md, prompts/web/03-test.md, prompts/web/FINDING_VALIDATION.md, prompts/web/VALIDATE_REPORT.md, prompts/reference/routing_and_handoff.md, prompts/reference/evidence_rules.md, prompts/reference/ledger_schema.md (one-way: schema owned by its own file), tools/ledger_gate.py (one-way: script), tools/session_entry_gate.py (one-way: script), tools/closeout.sh (one-way: script)

Activation line the human pastes: Read and follow prompts/web/WEB_LOOP.md exactly. Target: [target]. Run the 01, 02, 02.5, 03 sequence.

You are the orchestrator. You do no phase work. You start subagents, read one line from each, and run scripts. You do not read their logs.

## The phase files (exact paths)

1. `prompts/web/01-triage.md`: rank surfaces, create the ledger.
2. `prompts/web/02-characterize.md`: walk the app, inventory inputs.
3. `prompts/web/02_5-map-classes.md`: map evidence to classes, plan tests.
4. `prompts/web/03-test.md`: baseline, control, variant, read-back.
5. `prompts/web/FINDING_VALIDATION.md`: a fresh reader decides a verdict.
6. `prompts/web/VALIDATE_REPORT.md`: a fresh reader audits a drafted report.

Shared rules: `prompts/reference/routing_and_handoff.md`, `prompts/reference/evidence_rules.md`, `prompts/reference/ledger_schema.md`.

## Before the loop

1. Run `python3 tools/session_entry_gate.py start --target [target]`. If it refuses, print its message and stop; the human fixes it.
2. Load the Burp and Chrome tool sets with the tool search step now, so subagents inherit a session where they exist. Setup is in `docs/TOOL_WIRING.md`.
3. Resolve the target token once: it must match the folder name under `targets/`. Pass the same token to every subagent.
4. Decide where to start: if `recon_output/[target]/coverage_ledger.md` has an OPEN handoff row, start at the lowest phase it names. If a ledger exists with none open, start at 02. If no ledger exists, start at 01.

## For each phase P in order

1. Snapshot: `python3 tools/ledger_gate.py snapshot --target [target] --phase P`. For phase 01 with no ledger this writes an empty snapshot, which is how the first run gets past the missing ledger.
2. Dispatch one fresh subagent. Its prompt is the seed preamble and five parameter lines from `prompts/reference/routing_and_handoff.md`, then: Read and follow [phase file] exactly. Do not use an isolated copy of the repo: the phase writes the real files.
3. Read only the last line of its final report, which starts with ROUTING:.
4. Gate: `python3 tools/ledger_gate.py check --target [target] --phase P`. Exit 0 advances. Exit 3 prints rows: dispatch a repair subagent for those rows only, then run check again. Never advance on a fail. After two failed repairs for the same row, stop and tell the human.
5. If the check names a finding file with no Finding Validation row, dispatch a subagent with `prompts/web/FINDING_VALIDATION.md` for that file, then run check again.
6. Follow the ROUTING value as the table in `prompts/reference/routing_and_handoff.md` says. If the gate and the routing line disagree, the gate wins.

## Loop

Repeat the phases until the ledger shows no actionable work: no row with status untested or needs-depth in scope, and no OPEN handoff row. A LOOP_BACK returns to the phase the handoff row names. A BLOCKED stops and reports to the human.

## Findings and reports

When a finding has a VALID_READY_TO_REPORT verdict, tell the human a report is owed. A drafting session writes it into the report folder; then dispatch a fresh subagent with `prompts/web/VALIDATE_REPORT.md` until it ends with ROUTING: SUBMIT. Then run `python3 tools/ledger_gate.py submittable --target [target] --report-dir reports/[target]/[slug]`. Exit 0 means the human may submit, in a browser, outside this repo. Exit 3 prints the blockers.

## Session end

1. Write the cycle summary into the inbox folder (the inbox folder): date, target, phases run, rows changed, findings and verdicts, blocked items, next steps. No secrets.
2. Run `python3 tools/ledger_to_inbox.py --target [target]`.
3. Run `bash tools/closeout.sh --target [target]`. It refuses on a secret hit; do not work around it.
4. Print `bash tools/digest_inbox.sh` for the human, and stop. Do not run the digest.

## What you must not do

Do not edit a gate, a schema or a hook. Do not do a phase yourself. Do not read logs to decide routing. Do not start a live phase if the entry gate refused.
