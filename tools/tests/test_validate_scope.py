# What: Tests for tools/validate_scope.py: the good fixture passes and each rules-block mistake is refused.
# Who writes: the repo author.
# Who reads: tools/tests/run.sh and the human.
# Wired into: tools/validate_scope.py (one-way: reference only), tools/tests/fixtures/scope_good/scope.json (one-way: reference only)
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "tools" / "validate_scope.py"
GOOD = ROOT / "tools" / "tests" / "fixtures" / "scope_good"


class ValidateScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.dir = self.base / "scope_good"
        shutil.copytree(GOOD, self.dir)

    def tearDown(self):
        self.tmp.cleanup()

    def validate(self):
        return subprocess.run([sys.executable, "-B", str(VALIDATOR), "--raw-scope", str(self.dir / "scope_raw.txt"),
                               "--repo-root", str(self.base)], capture_output=True, text=True)

    def mutate(self, fn):
        path = self.dir / "scope.json"
        data = json.loads(path.read_text())
        fn(data)
        path.write_text(json.dumps(data, indent=2))
        return self.validate()

    def test_good_passes(self):
        p = self.validate()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("RESULT: PASS", p.stdout)

    def test_missing_raw_is_usage_error(self):
        p = subprocess.run([sys.executable, "-B", str(VALIDATOR), "--raw-scope", str(self.base / "none.txt")],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)

    def test_quote_not_in_raw_fails(self):
        p = self.mutate(lambda d: d["rules"]["automation"].update(source_text="Robots are welcome."))
        self.assertEqual(p.returncode, 1)
        self.assertIn("not verbatim", p.stderr)

    def test_rate_without_unit_fails(self):
        p = self.mutate(lambda d: d["rules"]["rate_limit"].pop("unit"))
        self.assertEqual(p.returncode, 1)
        self.assertIn("unit", p.stderr)

    def test_rate_bad_unit_fails(self):
        p = self.mutate(lambda d: d["rules"]["rate_limit"].update(unit="per_fortnight"))
        self.assertEqual(p.returncode, 1)

    def test_unspecified_must_be_listed_as_absent(self):
        def f(d):
            d["rules"]["ai_use"] = {"status": "unspecified", "source_text": ""}
        p = self.mutate(f)
        self.assertEqual(p.returncode, 1)
        self.assertIn("absent_in_source", p.stderr)

        def g(d):
            f(d)
            d["absent_in_source"] = ["rules.ai_use"]
        self.assertNotIn("absent_in_source", self.mutate(g).stderr)

    def test_bad_status_fails(self):
        p = self.mutate(lambda d: d["rules"]["ai_use"].update(status="maybe"))
        self.assertEqual(p.returncode, 1)

    def test_rules_block_missing_fails(self):
        p = self.mutate(lambda d: d.pop("rules"))
        self.assertEqual(p.returncode, 1)

    def test_confirmed_must_be_boolean(self):
        p = self.mutate(lambda d: d["rules"].update(confirmed_by_human="yes"))
        self.assertEqual(p.returncode, 1)

    def test_header_disagreement_fails(self):
        p = self.mutate(lambda d: d["rules"]["identification_header"].update(value="tester-b"))
        self.assertEqual(p.returncode, 1)
        self.assertIn("disagrees", p.stderr)

    def test_out_of_scope_host_as_recon_target_fails(self):
        p = self.mutate(lambda d: d["recon_targets"]["domains"].append("payments.example-shop.test"))
        self.assertEqual(p.returncode, 1)
        self.assertIn("oos-in-recon", p.stderr)

    def test_asset_missing_from_json_fails(self):
        p = self.mutate(lambda d: d["out_of_scope"].update(domains=[]))
        self.assertEqual(p.returncode, 1)

    def test_stale_output_files_refused(self):
        p = subprocess.run([sys.executable, "-B", str(VALIDATOR), "--raw-scope", str(self.dir / "scope_raw.txt"),
                            "--repo-root", str(self.base), "--require-fresh-since-ns", str(2 ** 62)],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 1)
        self.assertIn("stale", p.stderr)


if __name__ == "__main__":
    unittest.main()
