What: Prompt that writes the front door files from the template.
Who writes: The repo author.
Who reads: You, pasting it into Claude Code.
Wired into: prompts/setup/_TEMPLATE_FRONTDOOR.md
Template: prompts/setup/_TEMPLATE_FRONTDOOR.md. Input: the files on disk (list the tree first) and my purpose, [one paragraph]. Output: README.md, GETTING_STARTED.md, STRUCTURE.md, GLOSSARY.md, ETHICS.md.
Prompt: Read the template and list the tree. Write the five files in the template shape. STRUCTURE.md gets one row for every file on disk, with a lifecycle class B, C or U.
Do not copy text from any private source; use only what is in this repo and my input.
Check: python3 tools/wiring_check.py. Fix every finding it prints.
