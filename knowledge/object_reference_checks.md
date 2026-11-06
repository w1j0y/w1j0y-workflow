# Object reference checks
What: Use when a request names an object by id or name (order, profile, file): how to test with two accounts whether the server checks who owns it.
Who writes: The repo author; phases append one cited fact at a time, maintenance reviews.
Who reads: The phase subagent that the trigger table or the index points at.
Wired into: prompts/web/02_5-map-classes.md, knowledge/INDEX.md (one-way: generated index), tools/knowledge_index.py (one-way: script)

Class: authorization, object level access
Kind: technique

## Technique: Object reference checks

### When To Use
- A path, query, body or header carries an identifier for an object that belongs to a user (an order 101, a profile, a file, an invoice).
- The surface exists for both an owner and someone else (two roles or two accounts).
- You hold two test accounts, tester-a and tester-b, each with at least one object.

### Procedure
1. Baseline: as tester-a, request tester-a's own object. Save request and response.
2. Control: as tester-a, request an id that does not exist. Save it. This shows what a refusal and a not-found look like on this surface.
3. Variant: as tester-a, request tester-b's object (swap only the identifier; keep the session). Save it.
4. Delta: compare the variant with the baseline and the control. Look at the owner field, the content, the status code and the size.
5. Repeat for each method the surface supports (read, update, delete). For any write, only use objects you own on both accounts, get approval first, and finish with a read-back from the owner account.
6. Try the same identifier in every place it appears: path, query, body, header, and any batch or list endpoint.
7. Record the result in the ledger row with the evidence path, redacted.

### Key Indicators
- The variant returns tester-b's data, or a field showing tester-b as owner, where the control returns a refusal or not-found.
- A write by tester-a changes tester-b's object, and the read-back from tester-b shows it.
- A long random identifier is not protection by itself; test whether the server checks the owner when the identifier is known.

### Common Pitfalls
- A 200 alone is not proof. The body may be empty, generic, or the same for every id; compare it with the control.
- Public or shared objects look like a success. Confirm the object is private first.
- A cached response may return your own data. Repeat with a fresh session and a cache-busting parameter.
- A 403 versus a 404 can differ; a difference alone is information, not a finding.
- Never use a real person's identifier. Stay with the two test accounts.
- Blocked is not rejected: a rate-limit or login wall tells you nothing about authorization.

## Current Sources

| URL | Date | Tier |
|---|---|---|
| https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/05-Authorization_Testing/04-Testing_for_Insecure_Direct_Object_References | 2026-11-06 (to re-check) | 1 |
| https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/ | 2026-11-06 (to re-check) | 1 |
| https://portswigger.net/web-security/access-control/idor | 2026-11-06 (to re-check) | 2 |

Tier 1 is a standard or the vendor's own documentation. Tier 2 is well-known training material. Tier 3 is a blog or talk. The method above is written in this repo's own words from general public method knowledge; the links are for you to read and confirm, not copied text. Re-open each link before relying on it, and update the date when you do.
