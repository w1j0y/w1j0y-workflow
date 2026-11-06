# Playbook index

What: One line per skill file and entry, so a phase can open only the matching class file.
Who writes: tools/playbook_apply.py (rebuilt after every apply; do not edit).
Who reads: the phase prompts, before they open any memory/playbook class file.
Wired into: tools/playbook_apply.py, memory/playbook/object_reference.md, memory/playbook/spa_catch_all.md

## memory/playbook/object_reference.md (2 entries)
- PB-OBJECT_REFERENCE-001 [active] Change the id, then check the owner field. Applies when: a path or body carries a numeric id for an object the logged-in user owns.
- PB-OBJECT_REFERENCE-002 [provisional] Read back from the owner account. Applies when: a cross-account read or write looks successful.

## memory/playbook/spa_catch_all.md (1 entries)
- PB-SPA_CATCH_ALL-001 [active] Send a random-path control first. Applies when: unknown or guessed paths on a single-page app return 200.
