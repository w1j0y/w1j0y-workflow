# What: Shared test helpers: paths, temp repo roots, a subprocess runner and the schema editor.
# Who writes: the repo author.
# Who reads: every test_*.py in tools/tests
# Wired into: none: imported by the test files
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
REPO = os.path.dirname(TOOLS)
FIX = os.path.join(HERE, "fixtures")
GOOD = os.path.join(FIX, "good")
BAD = os.path.join(FIX, "bad")
SCHEMA = os.path.join(REPO, "prompts", "reference", "ledger_schema.md")
TARGET = "example-program"


def run(script, args, stdin="", env=None, cwd=None):
    e = dict(os.environ)
    e.pop("HOOK_LOG", None)
    e.update(env or {})
    return subprocess.run([sys.executable, "-B", os.path.join(TOOLS, script)] + list(args),
                          input=stdin, capture_output=True, text=True, env=e, cwd=cwd, timeout=60)


def make_root():
    """A temp repo root holding a copy of the real schema."""
    root = tempfile.mkdtemp(prefix="w1j0y_test_")
    dst = os.path.join(root, "prompts", "reference")
    os.makedirs(dst)
    shutil.copy(SCHEMA, dst)
    return root


def put(root, rel, src):
    dst = os.path.join(root, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy(src, dst)
    return dst


def put_scope(root, src):
    return put(root, "targets/%s/scope.json" % TARGET, src)


def put_ledger(root, src):
    return put(root, "recon_output/%s/coverage_ledger.md" % TARGET, src)


def edit_schema(root, fn):
    """Parse the fenced json block of the root's schema, apply fn, write it back."""
    p = os.path.join(root, "prompts", "reference", "ledger_schema.md")
    text = read_text(p)
    m = re.search(r"(```json\s*\n)(.*?)(\n```)", text, re.S)
    data = json.loads(m.group(2))
    fn(data)
    text = text[:m.start(2)] + json.dumps(data, indent=2) + text[m.end(2):]
    write_text(p, text)


def entry_start(root, scope_src):
    put_scope(root, scope_src)
    return run("session_entry_gate.py", ["start", "--target", TARGET, "--root", root])


def read_text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write_text(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def load_json(path):
    return json.loads(read_text(path))


def cleanup(root):
    shutil.rmtree(root, ignore_errors=True)
