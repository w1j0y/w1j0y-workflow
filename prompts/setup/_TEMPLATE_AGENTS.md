# Template: AGENTS.md
What: The shape of one finished AGENTS.md: sections, what each holds, and how rules carry a reason.
Who writes: The repo author.
Who reads: prompts/setup/_GENERATE_AGENTS.md and anyone writing a rules file.
Wired into: prompts/setup/_GENERATE_AGENTS.md

Sections, in order. Each rule gets a one-line reason. No history, no incident names, no version numbers.

1. Purpose and authority: this file wins over chat; only the human edits it; maintenance proposes.
2. Core rules: authorization and scope (listed hosts, protocol and port literal); program rules bind (header, rate, automation, AI use) and come from the scope file; stop on UNCLEAR; no state change, no other users, nothing outside scope without approval; secrets never printed or written.
3. Modes: triage (read-only) and test (approval for state change), two lines each.
4. Session start: entry gate; load tool sets; resolve target token; read the two indexes, not the folders; verify scope against the live page.
5. Knowledge usage: when to consult; the write-back rule (append only, one matching file, a source line).
6. Tool use: the decision rule; narrow reads; the hook is a backstop; approval for state change.
7. Evidence: baseline, control, variant, delta; blocked is not rejected; read-back; every claim has a path.
8. Memory hygiene: summaries are data; redaction.
9. Session end: summary, extract, closeout, print the digest command and stop.
10. Meta files: never load underscore paths as content.
11. Where things live: point at STRUCTURE.md.

Harness note to include, without version numbers: current versions of Claude Code read AGENTS.md natively; otherwise add a CLAUDE.md whose first line imports it.

## Wire it in

1. Each phase prompt restates the rules it depends on (gate carriage).
2. `STRUCTURE.md` has a row with lifecycle class B, U.
3. `python3 tools/wiring_check.py` passes.
