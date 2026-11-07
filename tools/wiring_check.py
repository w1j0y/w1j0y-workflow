#!/usr/bin/env python3
# What: Audits that every file is wired in: boxes, paths, two-way links, knowledge reachability, phase names, tool names and the STRUCTURE.md map.
# Who writes: the repo author; the checks live in this file only.
# Who reads: the human and the closeout step, prompts/maintenance/AUDIT.md, tools/tests/test_wiring_check.py
# Wired into: prompts/maintenance/AUDIT.md, tools/lib/meta.py, tools/tests/test_wiring_check.py
"""Usage: python3 tools/wiring_check.py [--root R] [--json]
Exit 0 when nothing is flagged, 1 otherwise. Meta files (any path part starting with
one underscore, see tools/lib/meta.py) are skipped as sources and as targets.

Checks (each finding has a check name):
  box           first 12 lines of .md/.py/.sh lack What, Who writes, Who reads or Wired into
  path-missing  a backticked repo path, or a Wired into path, does not exist
  one-way       Wired into names a file that does not mention this file (unless one-way or none)
  unreferenced  no other non-meta file mentions this file's path
  knowledge     a knowledge file is not in INDEX.md or not reachable from prompts/web
  phase         a prompts/web phase file is not named by exact path in WEB_LOOP.md
  tool-missing  a tool script path under tools (py or sh) named in a file does not exist
  tool-unnamed  a tools/*.py or tools/*.sh is named nowhere (outside tests)
  structure     a file has no STRUCTURE.md row with class B, C or U, or a row names a missing path
  meta-leak     a non-meta file refers to a meta file as content
Skipped everywhere: tools/tests/fixtures, __init__.py, .gitkeep, __pycache__, .git, .state.
Files under tools/tests are exempt from the backticked-path, unreferenced and STRUCTURE.md checks.
"""
import argparse
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import meta  # noqa: E402

TEXT_EXT = (".md", ".py", ".sh", ".json", ".txt", ".example")
BOX_EXT = (".md", ".py", ".sh")
SKIP_DIRS = {".git", ".state", "__pycache__", ".pytest_cache", "node_modules"}
KNOWN_TOP = {"tools", "prompts", "knowledge", "docs", "scripts", "targets", "recon_output", "reports",
             "non-reportable", "memory", ".claude"}
DATA_PREFIX = ("targets/", "recon_output/", "reports/", "non-reportable/", "memory/")
FRONT = {"README.md", "GETTING_STARTED.md", "STRUCTURE.md", "GLOSSARY.md", "ETHICS.md", "AGENTS.md",
         "LICENSE", ".gitignore", ".mcp.json.example", ".mcp.json"}
TOOL_RE = re.compile(r"\btools/[A-Za-z0-9_\-]+(?:/[A-Za-z0-9_\-]+)*\.(?:py|sh)\b")
TOKEN_RE = re.compile(r"^[A-Za-z0-9_.\-/]+$")
CLASS_RE = re.compile(r"^[BCU](?:\s*[,/+]\s*[BCU])*$")
ALLOWED_META_SOURCES = {"STRUCTURE.md", "prompts/README.md"}


def list_files(root):
    files = None
    if os.path.isdir(os.path.join(root, ".git")):
        try:
            out = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=root,
                                 capture_output=True, text=True, check=True).stdout
            files = [ln for ln in out.splitlines() if ln and os.path.isfile(os.path.join(root, ln))]
        except (OSError, subprocess.CalledProcessError):
            files = None
    if files is None:
        files = []
        for dp, dns, fns in os.walk(root):
            dns[:] = sorted(d for d in dns if d not in SKIP_DIRS)
            for fn in sorted(fns):
                files.append(os.path.relpath(os.path.join(dp, fn), root).replace(os.sep, "/"))
    keep = []
    for f in files:
        parts = f.split("/")
        if any(p in SKIP_DIRS for p in parts) or parts[-1] in ("__init__.py", ".gitkeep") or parts[-1].endswith(".pyc"):
            continue
        if f.startswith("tools/tests/fixtures/"):
            continue
        keep.append(f)
    return sorted(keep)


def read(root, rel):
    try:
        with open(os.path.join(root, rel), encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return ""


def path_tokens(text):
    """Backticked tokens that look like repo paths (contain a slash, known top folder)."""
    out = []
    for tok in re.findall(r"`([^`\n]+)`", text):
        tok = tok.strip()
        if not TOKEN_RE.match(tok) or "/" not in tok or tok.startswith(("/", "./", "../")) or ".." in tok:
            continue
        if tok.split("/")[0] not in KNOWN_TOP:
            continue
        out.append(tok)
    return out


def runtime_path(tok):
    parts = tok.split("/")
    return (tok.startswith((".state", "docs/decisions/", "docs/audits/")) or "evidence" in parts
            or any(p.startswith(("creds_", "cookies_")) for p in parts))


def wired_entries(box_value):
    """Split a Wired into value on top-level commas -> list of (path_or_None, one_way)."""
    entries, depth, cur = [], 0, ""
    for ch in box_value:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            entries.append(cur)
            cur = ""
        else:
            cur += ch
    entries.append(cur)
    out = []
    for e in entries:
        e = e.strip()
        if not e:
            continue
        if e.lower().startswith("none"):
            out.append((None, True))
            continue
        tok = e.split()[0].strip("`")
        out.append((tok, "(one-way" in e.lower()))
    return out


def structure_rows(text):
    rows = []
    for line in text.splitlines():
        m = re.match(r"^\s*\|\s*`([^`]+)`\s*\|(.*)$", line)
        if not m:
            continue
        cells = [c.strip().strip("`") for c in m.group(2).split("|")]
        rows.append((m.group(1), any(CLASS_RE.match(c) for c in cells)))
    return rows


def run(root):
    findings = []

    def add(check, file, detail):
        findings.append({"check": check, "file": file, "detail": detail})

    files = list_files(root)
    fileset = set(files)
    content = [f for f in files if not meta.is_meta(f) and not f.startswith(("docs/decisions/", "docs/audits/"))]  # records, not wired content
    text = {f: read(root, f) for f in content if f.endswith(TEXT_EXT) or "." not in os.path.basename(f)}
    tests = lambda f: f.startswith("tools/tests/")  # noqa: E731
    is_data = lambda f: f.startswith(DATA_PREFIX)  # noqa: E731

    # box
    for f in content:
        if f.endswith(BOX_EXT) and not meta.is_meta(f):
            box = meta.parse_box(text.get(f, ""))
            for label in meta.BOX_LABELS:
                if label not in box or not box[label]:
                    add("box", f, "missing four-line box label '%s' in the first 12 lines" % label)

    # path-missing, meta-leak, one-way
    for f in content:
        t = text.get(f)
        if t is None:
            continue
        if f.endswith((".md", ".py", ".sh", ".txt")) and not tests(f):
            for tok in path_tokens(t):
                if runtime_path(tok) or tok.endswith("/") and tok.startswith(DATA_PREFIX):
                    continue
                isdir = tok.endswith("/")
                t_clean = tok.rstrip("/")
                if meta.is_meta(tok) and not isdir and f not in ALLOWED_META_SOURCES:
                    add("meta-leak", f, "refers to meta file `%s` as content" % tok)
                if isdir:
                    if not os.path.isdir(os.path.join(root, t_clean)) and not tok.startswith(DATA_PREFIX):
                        add("path-missing", f, "folder `%s` does not exist" % tok)
                elif tok not in fileset and not os.path.isfile(os.path.join(root, tok)):
                    add("path-missing", f, "path `%s` does not exist" % tok)
        box = meta.parse_box(t) if f.endswith(BOX_EXT) else {}
        if "Wired into" in box:
            for tok, one_way in wired_entries(box["Wired into"]):
                if tok is None or runtime_path(tok):
                    continue
                full = os.path.join(root, tok.rstrip("/"))
                if not os.path.exists(full):
                    add("path-missing", f, "Wired into path `%s` does not exist" % tok)
                    continue
                if one_way or tok.endswith("/") or os.path.isdir(full):
                    continue
                if f not in read(root, tok.replace("\\", "/")):
                    add("one-way", f, "Wired into `%s` but that file does not mention `%s`" % (tok, f))

    # unreferenced
    for f in content:
        base = os.path.basename(f)
        if (tests(f) or is_data(f) or base in FRONT or base == "README.md" or f.startswith(".claude/")
                or runtime_path(f)):
            continue
        hit = any(f in t for g, t in text.items() if g != f and g != "STRUCTURE.md")
        if not hit:
            add("unreferenced", f, "no other non-meta file mentions this path")

    # knowledge
    kfiles = [f for f in content if f.startswith("knowledge/") and f.endswith(".md") and f != "knowledge/INDEX.md"]
    if kfiles:
        index = text.get("knowledge/INDEX.md")
        web = [g for g in content if g.startswith("prompts/web/")]
        if index is None:
            add("knowledge", "knowledge/INDEX.md", "missing; run python3 tools/knowledge_index.py")
        for f in kfiles:
            if index is not None and f not in index and os.path.basename(f) not in index:
                add("knowledge", f, "not listed in knowledge/INDEX.md")
            if not any(f in text.get(g, "") for g in web):
                add("knowledge", f, "not reachable from any prompts/web file or trigger row")

    # phases
    phases = [f for f in content if f.startswith("prompts/web/") and f.endswith(".md")
              and os.path.basename(f) != "WEB_LOOP.md"]
    if phases:
        loop = text.get("prompts/web/WEB_LOOP.md")
        if loop is None:
            add("phase", "prompts/web/WEB_LOOP.md", "missing but phase files exist")
        else:
            loop_body = re.sub(r"^Wired into:.*$", "", loop, count=1, flags=re.M)  # the box lists every file back, so it does not count as naming
            for f in phases:
                if f not in loop_body:
                    add("phase", f, "not named by exact path in prompts/web/WEB_LOOP.md")

    # tools
    named = {}
    for g, t in text.items():
        if tests(g):
            continue
        for m in set(TOOL_RE.findall(t)):
            named.setdefault(m, set()).add(g)
            if m not in fileset and not os.path.isfile(os.path.join(root, m)):
                add("tool-missing", g, "names `%s` which does not exist" % m)
    for f in content:
        if re.fullmatch(r"tools/[^/]+\.(py|sh)", f):
            if not any(g != f for g in named.get(f, set())):
                add("tool-unnamed", f, "is not named by any other file outside tests")

    # structure
    if "STRUCTURE.md" not in fileset:
        add("structure", "STRUCTURE.md", "missing")
    else:
        rows = structure_rows(text.get("STRUCTURE.md", ""))
        rowmap = {p: ok for p, ok in rows}
        for p, ok in rows:
            if not ok:
                add("structure", "STRUCTURE.md", "row `%s` has no class B, C or U" % p)
            if not (p in fileset or os.path.exists(os.path.join(root, p.rstrip("/")))):
                add("structure", "STRUCTURE.md", "row `%s` names a path that does not exist" % p)
        for f in content:
            if tests(f) or runtime_path(f) or f == ".mcp.json":
                continue
            covered = f in rowmap or any(p.endswith("/") and f.startswith(p) and rowmap[p] for p in rowmap)
            if not covered:
                add("structure", f, "no row with class B, C or U in STRUCTURE.md")
    return findings


def main(argv=None):
    ap = argparse.ArgumentParser(prog="wiring_check.py", description="Wiring audit.")
    ap.add_argument("--root", default=meta.repo_root())
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    root = os.path.abspath(args.root)
    findings = run(root)
    if args.json:
        print(json.dumps({"ok": not findings, "count": len(findings), "findings": findings}, indent=1))
    else:
        for x in findings:
            print("FLAG %s: %s: %s" % (x["check"], x["file"], x["detail"]))
        print("WIRING OK" if not findings else "WIRING FAIL (%d finding(s))" % len(findings))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
