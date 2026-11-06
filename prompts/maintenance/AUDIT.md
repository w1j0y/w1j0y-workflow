# Audit: the deep wiring check
What: The audit prompt: run the deterministic wiring check, read for what a script cannot check, write proposals, and apply only what the human approves.
Who writes: The repo author; maintenance proposes changes.
Who reads: The human, through the audit slash command, before or after any larger change.
Wired into: .claude/commands/audit.md, prompts/maintenance/MAINTENANCE.md, prompts/README.md, AGENTS.md, tools/wiring_check.py (one-way: script)

Rule for the whole run: propose, do not edit. No file changes until the human approves each proposal in this conversation.

## Step 1: the deterministic check

Run `python3 tools/wiring_check.py --json`. It reports, with file and line: missing paths; a Wired into line that is not true in both directions; files nothing mentions; knowledge files missing from the index or unreachable from a phase or trigger row; phase files not named by exact path in the loop; tools named in a prompt that do not exist, and tools named nowhere; files with no row or class in STRUCTURE.md; references to meta files as content.

Also run `bash tools/tests/run.sh` (the schema-drives-gate test and the hook tests must pass), `python3 tools/secret_scan.py` over the working tree, and a name check for anything that should not be public (names of real programs, hosts, home paths). Meta files (any path part starting with an underscore) are excluded from content checks.

## Step 2: read for what a script cannot check

1. Gate carriage: every rule in `AGENTS.md` section 2 is carried by at least one phase prompt, and no phase contradicts a rule.
2. Each template and its generator agree on the shape and the check command.
3. Each phase names its knowledge consult, its schema blocks and its gate, and the commands it names exist.
4. The trigger table in `prompts/web/02_5-map-classes.md` still points at files that exist and that say what the row claims.

## Step 3: write proposals

Write `docs/audits/[date].md` (the folder is kept by `docs/audits/.gitkeep`): a table with path, line, why it matters, proposed fix. Proposals only. Do not paste secrets or tokens into it. If a finding is a false alarm, say so and say why.

## Step 4: stop for approval

Show the table to the human and stop. The human approves each proposal. Apply only the approved ones, then rerun Step 1. The run ends when the check is clean.

## Test of the audit

Break one wire on purpose (rename a knowledge file a phase names, or delete a Wired into line). The audit must name the exact path. Apply the approved fix and rerun clean.
