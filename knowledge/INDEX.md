# Knowledge index
What: Generated list of every knowledge file with its one-sentence summary.
Who writes: tools/knowledge_index.py (generated, do not edit by hand).
Who reads: every phase file as its first consult step, and the wiring audit.
Wired into: tools/knowledge_index.py

Open at most the files whose line matches the surface you are testing.
Rebuild after any change: python3 tools/knowledge_index.py

- `knowledge/baseline_and_differential.md`: Use when you must show that a change in one input caused a change in the response: the baseline, control, variant and delta method.
- `knowledge/object_reference_checks.md`: Use when a request names an object by id or name (order, profile, file): how to test with two accounts whether the server checks who owns it.
- `knowledge/spa_catch_all_200.md`: Use when many unknown paths return 200 with the same page, or before a severity label: how to tell a catch-all page from a real response (false positives).
