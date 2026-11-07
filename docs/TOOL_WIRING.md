# Tool wiring: Burp MCP server and Claude in Chrome
What: How to connect Burp and Chrome to Claude Code, how the scope hook bounds them, how to verify it, and what remains unproven until you run it live.
Who writes: The repo author. Re-check the setup against the official docs on the day you use it.
Who reads: You, once per machine, before any live phase.
Wired into: AGENTS.md, GETTING_STARTED.md, docs/TOOLS_NEEDED.md, .claude/settings.json (one-way: JSON has no box), .mcp.json.example (one-way: JSON has no box), tools/mcp_scope_hook.py (one-way: script owned by another part), tools/scope_check.py (one-way: script owned by another part), tools/session_entry_gate.py (one-way: script owned by another part), tools/redact.py (one-way: script owned by another part), tools/secret_scan.py (one-way: script owned by another part)

Setup facts below were read from the vendors' documentation and may have changed. Anything marked "Verify live" has not been proven by this repo's offline tests.

## Why each is wired

- Chrome: the agent cannot drive a logged-in, multi-step web workflow (clicks, forms, state) without a browser. It shares the browser's login state.
- Burp MCP server: the agent cannot read recorded traffic or replay one exact request without it. Burp gives the request as sent, not as the browser reports it.
- Decision rule (also in `AGENTS.md`): a workflow, role or state question goes to Chrome. One request's parameter, auth or injection question goes to Burp. Each finding from one is the lookup key for the other.

## Setup: Burp

1. Install the "MCP Server" extension from the BApp Store inside Burp. The store listing says which Burp edition each tool needs (it names the Collaborator tools as Professional only); read it for your edition. Seen in the store listing: version 1.4.0, which will have moved.
2. Enable it in the MCP tab. The default address is `http://127.0.0.1:9876` and the streamable HTTP path is `/mcp`. The older SSE endpoint is deprecated in Claude Code.
3. Leave "Enable tools that can edit your config" off. Keep Burp's per-request approval on. Do not click "Always allow host": the dialog is a backstop, not permission.
4. Connect Claude Code from the project folder, either with `claude mcp add --transport http burp http://127.0.0.1:9876/mcp --scope project`, or by copying `.mcp.json.example` to `.mcp.json`. The first form is derived from two docs pages; neither prints it verbatim (Verify live).
5. Check with `/mcp` inside Claude Code.
6. A headless run (`claude -p`) loads project `.mcp.json` servers without asking, and Burp's approval prompt blocks until answered, so an unattended run hangs unless the target is on Burp's auto-approve list. Do not do that for a live target.

## Setup: Chrome

1. Google Chrome or Edge with the "Claude in Chrome" extension from the Chrome Web Store (id `fcoeoabgfenejglbffodgkkbkcdhcgfn`, minimum version 1.0.36 when this was written; re-check).
2. A direct paid Claude plan with `/login` (API key and setup-token logins keep it off; not available through some cloud providers). Re-check the plan list in the docs.
3. Start with `claude --chrome`, or use `/chrome` and choose enabled by default. The extension must be signed in to the same account and organization. A project's settings cannot enable it.
4. Use a separate browser profile that holds only test accounts. Set the extension's site permissions to the in-scope hosts only. Keep financial, medical, legal and work accounts out of that profile. Prompt injection from page content is the named main risk.

## Both are deferred tools

`AGENTS.md` session start tells the agent to load them with the tool search step before any live phase. If you skip it they look absent, and live sessions silently skip them.

## The hook

`.claude/settings.json` registers `tools/mcp_scope_hook.py` as a PreToolUse hook with the broad matcher `mcp__.*` and `"onFailure": "block"`, which the hooks documentation describes for recent versions: without it a hook that times out does not block the call. If your version does not know the setting, check the hooks page for your version. The script decides; any server or tool it does not know is denied (fail closed), and any exception in the script exits with 2, which blocks.

Facts from the Claude Code docs: a hook receives the tool name, the arguments and, for MCP tools, the server name and source; exit code 2 blocks and shows stderr to the model; a hook deny holds even under bypass modes; permission rules cannot match MCP arguments, so argument checks need a hook; matchers are unanchored regular expressions; hooks also run in subagents and in `claude -p`. In an interactive session, settings-file hooks wait until you accept the workspace trust dialog. Flags that disable hooks exist; for a gate nobody can bypass use managed settings (this is an inference from the docs; Verify live).

State: the hook reads `.state/active_target.json` that `python3 tools/session_entry_gate.py start --target [target]` writes. With no active target it denies every send, navigate and click.

| Tool call | Decision |
|---|---|
| Burp send_http1_request, send_http2_request | allow only if the host, port and https flag are in scope literally, the raw request contains the identification header, and the rate window has room; else deny and name the missing item |
| Burp history reads | allow only with a non-empty pattern that is not match-all and a bounded count |
| Burp repeater, intruder, editor, task engine, options, intercept | ask or deny; the options setters and the intercept toggle are also in the static deny list |
| Chrome navigate | allow only if the URL host is in scope; record the tab's last allowed URL |
| Chrome read tools (page text, read page, find, console, network, tabs) | allow |
| Chrome computer, form_input | allow only when the tab's last recorded URL is in scope; unknown tab: deny; state-changing actions ask |
| Chrome javascript_tool, file_upload, upload_image, gif_creator | deny or ask |
| Unknown MCP server or tool, or a server whose source does not match the registered one | deny |

## Honest limits

- The hook sees a call and its arguments before it runs, not what the page does afterwards. A click that navigates, a redirect or a script is invisible to it.
- The layers that exist: the extension's per-site permissions (the real boundary for clicks), the hook for what it can see, Burp's approval dialog, and you.
- The docs do not say how Chrome tool calls appear in hook input. The hook assumes `mcp__claude-in-chrome__[tool]`. The Burp argument names (content, targetHostname, targetPort, usesHttps; history: regex, count, offset) come from the Burp server, not from Anthropic. Log real calls before you trust the parser (next section).
- The browser cannot add an identification header by itself. One design choice, not an official recommendation: a match-and-replace rule in Burp that adds the header to browser traffic through the proxy. Verify live.

## Log real call shapes (HOOK_LOG)

1. Start Claude Code with the environment variable `HOOK_LOG=1` set for the session.
2. Make one harmless call of each kind against a host you own or a `.test` name that is in your scope file: one Burp history read, one Burp send, one Chrome navigate, one Chrome page read.
3. Open `.state/hook_samples.jsonl`. Each line is a redacted sample: tool name, argument names, server name and source.
4. Compare the names with the parser constants at the top of `tools/mcp_scope_hook.py`. If a name differs, change the script and add a fixture, then run the tests.
5. Remove `HOOK_LOG` when done. The sample file is under `.state/`, which is not committed.

## Verification commands (offline)

- `bash tools/tests/run.sh` runs all tests, including the hook tests with good and bad fixtures.
- `python3 tools/wiring_check.py` checks that this file, the settings and the hook are wired.
- `python3 tools/scope_check.py check --target [target] --host [host]` prints whether a host is in scope (exit 0 in scope, 1 out of scope).
- Feed the hook a sample by hand: pipe a JSON object with tool_name, tool_input and mcp_server into `python3 tools/mcp_scope_hook.py` and read the exit code (2 means blocked, with the reason on stderr).

## What is sensitive and how it is kept out

Burp history and browser sessions hold cookies, session ids, bearer tokens, Authorization headers, CSRF tokens, test-account credentials and other users' data; screenshots capture everything on screen. The vendors give thin guidance: PortSwigger's extension guidance says to strip authentication tokens where possible and send only in-scope traffic; its dialog warns that history may hold data from earlier sessions. Anthropic says Claude cannot filter sensitive content out of what it sees, and that transcripts are stored locally for a limited time (a settings value controls it) while tool results go to the model API.

The rest is this repo's own design:
1. Test accounts only, a separate browser profile, nothing sensitive open.
2. `tools/redact.py` removes Cookie, Set-Cookie, Authorization, bearer and JWT patterns, key-like strings and emails from text before it is saved to evidence, ledger or memory. `AGENTS.md` says to run it.
3. Evidence folders, credential files and `.state/` are not committed (see `.gitignore`).
4. `tools/secret_scan.py` runs at closeout and refuses on a hit, printing the file and line, never the value.
5. `.claude/settings.json` denies reading credential files, and denies the Burp options setters and the intercept toggle.
6. Shorten the transcript retention period in your own Claude Code settings.
A hook cannot rewrite what an MCP tool returned, so redaction is on the way out to files, not on the way in to the model.

## Setup prompt

Paste this into Claude Code after cloning (the same text is in the setup generator under prompts/setup):

~~~text
Read docs/TOOL_WIRING.md and tools/mcp_scope_hook.py. Copy .mcp.json.example to .mcp.json. Check that .claude/settings.json registers the hook for mcp tools. Run bash tools/tests/run.sh and show me the hook tests. Do not start Burp or the browser. List the steps I must do by hand and the checks I should run once Burp and Chrome are open.
~~~

## Verify live

Things this repo could not prove offline. Check each once Burp and Chrome are running, on a host you own or a local practice app:

1. The exact Burp tool names and argument names match the hook's constants (use the HOOK_LOG steps).
2. Chrome tool calls arrive as `mcp__claude-in-chrome__[tool]` with a tab id in the arguments.
3. The `mcp_server.source` value the hook sees, and whether to pin it in the optional sources file the hook reads.
4. The `claude mcp add --transport http` command form works and `/mcp` shows Burp connected.
5. The hook is active in your session: call a Burp send with a host that is not in scope and see it denied.
6. The match-and-replace header rule in Burp carries the identification header on browser traffic.
7. Burp's approval dialog appears for the first request to a host.
8. Version numbers, plan requirements and the extension id given above are still current.

## Permission note

Writes under .claude/ and to .mcp.json are protected paths. In an interactive session Claude Code asks you to approve each write. A headless run in acceptEdits mode refuses them, so make those two edits yourself or approve them when asked. Follow the official docs for your version for every setup step on this page; nothing here has been checked against a live Burp or Chrome session.
