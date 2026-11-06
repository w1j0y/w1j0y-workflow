# Decision rules stream

What: Append-only log of rules of thumb the digest finds in inbox summaries.
Who writes: tools/digest_inbox.sh (append only).
Who reads: the maintenance prompt, when it drafts a playbook delta.
Wired into: tools/digest_inbox.sh, tools/playbook_apply.py (one-way: reference only)

## Entries
- 2026-01-01 example-program: always send a control request to a random path before calling any 200 a signal. (source: non-reportable/example-program/spa-catch-all-closed.md)
