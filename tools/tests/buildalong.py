#!/usr/bin/env python3
# What: Optional build-along test that runs each generator and flow prompt in a fresh headless Claude Code process on a throwaway copy of the repo and checks the result with the repo's own checks.
# Who writes: the repo author.
# Who reads: the repo author before publishing; not part of the unit tests because it needs a Claude login.
# Wired into: tools/tests/fixtures/buildalong/resource/cors_basics.md (one-way: sample input), tools/wiring_check.py (one-way: reference only)
"""Usage: python3 tools/tests/buildalong.py [case ...]   (no args: all cases). Results: /tmp/buildalong-results/[case].json
Each run: claude -p with an explicit allowlist, no web or MCP tools, max 25 turns, in a temp copy, PATH reduced.
Network use: only the model API. Recon binaries are absent from PATH (checked)."""
import json, os, re, shutil, subprocess, sys, tempfile, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = "/tmp/buildalong-results"
CLAUDE = shutil.which("claude") or os.path.expanduser("~/.local/bin/claude")
ALLOW = ["Read", "Write", "Edit", "Edit(.claude/**)", "Edit(.mcp.json)", "Glob", "Grep", "Bash(python3 *)", "Bash(bash tools/*)", "Bash(ls *)", "Bash(mkdir *)",
         "Bash(cat *)", "Bash(cp *)", "Bash(mv *)", "Bash(rm *)", "Bash(sed *)", "Bash(head *)", "Bash(wc *)", "Bash(grep *)"]
DENY = ["WebFetch", "WebSearch", "mcp__*", "Bash(curl *)", "Bash(wget *)", "Bash(git push*)"]
# Cases that write under .claude/ or .mcp.json: headless acceptEdits mode protects those paths, so these two run in a throwaway copy
# with bypassPermissions (the deny list still applies, no web or MCP tools exist, and the hook still runs).
PROTECTED = {"toolwiring", "maintenance_gen"}
FIX = "tools/tests/fixtures/buildalong"


def body(path, subs=None):
    lines = open(os.path.join(ROOT, path)).read().split("\n")
    text = "\n".join(lines[4:]).strip()
    for k, v in (subs or {}).items():
        text = text.replace(k, v)
    return text


def tmpcopy():
    d = tempfile.mkdtemp(prefix="w1j0y_ba_")
    shutil.copytree(ROOT, d + "/r", ignore=shutil.ignore_patterns(".git", "__pycache__", ".state"))
    return d + "/r"


def sh(cwd, cmd, env=None):
    return subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, env=env)


def run_claude(cwd, prompt, turns=25, mode="acceptEdits"):
    env = {k: v for k, v in os.environ.items() if not k.startswith(("ANTHROPIC_", "CLAUDE_CODE_", "CLAUDECODE"))}
    env["PATH"] = "/usr/bin:/bin"
    cmd = [CLAUDE, "-p", prompt, "--permission-mode", mode, "--allowedTools", *ALLOW, "--disallowedTools", *DENY,
           "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}', "--no-session-persistence",
           "--max-turns", str(turns), "--output-format", "json"]
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env, timeout=1500)
    try:
        j = json.loads(r.stdout)
    except Exception:
        j = {"raw": r.stdout[-300:], "err": r.stderr[-300:]}
    return j


def wiring(cwd):
    r = sh(cwd, "python3 tools/wiring_check.py")
    return r.returncode == 0, r.stdout[-400:]


def exists(cwd, *paths):
    return all(os.path.exists(os.path.join(cwd, p)) for p in paths)


def tests_ok(cwd):
    r = sh(cwd, "python3 -B -m unittest discover -s tools/tests 2>&1 | tail -3")
    return "OK" in r.stdout and "FAILED" not in r.stdout


# case: (deletions, prompt, acceptance(cwd)->(ok, note))
def cases():
    c = {}
    c["knowledge"] = ([], body("knowledge/_GENERATE_KNOWLEDGE.md", {"[the resource: a path or a link]": FIX + "/resource/cors_basics.md", "[name]": "cors_basics"}),
        lambda d: (exists(d, "knowledge/cors_basics.md") and wiring(d)[0] and "cors_basics" in open(d + "/knowledge/INDEX.md").read(), wiring(d)[1]))
    c["phases"] = (["prompts/web/WEB_LOOP.md", "prompts/web/01-triage.md", "prompts/web/02-characterize.md", "prompts/web/02_5-map-classes.md", "prompts/web/03-test.md"],
        body("prompts/web/_GENERATE_PHASES.md", {"[list with one line each]": "01-triage (rank surfaces, create ledger), 02-characterize (workflow walk and input inventory), 02_5-map-classes (map evidence to knowledge files, with a trigger table), 03-test (baseline, control, variant, read-back)", "[phase]": "the phase file name"}),
        lambda d: (exists(d, "prompts/web/WEB_LOOP.md", "prompts/web/01-triage.md", "prompts/web/03-test.md") and wiring(d)[0], wiring(d)[1]))
    c["reference"] = ([], body("prompts/reference/_GENERATE_REFERENCE.md", {"[name]": "rate_rules", "[one-sentence purpose]": "how to apply the program's rate limit and header to every request"}),
        lambda d: (exists(d, "prompts/reference/rate_rules.md") and wiring(d)[0], wiring(d)[1]))
    c["gate"] = (["tools/ledger_gate.py"], body("tools/_GENERATE_GATE.md"), lambda d: (exists(d, "tools/ledger_gate.py") and tests_ok(d), ""))
    c["recon"] = (["tools/recon.py"], body("tools/_GENERATE_RECON.md", {"[target]": "example-program", "[list of passive tools, one line each: what it finds, how it takes a header and a rate]": "subfinder (passive subdomains, no header, no rate), httpx (live probe, takes -H header and -rate-limit), gau (archive urls, --threads)"}), lambda d: (exists(d, "tools/recon.py") and tests_ok(d), ""))
    c["organize"] = ([], "", lambda d: (sh(d, "python3 tools/validate_scope.py --help").returncode in (0, 2) and exists(d, "targets/example-program/scope.json", "targets/example-program/guidelines.json", "targets/example-program/README.md"), ""))
    c["organizer"] = ([], body("scripts/_GENERATE_ORGANIZER.md", {"[harness and its non-interactive command]": "Codex CLI, codex exec", "[harness]": "codex"}),
        lambda d: (exists(d, "scripts/organize_scope_codex.sh") and wiring(d)[0], wiring(d)[1]))
    c["agents"] = (["AGENTS.md"], body("prompts/setup/_GENERATE_AGENTS.md", {"[path or pasted text]": "README.md and prompts/web/WEB_LOOP.md in this repo"}),
        lambda d: (exists(d, "AGENTS.md") and wiring(d)[0], wiring(d)[1]))
    c["frontdoor"] = (["README.md", "GETTING_STARTED.md"], body("prompts/setup/_GENERATE_FRONTDOOR.md", {"[one paragraph]": "A teaching repo that shows how to organize an AI agent workflow with rules, knowledge, phases, gates and memory."}),
        lambda d: (exists(d, "README.md", "GETTING_STARTED.md") and wiring(d)[0], wiring(d)[1]))
    c["toolwiring"] = ([".mcp.json.example"] if False else [], body("prompts/setup/_GENERATE_TOOL_WIRING.md"),
        lambda d: (exists(d, ".mcp.json") and wiring(d)[0], wiring(d)[1]))
    c["maintenance_gen"] = ([], body("prompts/maintenance/_GENERATE_MAINTENANCE.md", {"[pass name]": "Release notes pass", "[one-sentence purpose and cadence]": "check that STRUCTURE.md rows match the disk before each release", "[NAME]": "RELEASE", "[name]": "release"}),
        lambda d: (exists(d, "prompts/maintenance/RELEASE.md", ".claude/commands/release.md") and wiring(d)[0], wiring(d)[1]))
    c["skill_gen"] = ([], body("memory/_GENERATE_SKILL.md", {"[stream]": "learnings", "[N]": "2"}),
        lambda d: (len([f for f in os.listdir(d + "/memory/playbook/_deltas") if f.endswith(".md")]) >= 1, ""))
    c["intake_good"] = ([], "Read prompts/intake/INTAKE_TOOL.md and follow it for the tool in " + FIX + "/intake_good. Run all three stages. The decision file goes in docs/decisions/.",
        lambda d: (len([f for f in os.listdir(d + "/docs/decisions") if f.endswith(".md")]) >= 1 and wiring(d)[0], wiring(d)[1]))
    c["intake_bad"] = ([], "Read prompts/intake/INTAKE_TOOL.md and follow it for the tool in " + FIX + "/intake_bad. Run all three stages. The decision file goes in docs/decisions/.",
        lambda d: (any(re.search(r"\bNOT\b", open(d + "/docs/decisions/" + f).read()) for f in os.listdir(d + "/docs/decisions") if f.endswith(".md")) and not exists(d, "tools/fast_scan.py"), ""))
    c["audit"] = (["knowledge/baseline_and_differential.md"], "Read prompts/maintenance/AUDIT.md and follow it. Write the findings to docs/audits/test-run.md. Proposals only: do not edit any other file. Stop after writing the findings.",
        lambda d: (exists(d, "docs/audits/test-run.md") and "baseline_and_differential" in open(d + "/docs/audits/test-run.md").read(), ""))
    c["maintenance"] = ([], "Read prompts/maintenance/MAINTENANCE.md and follow it, but write only the playbook delta file (output 4) under memory/playbook/_deltas/. Do not apply it.",
        lambda d: (len([f for f in os.listdir(d + "/memory/playbook/_deltas") if f.endswith(".md")]) >= 1, ""))
    c["phase01"] = ([], "Act as the Phase 01 subagent: read prompts/web/01-triage.md and follow it for target example-program using the recon data under recon_output/example-program. First run python3 tools/ledger_gate.py snapshot --target example-program --phase 01. Update the ledger, end with a ROUTING line, then run python3 tools/ledger_gate.py check --target example-program --phase 01 and report the output.",
        lambda d: (sh(d, "python3 tools/ledger_gate.py check --target example-program --phase 01").returncode in (0, 2), ""))
    return c


def digest_case():
    d = tmpcopy()
    env = {k: v for k, v in os.environ.items() if not k.startswith(("ANTHROPIC_", "CLAUDE_CODE_", "CLAUDECODE"))}
    env.update(PATH="/usr/bin:/bin", CLAUDE_BIN=CLAUDE)
    shutil.copy(os.path.join(ROOT, FIX, "inbox_sample.md"), d + "/memory/_inbox/20260103-0900-example-program-cycle.md")
    size = lambda: sum(os.path.getsize(os.path.join(d, "memory/streams", f)) for f in os.listdir(d + "/memory/streams"))
    b = size()
    r = subprocess.run("bash tools/digest_inbox.sh", shell=True, cwd=d, capture_output=True, text=True, env=env)
    ok1 = size() > b and not os.listdir(d + "/memory/_inbox") or size() > b and os.listdir(d + "/memory/_inbox") == [".gitkeep"]
    shutil.copy(os.path.join(ROOT, FIX, "inbox_sample.md"), d + "/memory/_inbox/20260103-1000-example-program-cycle.md")
    r2 = subprocess.run("bash tools/digest_inbox.sh", shell=True, cwd=d, capture_output=True, text=True, env=dict(env, DIGEST_MODEL="not-a-model"))
    ok2 = r2.returncode != 0 and any(f.endswith(".md") for f in os.listdir(d + "/memory/_inbox"))
    return {"ok": bool(ok1 and ok2), "note": "grew=%s stays_on_failure=%s" % (ok1, ok2), "workdir": d}


def main():
    os.makedirs(OUT, exist_ok=True)
    allc = cases()
    names = sys.argv[1:] or list(allc)
    assert not shutil.which("subfinder", path="/usr/bin:/bin") and not shutil.which("httpx", path="/usr/bin:/bin")
    for n in names:
        if n == "digest":
            res = dict(case="digest", **digest_case()); json.dump(res, open(f"{OUT}/digest.json", "w"), indent=1); print("digest", "PASS" if res["ok"] else "FAIL", res["note"]); continue
        dele, prompt, acc = allc[n]
        d = tmpcopy()
        for p in dele:
            os.remove(os.path.join(d, p))
        t = time.time()
        if n == "organize":
            r = sh(d, "bash scripts/organize_scope_claude.sh targets/example-program/scope_raw.txt", env={k: v for k, v in os.environ.items() if not k.startswith(("ANTHROPIC_", "CLAUDE_CODE_", "CLAUDECODE"))})
            j = {"result": r.stdout[-300:] + r.stderr[-300:]}
        else:
            j = run_claude(d, prompt, mode="bypassPermissions" if n in PROTECTED else "acceptEdits")
        ok, note = acc(d)
        res = {"case": n, "ok": bool(ok), "note": note, "turns": j.get("num_turns"), "secs": round(time.time() - t), "workdir": d, "result_tail": str(j.get("result", j))[-300:]}
        json.dump(res, open(f"{OUT}/{n}.json", "w"), indent=1)
        print(n, "PASS" if ok else "FAIL", res["turns"], res["secs"], flush=True)


if __name__ == "__main__":
    main()
