# Knowledge index
What: Generated list of every knowledge file with its one-sentence summary.
Who writes: tools/knowledge_index.py (generated, do not edit by hand).
Who reads: every phase file as its first consult step, and the wiring audit.
Wired into: tools/knowledge_index.py

Open at most the files whose line matches the surface you are testing.
Rebuild after any change: python3 tools/knowledge_index.py

- `knowledge/idor.md`: How to test whether one user can read another user's record by changing an id.
