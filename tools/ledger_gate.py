#!/usr/bin/env python3
# What: Gate that snapshots the coverage ledger before a phase and refuses to advance when touched rows are incomplete.
# Who writes: the repo author; regenerate from tools/_TEMPLATE_GATE.md and your own schema.
# Who reads: the orchestrator in prompts/web/WEB_LOOP.md, the human, and tools/tests/test_ledger_gate.py.
# Wired into: prompts/web/WEB_LOOP.md, prompts/reference/ledger_schema.md, tools/tests/test_ledger_gate.py
"""Usage:
  python3 tools/ledger_gate.py snapshot|check|packet --target T --phase P [--root R]
  python3 tools/ledger_gate.py submittable --target T --report-dir D [--root R]

Rules come from the json block in prompts/reference/ledger_schema.md, read at
run time. Nothing about columns, statuses or phases is hard-coded here.
Exit 0 pass, 2 usage or missing file, 3 refusal (text on stderr).
"""
import argparse
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import meta  # noqa: E402
import scope_check  # noqa: E402

SCHEMA_REL = os.path.join("prompts", "reference", "ledger_schema.md")
TARGET_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class Usage(Exception):
    pass


def die(msg, code=2):
    print(msg, file=sys.stderr)
    sys.exit(code)


def load_schema(root):
    path = os.path.join(root, SCHEMA_REL)
    if not os.path.isfile(path):
        raise Usage("schema not found: %s" % SCHEMA_REL)
    with open(path, encoding="utf-8") as f:
        try:
            schema = meta.fenced_json(f.read())
        except ValueError as e:
            raise Usage("schema json block is not valid JSON: %s" % e)
    if not isinstance(schema, dict) or "blocks" not in schema:
        raise Usage("schema has no fenced json block with blocks")
    return schema


def split_row(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def parse_ledger(text):
    """Return {heading: {"header": [...], "rows": [dict]}}."""
    sections = {}
    cur = None
    for line in text.splitlines():
        if line.startswith("## "):
            cur = line[3:].strip()
            sections[cur] = {"header": None, "rows": []}
            continue
        if cur is None or not line.strip().startswith("|"):
            continue
        cells = split_row(line)
        sec = sections[cur]
        if sec["header"] is None:
            sec["header"] = [c.lower() for c in cells]
            continue
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c) and any(cells):
            continue
        if not any(cells):
            continue
        cells += [""] * (len(sec["header"]) - len(cells))
        sec["rows"].append(dict(zip(sec["header"], cells)))
    return sections


def ledger_path(root, target):
    return os.path.join(root, "recon_output", target, "coverage_ledger.md")


def finding_files(root, target):
    d = os.path.join(root, "recon_output", target)
    out = {}
    if os.path.isdir(d):
        pre = "%s_finding_" % target
        for name in sorted(os.listdir(d)):
            if name.startswith(pre) and name.endswith(".md"):
                with open(os.path.join(d, name), "rb") as f:
                    out[name] = hashlib.sha256(f.read()).hexdigest()
    return out


def snapshot_path(root, target, phase):
    return os.path.join(root, ".state", "ledger_snapshot_%s_%s.json" % (target, phase))


def rows_by_id(sections, schema):
    out = {}
    for block in schema["blocks"]:
        sec = sections.get(block)
        out[block] = {}
        if sec:
            for r in sec["rows"]:
                out[block][r.get("id", "")] = r
    return out


def read_ledger(root, target):
    p = ledger_path(root, target)
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8") as f:
        return parse_ledger(f.read())


def cmd_snapshot(root, target, phase, schema):
    sections = read_ledger(root, target)
    if sections is None:
        if phase != schema["phases"][0]:
            raise Usage("no ledger for target '%s' (only phase %s may start without one)" % (target, schema["phases"][0]))
        rows = {b: {} for b in schema["blocks"]}
        note = "empty ledger (bootstrap)"
    else:
        rows = rows_by_id(sections, schema)
        note = "%d row(s)" % sum(len(v) for v in rows.values())
    snap = {"rows": rows, "findings": finding_files(root, target)}
    p = snapshot_path(root, target, phase)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(snap, f, indent=1, sort_keys=True)
    print("SNAPSHOT: phase %s for target '%s' -- %s" % (phase, target, note))
    return 0


def vocab_for(block, schema):
    return block.get("handoff_statuses") or schema.get("statuses", [])


def validate_row(name, block, row, phase, schema, problems):
    rid = row.get("id", "") or "(no id)"
    label = "%s row %s" % (name, rid)
    required = []
    if "required_by_phase" in block:
        required = list(block["required_by_phase"].get(phase, []))
    required += [c for c in block.get("required", []) if c not in required]
    scol = block.get("status_column")
    if scol and scol not in required:
        required.append(scol)
    if "id" not in required:
        required.insert(0, "id")
    for col in required:
        if not row.get(col, "").strip():
            problems.append("%s: column '%s' is blank" % (label, col))
    if scol:
        val = row.get(scol, "").strip()
        if val and val not in vocab_for(block, schema):
            problems.append("%s: %s '%s' is not in the vocabulary" % (label, scol, val))
    if "verdicts" in block:
        val = row.get("verdict", "").strip()
        if val and val not in block["verdicts"]:
            problems.append("%s: verdict '%s' is not in the vocabulary" % (label, val))


def cmd_check(root, target, phase, schema):
    sections = read_ledger(root, target)
    if sections is None:
        raise Usage("ledger not found: recon_output/%s/coverage_ledger.md" % target)
    sp = snapshot_path(root, target, phase)
    if not os.path.isfile(sp):
        raise Usage("no snapshot for phase %s (run snapshot first)" % phase)
    with open(sp, encoding="utf-8") as f:
        snap = json.load(f)
    problems = []
    checked = 0
    for name, block in schema["blocks"].items():
        sec = sections.get(name)
        if sec is None:
            problems.append("block '%s': heading '## %s' is missing" % (name, name))
            continue
        missing = [c for c in block.get("columns", []) if c not in (sec["header"] or [])]
        if missing:
            problems.append("block '%s': header lacks column(s) %s" % (name, ", ".join(missing)))
        seen = set()
        old_rows = snap["rows"].get(name, {})
        for row in sec["rows"]:
            rid = row.get("id", "")
            if rid and rid in seen:
                problems.append("%s row %s: duplicate id" % (name, rid))
            seen.add(rid)
            if old_rows.get(rid) == row:
                continue
            checked += 1
            validate_row(name, block, row, phase, schema, problems)
    fv_name = None
    fv_block = None
    for name, block in schema["blocks"].items():
        if "verdicts" in block:
            fv_name, fv_block = name, block
    old_f = snap.get("findings", {})
    for fname, digest in finding_files(root, target).items():
        if old_f.get(fname) == digest:
            continue
        checked += 1
        rows = sections.get(fv_name, {"rows": []})["rows"] if fv_name else []
        hit = [r for r in rows if fname in r.get("finding_file", "")]
        ok = [r for r in hit if r.get("verdict", "").strip() in (fv_block or {}).get("verdicts", [])]
        if not ok:
            problems.append("finding file %s changed this cycle and has no Finding Validation row with a verdict" % fname)
    if problems:
        print("GATE FAIL: phase %s for target '%s' -- %d row(s) incomplete:" % (phase, target, len(problems)), file=sys.stderr)
        for p in problems:
            print("  - %s" % p, file=sys.stderr)
        return 3
    os.remove(sp)
    print("GATE PASS: phase %s for target '%s' -- %d row(s) checked" % (phase, target, checked))
    return 0


def cmd_packet(root, target, phase, schema):
    sections = read_ledger(root, target)
    if sections is None:
        raise Usage("ledger not found: recon_output/%s/coverage_ledger.md" % target)
    cap = int(schema.get("packet_row_cap", 60))
    body = []
    shown = total = 0
    for name, block in schema["blocks"].items():
        scol = block.get("status_column")
        sec = sections.get(name)
        if not scol or not sec:
            continue
        open_set = block.get("open_statuses") or schema.get("open_statuses") or []
        rows = [r for r in sec["rows"] if r.get(scol, "").strip() in open_set]
        total += len(rows)
        cols = block.get("columns", sec["header"])
        body.append("## %s" % name)
        body.append("| " + " | ".join(cols) + " |")
        body.append("|" + "|".join("---" for _ in cols) + "|")
        for r in rows[:cap]:
            body.append("| " + " | ".join(r.get(c, "") for c in cols) + " |")
        shown += min(len(rows), cap)
    print("PACKET: phase %s for target '%s' -- %d of %d open row(s), cap %d per table" % (phase, target, shown, total, cap))
    print("\n".join(body))
    return 0


def cmd_submittable(root, target, report_dir, schema):
    rd = report_dir if os.path.isabs(report_dir) else (
        report_dir if os.path.isdir(report_dir) else os.path.join(root, report_dir))
    report = os.path.join(rd, "REPORT.md")
    if not os.path.isfile(report):
        raise Usage("report not found: %s" % report)
    sections = read_ledger(root, target)
    if sections is None:
        raise Usage("ledger not found: recon_output/%s/coverage_ledger.md" % target)
    problems = []
    fv_name, fv_block = None, None
    for name, block in schema["blocks"].items():
        if "ready_verdict" in block:
            fv_name, fv_block = name, block
    if fv_block is None:
        raise Usage("schema has no block with a ready_verdict")
    rows = sections.get(fv_name, {"rows": []})["rows"]
    if not any(r.get("verdict", "").strip() == fv_block["ready_verdict"] for r in rows):
        problems.append("no Finding Validation row has verdict %s" % fv_block["ready_verdict"])
    # The AI-use rule comes from the target's own scope file, never from session state, so a report
    # cannot pass just because the entry gate has not run in this checkout.
    sp = scope_check.scope_file(root, target)
    if not os.path.isfile(sp):
        problems.append("scope file missing: targets/%s/scope.json (cannot tell whether AI disclosure is required)" % target)
    else:
        try:
            with open(sp, encoding="utf-8") as f:
                scope = json.load(f)
        except ValueError:
            scope = None
            problems.append("scope file is not valid JSON: targets/%s/scope.json" % target)
        if isinstance(scope, dict):
            status = ((scope.get("rules") or {}).get("ai_use") or {}).get("status")
            if status in ("prohibited", "restricted"):
                problems.append("program ai_use rule is %s: do not submit" % status)
            elif status == "disclosure_required":
                with open(report, encoding="utf-8") as f:
                    if not any(ln.startswith("AI disclosure:") for ln in f.read().splitlines()):
                        problems.append("program requires AI disclosure: REPORT.md has no line starting 'AI disclosure:'")
            elif status not in ("allowed", "unspecified"):
                problems.append("scope file has no ai_use rule status (allowed, disclosure_required, restricted, prohibited or unspecified)")
    if problems:
        print("GATE FAIL: submittable for target '%s' -- %d row(s) incomplete:" % (target, len(problems)), file=sys.stderr)
        for p in problems:
            print("  - %s" % p, file=sys.stderr)
        return 3
    print("GATE PASS: submittable for target '%s' -- report %s" % (target, os.path.relpath(report, root)))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ledger_gate.py", description="Coverage ledger gate.")
    ap.add_argument("command", choices=["snapshot", "check", "packet", "submittable"])
    ap.add_argument("--target", required=True)
    ap.add_argument("--phase")
    ap.add_argument("--report-dir")
    ap.add_argument("--root", default=meta.repo_root())
    args = ap.parse_args(argv)
    try:
        if not TARGET_RE.match(args.target):
            raise Usage("bad target name")
        root = os.path.abspath(args.root)
        schema = load_schema(root)
        if args.command == "submittable":
            if not args.report_dir:
                raise Usage("submittable needs --report-dir")
            return cmd_submittable(root, args.target, args.report_dir, schema)
        if not args.phase:
            raise Usage("%s needs --phase" % args.command)
        if args.phase not in schema.get("phases", []):
            raise Usage("phase '%s' is not in the schema (%s)" % (args.phase, ", ".join(schema.get("phases", []))))
        fn = {"snapshot": cmd_snapshot, "check": cmd_check, "packet": cmd_packet}[args.command]
        return fn(root, args.target, args.phase, schema)
    except Usage as e:
        print("USAGE/MISSING: %s" % e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
