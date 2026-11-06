What: Prompt that regenerates tools/ledger_gate.py from the viewer's own schema using the template.
Who writes: The repo author.
Who reads: You, pasting it into Claude Code.
Wired into: tools/_TEMPLATE_GATE.md
Read tools/_TEMPLATE_GATE.md and my schema prompts/reference/ledger_schema.md.
Write tools/ledger_gate.py so that every rule in the schema's json block is enforced and nothing is hard-coded.
Write good and bad fixtures (real files) and one test per rule in tools/tests/.
Run: tools/tests/run.sh
Then break one rule on purpose, show that a test fails, and undo it.
Do not change the schema file.
