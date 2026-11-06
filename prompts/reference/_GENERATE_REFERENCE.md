What: Prompt that creates one reference file from the template.
Who writes: The repo author.
Who reads: You, pasting it into Claude Code.
Wired into: prompts/reference/_TEMPLATE_REFERENCE.md
Template: prompts/reference/_TEMPLATE_REFERENCE.md. Input: [name] and [one-sentence purpose]. Output: prompts/reference/[name].md.
Prompt: Read prompts/reference/_TEMPLATE_REFERENCE.md. Create prompts/reference/[name].md for [one-sentence purpose]. Anything a script must read goes into one fenced json block; name that script.
Then add the file to prompts/README.md and STRUCTURE.md, and name it in the Consult block of each prompt that needs it.
Check: python3 tools/wiring_check.py. Fix every finding it prints.
