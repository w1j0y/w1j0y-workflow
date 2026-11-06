What: Prompt that creates one maintenance prompt from the template.
Who writes: The repo author.
Who reads: You, pasting it into Claude Code.
Wired into: prompts/maintenance/_TEMPLATE_MAINTENANCE.md
Template: prompts/maintenance/_TEMPLATE_MAINTENANCE.md. Input: [pass name] and [one-sentence purpose and cadence]. Output: prompts/maintenance/[NAME].md and .claude/commands/[name].md.
Prompt: Read the template. Create the prompt in that shape, with a deterministic first step that names a real command in tools. Add a slash command that says: read the prompt, do not edit until I approve.
Add the prompt to prompts/README.md and a row to STRUCTURE.md.
Check: python3 tools/wiring_check.py. Fix every finding it prints.
