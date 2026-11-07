# What: Meta tests: flipping a good fixture to its bad twin must make the gates exit 3 (hooks exit 2), so a check that cannot fail is caught.
# Who writes: the repo author.
# Who reads: tools/tests/run.sh and the human running python3 -B -m unittest discover -s tools/tests
# Wired into: none: found by unittest discovery
import os
import unittest

import helpers as h

# (good file, bad twin) pairs for the ledger gate and the entry gate.
LEDGER_PAIRS = [(os.path.join(h.GOOD, "ledger_complete.md"), os.path.join(h.BAD, n)) for n in (
    "ledger_blank_status.md", "ledger_unknown_status.md", "ledger_handoff_no_status.md", "ledger_finding_no_verdict.md")]
SCOPE_PAIRS = [(os.path.join(h.GOOD, "scope_confirmed.json"), os.path.join(h.BAD, n)) for n in (
    "scope_unconfirmed.json", "scope_ai_prohibited.json", "scope_automation_prohibited.json", "scope_no_header.json")]
HOOK_PAIRS = [("burp_send_ok.json", n) for n in (
    "burp_send_out_of_scope.json", "burp_send_no_header.json", "burp_send_userinfo_trick.json")] + [
    ("chrome_navigate_ok.json", "chrome_navigate_off_scope.json")]


class FlipGoodToBadTests(unittest.TestCase):
    def ledger_exit(self, ledger):
        root = h.make_root()
        self.addCleanup(h.cleanup, root)
        base = ["--target", h.TARGET, "--root", root, "--phase", "01"]
        self.assertEqual(h.run("ledger_gate.py", ["snapshot"] + base).returncode, 0)
        h.put_ledger(root, ledger)
        h.put(root, "recon_output/%s/%s_finding_item_read.md" % (h.TARGET, h.TARGET),
              os.path.join(h.GOOD, "example-program_finding_item_read.md"))
        return h.run("ledger_gate.py", ["check"] + base).returncode

    def test_ledger_flip(self):
        for good, bad in LEDGER_PAIRS:
            with self.subTest(os.path.basename(bad)):
                self.assertEqual(self.ledger_exit(good), 0)
                self.assertEqual(self.ledger_exit(bad), 3)

    def test_entry_flip(self):
        for good, bad in SCOPE_PAIRS:
            with self.subTest(os.path.basename(bad)):
                root = h.make_root()
                self.addCleanup(h.cleanup, root)
                self.assertEqual(h.entry_start(root, good).returncode, 0)
                root2 = h.make_root()
                self.addCleanup(h.cleanup, root2)
                self.assertEqual(h.entry_start(root2, bad).returncode, 3)

    def test_hook_flip(self):
        for good, bad in HOOK_PAIRS:
            with self.subTest(bad):
                root = h.make_root()
                self.addCleanup(h.cleanup, root)
                self.assertEqual(h.entry_start(root, os.path.join(h.GOOD, "scope_confirmed.json")).returncode, 0)
                g = h.run("mcp_scope_hook.py", ["--root", root], stdin=h.read_text(os.path.join(h.GOOD, "hook", good)))
                b = h.run("mcp_scope_hook.py", ["--root", root], stdin=h.read_text(os.path.join(h.BAD, "hook", bad)))
                self.assertEqual(g.returncode, 0, g.stderr)
                self.assertEqual(b.returncode, 2, b.stdout)

    def test_every_bad_fixture_is_used_by_a_test(self):
        """Guard: a bad fixture nobody reads proves nothing."""
        here = os.path.dirname(os.path.abspath(__file__))
        blob = ""
        for fn in os.listdir(here):
            if fn.startswith("test_") and fn.endswith(".py") and fn != "test_meta.py":
                blob += h.read_text(os.path.join(here, fn))
        blob += h.read_text(os.path.join(here, "test_meta.py"))
        for dp, _, fns in os.walk(h.BAD):
            for fn in fns:
                self.assertIn(fn, blob, "bad fixture %s is not referenced by any test" % fn)


if __name__ == "__main__":
    unittest.main()
