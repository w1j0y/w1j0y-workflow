# What: Tests for tools/redact.py and tools/secret_scan.py; fake secrets are assembled from fragments at run time.
# Who writes: the repo author.
# Who reads: tools/tests/run.sh and the human running python3 -B -m unittest discover -s tools/tests
# Wired into: none: found by unittest discovery
import os
import shutil
import subprocess
import tempfile
import unittest

import helpers as h


def fakes():
    """Fake secrets built from fragments so no file in the repo holds one whole."""
    return {
        "jwt": "ey" + "JhbGciOiJIUzI1NiJ9" + "." + "ey" + "JzdWIiOiJ0ZXN0ZXItYSJ9" + "." + "c2lnbmF0dXJlMTIz",
        "aws": "AK" + "IA" + "ABCDEFGHIJKLMNOP",
        "bearer": "Bea" + "rer " + "abcd1234efgh5678ijkl",
        "gh": "gh" + "p_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8",
        "cookie": "Coo" + "kie: session=" + "abc123def456",
        "assign": "api" + "_key = \"" + "k9X2mQ7pL4vN8zT1" + "\"",
        "email": "real.person" + "@" + "corp-mail" + ".com",
        "pem": "-----BEGIN " + "RSA PRIVATE" + " KEY-----",
    }


class RedactTests(unittest.TestCase):
    def test_each_kind_removed(self):
        f = fakes()
        text = "\n".join([f["cookie"], "Set-Cookie: id=zz9988", "Authorization: Basic dXNlcjpwYXNz",
                          "x-" + "api-key: 123abc", "token is " + f["bearer"], "jwt " + f["jwt"],
                          f["aws"], f["gh"], f["assign"], "mail " + f["email"], f["pem"] + "\nMIIE\n-----END RSA PRIVATE KEY-----"])
        r = h.run("redact.py", [], stdin=text)
        self.assertEqual(r.returncode, 0)
        out = r.stdout
        for key, val in f.items():
            core = val.split(": ")[-1].split(" ")[-1].strip('"') if key in ("cookie", "bearer", "assign") else val
            self.assertNotIn(core, out, key)
        for needle in ("abc123def456", "zz9988", "dXNlcjpwYXNz", "MIIE", "corp-mail"):
            self.assertNotIn(needle, out)
        self.assertIn("Cookie: [REDACTED]", out)
        self.assertIn("Authorization: [REDACTED]", out)

    def test_plain_text_untouched(self):
        text = "GET /api/items/101 HTTP/1.1\nHost: shop.example-shop.test\nX-Research-Id: tester-a\n"
        self.assertEqual(h.run("redact.py", [], stdin=text).stdout, text)

    def test_args_are_usage(self):
        self.assertEqual(h.run("redact.py", ["x"]).returncode, 2)


class SecretScanTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="w1j0y_scan_")
        self.addCleanup(shutil.rmtree, self.dir, True)

    def test_usage_without_args(self):
        self.assertEqual(h.run("secret_scan.py", []).returncode, 2)

    def test_hits_print_file_line_kind_not_value(self):
        f = fakes()
        p = os.path.join(self.dir, "evidence_note.md")
        with open(p, "w") as fh:
            fh.write("clean line\n" + f["gh"] + "\n" + f["aws"] + "\n" + f["jwt"] + "\n" + f["pem"] + "\n" + f["email"] + "\n")
        r = h.run("secret_scan.py", [self.dir])
        self.assertEqual(r.returncode, 3)
        self.assertIn("evidence_note.md:2: github-token", r.stdout)
        self.assertIn("evidence_note.md:3: aws-key", r.stdout)
        self.assertIn("evidence_note.md:4: jwt", r.stdout)
        self.assertIn("evidence_note.md:5: private-key", r.stdout)
        self.assertIn("evidence_note.md:6: email", r.stdout)
        combined = r.stdout + r.stderr
        for key in ("gh", "aws", "jwt", "email"):
            self.assertNotIn(f[key], combined)

    def test_clean_and_allowed_values_pass(self):
        p = os.path.join(self.dir, "ok.md")
        with open(p, "w") as fh:
            fh.write("Cookie: [value]\nAuthorization: [value]\ntester-a@example.test\nsee tools/lib/meta.py and a/long/path/name\n")
        r = h.run("secret_scan.py", [p])
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_missing_path_is_usage(self):
        self.assertEqual(h.run("secret_scan.py", [os.path.join(self.dir, "nope")]).returncode, 2)

    @unittest.skipUnless(shutil.which("git"), "git not installed")
    def test_staged_mode(self):
        def git(*a):
            return subprocess.run(["git"] + list(a), cwd=self.dir, capture_output=True, text=True)
        git("init", "-q")
        git("config", "user.name", "tester-a")
        git("config", "user.email", "tester-a@example.test")
        p = os.path.join(self.dir, "note.md")
        h.write_text(p, "fine\n")
        git("add", "note.md")
        self.assertEqual(h.run("secret_scan.py", ["--staged", "--root", self.dir]).returncode, 0)
        h.write_text(p, "fine\n" + fakes()["aws"] + "\n")
        git("add", "note.md")
        r = h.run("secret_scan.py", ["--staged", "--root", self.dir])
        self.assertEqual(r.returncode, 3)
        self.assertIn("note.md:2: aws-key", r.stdout)

    def test_repo_tools_scan_clean(self):
        r = h.run("secret_scan.py", [h.TOOLS])
        self.assertEqual(r.returncode, 0, r.stdout)


if __name__ == "__main__":
    unittest.main()
