# Template: docs/TOOL_WIRING.md
What: The shape of the tool wiring document for any MCP tool you connect.
Who writes: The repo author.
Who reads: prompts/setup/_GENERATE_TOOL_WIRING.md and anyone wiring a new tool.
Wired into: prompts/setup/_GENERATE_TOOL_WIRING.md

Sections, per tool: why it is wired; setup commands; what it can do that is dangerous; the hook rule per tool call (allow, ask, deny); the static deny list; honest limits; what is sensitive and how it is kept out of logs; verification commands; a section named Verify live for anything you could not prove offline.

Rules: use only documented defaults, no device ids, no tokens, no handles, no home paths. Separate what is documented from what is this repo's design, and label the design.

## Wire it in

1. The hook script gets a rule per tool and a test with a good and a bad fixture.
2. `.claude/settings.json` registers the hook and lists the deny rules.
3. `AGENTS.md` names when to use the tool and what needs approval.
4. `python3 tools/wiring_check.py` passes.
