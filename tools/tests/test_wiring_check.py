# What: Tests for tools/wiring_check.py and tools/knowledge_index.py on a tiny fixture repo, including the meta-skip rule.
# Who writes: the repo author.
# Who reads: tools/tests/run.sh and the human running python3 -B -m unittest discover -s tools/tests
# Wired into: none: found by unittest discovery
import json
import os
import shutil
import sys
import tempfile
import unittest

import helpers as h

sys.path.insert(0, h.TOOLS)
from lib import meta  # noqa: E402

MINI = os.path.join(h.GOOD, "wiring_repo")


def checks(root):
    r = h.run("wiring_check.py", ["--root", root, "--json"])
    data = json.loads(r.stdout)
    return r.returncode, data, {f["check"] for f in data["findings"]}


class MetaRuleTests(unittest.TestCase):
    def test_is_meta(self):
        for p in ("knowledge/_TEMPLATE_KNOWLEDGE.md", "_inbox/x.md", "memory/_processed/a.md", "tools/_GENERATE_GATE.md"):
            self.assertTrue(meta.is_meta(p), p)
        for p in ("knowledge/idor.md", "tools/lib/__init__.py", "tools/__pycache__/x.pyc", "README.md"):
            self.assertFalse(meta.is_meta(p), p)

    def test_parse_box(self):
        b = meta.parse_box("# T\nWhat: a\nWho writes: b\nWho reads: c\nWired into: d, e\n")
        self.assertEqual(b, {"What": "a", "Who writes": "b", "Who reads": "c", "Wired into": "d, e"})
        b = meta.parse_box("#!/usr/bin/env python3\n# What: a\n# Who writes: b\n# Who reads: c\n# Wired into: none: x\n")
        self.assertEqual(len(b), 4)


class WiringTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="w1j0y_wire_")
        shutil.rmtree(self.root)
        shutil.copytree(MINI, self.root)
        self.addCleanup(h.cleanup, self.root)

    def w(self, rel, text, mode="w"):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, mode) as f:
            f.write(text)

    def sub(self, rel, old, new):
        p = os.path.join(self.root, rel)
        with open(p) as f:
            t = f.read()
        self.assertIn(old, t)
        with open(p, "w") as f:
            f.write(t.replace(old, new))

    def test_good_repo_passes_text_and_json(self):
        code, data, found = checks(self.root)
        self.assertEqual((code, found), (0, set()), data)
        r = h.run("wiring_check.py", ["--root", self.root])
        self.assertEqual(r.returncode, 0)
        self.assertIn("WIRING OK", r.stdout)

    def test_meta_files_are_skipped(self):
        self.w("knowledge/_BROKEN.md", "no box, `tools/nope.py`, `prompts/web/nothing.md`\n")
        self.w("tools/_scratch.py", "print(1)\n")
        self.w("prompts/web/_GENERATE_X.md", "mentions `knowledge/idor.md`\n")
        code, data, found = checks(self.root)
        self.assertEqual((code, found), (0, set()), data)

    def test_each_break_is_flagged(self):
        def break_missing_box():
            self.w("prompts/web/01-triage.md", "# Phase\nConsult `knowledge/INDEX.md` and `knowledge/idor.md`.\n")
        def break_phase_unnamed():
            self.sub("prompts/web/WEB_LOOP.md", "`prompts/web/01-triage.md`", "the triage file")
        def break_phase_named_only_in_box():
            self.sub("prompts/web/WEB_LOOP.md", "Wired into: ", "Wired into: prompts/web/01-triage.md, ")
            self.sub("prompts/web/WEB_LOOP.md", "`prompts/web/01-triage.md`", "the triage file")
        def break_path_missing():
            self.sub("prompts/web/WEB_LOOP.md", "Run `tools/a.py`", "Run `tools/a.py` and `docs/nowhere.md`")
        def break_tool_missing():
            self.sub("prompts/web/WEB_LOOP.md", "Run `tools/a.py`", "Run `tools/a.py` and `tools/ghost.py`")
        def break_one_way():
            self.sub("tools/a.py", "# Wired into: prompts/web/WEB_LOOP.md", "# Wired into: README.md")
        def break_structure():
            self.sub("STRUCTURE.md", "| `tools/a.py` | B | helper |\n", "")
        def break_structure_class():
            self.sub("STRUCTURE.md", "| `tools/a.py` | B | helper |", "| `tools/a.py` | helper |")
        def break_meta_leak():
            self.sub("prompts/web/01-triage.md", "Consult", "See `prompts/web/_TEMPLATE_PHASE.md`. Consult")
        def break_index():
            self.sub("knowledge/INDEX.md", "`knowledge/idor.md`", "`knowledge/other-name`")
            self.sub("knowledge/INDEX.md", "How to test", "How to test")
        def break_unreachable():
            self.sub("prompts/web/01-triage.md", "and, for object references, `knowledge/idor.md`", "")
        def break_unreferenced():
            self.w("docs/loose.md", "# Loose\nWhat: x\nWho writes: y\nWho reads: z\nWired into: none: test\n")
        def break_tool_unnamed():
            self.w("tools/b.py", "# What: x\n# Who writes: y\n# Who reads: z\n# Wired into: none: test\n")
        cases = [
            (break_missing_box, "box"), (break_phase_unnamed, "phase"), (break_phase_named_only_in_box, "phase"), (break_path_missing, "path-missing"),
            (break_tool_missing, "tool-missing"), (break_one_way, "one-way"), (break_structure, "structure"),
            (break_structure_class, "structure"), (break_meta_leak, "meta-leak"), (break_index, "knowledge"),
            (break_unreachable, "knowledge"), (break_unreferenced, "unreferenced"), (break_tool_unnamed, "tool-unnamed"),
        ]
        for fn, expected in cases:
            with self.subTest(fn.__name__):
                shutil.rmtree(self.root)
                shutil.copytree(MINI, self.root)
                fn()
                code, data, found = checks(self.root)
                self.assertEqual(code, 1, data)
                self.assertIn(expected, found)
                r = h.run("wiring_check.py", ["--root", self.root])
                self.assertEqual(r.returncode, 1)
                self.assertIn("WIRING FAIL", r.stdout)

    def test_one_way_marker_and_none_are_accepted(self):
        self.sub("tools/a.py", "# Wired into: prompts/web/WEB_LOOP.md", "# Wired into: README.md (one-way: front door only)")
        code, data, found = checks(self.root)
        self.assertEqual((code, found), (0, set()), data)
        self.sub("tools/a.py", "# Wired into: README.md (one-way: front door only)", "# Wired into: none: nothing links here")
        code, data, found = checks(self.root)
        self.assertEqual((code, found), (0, set()), data)

    def test_missing_structure_file(self):
        os.remove(os.path.join(self.root, "STRUCTURE.md"))
        self.assertIn("structure", checks(self.root)[2])


class KnowledgeIndexTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="w1j0y_kidx_")
        shutil.rmtree(self.root)
        shutil.copytree(MINI, self.root)
        self.addCleanup(h.cleanup, self.root)

    def test_index_lists_what_lines_and_skips_meta(self):
        with open(os.path.join(self.root, "knowledge", "_TEMPLATE_X.md"), "w") as f:
            f.write("What: should never appear\n")
        os.makedirs(os.path.join(self.root, "knowledge", "_inbox"))
        with open(os.path.join(self.root, "knowledge", "_inbox", "note.md"), "w") as f:
            f.write("What: also never\n")
        with open(os.path.join(self.root, "knowledge", "spa.md"), "w") as f:
            f.write("# SPA\nWhat: A catch-all 200 is not a finding.\nWho writes: a\nWho reads: b\nWired into: none: t\n")
        r = h.run("knowledge_index.py", ["--root", self.root])
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(os.path.join(self.root, "knowledge", "INDEX.md")) as f:
            text = f.read()
        self.assertIn("`knowledge/spa.md`: A catch-all 200 is not a finding.", text)
        self.assertIn("`knowledge/idor.md`", text)
        self.assertNotIn("never", text)
        self.assertNotIn("_TEMPLATE", text)
        self.assertEqual(h.run("knowledge_index.py", ["--root", self.root, "--check"]).returncode, 0)

    def test_check_detects_stale_and_missing_what(self):
        with open(os.path.join(self.root, "knowledge", "late.md"), "w") as f:
            f.write("# Late\nno what line here\n")
        self.assertEqual(h.run("knowledge_index.py", ["--root", self.root, "--check"]).returncode, 1)
        r = h.run("knowledge_index.py", ["--root", self.root])
        self.assertEqual(r.returncode, 1)
        self.assertIn("MISSING What line", r.stderr)

    def test_no_knowledge_folder_is_usage(self):
        empty = tempfile.mkdtemp(prefix="w1j0y_kidx_")
        self.addCleanup(h.cleanup, empty)
        self.assertEqual(h.run("knowledge_index.py", ["--root", empty]).returncode, 2)


if __name__ == "__main__":
    unittest.main()
