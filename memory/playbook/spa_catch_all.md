# Playbook: single-page app catch-all

What: Curated, evidence-backed entries for telling a catch-all 200 from a real response.
Who writes: tools/playbook_apply.py, from a delta the human approved.
Who reads: the phase prompts, after they find this class in memory/playbook/INDEX.md.
Wired into: memory/playbook/INDEX.md, tools/playbook_apply.py

### PB-SPA_CATCH_ALL-001 Send a random-path control first
- Applies when: unknown or guessed paths on a single-page app return 200.
- Do: request a random path and compare body length and hash with the interesting path; equal means catch-all, not exposure.
- Avoid: reporting a 200 on /admin or /config style paths without the control.
- Evidence: non-reportable/example-program/spa-catch-all-closed.md; recon_output/example-program/target_notes.md
- Confidence: high
- Last validated: 2026-01-01
- Status: active
