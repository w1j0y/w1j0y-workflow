# What: Tests for tools/ledger_gate.py: good and bad ledgers, packet cap, submittable and the schema-drives-gate meta test.
# Who writes: the repo author.
# Who reads: tools/tests/run.sh and the human running python3 -B -m unittest discover -s tools/tests
# Wired into: none: found by unittest discovery
import os
import shutil
import unittest

import helpers as h


def gate(root, cmd, phase="01", extra=()):
    args = [cmd, "--target", h.TARGET, "--root", root]
    if phase:
        args += ["--phase", phase]
    return h.run("ledger_gate.py", args + list(extra))


class LedgerGateTests(unittest.TestCase):
    def setUp(self):
        self.root = h.make_root()
        self.addCleanup(h.cleanup, self.root)

    def bootstrap(self):
        r = gate(self.root, "snapshot")
        self.assertEqual(r.returncode, 0, r.stderr)

    def place(self, ledger, finding=True):
        h.put_ledger(self.root, ledger)
        if finding:
            h.put(self.root, "recon_output/%s/%s_finding_item_read.md" % (h.TARGET, h.TARGET),
                  os.path.join(h.GOOD, "example-program_finding_item_read.md"))

    def test_usage_without_args(self):
        self.assertEqual(h.run("ledger_gate.py", []).returncode, 2)

    def test_bootstrap_snapshot_with_no_ledger(self):
        self.bootstrap()
        self.assertTrue(os.path.isfile(os.path.join(self.root, ".state", "ledger_snapshot_%s_01.json" % h.TARGET)))

    def test_snapshot_without_ledger_other_phase_is_missing(self):
        self.assertEqual(gate(self.root, "snapshot", "03").returncode, 2)

    def test_unknown_phase_is_usage(self):
        self.assertEqual(gate(self.root, "snapshot", "99").returncode, 2)

    def test_check_without_ledger_is_missing(self):
        self.bootstrap()
        self.assertEqual(gate(self.root, "check").returncode, 2)

    def test_good_ledger_passes_and_snapshot_removed(self):
        self.bootstrap()
        self.place(os.path.join(h.GOOD, "ledger_complete.md"))
        r = gate(self.root, "check")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("GATE PASS: phase 01 for target 'example-program'", r.stdout)
        self.assertFalse(os.path.exists(os.path.join(self.root, ".state", "ledger_snapshot_%s_01.json" % h.TARGET)))

    def test_bad_ledgers_are_refused(self):
        cases = {
            "ledger_blank_status.md": "status",
            "ledger_unknown_status.md": "vocabulary",
            "ledger_handoff_no_status.md": "Phase handoff row h1",
            "ledger_finding_no_verdict.md": "no Finding Validation row",
        }
        for name, needle in cases.items():
            with self.subTest(name):
                root = h.make_root()
                self.addCleanup(h.cleanup, root)
                self.assertEqual(gate(root, "snapshot").returncode, 0)
                h.put_ledger(root, os.path.join(h.BAD, name))
                h.put(root, "recon_output/%s/%s_finding_item_read.md" % (h.TARGET, h.TARGET),
                      os.path.join(h.GOOD, "example-program_finding_item_read.md"))
                r = gate(root, "check")
                self.assertEqual(r.returncode, 3, r.stdout)
                self.assertIn("GATE FAIL: phase 01 for target 'example-program' -- ", r.stderr)
                self.assertIn("row(s) incomplete:", r.stderr)
                self.assertIn(needle, r.stderr)

    def test_only_touched_rows_are_checked(self):
        self.bootstrap()
        self.place(os.path.join(h.GOOD, "ledger_complete.md"))
        self.assertEqual(gate(self.root, "check").returncode, 0)
        self.assertEqual(gate(self.root, "snapshot", "02").returncode, 0)
        p = os.path.join(self.root, "recon_output", h.TARGET, "coverage_ledger.md")
        text = h.read_text(p).replace("| s2 | GET /api/items/102 | object-reference | no-signal |",
                                      "| s2 | GET /api/items/102 | object-reference |  |")
        h.write_text(p, text)
        r = gate(self.root, "check", "02")
        self.assertEqual(r.returncode, 3)
        self.assertIn("row s2", r.stderr)
        self.assertNotIn("row s1", r.stderr)

    def test_unchanged_finding_needs_no_new_row(self):
        self.bootstrap()
        self.place(os.path.join(h.GOOD, "ledger_complete.md"))
        self.assertEqual(gate(self.root, "check").returncode, 0)
        self.assertEqual(gate(self.root, "snapshot", "02").returncode, 0)
        self.assertEqual(gate(self.root, "check", "02").returncode, 0)

    def test_changed_finding_needs_verdict_row(self):
        self.bootstrap()
        self.place(os.path.join(h.GOOD, "ledger_complete.md"))
        self.assertEqual(gate(self.root, "check").returncode, 0)
        self.assertEqual(gate(self.root, "snapshot", "02").returncode, 0)
        with open(os.path.join(self.root, "recon_output", h.TARGET, "%s_finding_new_one.md" % h.TARGET), "w") as f:
            f.write("new finding\n")
        r = gate(self.root, "check", "02")
        self.assertEqual(r.returncode, 3)
        self.assertIn("new_one", r.stderr)

    def test_packet_lists_open_rows_with_cap(self):
        self.place(os.path.join(h.GOOD, "ledger_complete.md"), finding=False)
        r = gate(self.root, "packet", "02")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("s1", r.stdout)
        self.assertNotIn("| s2 |", r.stdout)
        p = os.path.join(self.root, "recon_output", h.TARGET, "coverage_ledger.md")
        rows = "\n".join("| x%d | GET /a/%d | object-reference | untested |  |  |" % (i, i) for i in range(70))
        text = h.read_text(p).replace("## Phase handoff", rows + "\n\n## Phase handoff", 1)
        h.write_text(p, text)
        r = gate(self.root, "packet", "02")
        self.assertIn("61 of 72 open row(s), cap 60", r.stdout)
        shown = [ln for ln in r.stdout.splitlines() if ln.startswith("| x") or ln.startswith("| s1")]
        self.assertEqual(len(shown), 60)
        self.assertIn("| h1 |", r.stdout)

    def test_submittable(self):
        h.put_ledger(self.root, os.path.join(h.GOOD, "ledger_complete.md"))
        rd = os.path.join(self.root, "reports", h.TARGET, "example-finding")
        os.makedirs(rd)
        shutil.copy(os.path.join(h.BAD, "REPORT_missing_disclosure.md"), os.path.join(rd, "REPORT.md"))
        # no scope file in this checkout: fail closed, never pass because nothing says disclosure is needed
        r = gate(self.root, "submittable", None, ["--report-dir", rd])
        self.assertEqual(r.returncode, 3)
        self.assertIn("scope file missing", r.stderr)
        # the scope file alone is enough: the entry gate has not run, so there is no session state
        h.put_scope(self.root, os.path.join(h.GOOD, "scope_disclosure.json"))
        self.assertFalse(os.path.exists(os.path.join(self.root, ".state", "active_target.json")))
        r = gate(self.root, "submittable", None, ["--report-dir", rd])
        self.assertEqual(r.returncode, 3)
        self.assertIn("AI disclosure:", r.stderr)
        shutil.copy(os.path.join(h.GOOD, "REPORT_disclosure_ok.md"), os.path.join(rd, "REPORT.md"))
        self.assertEqual(gate(self.root, "submittable", None, ["--report-dir", rd]).returncode, 0)

    def test_submittable_refuses_when_ai_use_is_prohibited(self):
        h.put_ledger(self.root, os.path.join(h.GOOD, "ledger_complete.md"))
        h.put_scope(self.root, os.path.join(h.BAD, "scope_ai_prohibited.json"))
        rd = os.path.join(self.root, "reports", h.TARGET, "example-finding")
        os.makedirs(rd)
        shutil.copy(os.path.join(h.GOOD, "REPORT_disclosure_ok.md"), os.path.join(rd, "REPORT.md"))
        r = gate(self.root, "submittable", None, ["--report-dir", rd])
        self.assertEqual(r.returncode, 3)
        self.assertIn("ai_use rule is", r.stderr)

    def test_submittable_needs_ready_verdict_and_report(self):
        h.put_ledger(self.root, os.path.join(h.BAD, "ledger_finding_no_verdict.md"))
        rd = os.path.join(self.root, "reports", "r")
        self.assertEqual(gate(self.root, "submittable", None, ["--report-dir", rd]).returncode, 2)
        os.makedirs(rd)
        shutil.copy(os.path.join(h.GOOD, "REPORT_disclosure_ok.md"), os.path.join(rd, "REPORT.md"))
        r = gate(self.root, "submittable", None, ["--report-dir", rd])
        self.assertEqual(r.returncode, 3)
        self.assertIn("VALID_READY_TO_REPORT", r.stderr)


class SchemaDrivesGateTests(unittest.TestCase):
    """Meta test: the gate follows the schema file, nothing is hard-coded."""

    def run_with(self, root, ledger):
        self.assertEqual(gate(root, "snapshot").returncode, 0)
        h.put_ledger(root, ledger)
        h.put(root, "recon_output/%s/%s_finding_item_read.md" % (h.TARGET, h.TARGET),
              os.path.join(h.GOOD, "example-program_finding_item_read.md"))
        return gate(root, "check")

    def test_added_status_is_accepted(self):
        text = h.read_text(os.path.join(h.GOOD, "ledger_complete.md")).replace("| no-signal |", "| accepted |")
        tmp = os.path.join(h.make_root(), "l.md")
        self.addCleanup(h.cleanup, os.path.dirname(tmp))
        h.write_text(tmp, text)
        root = h.make_root()
        self.addCleanup(h.cleanup, root)
        self.assertEqual(self.run_with(root, tmp).returncode, 3)
        root2 = h.make_root()
        self.addCleanup(h.cleanup, root2)
        h.edit_schema(root2, lambda d: d["statuses"].append("accepted"))
        self.assertEqual(self.run_with(root2, tmp).returncode, 0)

    def test_removed_status_is_refused(self):
        root = h.make_root()
        self.addCleanup(h.cleanup, root)
        h.edit_schema(root, lambda d: d["statuses"].remove("candidate"))
        r = self.run_with(root, os.path.join(h.GOOD, "ledger_complete.md"))
        self.assertEqual(r.returncode, 3)
        self.assertIn("candidate", r.stderr)

    def test_required_column_added_to_schema_is_enforced(self):
        root = h.make_root()
        self.addCleanup(h.cleanup, root)
        h.edit_schema(root, lambda d: d["blocks"]["Surfaces"]["required_by_phase"]["01"].append("next"))
        text = h.read_text(os.path.join(h.GOOD, "ledger_complete.md")).replace("| validate |", "|  |")
        tmp = os.path.join(root, "l.md")
        h.write_text(tmp, text)
        r = self.run_with(root, tmp)
        self.assertEqual(r.returncode, 3)
        self.assertIn("column 'next' is blank", r.stderr)

    def test_unknown_phase_comes_from_schema(self):
        root = h.make_root()
        self.addCleanup(h.cleanup, root)
        h.put_ledger(root, os.path.join(h.GOOD, "ledger_complete.md"))
        self.assertEqual(gate(root, "snapshot", "04").returncode, 2)
        h.edit_schema(root, lambda d: d["phases"].append("04"))
        self.assertEqual(gate(root, "snapshot", "04").returncode, 0)


if __name__ == "__main__":
    unittest.main()
