Template: an organizer launcher for one agent harness
What: Shape of a launcher script that makes an agent turn a raw program page into the five scope files, then refuses unless a validator passes.
Who writes: You, once per harness, from this template with scripts/_GENERATE_ORGANIZER.md.
Who reads: You, and the generator prompt that builds a launcher for another harness.
Wired into: scripts/_GENERATE_ORGANIZER.md, scripts/organize_scope_claude.sh

A launcher has five duties, in this order:
1. Take exactly one argument: a raw scope file that resolves under targets/. Refuse anything else.
2. Record the SHA-256 of the raw file, the folder listing and the start time.
3. Build the prompt from prompts/organize_scope.md plus a parameter block (paths and the validator command). Refuse a prompt over 100000 bytes.
4. Run the agent with an explicit tool allowlist: read, write only in the target folder, the validator command. No web tools, no skip-permissions flag.
5. After the agent exits, fail unless: exit code 0, raw hash unchanged, only the five output files appeared, tools/validate_scope.py passes, outputs are newer than the start time.

Wire it in: add the launcher path to STRUCTURE.md with class B, and name it in prompts/organize_scope.md.
