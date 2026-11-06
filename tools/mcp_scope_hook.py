#!/usr/bin/env python3
# What: PreToolUse hook that allows, asks or blocks Burp and Chrome MCP calls by scope, identification header and request rate.
# Who writes: the repo author; hosts, header and rate come from .state/active_target.json at run time.
# Who reads: Claude Code (registered in .claude/settings.json), the human reading docs/TOOL_WIRING.md, tools/tests/test_mcp_hook.py
# Wired into: .claude/settings.json, docs/TOOL_WIRING.md, tools/tests/test_mcp_hook.py
"""Reads one PreToolUse JSON object on stdin: tool_name, tool_input, mcp_server{name,source}.
Exit 2 plus a reason on stderr blocks. Exit 0 with no output allows. Exit 0 with a
JSON permissionDecision of ask on stdout asks the human. Any exception exits 2 (fail closed).

Scope decisions come from tools/scope_check.py.
State read: .state/active_target.json (written by tools/session_entry_gate.py).
State written: .state/requests.jsonl (timestamps for the rate window), .state/tabs.json
(tab id to last allowed url). HOOK_LOG=1 appends redacted samples to .state/hook_samples.jsonl
so you can check the real call shapes on your machine before trusting the parser.
Optional .state/mcp_sources.json {"burp": "...", "claude-in-chrome": "..."} pins mcp_server.source.

Limits: the hook sees a call before it runs, not what a page does afterwards.
A click that navigates, a redirect or a script is invisible to it.
Burp argument names assumed: content, targetHostname, targetPort, usesHttps; history: regex, count, offset.
Chrome: navigate uses url and tabId; computer and form_input use tabId.
"""
import argparse
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import meta  # noqa: E402
import scope_check  # noqa: E402

BURP = "burp"
CHROME = "claude-in-chrome"

BURP_SEND = {"send_http1_request", "send_http2_request"}
BURP_HISTORY = {"get_proxy_http_history_regex", "get_proxy_websocket_history_regex"}
BURP_HISTORY_PLAIN = {"get_proxy_http_history", "get_proxy_websocket_history"}
BURP_ASK = {"create_repeater_tab", "send_to_intruder", "get_active_editor_contents", "set_active_editor_contents"}
BURP_UTIL = {"url_encode", "url_decode", "base64encode", "base64decode", "base64_encode", "base64_decode",
             "generate_random_string"}
# Static deny list: these change Burp itself, or read its whole config.
BURP_DENY = {"set_proxy_intercept_state", "set_task_execution_engine_state", "set_project_options",
             "set_user_options", "output_project_options", "output_user_options"}

CHROME_READ = {"get_page_text", "read_page", "find", "read_console_messages", "read_network_requests",
               "tabs_context_mcp", "tabs_create_mcp", "tabs_close_mcp", "list_connected_browsers",
               "resize_window", "shortcuts_list"}
CHROME_ASK = {"select_browser", "switch_browser", "shortcuts_execute"}
CHROME_DENY = {"javascript_tool", "file_upload", "upload_image", "gif_creator", "browser_batch"}
CHROME_TAB = {"computer", "form_input"}
COMPUTER_READ_ACTIONS = {"screenshot", "scroll", "scroll_to", "zoom", "wait", "hover", "mouse_move"}

WINDOWS = {"per_second": 1, "per_minute": 60, "per_hour": 3600}
MAX_HISTORY_COUNT = 50


class Decision(Exception):
    def __init__(self, kind, reason):
        Exception.__init__(self, reason)
        self.kind = kind
        self.reason = reason


def deny(reason):
    raise Decision("deny", reason)


def ask(reason):
    raise Decision("ask", reason)


def split_tool(name):
    """mcp__server__tool -> (server, tool); None if not an MCP tool name."""
    if not isinstance(name, str) or not name.startswith("mcp__"):
        return None
    rest = name[5:]
    if "__" not in rest:
        return None
    server, tool = rest.split("__", 1)
    return (server, tool) if server and tool else None


def state_path(root, name):
    return os.path.join(root, ".state", name)


def load_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def need_active(root):
    active = load_json(state_path(root, "active_target.json"))
    if not isinstance(active, dict) or not active.get("target"):
        deny("no active target: run python3 tools/session_entry_gate.py start --target [target] first")
    return active


def rate_room(root, active, now=None):
    """Raise deny if the sliding window is full; otherwise do nothing."""
    rate = active.get("rate")
    if not isinstance(rate, dict) or not rate.get("value") or rate.get("unit") not in WINDOWS:
        return
    now = now if now is not None else time.time()
    span = WINDOWS[rate["unit"]]
    count = 0
    try:
        with open(state_path(root, "requests.jsonl"), encoding="utf-8") as f:
            for ln in f:
                try:
                    ts = float(json.loads(ln).get("ts", 0))
                except (ValueError, AttributeError, TypeError):
                    continue
                if ts > now - span:
                    count += 1
    except OSError:
        pass
    if count >= int(rate["value"]):
        deny("rate limit reached: %d request(s) in the last %d s, limit %s %s" % (count, span, rate["value"], rate["unit"]))


def record_request(root, kind):
    os.makedirs(os.path.join(root, ".state"), exist_ok=True)
    with open(state_path(root, "requests.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), "kind": kind}) + "\n")


def check_burp_send(root, args):
    active = need_active(root)
    host = args.get("targetHostname")
    port = args.get("targetPort")
    https = args.get("usesHttps")
    content = args.get("content")
    if not isinstance(host, str) or not host:
        deny("targetHostname is missing")
    if isinstance(port, bool) or not isinstance(port, int):
        deny("targetPort must be an integer (the port must be literal)")
    if not isinstance(https, bool):
        deny("usesHttps must be true or false (the protocol must be literal)")
    if not isinstance(content, str) or not content.strip():
        deny("raw request content is missing")
    if not scope_check.host_in_scope(host, active, port=port):
        deny("host %s port %s is not in scope for target %s" % (host, port, active["target"]))
    hdr = active.get("header")
    if isinstance(hdr, dict) and hdr.get("name") and hdr.get("value"):
        head = content.replace("\r\n", "\n").split("\n\n", 1)[0]
        rx = re.compile(r"(?im)^%s\s*:\s*%s\s*$" % (re.escape(hdr["name"]), re.escape(hdr["value"])))
        if not rx.search(head):
            deny("identification header missing: add '%s: %s' to the raw request" % (hdr["name"], hdr["value"]))
    else:
        deny("active target has no identification header")
    m = re.search(r"(?im)^host\s*:\s*(\S+)\s*$", content.replace("\r\n", "\n").split("\n\n", 1)[0])
    if m:
        hh = scope_check.parse_address(m.group(1))
        if hh is None or hh[0] != host.lower().rstrip("."):
            deny("Host header %s does not match targetHostname %s" % (m.group(1), host))
    rate_room(root, active)
    record_request(root, "burp_send")


def match_all(pattern):
    try:
        rx = re.compile(pattern)
    except re.error:
        return None
    probes = ["", "a", "zz9q /x", "GET /a HTTP/1.1\r\nHost: q.test\r\n\r\n"]
    return all(rx.search(p) for p in probes)


def check_burp_history(root, args):
    need_active(root)
    pat = args.get("regex")
    if not isinstance(pat, str) or not pat.strip():
        deny("history read needs a non-empty regex")
    m = match_all(pat)
    if m is None:
        deny("history regex does not compile")
    if m:
        deny("history regex matches everything; capture wide, read narrow")
    count = args.get("count")
    if isinstance(count, bool) or not isinstance(count, int) or not (1 <= count <= MAX_HISTORY_COUNT):
        deny("history read needs an integer count from 1 to %d" % MAX_HISTORY_COUNT)
    off = args.get("offset", 0)
    if isinstance(off, bool) or not isinstance(off, int) or off < 0:
        deny("offset must be a non-negative integer")


def url_host_port(url):
    if not isinstance(url, str) or not url.strip():
        deny("url is missing")
    u = url.strip()
    if "://" not in u:
        u = "https://" + u
    r = scope_check.parse_address(u)
    if r is None:
        deny("url does not parse to a plain host: %s" % url[:80])
    host, port, scheme = r
    if port is None:
        port = 80 if scheme == "http" else 443
    return host, port


def check_chrome_navigate(root, args):
    active = need_active(root)
    url = args.get("url")
    if isinstance(url, str) and url.strip().lower() in ("back", "forward"):
        ask("history navigation: the destination is not visible to the hook")
    host, port = url_host_port(url)
    tab = args.get("tabId")
    if tab is None:
        deny("tabId is missing")
    if not scope_check.host_in_scope(host, active, port=port):
        deny("navigation to %s is not in scope for target %s" % (host, active["target"]))
    rate_room(root, active)
    record_request(root, "chrome_navigate")
    tabs = load_json(state_path(root, "tabs.json"), {}) or {}
    tabs[str(tab)] = url.strip()
    with open(state_path(root, "tabs.json"), "w", encoding="utf-8") as f:
        json.dump(tabs, f)


def check_chrome_tab_tool(root, tool, args):
    active = need_active(root)
    tab = args.get("tabId")
    if tab is None:
        deny("tabId is missing")
    tabs = load_json(state_path(root, "tabs.json"), {}) or {}
    last = tabs.get(str(tab))
    if not last:
        deny("tab %s is unknown: navigate it through the hook first" % tab)
    host, port = url_host_port(last)
    if not scope_check.host_in_scope(host, active, port=port):
        deny("tab %s last allowed url is no longer in scope" % tab)
    if tool == "form_input" or args.get("action") not in COMPUTER_READ_ACTIONS:
        ask("state-changing browser action on %s" % host)


def decide(payload, root):
    """Raise Decision for deny or ask; return normally to allow."""
    if not isinstance(payload, dict):
        deny("hook input is not a JSON object")
    parsed = split_tool(payload.get("tool_name"))
    if parsed is None:
        deny("not an MCP tool name this hook knows: %r" % payload.get("tool_name"))
    server, tool = parsed
    srv = payload.get("mcp_server")
    if isinstance(srv, dict):
        if srv.get("name") and srv.get("name") != server:
            deny("mcp_server.name %r does not match the tool name" % srv.get("name"))
        pins = load_json(state_path(root, "mcp_sources.json"), None)
        if isinstance(pins, dict) and server in pins and srv.get("source") != pins[server]:
            deny("mcp_server.source does not match the registered source for %s" % server)
    if server not in (BURP, CHROME):
        deny("unknown MCP server %r" % server)
    args = payload.get("tool_input")
    if not isinstance(args, dict):
        args = {}
    if server == BURP:
        if tool in BURP_DENY:
            deny("%s is on the static deny list" % tool)
        if tool in BURP_SEND:
            return check_burp_send(root, args)
        if tool in BURP_HISTORY:
            return check_burp_history(root, args)
        if tool in BURP_HISTORY_PLAIN:
            deny("unbounded history read: use the regex history tool with a pattern and a count")
        if tool in BURP_ASK:
            ask("%s stages work in Burp for the human" % tool)
        if tool in BURP_UTIL:
            return None
        deny("unknown Burp tool %r" % tool)
    if tool in CHROME_DENY:
        deny("%s is denied (a script can reach anywhere; recordings capture account data; uploads leave the machine)" % tool)
    if tool == "navigate":
        return check_chrome_navigate(root, args)
    if tool in CHROME_TAB:
        return check_chrome_tab_tool(root, tool, args)
    if tool in CHROME_READ:
        return None
    if tool in CHROME_ASK:
        ask("%s changes which browser or macro runs" % tool)
    deny("unknown Chrome tool %r" % tool)


def log_sample(root, payload):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import redact
    def clean(v):
        if isinstance(v, str):
            return redact.redact(v)[:200]
        if isinstance(v, dict):
            return {k: clean(x) for k, x in v.items()}
        return v
    os.makedirs(os.path.join(root, ".state"), exist_ok=True)
    with open(state_path(root, "hook_samples.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": time.time(), "sample": clean(payload)}) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mcp_scope_hook.py", description="PreToolUse scope hook (reads JSON on stdin).")
    ap.add_argument("--root", default=os.environ.get("CLAUDE_PROJECT_DIR") or meta.repo_root())
    args, _ = ap.parse_known_args(argv)
    root = os.path.abspath(args.root)
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw)
        if os.environ.get("HOOK_LOG") == "1":
            try:
                log_sample(root, payload)
            except Exception:
                pass
        try:
            decide(payload, root)
        except Decision as d:
            if d.kind == "ask":
                print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                                         "permissionDecision": "ask",
                                                         "permissionDecisionReason": d.reason}}))
                return 0
            print("BLOCKED by scope hook: %s" % d.reason, file=sys.stderr)
            return 2
        return 0
    except Exception as e:  # fail closed
        print("BLOCKED by scope hook: internal error (%s: %s)" % (type(e).__name__, e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
