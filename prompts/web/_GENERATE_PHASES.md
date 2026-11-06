What: Prompt that creates the phase prompts and the loop file from the two templates.
Who writes: The repo author.
Who reads: You, pasting it into Claude Code.
Wired into: prompts/web/_TEMPLATE_PHASE.md, prompts/web/_TEMPLATE_LOOP.md
Templates: prompts/web/_TEMPLATE_PHASE.md and prompts/web/_TEMPLATE_LOOP.md, with prompts/reference/ledger_schema.md. Input: my phases, [list with one line each]. Output: prompts/web/[phase].md for each, and prompts/web/WEB_LOOP.md.
Prompt: Read the two templates and the schema. Create one file per phase and the loop file. Each phase must name its knowledge consult, its schema blocks and its gate.
The loop must name every phase file by its exact path. Do not invent a gate command that is not in the schema or tools.
Check: python3 tools/wiring_check.py. Fix every finding it prints.
