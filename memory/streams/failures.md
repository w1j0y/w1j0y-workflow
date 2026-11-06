# Failures stream

What: Append-only log of things that went wrong, so they are not repeated.
Who writes: tools/digest_inbox.sh (append only).
Who reads: the maintenance prompt, when it drafts a playbook delta.
Wired into: tools/digest_inbox.sh, tools/playbook_apply.py (one-way: reference only)

## Entries
- 2026-01-01 example-program: a 200 on an unknown path was first read as exposure; the control request showed a catch-all. (source: non-reportable/example-program/spa-catch-all-closed.md)
