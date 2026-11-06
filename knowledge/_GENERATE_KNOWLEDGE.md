What: Prompt that creates one knowledge file from a resource you are licensed to use.
Who writes: The repo author.
Who reads: You, pasting it into Claude Code.
Wired into: knowledge/_TEMPLATE_KNOWLEDGE.md
Template: knowledge/_TEMPLATE_KNOWLEDGE.md. Input: [the resource: a path or a link]. Output: knowledge/[name].md.
Prompt: Read the template. Read the resource. Create knowledge/[name].md in that shape. Every line must come from the resource; do not invent steps.
After the file, list what you left out and why. Add one row to the trigger table in prompts/web/02_5-map-classes.md.
Check: python3 tools/knowledge_index.py, then python3 tools/wiring_check.py. Fix what they report.
