# What: Tests for tools/ledger_to_inbox.py: extract only changed rows, notes delta, state update.
# Who writes: the repo author.
# Who reads: tools/tests/run.sh and the human.
# Wired into: tools/ledger_to_inbox.py (one-way: reference only), recon_output/example-program/coverage_ledger.md (one-way: reference only)
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "ledger_to_inbox.py"


class LedgerToInboxTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.tdir = self.root / "recon_output" / "example-program"
        self.tdir.mkdir(parents=True)
        for f in ("coverage_ledger.md", "target_notes.md"):
            shutil.copy(ROOT / "recon_output" / "example-program" / f, self.tdir / f)

    def tearDown(self):
        self.tmp.cleanup()

    def run_tool(self, ts, *extra):
        return subprocess.run([sys.executable, "-B", str(TOOL), "--target", "example-program",
                               "--root", str(self.root), *extra],
                              capture_output=True, text=True, env=dict(os.environ, LEDGER_INBOX_TS=ts))

    def inbox(self):
        return sorted((self.root / "memory" / "_inbox").glob("*.md"))

    def test_first_run_extracts_everything(self):
        p = self.run_tool("t1")
        self.assertEqual(p.returncode, 0, p.stderr)
        text = self.inbox()[0].read_text()
        self.assertIn("S-001", text)
        self.assertIn("FV-001", text)
        self.assertIn("Target notes added", text)
        self.assertFalse((self.tdir / ".last_consolidated.json").exists())

    def test_state_makes_second_run_empty(self):
        self.run_tool("t1", "--update-state")
        self.assertTrue((self.tdir / ".last_consolidated.json").is_file())
        p = self.run_tool("t2")
        self.assertIn("nothing changed", p.stdout)
        self.assertEqual(len(self.inbox()), 1)

    def test_only_changed_row_and_new_note_are_extracted(self):
        self.run_tool("t1", "--update-state")
        ledger = self.tdir / "coverage_ledger.md"
        ledger.write_text(ledger.read_text().replace("| S-004 | api.example-shop.test | object reference | untested |",
                                                     "| S-004 | api.example-shop.test | object reference | no-signal |"))
        with open(self.tdir / "target_notes.md", "a") as fh:
            fh.write("- 2026-01-02 api returns 401 without a session.\n")
        self.run_tool("t2")
        text = self.inbox()[-1].read_text()
        self.assertIn("S-004", text)
        self.assertNotIn("S-001", text)
        self.assertIn("api returns 401", text)
        self.assertNotIn("catch-all", text)

    def test_missing_ledger_is_usage_error(self):
        (self.tdir / "coverage_ledger.md").unlink()
        self.assertEqual(self.run_tool("t1").returncode, 2)


if __name__ == "__main__":
    unittest.main()
