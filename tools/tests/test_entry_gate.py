# What: Tests for tools/scope_check.py and tools/session_entry_gate.py.
# Who writes: the repo author.
# Who reads: tools/tests/run.sh and the human running python3 -B -m unittest discover -s tools/tests
# Wired into: none: found by unittest discovery
import json
import os
import sys
import unittest

import helpers as h

sys.path.insert(0, h.TOOLS)
import scope_check  # noqa: E402

SCOPE = h.load_json(os.path.join(h.GOOD, "scope_confirmed.json"))


class ConfirmTests(unittest.TestCase):
    def test_confirm_changes_exactly_one_line(self):
        root = h.make_root()
        self.addCleanup(h.cleanup, root)
        dst = h.put_scope(root, os.path.join(h.BAD, "scope_unconfirmed.json"))
        before = h.read_text(dst).splitlines()
        r = h.run("scope_check.py", ["confirm", "--target", h.TARGET, "--root", root], stdin="y\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        after = h.read_text(dst).splitlines()
        self.assertEqual(len(before), len(after))
        self.assertEqual([i for i, (a, b) in enumerate(zip(before, after)) if a != b].__len__(), 1)
        self.assertTrue(h.load_json(dst)["rules"]["confirmed_by_human"])


class ScopeLibraryTests(unittest.TestCase):
    def test_in_scope(self):
        for host in ("shop.example-shop.test", "api.example-shop.test", "example-shop.test",
                     "https://shop.example-shop.test/path?x=1", "a.b.example-shop.test:8443", "SHOP.Example-Shop.test."):
            with self.subTest(host):
                self.assertTrue(scope_check.host_in_scope(host, SCOPE))

    def test_out_of_scope(self):
        for host in ("evil.test", "example-shop.test.evil.test", "notexample-shop.test", "admin.example-shop.test",
                     "https://allowed.test@evil.test/", "https://shop.example-shop.test@evil.test/",
                     "https://evil.test\\@shop.example-shop.test/", "", "http://%73hop.example-shop.test/", "127.0.0.1"):
            with self.subTest(host):
                self.assertFalse(scope_check.host_in_scope(host, SCOPE))

    def test_wildcard_does_not_match_apex(self):
        s = {"recon_targets": {"wildcards": ["*.only.test"]}}
        self.assertTrue(scope_check.host_in_scope("a.only.test", s))
        self.assertFalse(scope_check.host_in_scope("only.test", s))

    def test_cidr_and_ports(self):
        s = {"recon_targets": {"cidrs": ["10.1.0.0/24"]}}
        self.assertTrue(scope_check.host_in_scope("10.1.0.9", s))
        self.assertFalse(scope_check.host_in_scope("10.2.0.9", s))
        active = {"hosts": ["shop.example-shop.test"], "wildcards": [], "ports": [443]}
        self.assertTrue(scope_check.host_in_scope("shop.example-shop.test", active, port=443))
        self.assertFalse(scope_check.host_in_scope("shop.example-shop.test", active, port=8080))

    def test_active_shape(self):
        a = scope_check.build_active(SCOPE, "targets/example-program/scope.json")
        self.assertIn("shop.example-shop.test", a["hosts"])
        self.assertEqual(a["wildcards"], ["*.example-shop.test"])
        self.assertTrue(scope_check.host_in_scope("x.example-shop.test", a))
        self.assertFalse(scope_check.host_in_scope("admin.example-shop.test", a))


class ScopeCliTests(unittest.TestCase):
    def setUp(self):
        self.root = h.make_root()
        self.addCleanup(h.cleanup, self.root)

    def test_usage_without_args(self):
        self.assertEqual(h.run("scope_check.py", []).returncode, 2)

    def test_check_exit_codes(self):
        h.put_scope(self.root, os.path.join(h.GOOD, "scope_confirmed.json"))
        base = ["check", "--target", h.TARGET, "--root", self.root, "--host"]
        self.assertEqual(h.run("scope_check.py", base + ["shop.example-shop.test"]).returncode, 0)
        self.assertEqual(h.run("scope_check.py", base + ["evil.test"]).returncode, 1)
        self.assertEqual(h.run("scope_check.py", ["check", "--target", h.TARGET, "--root", self.root]).returncode, 2)

    def test_confirm_yes_and_no(self):
        dst = h.put_scope(self.root, os.path.join(h.BAD, "scope_unconfirmed.json"))
        args = ["confirm", "--target", h.TARGET, "--root", self.root]
        r = h.run("scope_check.py", args, stdin="n\n")
        self.assertEqual(r.returncode, 1)
        self.assertFalse(h.load_json(dst)["rules"]["confirmed_by_human"])
        r = h.run("scope_check.py", args, stdin="y\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("No more than 60 requests per minute.", r.stdout)
        self.assertTrue(h.load_json(dst)["rules"]["confirmed_by_human"])


class EntryGateTests(unittest.TestCase):
    def setUp(self):
        self.root = h.make_root()
        self.addCleanup(h.cleanup, self.root)

    def test_usage_without_args(self):
        self.assertEqual(h.run("session_entry_gate.py", []).returncode, 2)

    def test_good_scope_passes_and_writes_state(self):
        r = h.entry_start(self.root, os.path.join(h.GOOD, "scope_confirmed.json"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("NOTE: automation is limited", r.stdout)
        active = h.load_json(os.path.join(self.root, ".state", "active_target.json"))
        self.assertEqual(active["target"], h.TARGET)
        self.assertEqual(active["header"], {"name": "X-Research-Id", "value": "tester-a"})
        self.assertEqual(active["rate"], {"value": 60, "unit": "per_minute"})
        self.assertIn("rules", active)
        self.assertIn("started", active)

    def test_disclosure_scope_passes_with_note(self):
        r = h.entry_start(self.root, os.path.join(h.GOOD, "scope_disclosure.json"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("AI disclosure", r.stdout)

    def test_bad_scopes_are_refused(self):
        cases = {"scope_unconfirmed.json": "not confirmed", "scope_ai_prohibited.json": "ai_use",
                 "scope_automation_prohibited.json": "prohibits automation", "scope_no_header.json": "header"}
        for name, needle in cases.items():
            with self.subTest(name):
                root = h.make_root()
                self.addCleanup(h.cleanup, root)
                r = h.entry_start(root, os.path.join(h.BAD, name))
                self.assertEqual(r.returncode, 3, r.stdout)
                self.assertIn("ENTRY GATE FAIL (", r.stderr)
                self.assertIn("problem(s))", r.stderr)
                self.assertIn(needle, r.stderr)
                self.assertFalse(os.path.exists(os.path.join(root, ".state", "active_target.json")))

    def test_missing_scope_is_refused(self):
        r = h.run("session_entry_gate.py", ["start", "--target", h.TARGET, "--root", self.root])
        self.assertEqual(r.returncode, 3)
        self.assertIn("ENTRY GATE FAIL (1 problem(s))", r.stderr)

    def test_rule_missing_is_refused(self):
        d = h.load_json(os.path.join(h.GOOD, "scope_confirmed.json"))
        del d["rules"]["ai_use"]
        p = os.path.join(self.root, "s.json")
        h.write_text(p, json.dumps(d))
        r = h.entry_start(self.root, p)
        self.assertEqual(r.returncode, 3)
        self.assertIn("ai_use", r.stderr)

    def test_fixture_quote_is_not_in_raw_text(self):
        d = h.load_json(os.path.join(h.BAD, "scope_quote_not_in_raw.json"))
        raw = h.read_text(os.path.join(h.BAD, "scope_quote_not_in_raw_raw.txt"))
        self.assertNotIn(d["rules"]["rate_limit"]["source_text"], raw)
        good = h.load_json(os.path.join(h.GOOD, "scope_confirmed.json"))
        self.assertIn(good["rules"]["rate_limit"]["source_text"], h.read_text(os.path.join(h.GOOD, "scope_raw.txt")))


if __name__ == "__main__":
    unittest.main()
