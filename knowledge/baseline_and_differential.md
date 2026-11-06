# Baseline and differential testing
What: Use when you must show that a change in one input caused a change in the response: the baseline, control, variant and delta method.
Who writes: The repo author; phases append one cited fact at a time, maintenance reviews.
Who reads: The phase subagent that the trigger table or the index points at.
Wired into: prompts/web/02_5-map-classes.md, knowledge/INDEX.md (one-way: generated index), tools/knowledge_index.py (one-way: script)

Class: method, evidence
Kind: technique

## Technique: Baseline and differential testing

### When To Use
- Any test where the claim is that a change in input changes behaviour.
- Before you give a result a status of confirmed or rejected.
- When a response looks odd and you need to know whether it is normal for the application.

### Procedure
1. Baseline: send the normal request and save the full response (status, key headers, size, the parts of the body that matter).
2. Control: send a request that must work, so you know the test can work. A second control that must fail (an invalid value) shows what a refusal looks like.
3. Variant: change exactly one thing from the baseline. Send it. Save it.
4. Delta: write down what differs between the variant and the baseline, field by field. If nothing differs, the result is no-signal or rejected, not confirmed.
5. Repeat once. A result that does not repeat is a candidate at best.
6. For a write, send a separate read request afterwards and compare it with the earlier read.
7. Save the evidence with secrets redacted, and put the path in the ledger row.

### Key Indicators
- The delta is specific and repeatable: the same change gives the same difference.
- The control passes and the invalid control fails, so the surface is behaving as a test target.
- A difference in size or timing alone is a lead; confirm with content or state.

### Common Pitfalls
- Changing two things at once makes the delta meaningless.
- Timestamps, tokens, request ids and ordering change on every request; strip them before comparing.
- A blocked request is not a rejection. Record blocked and what would unblock it.
- A 200 on a write proves nothing until a read-back shows the state.
- A baseline taken minutes earlier may be stale if the state changed; retake it.

## Current Sources

| URL | Date | Tier |
|---|---|---|
| https://owasp.org/www-project-web-security-testing-guide/ | 2026-11-06 (to re-check) | 1 |
| https://portswigger.net/web-security | 2026-11-06 (to re-check) | 2 |

Tier 1 is a standard or the vendor's own documentation. Tier 2 is well-known training material. Tier 3 is a blog or talk. The method above is written in this repo's own words from general public method knowledge; the links are for you to read and confirm, not copied text. Re-open each link before relying on it, and update the date when you do.
