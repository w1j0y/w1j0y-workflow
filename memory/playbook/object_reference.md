# Playbook: object reference

What: Curated, evidence-backed entries for testing object references (ids in paths and bodies).
Who writes: tools/playbook_apply.py, from a delta the human approved.
Who reads: the phase prompts, after they find this class in memory/playbook/INDEX.md.
Wired into: memory/playbook/INDEX.md, tools/playbook_apply.py

### PB-OBJECT_REFERENCE-001 Change the id, then check the owner field
- Applies when: a path or body carries a numeric id for an object the logged-in user owns.
- Do: with two test accounts, request account A's object with account B's session; compare the owner field and the body to a request for a nonexistent id.
- Avoid: calling it a finding from the status code alone; a 200 needs the owner field or content to differ from the control.
- Evidence: recon_output/example-program/coverage_ledger.md; reports/example-program/example-finding/REPORT.md
- Confidence: high
- Last validated: 2026-01-01
- Status: active

### PB-OBJECT_REFERENCE-002 Read back from the owner account
- Applies when: a cross-account read or write looks successful.
- Do: log in as the owner and confirm the data matches what the other account saw, or that the write landed.
- Avoid: stopping at the response of the non-owner request.
- Evidence: reports/example-program/example-finding/REPORT_AUDIT.md; reports/example-program/example-finding/evidence/order_read_redacted.txt
- Confidence: medium
- Last validated: 2026-01-01
- Status: provisional
