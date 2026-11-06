# Template: a maintenance prompt
What: The shape of one finished maintenance prompt such as the audit or the learning pass.
Who writes: The repo author.
Who reads: prompts/maintenance/_GENERATE_MAINTENANCE.md and anyone adding a recurring pass.
Wired into: prompts/maintenance/_GENERATE_MAINTENANCE.md

A maintenance prompt is read by a human-started session and ends at an approval step.

Shape: the box; the rule for the whole run (propose, do not edit); cadence; what it reads; what it produces and where; the deterministic check it runs first (a command); how it asks for approval; how it applies approved items; the test that proves it works (break one thing on purpose, see it named, fix, rerun clean).

## Wire it in

1. A slash command in `.claude/commands` reads the prompt.
2. `prompts/README.md` lists it.
3. `STRUCTURE.md` has a row with a lifecycle class.
4. `python3 tools/wiring_check.py` passes.
