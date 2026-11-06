#!/usr/bin/env python3
# What: Regex scanner that finds secret-like strings in a path or in git-staged files and prints file, line and kind, never the value.
# Who writes: the repo author; the pattern list is shared with tools/redact.py.
# Who reads: tools/closeout.sh at closeout, the human before publishing, tools/tests/test_redact.py
# Wired into: tools/closeout.sh, tools/redact.py, tools/tests/test_redact.py
"""Usage:
  python3 tools/secret_scan.py PATH [PATH ...]     scan files or folders
  python3 tools/secret_scan.py --staged [--root R] scan the staged version of changed files
Exit 0 clean, 2 usage, 3 at least one hit. Output lines: file:line: kind.
Skips .git, __pycache__, files over 1 MB and binary files.
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import redact  # noqa: E402

SKIP_DIRS = {".git", "__pycache__", ".state", "node_modules"}
MAX_BYTES = 1000000
OK_EMAIL_SUFFIXES = (".test", ".invalid", ".example", "example.com", "example.org", "example.net",
                     "localhost", "noreply.github.com")
HEADER_KINDS = {"cookie", "authorization", "token-header"}
BLOB_OK = re.compile(r"^[a-z0-9_./-]+$")


def line_kinds(line):
    hits = []
    for kind, rx, _ in redact.KINDS:
        m = rx.search(line)
        if not m:
            continue
        if kind in HEADER_KINDS:
            value = m.group(2).strip()
            if not value or value.startswith("[") or value.startswith("$") or "[REDACTED]" in value:
                continue
        if kind == "email":
            domain = m.group(0).rsplit("@", 1)[1].lower()
            if domain.endswith(OK_EMAIL_SUFFIXES):
                continue
        if kind == "long-blob":
            tok = m.group(0)
            if re.search(r"https?://\S*" + re.escape(tok[:20]), line):
                continue
            if BLOB_OK.match(tok) or "/" in tok and "=" not in tok and not re.search(r"\d", tok):
                continue
        hits.append(kind)
    return hits


def scan_text(label, text):
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        for kind in line_kinds(line):
            out.append((label, n, kind))
    return out


def scan_path(path):
    out = []
    if os.path.isdir(path):
        for dp, dns, fns in os.walk(path):
            dns[:] = [d for d in dns if d not in SKIP_DIRS]
            for fn in sorted(fns):
                out += scan_path(os.path.join(dp, fn))
        return out
    try:
        if os.path.getsize(path) > MAX_BYTES:
            return out
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return out
    if b"\x00" in data:
        return out
    return scan_text(path, data.decode("utf-8", "replace"))


def scan_staged(root):
    out = []
    try:
        names = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                               cwd=root, capture_output=True, text=True, check=True).stdout.splitlines()
    except (OSError, subprocess.CalledProcessError) as e:
        print("cannot read staged files: %s" % e, file=sys.stderr)
        return None
    for name in names:
        r = subprocess.run(["git", "show", ":" + name], cwd=root, capture_output=True)
        if r.returncode != 0 or b"\x00" in r.stdout or len(r.stdout) > MAX_BYTES:
            continue
        out += scan_text(name, r.stdout.decode("utf-8", "replace"))
    return out


def main(argv):
    args = list(argv)
    root = os.getcwd()
    if "--root" in args:
        i = args.index("--root")
        if i + 1 >= len(args):
            print("--root needs a value", file=sys.stderr)
            return 2
        root = args[i + 1]
        del args[i:i + 2]
    if not args:
        print(__doc__.strip().split("\n\n")[0], file=sys.stderr)
        return 2
    if args == ["--staged"]:
        hits = scan_staged(root)
        if hits is None:
            return 2
    elif any(a.startswith("--") for a in args):
        print("unknown option", file=sys.stderr)
        return 2
    else:
        hits = []
        for a in args:
            if not os.path.exists(a):
                print("no such path: %s" % a, file=sys.stderr)
                return 2
            hits += scan_path(a)
    for label, n, kind in hits:
        print("%s:%d: %s" % (label, n, kind))
    if hits:
        print("SECRET SCAN FAIL: %d hit(s); values are not printed" % len(hits), file=sys.stderr)
        return 3
    print("SECRET SCAN OK: no hits")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
