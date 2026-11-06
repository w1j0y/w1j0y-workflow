# Tool intake: subtraction first
What: The intake prompt: decide in three stages whether a new tool is allowed in, installing nothing until stage 3 and defaulting to no.
Who writes: The repo author; maintenance proposes changes.
Who reads: The human, through the intake slash command, naming one tool.
Wired into: .claude/commands/intake.md, prompts/README.md, docs/TOOLS_NEEDED.md, AGENTS.md

Input: the name or link of one tool. Rule for the whole run: nothing is installed or edited until stage 3, and the default answer is no. Subtraction first: ask whether the tool is needed at all, or whether an existing tool or a removed step solves the problem.

## Stage 1: audit

Write down, quoting the tool's own repository with links:

1. The problem it solves. It must name a row in a ledger, a gap in the knowledge-gap stream, or a failure in the failure stream. If it names none, stop here with NOT.
2. Overlap with what exists. Read `STRUCTURE.md`, `docs/TOOLS_NEEDED.md` and the tools folder.
3. Scope and safety. What does it send, and to whom (egress)? What does it write? Can it be told the identification header and the rate? Does it send saved page content anywhere?
4. License: read its license file and state the terms in one line.
5. Maintenance: last commit, open issues, release cadence.
6. Cost: money, time, keys, extra install steps.

## Stage 2: decide

Write `docs/decisions/[tool].md` (the folder is kept by `docs/decisions/.gitkeep`) from the decision template (the shape is in `prompts/README.md`): WORTH IT or NOT, one paragraph of reasoning, the evidence links. If NOT, stop. The decision file is the only change.

## Stage 3: implement (only if WORTH IT, and after the human says go)

1. Install a pinned version, locally, without editing shell profiles and without sudo where possible.
2. Add a row to `docs/TOOLS_NEEDED.md`.
3. Wire it into `AGENTS.md` (when to use it), into the phases that call it, and into the gate: host, header and rate through `tools/scope_check.py`.
4. Add a row to `STRUCTURE.md` with a lifecycle class.
5. Add one good and one bad fixture and a test.
6. Run `prompts/maintenance/AUDIT.md` and confirm nothing is left unwired.

## Test of the intake

Run it on an invented tool: a small list-urls utility in a temporary folder with a short README and a license file. The run must produce an audit section, a decision file and, if worth it, the wiring. A second run on an invented tool that claims no network use but sends requests must end in NOT.
