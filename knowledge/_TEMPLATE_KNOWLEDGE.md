# Template: a knowledge file
What: The shape of one finished knowledge file: a class line, one technique in four parts, and current sources.
Who writes: The repo author.
Who reads: knowledge/_GENERATE_KNOWLEDGE.md and anyone adding or appending to a technique file.
Wired into: knowledge/_GENERATE_KNOWLEDGE.md

~~~text
# [Technique name]
What: [one sentence that starts with "Use when" so the index line tells a phase whether to open it]
Who writes: [who]
Who reads: [which phase or trigger row opens it]
Wired into: [the phase or trigger row, the index; each must mention this file]

Class: [vulnerability class or topic]
Kind: technique   (or: reference, for a file that holds facts instead of a procedure)

## Technique: [name]

### When To Use
[Signals that make this file apply]

### Procedure
[Numbered steps. Baseline, control, variant, delta where a test is involved.]

### Key Indicators
[What a real positive looks like]

### Common Pitfalls
[False positives and mistakes]

## Current Sources

| URL | Date | Tier |
|---|---|---|
[One row per source. Date is the day you read it. Tier 1 standard or vendor docs, 2 training material, 3 blog or talk.]
~~~

Rules: every line must come from a source you are licensed to use or from your own tests. Do not copy long passages; write in your own words and cite. Append-only during a test run: add one section with one source line to a matching file; never create a file during a run.

## Wire it in

1. Add a row to the trigger table in `prompts/web/02_5-map-classes.md`, or the file is unreachable.
2. Run `python3 tools/knowledge_index.py` to list it in the index.
3. Add a row to `STRUCTURE.md` with a lifecycle class.
4. Run `python3 tools/wiring_check.py`.
