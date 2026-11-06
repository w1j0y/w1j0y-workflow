#!/usr/bin/env python3
# What: Filter that reads text on stdin and writes it to stdout with cookies, auth headers, tokens, key-like strings and emails replaced by markers.
# Who writes: the repo author; the pattern list lives in this file only.
# Who reads: the agent before it saves anything to evidence, the ledger or memory; tools/secret_scan.py (pattern list); tools/tests/test_redact.py
# Wired into: AGENTS.md, tools/secret_scan.py, tools/tests/test_redact.py
"""Usage: some_command | python3 tools/redact.py > cleaned.txt

Redacts: Cookie and Set-Cookie lines, Authorization lines, token-bearing
X- header lines, bearer tokens, JWTs, private key blocks, cloud and API key
shapes, assignments of secret-named variables, emails, long base64-like blobs.
Pattern-based, so it can miss odd shapes and can over-redact long hashes.
Always read the output before saving it.
"""
import re
import sys

PRIVATE_KEY_BLOCK = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?(?:-----END [A-Z ]*PRIVATE KEY-----|\Z)", re.S)

# (kind, regex, replacement). Header kinds keep the header name and redact the rest of the line.
KINDS = [
    ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "[REDACTED_PRIVATE_KEY]"),
    ("cookie", re.compile(r"(?im)^(\s*(?:set-cookie|cookie)\s*:)(.*)$"), r"\1 [REDACTED]"),
    ("authorization", re.compile(r"(?im)^(\s*(?:proxy-)?authorization\s*:)(.*)$"), r"\1 [REDACTED]"),
    ("token-header", re.compile(r"(?im)^(\s*x-[a-z0-9-]*(?:token|key|secret|auth)[a-z0-9-]*\s*:)(.*)$"), r"\1 [REDACTED]"),
    ("bearer", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}"), "Bearer [REDACTED]"),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{4,}"), "[REDACTED_JWT]"),
    ("aws-key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"), "[REDACTED_KEY]"),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"), "[REDACTED_KEY]"),
    ("slack-token", re.compile(r"\bxox[abpr]-[A-Za-z0-9-]{10,}"), "[REDACTED_KEY]"),
    ("google-key", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}"), "[REDACTED_KEY]"),
    ("secret-key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"), "[REDACTED_KEY]"),
    ("secret-assign", re.compile(
        r"(?i)\b((?:api[_-]?key|secret|token|passwd|password|pwd|access[_-]?key)[\w-]*)(\s*[:=]\s*)([\"']?)"
        r"((?=[A-Za-z0-9+/=_.\-]*\d)[A-Za-z0-9+/=_.\-]{12,})\3"), r"\1\2\3[REDACTED]\3"),
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+"), "[REDACTED_EMAIL]"),
    ("long-blob", re.compile(r"\b[A-Za-z0-9+/_-]{48,}={0,2}"), "[REDACTED_BLOB]"),
]


def redact(text):
    """Return text with every secret-like shape replaced."""
    text = PRIVATE_KEY_BLOCK.sub("[REDACTED_PRIVATE_KEY]", text)
    for kind, rx, repl in KINDS:
        if kind == "private-key":
            continue
        text = rx.sub(repl, text)
    return text


def main():
    if len(sys.argv) > 1:
        print("Usage: python3 tools/redact.py < input > output", file=sys.stderr)
        return 2
    sys.stdout.write(redact(sys.stdin.read()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
