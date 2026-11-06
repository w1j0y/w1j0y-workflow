#!/usr/bin/env python3
# What: Entry gate that refuses to start a live session unless the target scope file and its four program rules are complete and human confirmed.
# Who writes: the repo author; it reads targets/[target]/scope.json and writes .state/active_target.json.
# Who reads: the orchestrator in prompts/web/WEB_LOOP.md, tools/mcp_scope_hook.py (through the state file), tools/tests/test_entry_gate.py
# Wired into: prompts/web/WEB_LOOP.md, tools/mcp_scope_hook.py, tools/tests/test_entry_gate.py
"""Usage: python3 tools/session_entry_gate.py start --target T [--root R]

Refuses (exit 3, 'ENTRY GATE FAIL (N problem(s))') when: scope.json is missing,
a rule is neither specified nor marked unspecified, confirmed_by_human is not
true, automation is prohibited, ai_use is prohibited or restricted, or no
identification header is available. A dirty git tree only warns.
On pass it writes .state/active_target.json for tools/scope_check.py and the hook.
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import meta  # noqa: E402
import scope_check  # noqa: E402

AUTOMATION = ("allowed", "limited", "prohibited", "unspecified")
AI_USE = ("allowed", "disclosure_required", "restricted", "prohibited", "unspecified")
UNITS = ("per_second", "per_minute", "per_hour")


def check_rules(scope, problems, notes):
    rules = scope.get("rules")
    if not isinstance(rules, dict):
        problems.append("scope has no rules block (automation, ai_use, rate_limit, identification_header)")
        return
    for name, vocab in (("automation", AUTOMATION), ("ai_use", AI_USE)):
        r = rules.get(name)
        st = r.get("status") if isinstance(r, dict) else None
        if st not in vocab:
            problems.append("rule %s is not specified (status must be one of %s)" % (name, ", ".join(vocab)))
    rl = rules.get("rate_limit")
    if not isinstance(rl, dict) or not (rl.get("status") == "unspecified" or (rl.get("value") and rl.get("unit") in UNITS)):
        problems.append("rule rate_limit needs a value and a unit (%s) or status unspecified" % ", ".join(UNITS))
    ih = rules.get("identification_header")
    if not isinstance(ih, dict) or not (ih.get("status") == "unspecified" or (ih.get("name") and ih.get("value"))):
        problems.append("rule identification_header needs a name and value or status unspecified")
    if rules.get("confirmed_by_human") is not True:
        problems.append("rules are not confirmed by a human (run: python3 tools/scope_check.py confirm --target T)")
    auto = (rules.get("automation") or {}).get("status")
    if auto == "prohibited":
        problems.append("program prohibits automation; this workflow is automated")
    elif auto == "limited":
        notes.append("NOTE: automation is limited by the program: %s" % (rules["automation"].get("source_text") or "(no text)"))
        notes.append("NOTE: restate the limit to the session before any live step")
    ai = (rules.get("ai_use") or {}).get("status")
    if ai in ("prohibited", "restricted"):
        problems.append("program ai_use rule is %s" % ai)
    elif ai == "disclosure_required":
        notes.append("NOTE: AI disclosure is required; the report needs a line starting 'AI disclosure:'")


def git_warn(root):
    if not os.path.isdir(os.path.join(root, ".git")):
        return ["WARN: not a git repository, no state to compare"]
    try:
        out = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True,
                             text=True, timeout=20).stdout
    except (OSError, subprocess.SubprocessError):
        return ["WARN: could not read git status"]
    n = len([ln for ln in out.splitlines() if ln.strip()])
    return ["WARN: git tree has %d uncommitted change(s)" % n] if n else []


def cmd_start(root, target):
    problems, notes = [], []
    path = scope_check.scope_file(root, target)
    rel = os.path.join("targets", target, "scope.json")
    scope = None
    if not os.path.isfile(path):
        problems.append("scope file missing: %s" % rel)
    else:
        try:
            with open(path, encoding="utf-8") as f:
                scope = json.load(f)
        except ValueError as e:
            problems.append("scope file is not valid JSON: %s" % e)
    if isinstance(scope, dict):
        check_rules(scope, problems, notes)
        if scope_check.header_from(scope) is None:
            problems.append("no identification header in scope (rules.identification_header or required_header)")
        active = scope_check.build_active(scope, rel)
        if not active["hosts"] and not active["wildcards"] and not active["cidrs"]:
            problems.append("scope lists no in-scope hosts")
    elif scope is not None:
        problems.append("scope file is not a JSON object")
    if problems:
        print("ENTRY GATE FAIL (%d problem(s)):" % len(problems), file=sys.stderr)
        for p in problems:
            print("  - %s" % p, file=sys.stderr)
        return 3
    for w in git_warn(root):
        print(w, file=sys.stderr)
    state = os.path.join(root, ".state")
    os.makedirs(state, exist_ok=True)
    with open(os.path.join(state, "active_target.json"), "w", encoding="utf-8") as f:
        json.dump(active, f, indent=2)
        f.write("\n")
    print("ENTRY GATE PASS: target '%s' -- %d host(s), %d wildcard(s); wrote .state/active_target.json"
          % (target, len(active["hosts"]), len(active["wildcards"])))
    for n in notes:
        print(n)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="session_entry_gate.py", description="Entry gate for a live session.")
    ap.add_argument("command", choices=["start"])
    ap.add_argument("--target", required=True)
    ap.add_argument("--root", default=meta.repo_root())
    args = ap.parse_args(argv)
    return cmd_start(os.path.abspath(args.root), args.target)


if __name__ == "__main__":
    sys.exit(main())
