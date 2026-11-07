What: Prompt that writes AGENTS.md from the template and your own rules.
Who writes: The repo author.
Who reads: You, pasting it into Claude Code.
Wired into: prompts/setup/_TEMPLATE_AGENTS.md
Template: prompts/setup/_TEMPLATE_AGENTS.md. Input: my rules and notes, [path or pasted text]. Output: AGENTS.md at the repo root.
Prompt: Read the template and my input. Write AGENTS.md in that section order. Each rule is one line plus a one-line reason. Do not invent a rule that is not in my input; list what you left out and why.
Do not put version numbers or incident names in the file.
Keep every section of the current AGENTS.md numbered 12 or higher exactly as it is, and tell me which sections 1 to 11 you replaced.
Check: python3 tools/wiring_check.py. Fix every finding it prints.
