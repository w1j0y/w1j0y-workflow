# Learnings stream

What: Append-only log of lessons the digest extracts from inbox summaries.
Who writes: tools/digest_inbox.sh (append only).
Who reads: the maintenance prompt, when it drafts a playbook delta.
Wired into: tools/digest_inbox.sh, tools/playbook_apply.py (one-way: reference only)

## Entries
- 2026-01-01 example-program: changing an id in the path and checking the owner field in the response is a fast object reference check. (source: recon_output/example-program/coverage_ledger.md)
- 2026-01-02 example-program: a single-page app returned 200 with the same shell page for every route, so status codes alone said nothing about whether a route existed. (source: recon_output/example-program/target_notes.md)
- 2026-01-02 example-program: a write that returned 200 was not a finding until a read back from the owner account showed the data had changed. (source: reports/example-program/example-finding/REPORT_AUDIT.md)
