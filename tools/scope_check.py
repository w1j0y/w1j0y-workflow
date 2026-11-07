#!/usr/bin/env python3
# What: Scope library and CLI: decides whether a host is in scope by the host an address points at, and records the human confirmation of the four program rules.
# Who writes: the repo author; hosts and rules come from targets/[target]/scope.json at run time, never from this file.
# Who reads: tools/session_entry_gate.py, tools/mcp_scope_hook.py, the human running confirm, tools/tests/test_entry_gate.py
# Wired into: tools/session_entry_gate.py, tools/mcp_scope_hook.py, tools/recon.py, tools/tests/test_entry_gate.py
"""Usage:
  python3 tools/scope_check.py check --target T --host H [--root R]   exit 0 in scope, 1 out of scope
  python3 tools/scope_check.py confirm --target T [--root R]         asks y or n, sets confirmed_by_human
Used by tools/recon.py to filter hosts. Library: host_in_scope(host, scope, port=None), parse_address(addr), build_active(scope, scope_path).
Matching is on the host only (not paths). A wildcard "*.x" matches subdomains of x, not x itself.
Out of scope wins over in scope. Exit codes: 0 ok, 1 out of scope, 2 usage.
"""
import argparse
import ipaddress
import json
import os
import re
import sys
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import meta  # noqa: E402

HOST_RE = re.compile(r"^[a-z0-9]([a-z0-9._-]*[a-z0-9])?$")
KEYS = ("domains", "wildcards", "urls", "api_urls", "ips", "cidrs")


def parse_address(addr):
    """Return (host, port, scheme) for the host an address points at, or None.

    Rejects userinfo ("allowed.test@evil.test"), backslashes, whitespace,
    percent-escapes and anything that is not a plain ASCII host name or IPv4.
    """
    if not isinstance(addr, str):
        return None
    a = addr.strip()
    if not a or any(c in a for c in "\\ \t\r\n\x00%"):
        return None
    a2 = a if "://" in a else "//" + a
    try:
        p = urlparse(a2)
        host = p.hostname
        port = p.port
    except ValueError:
        return None
    if p.username is not None or p.password is not None or "@" in p.netloc:
        return None
    if not host:
        return None
    host = host.lower().rstrip(".")
    if not HOST_RE.match(host):
        return None
    return host, port, (p.scheme or None)


def _collect(d):
    exact, wild, cidrs = set(), [], []
    d = d or {}
    for key in KEYS:
        for item in d.get(key) or []:
            if not isinstance(item, str) or not item.strip():
                continue
            item = item.strip().lower()
            if key == "cidrs":
                try:
                    cidrs.append(ipaddress.ip_network(item, strict=False))
                except ValueError:
                    pass
            elif item.startswith("*."):
                wild.append(item[2:])
            elif key in ("urls", "api_urls"):
                r = parse_address(item)
                if r:
                    exact.add(r[0])
            else:
                r = parse_address(item)
                if r:
                    exact.add(r[0])
    return exact, wild, cidrs


def _inside(host, exact, wild, cidrs):
    if host in exact:
        return True
    if any(host.endswith("." + w) for w in wild):
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return any(ip in n for n in cidrs)


def normalize(scope):
    """Return (in_set, out_set, ports) from a scope.json dict or an active dict."""
    if "hosts" in scope:  # active_target.json shape
        inc = {"domains": scope.get("hosts"), "wildcards": scope.get("wildcards"),
               "cidrs": scope.get("cidrs")}
        out = scope.get("out_of_scope")
        ports = scope.get("ports")
    else:
        inc = scope.get("recon_targets")
        out = scope.get("out_of_scope")
        ports = None
    return _collect(inc), _collect(out), ports


def host_in_scope(host, scope, port=None):
    """True if the host an address points at is in scope (and the port is allowed)."""
    r = parse_address(host)
    if r is None:
        return False
    h, p, _ = r
    if port is None:
        port = p
    inc, out, ports = normalize(scope)
    if not _inside(h, *inc):
        return False
    if _inside(h, *out):
        return False
    if ports is not None:
        try:
            return int(port) in [int(x) for x in ports]
        except (TypeError, ValueError):
            return False
    return True


def header_from(scope):
    """The identification header as {"name","value"} or None."""
    rules = scope.get("rules") or {}
    h = rules.get("identification_header") or {}
    if h.get("name") and h.get("value"):
        return {"name": h["name"], "value": h["value"]}
    h = scope.get("required_header")
    if isinstance(h, dict) and h.get("name") and h.get("value"):
        return {"name": h["name"], "value": h["value"]}
    return None


def build_active(scope, scope_path):
    """Build the .state/active_target.json content from a scope.json dict."""
    rt = scope.get("recon_targets") or {}
    exact, wild, cidrs = _collect(rt)
    rules = scope.get("rules") or {}
    rl = rules.get("rate_limit") or {}
    rate = None
    if rl.get("value") and rl.get("unit"):
        rate = {"value": rl["value"], "unit": rl["unit"]}
    import datetime
    return {
        "target": scope.get("target_name"),
        "scope_path": scope_path,
        "hosts": sorted(exact),
        "wildcards": sorted("*." + w for w in wild),
        "cidrs": [str(c) for c in cidrs],
        "out_of_scope": scope.get("out_of_scope") or {},
        "ports": None,
        "header": header_from(scope),
        "rate": rate,
        "rules": rules,
        "started": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def scope_file(root, target):
    return os.path.join(root, "targets", target, "scope.json")


def cmd_confirm(root, target):
    path = scope_file(root, target)
    if not os.path.isfile(path):
        print("scope file not found: targets/%s/scope.json" % target, file=sys.stderr)
        return 2
    with open(path, encoding="utf-8") as f:
        text = f.read()
    scope = json.loads(text)
    rules = scope.get("rules")
    if not isinstance(rules, dict):
        print("scope has no rules block", file=sys.stderr)
        return 2
    print("Program rules for target '%s'. Compare each with the live program page." % target)
    for name in ("automation", "ai_use", "rate_limit", "identification_header"):
        r = rules.get(name, {})
        shown = {k: v for k, v in r.items() if k != "source_text"}
        print("- %s: %s" % (name, json.dumps(shown, sort_keys=True)))
        print("    source text: %s" % (r.get("source_text") or "(none)"))
    try:
        ans = input("Do these four rules match the program page? [y/n] ")
    except EOFError:
        ans = ""
    if ans.strip().lower() not in ("y", "yes"):
        print("not confirmed; nothing changed")
        return 1
    rules["confirmed_by_human"] = True
    # Flip the one value in place so the file keeps its layout and the change shows as one line in git.
    flipped, n = re.subn(r'("confirmed_by_human"\s*:\s*)false', r"\1true", text, count=1)
    if n == 1 and json.loads(flipped).get("rules", {}).get("confirmed_by_human") is True:
        out = flipped
    else:
        out = json.dumps(scope, indent=2) + "\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(out)
    print("confirmed_by_human set to true in targets/%s/scope.json" % target)
    return 0


def cmd_check(root, target, host):
    path = scope_file(root, target)
    if not os.path.isfile(path):
        print("scope file not found: targets/%s/scope.json" % target, file=sys.stderr)
        return 2
    with open(path, encoding="utf-8") as f:
        scope = json.load(f)
    if host_in_scope(host, scope):
        print("IN SCOPE: %s" % host)
        return 0
    print("OUT OF SCOPE: %s" % host)
    return 1


def main(argv=None):
    ap = argparse.ArgumentParser(prog="scope_check.py", description="Scope checks and rule confirmation.")
    ap.add_argument("command", choices=["check", "confirm"])
    ap.add_argument("--target", required=True)
    ap.add_argument("--host")
    ap.add_argument("--root", default=meta.repo_root())
    args = ap.parse_args(argv)
    root = os.path.abspath(args.root)
    if args.command == "confirm":
        return cmd_confirm(root, args.target)
    if not args.host:
        print("check needs --host", file=sys.stderr)
        return 2
    return cmd_check(root, args.target, args.host)


if __name__ == "__main__":
    sys.exit(main())
