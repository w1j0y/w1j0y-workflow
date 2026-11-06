What: Prompt that sets up the tool wiring files and tests the hook offline.
Who writes: The repo author.
Who reads: You, pasting it into Claude Code.
Wired into: prompts/setup/_TEMPLATE_TOOL_WIRING.md
Template: prompts/setup/_TEMPLATE_TOOL_WIRING.md. Input: docs/TOOL_WIRING.md and tools/mcp_scope_hook.py. Output: .mcp.json copied from .mcp.json.example, nothing else changed.
Prompt: Read docs/TOOL_WIRING.md and tools/mcp_scope_hook.py. Copy .mcp.json.example to .mcp.json. Check that .claude/settings.json registers the hook for mcp tools. Do not start Burp or the browser.
Run bash tools/tests/run.sh and show me the hook tests. List the steps I must do by hand and the checks to run once Burp and Chrome are open.
Check: python3 tools/wiring_check.py.
