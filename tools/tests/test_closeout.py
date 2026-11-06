# What: Tests for tools/closeout.sh in a throwaway git repo: it commits clean coverage paths, refuses a secret, and never pushes.
# Who writes: the repo author.
# Who reads: tools/tests/run.sh and the human.
# Wired into: tools/closeout.sh (one-way: reference only), tools/secret_scan.py (one-way: reference only)
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class CloseoutTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        (self.repo / "tools").mkdir(parents=True)
        for name in ("closeout.sh", "secret_scan.py", "redact.py"):
            shutil.copy(ROOT / "tools" / name, self.repo / "tools" / name)
        self.git("init", "-q")
        self.git("config", "user.name", "tester-a")
        self.git("config", "user.email", "tester-a@example-shop.test")
        (self.repo / "README.md").write_text("start\n")
        self.git("add", "README.md")
        self.git("commit", "-q", "-m", "start")
        (self.repo / "reports" / "ex").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, capture_output=True, text=True)

    def closeout(self, *args):
        return subprocess.run(["bash", str(self.repo / "tools" / "closeout.sh"), "--target", "ex", *args],
                              cwd=self.repo, capture_output=True, text=True)

    def test_commits_clean_files_only_in_coverage_paths(self):
        (self.repo / "reports" / "ex" / "REPORT.md").write_text("clean text\n")
        (self.repo / "unrelated.txt").write_text("not covered\n")
        p = self.closeout()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("Not pushed", p.stdout)
        shown = self.git("show", "--name-only", "--format=%s", "HEAD").stdout
        self.assertIn("reports/ex/REPORT.md", shown)
        self.assertNotIn("unrelated.txt", shown)

    def test_refuses_secret_and_unstages(self):
        fake = "AKIA" + "ABCDEFGHIJKLMNOP"
        (self.repo / "reports" / "ex" / "leak.md").write_text(f"aws_access_key_id = {fake}\n")
        before = self.git("rev-parse", "HEAD").stdout
        p = self.closeout()
        self.assertEqual(p.returncode, 3, p.stdout + p.stderr)
        self.assertEqual(before, self.git("rev-parse", "HEAD").stdout)
        self.assertEqual(self.git("diff", "--cached", "--name-only").stdout.strip(), "")
        self.assertNotIn(fake, p.stdout + p.stderr)

    def test_dry_run_stages_nothing(self):
        (self.repo / "reports" / "ex" / "REPORT.md").write_text("clean text\n")
        p = self.closeout("--dry-run")
        self.assertEqual(p.returncode, 0)
        self.assertEqual(self.git("diff", "--cached", "--name-only").stdout.strip(), "")

    def test_bad_target_name_is_usage_error(self):
        p = subprocess.run(["bash", str(self.repo / "tools" / "closeout.sh"), "--target", "../x"],
                           cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)

    def test_script_never_pushes(self):
        text = (ROOT / "tools" / "closeout.sh").read_text()
        code = "\n".join(l for l in text.splitlines() if not l.lstrip().startswith("#"))
        self.assertNotIn("git push", code)
        self.assertNotIn("add -A", code)
        self.assertNotIn("add .", code)


if __name__ == "__main__":
    unittest.main()
