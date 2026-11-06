# What: Tests for tools/playbook_apply.py: ADD, REFINE, RETIRE, budgets, evidence refs, dry run and index rebuild.
# Who writes: the repo author.
# Who reads: tools/tests/run.sh and the human.
# Wired into: tools/playbook_apply.py (one-way: reference only), memory/playbook/object_reference.md (one-way: reference only)
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "playbook_apply.py"
EV = "recon_output/example-program/coverage_ledger.md; reports/example-program/example-finding/REPORT.md"


def entry(n, cls="OBJECT_REFERENCE", ev=EV, extra=""):
    return (f"### PB-{cls}-{n:03d} Check ownership on updates\n"
            "- Applies when: a write request carries an object id.\n"
            "- Do: repeat the write with the second test account and read back from the owner.\n"
            f"- Avoid: trusting the status code.{extra}\n"
            f"- Evidence: {ev}\n"
            "- Confidence: medium\n- Last validated: 2026-01-02\n- Status: provisional\n")


class PlaybookTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for d in ("memory/playbook", "recon_output", "reports", "non-reportable"):
            shutil.copytree(ROOT / d, self.root / d)
        (self.root / "memory" / "playbook" / "INDEX.md").unlink(missing_ok=True)

    def tearDown(self):
        self.tmp.cleanup()

    def apply(self, text, *extra, name="d1.md"):
        delta = self.root / name
        delta.write_text(text)
        return subprocess.run([sys.executable, "-B", str(TOOL), str(delta), "--root", str(self.root),
                               "--today", "2026-02-02", *extra], capture_output=True, text=True)

    def cls(self, stem="object_reference"):
        return (self.root / "memory" / "playbook" / f"{stem}.md").read_text()

    def test_add_writes_entry_and_rebuilds_index(self):
        p = self.apply("## ADD object_reference\n" + entry(3))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("PB-OBJECT_REFERENCE-003", self.cls())
        index = (self.root / "memory" / "playbook" / "INDEX.md").read_text()
        self.assertIn("PB-OBJECT_REFERENCE-003", index)
        self.assertIn("PB-SPA_CATCH_ALL-001", index)

    def test_add_creates_new_class_file(self):
        p = self.apply("## ADD race_conditions\n" + entry(1, cls="RACE_CONDITIONS"))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("PB-RACE_CONDITIONS-001", self.cls("race_conditions"))

    def test_dry_run_writes_nothing(self):
        before = self.cls()
        p = self.apply("## ADD object_reference\n" + entry(3), "--dry-run")
        self.assertEqual(p.returncode, 0)
        self.assertIn("DRY RUN OK", p.stdout)
        self.assertEqual(before, self.cls())
        self.assertFalse((self.root / "memory" / "playbook" / "INDEX.md").exists())

    def test_unresolved_evidence_is_refused(self):
        p = self.apply("## ADD object_reference\n" + entry(3, ev="reports/nope.md; reports/also-nope.md"))
        self.assertEqual(p.returncode, 3)
        self.assertIn("does not resolve", p.stderr)
        self.assertNotIn("-003", self.cls())

    def test_evidence_count_is_enforced(self):
        p = self.apply("## ADD object_reference\n" + entry(3, ev="reports/example-program/example-finding/REPORT.md"))
        self.assertEqual(p.returncode, 3)
        self.assertIn("2 to 3", p.stderr)

    def test_entry_budget(self):
        p = self.apply("## ADD object_reference\n" + entry(3, extra=" " + "x" * 1300))
        self.assertEqual(p.returncode, 3)
        self.assertIn("budget", p.stderr)

    def test_class_entry_budget(self):
        text = "".join("## ADD object_reference\n" + entry(n) + "\n" for n in range(3, 40))
        p = self.apply(text)
        self.assertEqual(p.returncode, 3)
        self.assertIn("budget is 30", p.stderr)

    def test_duplicate_id_and_wrong_class_refused(self):
        self.assertEqual(self.apply("## ADD object_reference\n" + entry(1)).returncode, 3)
        self.assertEqual(self.apply("## ADD object_reference\n" + entry(5, cls="OTHER"), name="d2.md").returncode, 3)

    def test_refine_changes_field_and_validates_date(self):
        p = self.apply("## REFINE PB-OBJECT_REFERENCE-001\n- Do: compare owner field and body to a control.\n")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("compare owner field and body", self.cls())
        self.assertIn("Last validated: 2026-02-02", self.cls())

    def test_retire_needs_reason(self):
        self.assertEqual(self.apply("## RETIRE PB-OBJECT_REFERENCE-002\n").returncode, 3)
        p = self.apply("## RETIRE PB-OBJECT_REFERENCE-002\n- Reason: superseded.\n", name="d2.md")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("Status: retired", self.cls())

    def test_unknown_entry_refused_and_nothing_partial_written(self):
        before = self.cls()
        p = self.apply("## ADD object_reference\n" + entry(3) + "\n## REFINE PB-NOPE-001\n- Do: x\n")
        self.assertEqual(p.returncode, 3)
        self.assertEqual(before, self.cls())

    def test_same_delta_cannot_apply_twice(self):
        text = "## ADD object_reference\n" + entry(3)
        self.assertEqual(self.apply(text).returncode, 0)
        self.assertEqual(self.apply(text).returncode, 3)

    def test_missing_delta_is_usage_error(self):
        p = subprocess.run([sys.executable, "-B", str(TOOL), str(self.root / "none.md"), "--root", str(self.root)],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)


if __name__ == "__main__":
    unittest.main()
