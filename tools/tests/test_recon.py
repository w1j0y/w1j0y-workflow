# What: Tests for tools/recon.py: refusals, dry run, fixture mode and the three scope filters, all offline.
# Who writes: the repo author.
# Who reads: tools/tests/run.sh and the human.
# Wired into: tools/recon.py (one-way: reference only), tools/scope_check.py (one-way: reference only), tools/tests/fixtures/recon_scope.json (one-way: reference only)
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECON = ROOT / "tools" / "recon.py"
FX = ROOT / "tools" / "tests" / "fixtures"
SCOPE = FX / "recon_scope.json"


def run(*args, env=None):
    e = dict(os.environ, **(env or {}))
    return subprocess.run([sys.executable, "-B", str(RECON), *args], capture_output=True, text=True, env=e)


class ReconTests(unittest.TestCase):
    def test_validate_scope_only(self):
        p = run("--scope-json", str(SCOPE), "--target-name", "t", "--validate-scope-only")
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("example-shop.test", p.stdout)

    def test_dry_run_prints_commands_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            p = run("--scope-json", str(SCOPE), "--target-name", "t", "--dry-run", "--output", d)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertIn("subfinder -d example-shop.test", p.stdout)
            self.assertIn("-rate-limit-minute 60", p.stdout)
            self.assertIn("X-Research: tester-a", p.stdout)
            self.assertEqual(list(Path(d).iterdir()), [])

    def test_refuses_rate_above_scope(self):
        p = run("--scope-json", str(SCOPE), "--target-name", "t", "--rate", "61", "--dry-run")
        self.assertEqual(p.returncode, 3)
        self.assertIn("above the scope", p.stderr)

    def test_accepts_lower_rate(self):
        p = run("--scope-json", str(SCOPE), "--target-name", "t", "--rate", "30", "--dry-run")
        self.assertEqual(p.returncode, 0)
        self.assertIn("-rate-limit-minute 30", p.stdout)

    def test_refuses_without_header_when_scope_has_none(self):
        scope = json.loads(SCOPE.read_text())
        scope["rules"]["identification_header"] = {"status": "unspecified"}
        scope["required_header"] = None
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "s.json"
            f.write_text(json.dumps(scope))
            p = run("--scope-json", str(f), "--target-name", "t", "--dry-run")
            self.assertEqual(p.returncode, 3)
            self.assertIn("no identification header", p.stderr)
            p = run("--scope-json", str(f), "--target-name", "t", "--dry-run", "--no-identifier-header")
            self.assertEqual(p.returncode, 3)  # not a localhost target
            p = run("--scope-json", str(f), "--target-name", "t", "--dry-run", "--header", "X-Research: tester-a")
            self.assertEqual(p.returncode, 0, p.stderr)

    def test_refuses_without_rate_when_scope_has_none(self):
        scope = json.loads(SCOPE.read_text())
        scope["rules"]["rate_limit"] = {"status": "unspecified"}
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "s.json"
            f.write_text(json.dumps(scope))
            self.assertEqual(run("--scope-json", str(f), "--target-name", "t", "--dry-run").returncode, 3)

    def test_live_refuses_unconfirmed_rules_before_any_tool_runs(self):
        p = run("--scope-json", str(SCOPE), "--target-name", "t")
        self.assertEqual(p.returncode, 3)
        self.assertIn("confirmed_by_human", p.stderr)

    def test_fixture_mode_filters_three_points(self):
        with tempfile.TemporaryDirectory() as d:
            p = run("--scope-json", str(SCOPE), "--target-name", "t", "--fixture", str(FX / "recon_fixture"),
                    "--output", d, env={"RECON_TS": "T1"})
            self.assertEqual(p.returncode, 0, p.stderr)
            out = Path(d) / "T1"
            hosts = (out / "subdomains.txt").read_text().split()
            self.assertIn("api.example-shop.test", hosts)
            self.assertNotIn("payments.example-shop.test", hosts)
            self.assertNotIn("admin.other-company.test", hosts)
            rows = json.loads((out / "httpx_results.json").read_text())
            urls = [r["url"] for r in rows]
            self.assertNotIn("https://payments.example-shop.test", urls)
            self.assertNotIn("https://admin.example-shop.test", urls)  # redirects out of scope
            archive = (out / "archive_urls.txt").read_text()
            self.assertIn("shop.example-shop.test/orders/101", archive)
            self.assertNotIn("evil.test", archive)
            self.assertNotIn("payments", archive)
            self.assertTrue((out / "dropped_out_of_scope.txt").read_text().strip())

    def test_resolution_filter_drops_out_of_scope_ip(self):
        scope = json.loads(SCOPE.read_text())
        scope["out_of_scope"]["cidrs"] = ["192.0.2.0/24"]
        with tempfile.TemporaryDirectory() as d:
            sf = Path(d) / "s.json"
            sf.write_text(json.dumps(scope))
            fx = Path(d) / "fx"
            fx.mkdir()
            (fx / "subdomains.txt").write_text("api.example-shop.test\nwww.example-shop.test\n")
            (fx / "resolved.json").write_text(json.dumps({"api.example-shop.test": "192.0.2.9",
                                                           "www.example-shop.test": "198.51.100.4"}))
            p = run("--scope-json", str(sf), "--target-name", "t", "--fixture", str(fx), "--output", d,
                    env={"RECON_TS": "T1"})
            self.assertEqual(p.returncode, 0, p.stderr)
            hosts = (Path(d) / "T1" / "subdomains.txt").read_text().split()
            self.assertNotIn("api.example-shop.test", hosts)
            self.assertIn("www.example-shop.test", hosts)

    def test_no_token_shapes_in_commands(self):
        p = run("--scope-json", str(SCOPE), "--target-name", "t", "--dry-run")
        self.assertIsNone(re.search(r"(?i)(token|apikey|api_key|secret|bearer)\s*[=:]", p.stdout))
        self.assertNotIn("--insecure", p.stdout)
        self.assertNotIn("sudo", p.stdout)

    def test_fixture_mode_starts_no_process(self):
        # An empty PATH and no tools/bin entry: fixture mode must still succeed.
        with tempfile.TemporaryDirectory() as d:
            p = run("--scope-json", str(SCOPE), "--target-name", "t", "--fixture", str(FX / "recon_fixture"),
                    "--output", d, env={"PATH": "/nonexistent"})
            self.assertEqual(p.returncode, 0, p.stderr)

    def test_missing_scope_is_usage_error(self):
        self.assertEqual(run("--scope-json", "/nonexistent.json", "--target-name", "t", "--dry-run").returncode, 2)


if __name__ == "__main__":
    unittest.main()
