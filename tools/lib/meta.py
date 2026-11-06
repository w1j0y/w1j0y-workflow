# What: Shared helpers: the meta-file rule, the four-line box parser and the repo root finder.
# Who writes: the repo author; regenerate from tools/_TEMPLATE_GATE.md if the box labels change.
# Who reads: tools/wiring_check.py, tools/knowledge_index.py, tools/ledger_gate.py, tools/tests/test_wiring_check.py
# Wired into: tools/wiring_check.py, tools/knowledge_index.py
"""Meta files: any path component that starts with one underscore (not a double
underscore such as __init__.py or __pycache__) marks a file as meta. Meta files
are for building the repo (templates, generators, runtime folders), never content.
"""
import json
import os
import re

BOX_LABELS = ("What", "Who writes", "Who reads", "Wired into")
_BOX_RE = re.compile(r"^\s*(?:#\s*)?(What|Who writes|Who reads|Wired into):\s*(.*?)\s*$")


def is_meta(path):
    """True if any component of the path starts with a single underscore."""
    parts = str(path).replace("\\", "/").split("/")
    for p in parts:
        if p.startswith("_") and not p.startswith("__"):
            return True
    return False


def parse_box(text, max_lines=12):
    """Return {label: value} for the four-line box found in the first lines."""
    found = {}
    for line in text.splitlines()[:max_lines]:
        m = _BOX_RE.match(line)
        if m and m.group(1) not in found:
            found[m.group(1)] = m.group(2)
    return found


def repo_root():
    """The repository root: the parent of the tools directory."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(here))


def fenced_json(text):
    """Parse the first fenced json block in a markdown text; None if absent."""
    m = re.search(r"```json\s*\n(.*?)\n```", text, re.S)
    if not m:
        return None
    return json.loads(m.group(1))
