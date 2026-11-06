# Template: the front door files
What: The shape of README, GETTING_STARTED, STRUCTURE, GLOSSARY and ETHICS.
Who writes: The repo author.
Who reads: prompts/setup/_GENERATE_FRONTDOOR.md and anyone writing front door files.
Wired into: prompts/setup/_GENERATE_FRONTDOOR.md

- README: what this is, who it is for, how to use it, safety. No link to anything private.
- GETTING_STARTED: machine, git, Python, install Claude Code from its official steps, clone, run the tests, first prompt; optional tools later.
- STRUCTURE: a table of every file with columns path, part of the house, written by, read by, lifecycle class (B, C or U), episode. Rows start with the backticked path. Then the pipeline picture, the meta file convention, where to go next.
- GLOSSARY: every term once, alphabetical, with a definition and a real-life example.
- ETHICS: the rules you work inside, including program rules; where to practice.

Each file starts with the four-line box. Placeholders use square brackets.

## Wire it in

1. README points at GETTING_STARTED and STRUCTURE; STRUCTURE lists every file on disk.
2. `python3 tools/wiring_check.py` checks that STRUCTURE.md has a row and a class for every file.
