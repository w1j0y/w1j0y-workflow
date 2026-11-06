# What: Tests for scripts/organize_scope_claude.sh with a fake claude: flags, refusals and post-run checks.
# Who writes: the repo author.
# Who reads: tools/tests/run.sh and the human.
# Wired into: scripts/organize_scope_claude.sh (one-way: reference only), scripts/lib/organize_scope_common.sh (one-way: reference only), tools/validate_scope.py (one-way: reference only)
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FX = ROOT / "tools" / "tests" / "fixtures"


class OrganizeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        (self.repo / "scripts" / "lib").mkdir(parents=True)
        (self.repo / "tools").mkdir()
        (self.repo / "prompts").mkdir()
        for rel in ("scripts/organize_scope_claude.sh", "scripts/lib/organize_scope_common.sh",
                    "tools/validate_scope.py"):
            shutil.copy(ROOT / rel, self.repo / rel)
        (self.repo / "prompts" / "organize_scope.md").write_text("Organize the scope.\n")
        self.target = self.repo / "targets" / "ex"
        self.target.mkdir(parents=True)
        shutil.copy(FX / "scope_good" / "scope_raw.txt", self.target / "scope_raw.txt")
        self.args_file = Path(self.tmp.name) / "args.txt"

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self, raw=None, mode="ok", claude=None):
        env = dict(os.environ, CLAUDE_BIN=claude or str(FX / "fake_claude_organize.sh"),
                   FAKE_ARGS_FILE=str(self.args_file), FAKE_FIXTURE=str(FX / "scope_good"), FAKE_MODE=mode)
        return subprocess.run(["bash", str(self.repo / "scripts" / "organize_scope_claude.sh"),
                               str(raw or self.target / "scope_raw.txt")],
                              capture_output=True, text=True, env=env, cwd=self.tmp.name)

    def test_success_and_flags(self):
        p = self.run_script()
        self.assertEqual(p.returncode, 0, p.stderr)
        args = self.args_file.read_text().split("\n")
        self.assertNotIn("--dangerously-skip-permissions", args)
        self.assertIn("--permission-mode", args)
        self.assertIn("acceptEdits", args)
        self.assertIn("--allowedTools", args)
        self.assertIn("--disallowedTools", args)
        for denied in ("WebFetch", "WebSearch", "mcp__*"):
            self.assertIn(denied, args)
        allowed = [a for a in args if a.startswith("Edit(")]
        self.assertEqual(len(allowed), 1)
        self.assertTrue(all(str(self.target) in a for a in allowed))

    def test_refuses_path_outside_targets(self):
        other = Path(self.tmp.name) / "elsewhere"
        other.mkdir()
        (other / "scope_raw.txt").write_text("hello\n")
        p = self.run_script(raw=other / "scope_raw.txt")
        self.assertEqual(p.returncode, 1)
        self.assertIn("REFUSED", p.stderr)
        self.assertFalse(self.args_file.exists())

    def test_refuses_wrong_file_name(self):
        (self.target / "notes.txt").write_text("hello\n")
        self.assertEqual(self.run_script(raw=self.target / "notes.txt").returncode, 1)

    def test_agent_failure_propagates(self):
        p = self.run_script(mode="fail")
        self.assertEqual(p.returncode, 1)
        self.assertIn("NOT complete", p.stderr)

    def test_raw_file_modified_is_refused(self):
        p = self.run_script(mode="tamper")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("raw scope file was modified", p.stderr)

    def test_extra_file_is_refused(self):
        p = self.run_script(mode="extra")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("unexpected new files", p.stderr)

    def test_no_outputs_fails_validation(self):
        p = self.run_script(mode="nowrite")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("missing output file", p.stderr)

    def test_stale_outputs_are_refused(self):
        self.run_script()
        old = 1_000_000_000
        for f in self.target.iterdir():
            if f.name != "scope_raw.txt":
                os.utime(f, (old, old))
        p = self.run_script(mode="nowrite")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("stale mtime", p.stderr)

    def test_missing_claude_binary(self):
        p = self.run_script(claude="no-such-claude-binary")
        self.assertEqual(p.returncode, 1)
        self.assertIn("missing", p.stderr)


if __name__ == "__main__":
    unittest.main()
