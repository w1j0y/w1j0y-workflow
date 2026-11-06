#!/usr/bin/env python3
# What: Generates knowledge/INDEX.md from the What line of every knowledge file, skipping meta files.
# Who writes: the repo author; INDEX.md is its output and is never edited by hand.
# Who reads: the human and every phase file (INDEX.md is the first consult step), tools/wiring_check.py, tools/tests/test_wiring_check.py
# Wired into: knowledge/INDEX.md, tools/wiring_check.py, tools/tests/test_wiring_check.py
"""Usage: python3 tools/knowledge_index.py [--root R] [--check]

Writes knowledge/INDEX.md. With --check it only compares and exits 1 if the file
on disk is stale. A knowledge file with no What line is listed as missing and
makes the exit code 1. Files whose path has an underscore-prefixed part are meta
(see tools/lib/meta.py) and are skipped, as is INDEX.md itself.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import meta  # noqa: E402

HEAD = """# Knowledge index
What: Generated list of every knowledge file with its one-sentence summary.
Who writes: tools/knowledge_index.py (generated, do not edit by hand).
Who reads: every phase file as its first consult step, and the wiring audit.
Wired into: tools/knowledge_index.py

Open at most the files whose line matches the surface you are testing.
Rebuild after any change: python3 tools/knowledge_index.py

"""


def build(root):
    kdir = os.path.join(root, "knowledge")
    lines, missing = [], []
    for dp, dns, fns in os.walk(kdir):
        dns[:] = sorted(d for d in dns if not meta.is_meta(d))
        for fn in sorted(fns):
            if not fn.endswith(".md") or meta.is_meta(fn) or fn == "INDEX.md" and dp == kdir:
                continue
            rel = os.path.relpath(os.path.join(dp, fn), root).replace(os.sep, "/")
            with open(os.path.join(dp, fn), encoding="utf-8") as f:
                what = meta.parse_box(f.read()).get("What", "")
            if not what:
                missing.append(rel)
                what = "(missing What line)"
            lines.append("- `%s`: %s" % (rel, what))
    lines.sort()
    return HEAD + "\n".join(lines) + ("\n" if lines else ""), missing


def main(argv=None):
    ap = argparse.ArgumentParser(prog="knowledge_index.py", description="Generate knowledge/INDEX.md.")
    ap.add_argument("--root", default=meta.repo_root())
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    root = os.path.abspath(args.root)
    if not os.path.isdir(os.path.join(root, "knowledge")):
        print("no knowledge folder under %s" % root, file=sys.stderr)
        return 2
    text, missing = build(root)
    path = os.path.join(root, "knowledge", "INDEX.md")
    for m in missing:
        print("MISSING What line: %s" % m, file=sys.stderr)
    if args.check:
        cur = open(path, encoding="utf-8").read() if os.path.isfile(path) else None
        if cur != text:
            print("knowledge/INDEX.md is stale", file=sys.stderr)
            return 1
        return 1 if missing else 0
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("wrote knowledge/INDEX.md (%d file(s))" % text.count("\n- `"))
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
