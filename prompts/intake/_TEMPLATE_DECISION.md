# Template: a tool decision record
What: The shape of one decision file in docs/decisions.
Who writes: The repo author.
Who reads: prompts/intake/INTAKE_TOOL.md while it writes a decision.
Wired into: prompts/intake/INTAKE_TOOL.md

~~~text
# Decision: [tool]
What: A yes or no on adding [tool], with the reasons.
Who writes: the intake run, after the human reads it.
Who reads: maintenance and the audit.
Wired into: docs/TOOLS_NEEDED.md

Decision: WORTH IT or NOT
Date: [date]
Problem it solves: [the ledger row, gap or failure it names]
Overlap: [what exists that does the same]
Egress and safety: [what it sends, where, what it writes, header and rate support]
License: [one line]
Maintenance: [last commit, issues, releases]
Cost: [money, time, keys]
Reasoning: [one paragraph]
Evidence: [links into the tool's own repository]
~~~

## Wire it in

If WORTH IT: add the tool to `docs/TOOLS_NEEDED.md`, `AGENTS.md`, the phases and `STRUCTURE.md`, then run the audit. If NOT: nothing else changes.
