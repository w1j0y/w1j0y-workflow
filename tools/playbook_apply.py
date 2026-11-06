#!/usr/bin/env python3
# What: Applies an approved delta file (ADD, REFINE, RETIRE) to the playbook skill files, enforcing budgets and evidence, and rebuilds the playbook index.
# Who writes: the repo author.
# Who reads: the human runs it after approving a delta; the maintenance prompt names it as the only way to change the playbook.
# Wired into: memory/playbook/INDEX.md, memory/playbook/object_reference.md, memory/playbook/spa_catch_all.md, tools/_TEMPLATE_GATE.md (one-way: same refusal style)
"""Apply a playbook delta.

Delta file format (markdown):

  ## ADD [class_file_stem]
  ### PB-[CLASS]-[NNN] [title]
  - Applies when: ...
  - Do: ...
  - Avoid: ...
  - Evidence: [path]; [path]
  - Confidence: low|medium|high
  - Last validated: YYYY-MM-DD
  - Status: provisional|active|contested|retired

  ## REFINE PB-[CLASS]-[NNN]
  - Do: replacement text for any field named here

  ## RETIRE PB-[CLASS]-[NNN]
  - Reason: why

Everything is checked before anything is written. Exit 0 applied (or dry run clean),
2 usage or missing file, 3 refusal (nothing written).
"""

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRY_BYTES = 1200
CLASS_ENTRIES = 30
TOTAL_BYTES = 400 * 1024
FIELDS = ["Applies when", "Do", "Avoid", "Evidence", "Confidence", "Last validated", "Status"]
STATUSES = {"provisional", "active", "contested", "retired"}
CONFIDENCE = {"low", "medium", "high"}
ID_RE = re.compile(r"^PB-([A-Z0-9_]+)-(\d{3})$")
ENTRY_HEAD = re.compile(r"^### (PB-[A-Z0-9_]+-\d{3})\s+(.+?)\s*$")
FIELD_RE = re.compile(r"^- ([A-Za-z ]+): ?(.*)$")
BOX = ("What: Curated, evidence-backed entries for the {stem} class.\n"
       "Who writes: tools/playbook_apply.py, from a delta the human approved.\n"
       "Who reads: the phase prompts, after they find this class in memory/playbook/INDEX.md.\n"
       "Wired into: memory/playbook/INDEX.md, tools/playbook_apply.py\n")


class Refuse(Exception):
    pass


def parse_class_file(text):
    """(header_text, [entry dict]) where an entry has id, title, fields (ordered)."""
    header, entries, cur = [], [], None
    for line in text.splitlines():
        m = ENTRY_HEAD.match(line)
        if m:
            cur = {"id": m.group(1), "title": m.group(2), "fields": {}}
            entries.append(cur)
            continue
        if cur is None:
            header.append(line)
            continue
        fm = FIELD_RE.match(line)
        if fm:
            cur["fields"][fm.group(1).strip()] = fm.group(2).strip()
    return "\n".join(header).rstrip() + "\n", entries


def render_entry(e):
    lines = [f"### {e['id']} {e['title']}"]
    for k in FIELDS:
        if k in e["fields"]:
            lines.append(f"- {k}: {e['fields'][k]}")
    for k, v in e["fields"].items():
        if k not in FIELDS:
            lines.append(f"- {k}: {v}")
    return "\n".join(lines) + "\n"


def render_file(header, entries):
    return header.rstrip() + "\n\n" + "\n".join(render_entry(e) for e in entries)


def parse_delta(text):
    ops, cur = [], None
    for line in text.splitlines():
        m = re.match(r"^## (ADD|REFINE|RETIRE) (\S+)\s*$", line)
        if m:
            cur = {"op": m.group(1), "arg": m.group(2), "lines": []}
            ops.append(cur)
        elif cur is not None:
            cur["lines"].append(line)
    for op in ops:
        entry, fields = None, {}
        for line in op["lines"]:
            hm = ENTRY_HEAD.match(line)
            if hm:
                entry = {"id": hm.group(1), "title": hm.group(2), "fields": {}}
                continue
            fm = FIELD_RE.match(line)
            if fm:
                (entry["fields"] if entry else fields)[fm.group(1).strip()] = fm.group(2).strip()
        op["entry"], op["fields"] = entry, fields
    return ops


def evidence_paths(value):
    return [p.strip() for p in re.split(r"[;,]", value) if p.strip()]


def lint_entry(e, root, problems):
    eid = e["id"]
    if not ID_RE.match(eid):
        problems.append(f"{eid}: id must look like PB-[CLASS]-[NNN]")
    for f in FIELDS:
        if not e["fields"].get(f, "").strip():
            problems.append(f"{eid}: field '{f}' missing or empty")
    st = e["fields"].get("Status", "")
    if st and st not in STATUSES:
        problems.append(f"{eid}: Status '{st}' not in {sorted(STATUSES)}")
    cf = e["fields"].get("Confidence", "")
    if cf and cf not in CONFIDENCE:
        problems.append(f"{eid}: Confidence '{cf}' not in {sorted(CONFIDENCE)}")
    lv = e["fields"].get("Last validated", "")
    if lv and not re.match(r"^\d{4}-\d{2}-\d{2}$", lv):
        problems.append(f"{eid}: Last validated must be YYYY-MM-DD")
    ev = evidence_paths(e["fields"].get("Evidence", ""))
    if ev and not 2 <= len(ev) <= 3:
        problems.append(f"{eid}: Evidence needs 2 to 3 references, has {len(ev)}")
    for p in ev:
        if p.startswith("/") or ".." in Path(p).parts or not (root / p).is_file():
            problems.append(f"{eid}: evidence reference does not resolve on disk: {p}")
    size = len(render_entry(e).encode("utf-8"))
    if size > ENTRY_BYTES:
        problems.append(f"{eid}: entry is {size} bytes, budget is {ENTRY_BYTES}")


def build_index(files):
    out = ["# Playbook index", "",
           "What: One line per skill file and entry, so a phase can open only the matching class file.",
           "Who writes: tools/playbook_apply.py (rebuilt after every apply; do not edit).",
           "Who reads: the phase prompts, before they open any memory/playbook class file.",
           "Wired into: tools/playbook_apply.py, memory/playbook/object_reference.md, memory/playbook/spa_catch_all.md",
           ""]
    for stem in sorted(files):
        entries = files[stem][1]
        out.append(f"## memory/playbook/{stem}.md ({len(entries)} entries)")
        for e in entries:
            applies = e["fields"].get("Applies when", "")
            if len(applies) > 110:
                applies = applies[:107] + "..."
            out.append(f"- {e['id']} [{e['fields'].get('Status', '?')}] {e['title']}. Applies when: {applies}")
        out.append("")
    return "\n".join(out)


def apply(root, delta_path, dry_run, today):
    pb = root / "memory" / "playbook"
    files = {}
    for f in sorted(pb.glob("*.md")):
        if f.name == "INDEX.md" or f.name.startswith("_"):
            continue
        files[f.stem] = list(parse_class_file(f.read_text(encoding="utf-8")))
    boundary_path = pb / "_boundary.json"
    boundary = json.loads(boundary_path.read_text()) if boundary_path.is_file() else {"applied": []}
    if delta_path.name in boundary["applied"]:
        raise Refuse([f"delta {delta_path.name} was already applied"])
    ops = parse_delta(delta_path.read_text(encoding="utf-8"))
    problems, log = [], []
    if not ops:
        raise Refuse(["delta has no ADD, REFINE or RETIRE sections"])

    def find(eid):
        for stem, (_, entries) in files.items():
            for e in entries:
                if e["id"] == eid:
                    return stem, e
        return None, None

    for op in ops:
        if op["op"] == "ADD":
            stem, e = op["arg"], op["entry"]
            if not e:
                problems.append(f"ADD {stem}: no '### PB-...' entry under it")
                continue
            if not re.match(r"^[a-z0-9_]+$", stem):
                problems.append(f"ADD {stem}: class file stem must be lowercase letters, digits, underscore")
                continue
            m = ID_RE.match(e["id"])
            if m and m.group(1) != stem.upper():
                problems.append(f"{e['id']}: class part must be {stem.upper()} for file {stem}.md")
            if find(e["id"])[1]:
                problems.append(f"{e['id']}: id already exists")
            e["fields"].setdefault("Last validated", today)
            e["fields"].setdefault("Status", "provisional")
            lint_entry(e, root, problems)
            name = stem.replace("_", " ")
            files.setdefault(stem, [f"# Playbook: {name}\n\n" + BOX.format(stem=name), []])[1].append(e)
            log.append(f"ADD {e['id']}")
        else:
            stem, e = find(op["arg"])
            if not e:
                problems.append(f"{op['op']} {op['arg']}: no such entry")
                continue
            if op["op"] == "REFINE":
                if not op["fields"]:
                    problems.append(f"REFINE {e['id']}: no field lines")
                for k, v in op["fields"].items():
                    if k not in FIELDS:
                        problems.append(f"REFINE {e['id']}: unknown field '{k}'")
                    else:
                        e["fields"][k] = v
                e["fields"]["Last validated"] = op["fields"].get("Last validated", today)
                lint_entry(e, root, problems)
                log.append(f"REFINE {e['id']}")
            else:
                if not op["fields"].get("Reason"):
                    problems.append(f"RETIRE {e['id']}: a '- Reason:' line is required")
                e["fields"]["Status"] = "retired"
                e["fields"]["Last validated"] = today
                log.append(f"RETIRE {e['id']}")

    total = 0
    for stem, (header, entries) in files.items():
        if len(entries) > CLASS_ENTRIES:
            problems.append(f"{stem}.md would hold {len(entries)} entries, budget is {CLASS_ENTRIES}")
        total += len(render_file(header, entries).encode("utf-8"))
    if total > TOTAL_BYTES:
        problems.append(f"playbook would be {total} bytes, budget is {TOTAL_BYTES}")
    if problems:
        raise Refuse(problems)
    if dry_run:
        return log, files
    for stem, (header, entries) in files.items():
        (pb / f"{stem}.md").write_text(render_file(header, entries), encoding="utf-8")
    (pb / "INDEX.md").write_text(build_index(files), encoding="utf-8")
    boundary["applied"].append(delta_path.name)
    boundary["date"] = today
    boundary_path.write_text(json.dumps(boundary, indent=2) + "\n", encoding="utf-8")
    return log, files


def main(argv=None):
    ap = argparse.ArgumentParser(description="Apply a playbook delta.")
    ap.add_argument("delta", nargs="?", help="delta file under memory/playbook/_deltas/")
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--dry-run", action="store_true", help="check and print; write nothing")
    ap.add_argument("--rebuild-index", action="store_true", help="only rebuild INDEX.md")
    ap.add_argument("--today", default=datetime.date.today().isoformat())
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    pb = root / "memory" / "playbook"
    if not pb.is_dir():
        print(f"usage error: no playbook folder at {pb}", file=sys.stderr)
        return 2
    if args.rebuild_index:
        files = {f.stem: parse_class_file(f.read_text(encoding="utf-8"))
                 for f in sorted(pb.glob("*.md")) if f.name != "INDEX.md" and not f.name.startswith("_")}
        (pb / "INDEX.md").write_text(build_index(files), encoding="utf-8")
        print(f"rebuilt {pb / 'INDEX.md'}")
        return 0
    if not args.delta:
        print("usage error: give a delta file (or --rebuild-index)", file=sys.stderr)
        return 2
    delta = Path(args.delta)
    if not delta.is_file():
        print(f"usage error: delta not found: {delta}", file=sys.stderr)
        return 2
    try:
        log, _ = apply(root, delta, args.dry_run, args.today)
    except Refuse as exc:
        probs = exc.args[0]
        print(f"APPLY FAIL: {len(probs)} problem(s), nothing written:", file=sys.stderr)
        for p in probs:
            print(f"  - {p}", file=sys.stderr)
        return 3
    print(("DRY RUN OK: " if args.dry_run else "APPLIED: ") + "; ".join(log))
    return 0


if __name__ == "__main__":
    sys.exit(main())
