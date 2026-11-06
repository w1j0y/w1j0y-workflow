# Single-page app catch-all 200
What: Use when many unknown paths return 200 with the same page, or before a severity label: how to tell a catch-all page from a real response (false positives).
Who writes: The repo author; phases append one cited fact at a time, maintenance reviews.
Who reads: The phase subagent that the trigger table or the index points at.
Wired into: prompts/web/02_5-map-classes.md, knowledge/INDEX.md (one-way: generated index), tools/knowledge_index.py (one-way: script)

Class: false positives, response analysis
Kind: technique

## Technique: Single-page app catch-all 200

### When To Use
- Guessed or unknown paths on a single-page application return 200.
- A scan or a wordlist run reports many hits with identical size.
- Before any candidate gets a severity label or the status confirmed (this is the false-positive file).

### Procedure
1. Control: request a random path that cannot exist (a long random string). Save status, size and the first lines of the body.
2. Compare the interesting response with the control: same size, same title, same shell markup means a catch-all.
3. Look at the content type. An API path that returns an HTML shell for an unknown route is the catch-all behaviour, not a data leak.
4. Ask the application the real question: call the underlying API route the page uses, with the right method, and read that response instead of the page.
5. If the response differs from the control in content (not just size), keep it as a candidate and continue with the baseline and differential method.
6. If it is identical to the control, mark the row rejected with the control as evidence.

### Key Indicators
- Many different paths with the same status, size and title.
- The body is the application shell and a script bundle, with no data from the path you asked for.
- The real data comes from a separate API call that the page makes after load.

### Common Pitfalls
- Judging by status code alone. Compare content with a random-path control.
- Judging by size alone: a catch-all can vary in size if it echoes the path.
- Reporting an exposed file that is only the shell. Check the body, not the code.
- Forgetting that a server may return 200 for HEAD and a different body for GET.

## Current Sources

| URL | Date | Tier |
|---|---|---|
| https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/200 | 2026-11-06 (to re-check) | 1 |
| https://developer.mozilla.org/en-US/docs/Glossary/SPA | 2026-11-06 (to re-check) | 1 |

Tier 1 is a standard or the vendor's own documentation. Tier 2 is well-known training material. Tier 3 is a blog or talk. The method above is written in this repo's own words from general public method knowledge; the links are for you to read and confirm, not copied text. Re-open each link before relying on it, and update the date when you do.
