What: Prompt that drafts a playbook delta from the streams since the boundary.
Who writes: The repo author.
Who reads: You, pasting it into Claude Code after maintenance.
Wired into: memory/_TEMPLATE_SKILL.md
Template: memory/_TEMPLATE_SKILL.md. Input: memory/streams/[stream].md after the boundary. Output: a delta file under memory/playbook/_deltas/, nothing else.
Prompt: Read the template. Read the stream after the boundary. Draft up to [N] entries in a delta file. Each entry must cite evidence paths that exist and stay under 1200 bytes. Do not touch any other file.
Check: python3 tools/playbook_apply.py --dry-run on the delta file; show me the result before anything is applied.
