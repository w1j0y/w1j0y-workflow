# Template: a reference file
What: The shape of one finished reference file in prompts/reference.
Who writes: The repo author.
Who reads: prompts/reference/_GENERATE_REFERENCE.md and anyone adding a reference file.
Wired into: prompts/reference/_GENERATE_REFERENCE.md

Copy this shape. Reference files hold rules that more than one prompt needs, so each rule lives once.

~~~text
# [Name]
What: [one sentence]
Who writes: [who]
Who reads: [which prompts or scripts]
Wired into: [repo-relative paths, each of which must list this file back]

## [Rule group]
[Plain rules, numbered, each with a short reason]

## Data a script reads
[Only if a script parses it: one fenced json block, and the name of that script]

## Wire it in
[The exact lines the other files must receive]
~~~

## Wire it in

1. Each prompt that depends on the new file names it in its Consult block.
2. `prompts/README.md` lists it.
3. `STRUCTURE.md` has a row with a lifecycle class.
4. `python3 tools/wiring_check.py` passes.
