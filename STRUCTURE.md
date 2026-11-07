# Structure: the map
What: The map of every file in the repo with its part of the house, writer, reader and lifecycle class, plus the pipeline and the meta file convention.
Who writes: The author; kept in step with the disk by tools/wiring_check.py.
Who reads: You, to find any file and to see how files point at each other.
Wired into: README.md, GETTING_STARTED.md, GLOSSARY.md, AGENTS.md

The map of the house. Columns: path, part of the house, written by, read by, lifecycle class (B, C or U), episode.

| path | part of the house | written by | read by | lifecycle class | episode |
|---|---|---|---|---|---|
| `.gitignore` | settings | author | git | B | 0 |
| `.mcp.json.example` | tool wiring | author | you copy it to the local .mcp.json | B | 8 |
| `AGENTS.md` | rules | author; maintenance proposes | every session and subagent | B,U | 2 |
| `ETHICS.md` | front door | author | you, first | B | 0 |
| `GETTING_STARTED.md` | front door | author | you, first | B | 0 |
| `GLOSSARY.md` | front door | author | you, whenever a word is new | B,U | 0 |
| `LICENSE` | front door | author | you, first | B | 0 |
| `README.md` | front door | author | you, first | B | 0 |
| `STRUCTURE.md` | front door | author | you, first | B | 0 |
| `.claude/settings.json` | tool wiring | author | Claude Code (hook registration and deny rules) | B | 8 |
| `.claude/commands/audit.md` | commands | author | Claude Code slash commands | B | 11 |
| `.claude/commands/intake.md` | commands | author | Claude Code slash commands | B | 16 |
| `.claude/commands/maintenance.md` | commands | author | Claude Code slash commands | B | 15 |
| `docs/TOOLS_NEEDED.md` | docs | author | you | B | 10 |
| `docs/TOOL_WIRING.md` | docs | author | you | B | 8 |
| `docs/audits/.gitkeep` | docs | audit run | you | C | 11 |
| `docs/decisions/.gitkeep` | docs | intake run | maintenance, audit | C | 16 |
| `knowledge/INDEX.md` | knowledge | tools/knowledge_index.py | every phase, first | C,U | 3 |
| `knowledge/_GENERATE_KNOWLEDGE.md` | knowledge (meta) | author | you, pasting the generator | B | 3 |
| `knowledge/_TEMPLATE_KNOWLEDGE.md` | knowledge (meta) | author | you, pasting the generator | B | 3 |
| `knowledge/baseline_and_differential.md` | knowledge | author; phases append one cited fact | phases, by index line or trigger row | B,U | 3 |
| `knowledge/object_reference_checks.md` | knowledge | author; phases append one cited fact | phases, by index line or trigger row | B,U | 3 |
| `knowledge/spa_catch_all_200.md` | knowledge | author; phases append one cited fact | phases, by index line or trigger row | B,U | 3 |
| `memory/README.md` | memory | author | you and maintenance | B | 14 |
| `memory/_GENERATE_SKILL.md` | memory (meta) | author | you, pasting the generator | B | 14 |
| `memory/_TEMPLATE_SKILL.md` | memory (meta) | author | you, pasting the generator | B | 14 |
| `memory/target-registry.json` | memory | phases and the human | phases, at session start | C,U | 14 |
| `memory/_inbox/.gitkeep` | memory (runtime) | orchestrator and tools/ledger_to_inbox.py | tools/digest_inbox.sh | C | 14 |
| `memory/_processed/.gitkeep` | memory (runtime) | tools/digest_inbox.sh | maintenance | C | 14 |
| `memory/playbook/INDEX.md` | memory | tools/playbook_apply.py | phases, by class | C,U | 15 |
| `memory/playbook/README.md` | memory | author | maintenance, tools/playbook_apply.py | B | 15 |
| `memory/playbook/_boundary.json` | memory (runtime) | tools/playbook_apply.py | tools/playbook_apply.py, maintenance | C,U | 15 |
| `memory/playbook/object_reference.md` | memory | tools/playbook_apply.py | phases, by class | C,U | 15 |
| `memory/playbook/spa_catch_all.md` | memory | tools/playbook_apply.py | phases, by class | C,U | 15 |
| `memory/playbook/_deltas/.gitkeep` | memory (runtime) | maintenance | tools/playbook_apply.py | C | 15 |
| `memory/streams/decision_rules.md` | memory | tools/digest_inbox.sh | maintenance | C,U | 14 |
| `memory/streams/failures.md` | memory | tools/digest_inbox.sh | maintenance | C,U | 14 |
| `memory/streams/knowledge_gaps.md` | memory | tools/digest_inbox.sh | maintenance | C,U | 14 |
| `memory/streams/learnings.md` | memory | tools/digest_inbox.sh | maintenance | C,U | 14 |
| `memory/targets/example-program/example-program.md` | memory | phases and the human | phases, at session start | C,U | 14 |
| `non-reportable/README.md` | example data | you, after the program answers | maintenance | C | 13 |
| `non-reportable/example-program/spa-catch-all-closed.md` | example data | you, after the program answers | maintenance | C | 13 |
| `prompts/README.md` | prompts | author | you | B,U | 4 |
| `prompts/organize_scope.md` | prompts | author | scripts/organize_scope_claude.sh | B | 9 |
| `prompts/intake/INTAKE_TOOL.md` | prompts | author | you, through a slash command | B | 16 |
| `prompts/intake/_TEMPLATE_DECISION.md` | prompts (meta) | author | the intake run | B | 16 |
| `prompts/maintenance/AUDIT.md` | prompts | author | you, through a slash command | B | 11 |
| `prompts/maintenance/MAINTENANCE.md` | prompts | author | you, through a slash command | B | 15 |
| `prompts/maintenance/_GENERATE_MAINTENANCE.md` | prompts (meta) | author | you, pasting the generator | B | 15 |
| `prompts/maintenance/_TEMPLATE_MAINTENANCE.md` | prompts (meta) | author | you, pasting the generator | B | 15 |
| `prompts/reference/_GENERATE_REFERENCE.md` | prompts (meta) | author | you, pasting the generator | B | 5 |
| `prompts/reference/_TEMPLATE_REFERENCE.md` | prompts (meta) | author | you, pasting the generator | B | 5 |
| `prompts/reference/evidence_rules.md` | prompts | author; maintenance proposes | phases and tools/ledger_gate.py | B,U | 5 |
| `prompts/reference/ledger_schema.md` | prompts | author; maintenance proposes | phases and tools/ledger_gate.py | B,U | 5 |
| `prompts/reference/routing_and_handoff.md` | prompts | author; maintenance proposes | phases and tools/ledger_gate.py | B,U | 5, 12 |
| `prompts/setup/_GENERATE_AGENTS.md` | prompts (meta) | author | you, pasting the generator | B | 2 |
| `prompts/setup/_GENERATE_FRONTDOOR.md` | prompts (meta) | author | you, pasting the generator | B | 0 |
| `prompts/setup/_GENERATE_TOOL_WIRING.md` | prompts (meta) | author | you, pasting the generator | B | 8 |
| `prompts/setup/_TEMPLATE_AGENTS.md` | prompts (meta) | author | you, pasting the generator | B | 2 |
| `prompts/setup/_TEMPLATE_FRONTDOOR.md` | prompts (meta) | author | you, pasting the generator | B | 0 |
| `prompts/setup/_TEMPLATE_TOOL_WIRING.md` | prompts (meta) | author | you, pasting the generator | B | 8 |
| `prompts/web/01-triage.md` | prompts | author; maintenance proposes | orchestrator and phase subagents | B,U | 4 |
| `prompts/web/02-characterize.md` | prompts | author; maintenance proposes | orchestrator and phase subagents | B,U | 4 |
| `prompts/web/02_5-map-classes.md` | prompts | author; maintenance proposes | orchestrator and phase subagents | B,U | 4 |
| `prompts/web/03-test.md` | prompts | author; maintenance proposes | orchestrator and phase subagents | B,U | 4 |
| `prompts/web/FINDING_VALIDATION.md` | prompts | author; maintenance proposes | orchestrator and phase subagents | B,U | 4, 13 |
| `prompts/web/VALIDATE_REPORT.md` | prompts | author; maintenance proposes | orchestrator and phase subagents | B,U | 4, 13 |
| `prompts/web/WEB_LOOP.md` | prompts | author; maintenance proposes | orchestrator and phase subagents | B,U | 4, 12 |
| `prompts/web/_GENERATE_PHASES.md` | prompts (meta) | author | you, pasting the generator | B | 4 |
| `prompts/web/_TEMPLATE_LOOP.md` | prompts (meta) | author | you, pasting the generator | B | 4 |
| `prompts/web/_TEMPLATE_PHASE.md` | prompts (meta) | author | you, pasting the generator | B | 4 |
| `recon_output/example-program/coverage_ledger.md` | example data | phases | phases, tools/ledger_gate.py | C,U | 12 |
| `recon_output/example-program/example-program_finding_order_read.md` | example data | tools/recon.py or phases | phases | C | 10 |
| `recon_output/example-program/target_notes.md` | example data | phases | phases, tools/ledger_gate.py | C,U | 10 |
| `recon_output/example-program/20260101_000000/archive_urls.txt` | example data | tools/recon.py or phases | phases | C | 10 |
| `recon_output/example-program/20260101_000000/httpx_results.json` | example data | tools/recon.py or phases | phases | C | 10 |
| `recon_output/example-program/20260101_000000/subdomains.txt` | example data | tools/recon.py or phases | phases | C | 10 |
| `reports/example-program/example-finding/REPORT.md` | example data | drafting session; report audit | you, the report audit | C,U | 13 |
| `reports/example-program/example-finding/REPORT_AUDIT.md` | example data | drafting session; report audit | you, the report audit | C,U | 13 |
| `reports/example-program/example-finding/evidence/order_read_redacted.txt` | example data | drafting session; report audit | you, the report audit | C,U | 13 |
| `scripts/organize_scope_claude.sh` | scripts | author | you | B | 9 |
| `scripts/lib/organize_scope_common.sh` | scripts | author | you | B | 9 |
| `targets/example-program/scope_raw.txt` | example data | you (pasted) | scripts/organize_scope_claude.sh | B | 9 |
| `targets/example-program/scope.json` | example data | scripts/organize_scope_claude.sh | tools/recon.py, tools/session_entry_gate.py | C | 9 |
| `targets/example-program/scope.txt` | example data | scripts/organize_scope_claude.sh | tools/recon.py, tools/session_entry_gate.py | C | 9 |
| `targets/example-program/guidelines.json` | example data | scripts/organize_scope_claude.sh | tools/recon.py, tools/session_entry_gate.py | C | 9 |
| `targets/example-program/guidelines.txt` | example data | scripts/organize_scope_claude.sh | tools/recon.py, tools/session_entry_gate.py | C | 9 |
| `targets/example-program/README.md` | example data | scripts/organize_scope_claude.sh | tools/recon.py, tools/session_entry_gate.py | C | 9 |
| `tools/_GENERATE_GATE.md` | tools (meta) | author | you, pasting the generator | B | 6 |
| `tools/_GENERATE_RECON.md` | tools (meta) | author | you, pasting the generator | B | 10 |
| `tools/_TEMPLATE_GATE.md` | tools (meta) | author | you, pasting the generator | B | 6 |
| `tools/_TEMPLATE_RECON.md` | tools (meta) | author | you, pasting the generator | B | 10 |
| `tools/closeout.sh` | tools | author | phases, orchestrator, you | B | 14 |
| `tools/digest_inbox.sh` | tools | author | phases, orchestrator, you | B | 14 |
| `tools/install_tools.sh` | tools | author | phases, orchestrator, you | B | 10 |
| `tools/knowledge_index.py` | tools | author | phases, orchestrator, you | B | 3 |
| `tools/ledger_gate.py` | tools | author | phases, orchestrator, you | B | 6 |
| `tools/ledger_to_inbox.py` | tools | author | phases, orchestrator, you | B | 14 |
| `tools/mcp_scope_hook.py` | tools | author | phases, orchestrator, you | B | 8 |
| `tools/playbook_apply.py` | tools | author | phases, orchestrator, you | B | 15 |
| `tools/recon.py` | tools | author | phases, orchestrator, you | B | 10 |
| `tools/redact.py` | tools | author | phases, orchestrator, you | B | 8 |
| `tools/scope_check.py` | tools | author | phases, orchestrator, you | B | 6, 9 |
| `tools/secret_scan.py` | tools | author | phases, orchestrator, you | B | 8 |
| `tools/session_entry_gate.py` | tools | author | phases, orchestrator, you | B | 6 |
| `tools/validate_scope.py` | tools | author | phases, orchestrator, you | B | 9 |
| `tools/wiring_check.py` | tools | author | phases, orchestrator, you | B | 11 |
| `tools/lib/__init__.py` | tools | author | phases, orchestrator, you | B | 6 |
| `tools/lib/meta.py` | tools | author | phases, orchestrator, you | B | 6 |
| `tools/tests/helpers.py` | tests | author | tools/tests/run.sh | B | 7 |
| `tools/tests/run.sh` | tests | author | tools/tests/run.sh | B | 7 |
| `tools/tests/test_closeout.py` | tests | author | tools/tests/run.sh | B | 14 |
| `tools/tests/test_digest_inbox.py` | tests | author | tools/tests/run.sh | B | 14 |
| `tools/tests/test_entry_gate.py` | tests | author | tools/tests/run.sh | B | 6 |
| `tools/tests/test_ledger_gate.py` | tests | author | tools/tests/run.sh | B | 6 |
| `tools/tests/test_ledger_to_inbox.py` | tests | author | tools/tests/run.sh | B | 14 |
| `tools/tests/test_mcp_hook.py` | tests | author | tools/tests/run.sh | B | 8 |
| `tools/tests/test_meta.py` | tests | author | tools/tests/run.sh | B | 6 |
| `tools/tests/test_organize_scope.py` | tests | author | tools/tests/run.sh | B | 9 |
| `tools/tests/test_playbook_apply.py` | tests | author | tools/tests/run.sh | B | 15 |
| `tools/tests/test_recon.py` | tests | author | tools/tests/run.sh | B | 10 |
| `tools/tests/test_redact.py` | tests | author | tools/tests/run.sh | B | 8 |
| `tools/tests/test_validate_scope.py` | tests | author | tools/tests/run.sh | B | 9 |
| `tools/tests/test_wiring_check.py` | tests | author | tools/tests/run.sh | B | 11 |
| `tools/tests/fixtures/fake_claude_digest.sh` | tests | author | tools/tests | B | 7 |
| `tools/tests/fixtures/fake_claude_organize.sh` | tests | author | tools/tests | B | 7 |
| `tools/tests/fixtures/recon_scope.json` | tests | author | tools/tests | B | 7 |
| `tools/tests/fixtures/bad/` | tests | author | tools/tests | B | 7 |
| `tools/tests/fixtures/good/` | tests | author | tools/tests | B | 7 |
| `tools/tests/fixtures/recon_fixture/` | tests | author | tools/tests | B | 7 |
| `tools/tests/fixtures/scope_good/` | tests | author | tools/tests | B | 7 |

## The pipeline

~~~text
 1. You paste the program page text into targets/[target]/scope_raw.txt
 2. prompts/organize_scope.md, run by scripts/organize_scope_claude.sh, writes five scope files with the four program rules
 3. tools/validate_scope.py checks them offline
 4. You confirm the four rules: python3 tools/scope_check.py confirm --target [target]
 5. tools/session_entry_gate.py start writes the active target, or refuses
 6. tools/recon.py (scope filter, header, rate) writes recon_output/[target]
 7. prompts/web/WEB_LOOP.md orchestrates, for each phase:
      ledger_gate snapshot, one fresh subagent, read its ROUTING line, ledger_gate check
      phases in order: 01 triage, 02 characterize, 02.5 map classes, 03 test
      a finding goes to FINDING_VALIDATION, then a report, then VALIDATE_REPORT, then ledger_gate submittable
 8. You submit in a browser, outside this repo
 9. Cycle summary, tools/ledger_to_inbox.py, tools/closeout.sh
10. You run tools/digest_inbox.sh (appends to the streams)
11. prompts/maintenance/MAINTENANCE.md turns streams into playbook skill files, you approve
12. prompts/maintenance/AUDIT.md checks the wiring, you approve
~~~

Burp and Chrome sit beside the loop, behind the hook in tools/mcp_scope_hook.py (see docs/TOOL_WIRING.md).

## Lifecycle classes

B: exists before the work starts. C: created during the work. U: updated during the work. A file may be B,U (written first, then changed). The class is per file, not per folder.

## The meta file convention

A path with any component starting with an underscore is a meta file or a runtime folder. Templates are named _TEMPLATE_[THING].md and show one finished file of that kind. Generators are named _GENERATE_[THING].md: at most ten lines, each names its template, its input, its output path and a check command. They live in the folder of the thing they make (files at the repo root have theirs under prompts/setup). The agent never loads a meta file as content: the knowledge index and the wiring check skip them through tools/lib/meta.py, and AGENTS.md says so. The digest reads the inbox folder on purpose.

## Where to go next

1. Read ETHICS.md, then GETTING_STARTED.md.
2. Open AGENTS.md and the prompts index in prompts/README.md.
3. Run the tests (bash tools/tests/run.sh) and the wiring check (python3 tools/wiring_check.py).
4. Build your own version with a generator prompt, then wire it in and rerun the check.
5. For live work, wire the tools with docs/TOOL_WIRING.md, and add new tools only through prompts/intake/INTAKE_TOOL.md.

What this repo does not ship, and when to add it. Each is added through `prompts/intake/INTAKE_TOOL.md` and the audit, and only when its problem has shown up in your own streams:

- Chain synthesis: a step that reconciles leads from different phases across the whole ledger. Add it when chains are lost between phases.
- An exploration frontier: a written record of what has been explored and what has not, checked before a phase may say it is done. Add it when sessions stop while surface remains.
- A fresh overview mode: a skeptical re-read of the whole ledger by a new conversation. Add it when a long project grows stale.
- Retesting: repeating the original requests to check a fix. Add it when you start to receive fixes to check.
- A target registry: one list of every target and its one name. Add it when the same target starts to carry two names.
- A second machine: a second checkout, which needs its own marker and a check that the two stay in step. Add it when you use two machines.
