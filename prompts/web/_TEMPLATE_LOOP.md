# Template: the loop prompt
What: The shape of the orchestrator prompt in prompts/web.
Who writes: The repo author.
Who reads: prompts/web/_GENERATE_PHASES.md and anyone adding a phase.
Wired into: prompts/web/_GENERATE_PHASES.md, prompts/web/_TEMPLATE_PHASE.md

The loop does no phase work. It starts subagents, reads one line, runs gates.

~~~text
# [Name]: the orchestrator
[Four-line box]

## The phase files (exact paths)
[A numbered list with the full repo-relative path of every phase file. Never a placeholder.]

## Before the loop
[Entry gate command (a refusal stops the run; a WARN about uncommitted changes does not, because the human's confirm command changes the scope file on purpose); load tool sets; resolve the target token; choose the start phase]

## Practice run
[When every in-scope host ends in .test: send no request, phases work from saved files only, steps that need Burp or Chrome are recorded as blocked, and one line saying so is added to every subagent prompt]

## For each phase P in order
[Snapshot; dispatch one fresh subagent with the seed preamble and five lines; read only the ROUTING line; run the check; repair on fail; validation on a finding]

## Loop
[When to stop]

## Session end
[Summary; extract; closeout; print the digest command; stop]

## What you must not do
[Edit gates; do phase work; read logs]
~~~

## Wire it in

1. Every phase prompt lists the loop in its Wired into line, and the loop lists every phase back.
2. `AGENTS.md` and `prompts/README.md` name the loop.
3. `python3 tools/wiring_check.py` passes.
