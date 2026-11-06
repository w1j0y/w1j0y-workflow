# What: Tests for tools/mcp_scope_hook.py: good and bad hook inputs, rate window, fail-closed behaviour and sample logging.
# Who writes: the repo author.
# Who reads: tools/tests/run.sh and the human running python3 -B -m unittest discover -s tools/tests
# Wired into: none: found by unittest discovery
import json
import os
import time
import unittest

import helpers as h


def fx(kind, name):
    return os.path.join(h.GOOD if kind == "good" else h.BAD, "hook", name)


class HookTests(unittest.TestCase):
    def setUp(self):
        self.root = h.make_root()
        self.addCleanup(h.cleanup, self.root)
        r = h.entry_start(self.root, os.path.join(h.GOOD, "scope_confirmed.json"))
        self.assertEqual(r.returncode, 0, r.stderr)

    def hook(self, path, stdin=None, env=None, root=None):
        data = open(path).read() if stdin is None else stdin
        return h.run("mcp_scope_hook.py", ["--root", root or self.root], stdin=data, env=env)

    def test_good_inputs_allowed(self):
        for name in ("burp_send_ok.json", "burp_history_ok.json", "chrome_navigate_ok.json", "chrome_read_ok.json"):
            with self.subTest(name):
                r = self.hook(fx("good", name))
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(r.stdout.strip(), "")

    def test_screenshot_after_navigate_allowed(self):
        self.assertEqual(self.hook(fx("good", "chrome_navigate_ok.json")).returncode, 0)
        self.assertEqual(self.hook(fx("good", "chrome_screenshot_ok.json")).returncode, 0)
        tabs = json.load(open(os.path.join(self.root, ".state", "tabs.json")))
        self.assertIn("7", tabs)

    def test_click_after_navigate_asks(self):
        self.hook(fx("good", "chrome_navigate_ok.json"))
        p = json.load(open(fx("good", "chrome_screenshot_ok.json")))
        p["tool_input"]["action"] = "left_click"
        r = self.hook(None, stdin=json.dumps(p))
        self.assertEqual(r.returncode, 0)
        out = json.loads(r.stdout)
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "ask")

    def test_bad_inputs_blocked(self):
        cases = {
            "burp_send_out_of_scope.json": "not in scope",
            "burp_send_userinfo_trick.json": "",
            "burp_send_out_of_scope_listed.json": "not in scope",
            "burp_send_no_header.json": "identification header",
            "burp_history_match_all.json": "matches everything",
            "burp_intercept_toggle.json": "deny list",
            "chrome_navigate_off_scope.json": "not in scope",
            "chrome_click_unknown_tab.json": "unknown",
            "chrome_javascript.json": "denied",
            "unknown_server.json": "unknown MCP server",
        }
        for name, needle in cases.items():
            with self.subTest(name):
                r = self.hook(fx("bad", name))
                self.assertEqual(r.returncode, 2, r.stdout)
                self.assertIn("BLOCKED", r.stderr)
                self.assertIn(needle, r.stderr)

    def test_not_json_and_empty_fail_closed(self):
        self.assertEqual(self.hook(fx("bad", "not_json.txt")).returncode, 2)
        self.assertEqual(self.hook(None, stdin="").returncode, 2)
        self.assertEqual(self.hook(None, stdin="[1, 2]").returncode, 2)
        self.assertEqual(self.hook(None, stdin='{"tool_name": "Bash", "tool_input": {}}').returncode, 2)
        self.assertEqual(self.hook(None, stdin='{"tool_name": "mcp__burp__", "tool_input": {}}').returncode, 2)

    def test_no_active_target_blocks_sends(self):
        empty = h.make_root()
        self.addCleanup(h.cleanup, empty)
        r = self.hook(fx("good", "burp_send_ok.json"), root=empty)
        self.assertEqual(r.returncode, 2)
        self.assertIn("no active target", r.stderr)
        r = self.hook(fx("good", "chrome_navigate_ok.json"), root=empty)
        self.assertEqual(r.returncode, 2)

    def test_rate_window(self):
        path = os.path.join(self.root, ".state", "requests.jsonl")
        with open(path, "w") as f:
            for _ in range(60):
                f.write(json.dumps({"ts": time.time(), "kind": "burp_send"}) + "\n")
        r = self.hook(fx("good", "burp_send_ok.json"))
        self.assertEqual(r.returncode, 2)
        self.assertIn("rate limit", r.stderr)
        r = self.hook(fx("good", "chrome_navigate_ok.json"))
        self.assertEqual(r.returncode, 2)
        with open(path, "w") as f:
            for _ in range(60):
                f.write(json.dumps({"ts": time.time() - 3600, "kind": "burp_send"}) + "\n")
        self.assertEqual(self.hook(fx("good", "burp_send_ok.json")).returncode, 0)

    def test_allowed_send_is_recorded(self):
        self.assertEqual(self.hook(fx("good", "burp_send_ok.json")).returncode, 0)
        lines = open(os.path.join(self.root, ".state", "requests.jsonl")).read().splitlines()
        self.assertEqual(len(lines), 1)

    def test_source_pin(self):
        with open(os.path.join(self.root, ".state", "mcp_sources.json"), "w") as f:
            json.dump({"burp": "some-other-source"}, f)
        r = self.hook(fx("good", "burp_send_ok.json"))
        self.assertEqual(r.returncode, 2)
        self.assertIn("source", r.stderr)

    def test_hook_log_writes_redacted_sample(self):
        r = self.hook(fx("good", "burp_send_ok.json"), env={"HOOK_LOG": "1"})
        self.assertEqual(r.returncode, 0)
        p = os.path.join(self.root, ".state", "hook_samples.jsonl")
        self.assertTrue(os.path.isfile(p))
        self.assertEqual(len(open(p).read().splitlines()), 1)
        r = self.hook(fx("good", "burp_send_ok.json"))
        self.assertEqual(len(open(p).read().splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
