#!/usr/bin/env python3
# What: Deterministic extract of ledger rows and target-note lines changed since the last consolidation into one inbox file; no model, no network.
# Who writes: the repo author.
# Who reads: the orchestrator runs it at the end of a cycle; tools/digest_inbox.sh later reads the file it writes.
# Wired into: tools/digest_inbox.sh, recon_output/example-program/coverage_ledger.md, memory/_inbox/.gitkeep (one-way: reference only)
"""Usage: python3 tools/ledger_to_inbox.py --target T [--update-state] [--root DIR]

Writes memory/_inbox/[timestamp]-[target]-extract.md holding every Surfaces, Phase handoff
and Finding Validation row that is new or changed since the state file, plus lines added to
target_notes.md. With --update-state it then records the current rows in
recon_output/[target]/.last_consolidated.json. Without it, nothing but the inbox file is written.
Exit 0 ok (including nothing to extract), 2 usage or missing ledger.
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOCKS = ["Surfaces", "Phase handoff", "Finding Validation"]


def parse_ledger(text):
    """{block: {row_id: (cells, columns)}} from the markdown tables under '## Block' headings."""
    out, block, cols = {}, None, None
    for line in text.splitlines():
        h = re.match(r"^##\s+(.+?)\s*$", line)
        if h:
            block, cols = h.group(1), None
            out.setdefault(block, {})
            continue
        if block is None or not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cols is None:
            cols = [c.lower() for c in cells]
            continue
        if all(re.fullmatch(r":?-{3,}:?", c) for c in cells if c):
            continue
        if cells and cells[0]:
            out[block][cells[0]] = (cells, cols)
    return out


def row_hash(cells):
    return hashlib.sha256("|".join(cells).encode("utf-8")).hexdigest()[:16]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Extract changed ledger rows into the memory inbox.")
    ap.add_argument("--target", required=True)
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--update-state", action="store_true")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    tdir = root / "recon_output" / args.target
    ledger = tdir / "coverage_ledger.md"
    if not ledger.is_file():
        print(f"usage error: no ledger at {ledger}", file=sys.stderr)
        return 2
    state_path = tdir / ".last_consolidated.json"
    state = {"rows": {}, "notes_lines": 0}
    if state_path.is_file():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"usage error: {state_path} is not valid JSON", file=sys.stderr)
            return 2

    tables = parse_ledger(ledger.read_text(encoding="utf-8"))
    current = {b: {rid: row_hash(c) for rid, (c, _) in rows.items()} for b, rows in tables.items()}
    sections = []
    for block in BLOCKS:
        changed = [rid for rid, h in current.get(block, {}).items()
                   if state["rows"].get(block, {}).get(rid) != h]
        if not changed:
            continue
        cols = next(iter(tables[block].values()))[1]
        lines = [f"### {block}", "", "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
        for rid in changed:
            lines.append("| " + " | ".join(tables[block][rid][0]) + " |")
        sections.append("\n".join(lines))

    notes_path = tdir / "target_notes.md"
    note_lines = notes_path.read_text(encoding="utf-8").splitlines() if notes_path.is_file() else []
    new_notes = [l for l in note_lines[state.get("notes_lines", 0):] if l.strip()]
    if state.get("notes_lines", 0) > len(note_lines):
        new_notes = [l for l in note_lines if l.strip()]
    if new_notes:
        sections.append("### Target notes added\n\n" + "\n".join(new_notes))

    if not sections:
        print(f"nothing changed for {args.target} since the last consolidation")
        return 0

    ts = os.environ.get("LEDGER_INBOX_TS") or datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    inbox = root / "memory" / "_inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    out = inbox / f"{ts}-{args.target}-extract.md"
    out.write_text(f"# Extract: {args.target} ({ts})\n\n"
                   f"Deterministic extract of ledger rows and notes changed since the last consolidation. "
                   f"No model was used.\n\n" + "\n\n".join(sections) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(root)}")

    if args.update_state:
        state_path.write_text(json.dumps({
            "updated": datetime.datetime.now().isoformat(timespec="seconds"),
            "rows": current, "notes_lines": len(note_lines)}, indent=2) + "\n", encoding="utf-8")
        print(f"updated {state_path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
