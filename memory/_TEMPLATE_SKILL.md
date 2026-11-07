# Template: a skill file entry
What: The shape of one skill file and of the delta entries that add to it.
Who writes: The repo author.
Who reads: memory/_GENERATE_SKILL.md and maintenance.
Wired into: memory/_GENERATE_SKILL.md

A class file starts with the four-line box, then a title, then entries. A delta file adds entries under a heading naming the class file.

~~~text
# Playbook: [class]
What: [curated entries for the class]
Who writes: tools/playbook_apply.py, from a delta the human approved.
Who reads: the phase prompts, after they find this class in memory/playbook/INDEX.md.
Wired into: memory/playbook/INDEX.md, tools/playbook_apply.py

### PB-[CLASS]-[NNN] [title]
- Applies when: [situation]
- Do: [action]
- Avoid: [mistake]
- Evidence: [path that exists]; [path that exists]
- Confidence: [low, medium or high]
- Last validated: [date]
- Status: [provisional, active, contested or retired]
~~~

Delta file shape: a heading `## ADD [class file stem]` with entries (the stem is lowercase letters, digits and underscores, with no .md, for example object_reference); `## REFINE PB-[CLASS]-[NNN]` with the changed fields as `- Field: value` lines; `## RETIRE PB-[CLASS]-[NNN]` with a `- Reason: [why]` line. The apply tool refuses a stem that ends in .md and a RETIRE with no Reason line.

## Wire it in

1. The apply tool rebuilds `memory/playbook/INDEX.md`.
2. `STRUCTURE.md` has a row with a lifecycle class for each class file.
3. `python3 tools/wiring_check.py` passes.
