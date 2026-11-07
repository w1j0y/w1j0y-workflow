# Playbook: skill file rules
What: The rules for skill files in the playbook: entry shape, budgets, evidence and how entries change.
Who writes: The repo author.
Who reads: Maintenance, tools/playbook_apply.py and the phases that open a class file.
Wired into: memory/README.md, prompts/maintenance/MAINTENANCE.md, tools/playbook_apply.py (one-way: script owned by another part)

A skill file is a short curated list of what to do and avoid in one class of situation, with evidence. Phases read `memory/playbook/INDEX.md` and open only the class file that matches.

## Entry shape

~~~text
### PB-[CLASS]-[NNN] [title]
- Applies when: [the situation]
- Do: [the action]
- Avoid: [the mistake]
- Evidence: [two or three repo paths that exist, separated by semicolons]
- Confidence: low, medium or high
- Last validated: [date]
- Status: provisional, active, contested or retired
~~~

## Budgets

- 1,200 bytes per entry.
- 30 entries per class file.
- 400 KB for the whole playbook.

## Evidence

Every Evidence path must resolve on disk when the entry is applied. An entry whose evidence cannot be found is refused. Evidence is a path to a ledger, finding, report audit, evidence file or non-reportable record, not a quote from memory.

## How entries change

Maintenance writes a delta file in the `_deltas` folder with operations ADD, REFINE and RETIRE. After the human approves it, `python3 tools/playbook_apply.py --dry-run [delta file]` shows what would happen; the real run applies it, rebuilds the index and advances the boundary file. Nobody edits skill files by hand.

The boundary file sits in this folder and is named _boundary.json (it is a runtime file, so the underscore keeps it out of content listings). It lists the delta files already applied, so the same delta cannot be applied twice. Delta files are named by date, so when the maintenance prompt reads "the streams after the boundary" it means the stream lines dated after the newest applied delta; with nothing applied yet, it means all of them. A false positive found later becomes an Avoid line with its evidence path; a retired entry stays, marked retired, until maintenance deletes it.
