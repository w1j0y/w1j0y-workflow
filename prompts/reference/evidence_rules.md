# Evidence rules
What: What counts as evidence in a test: baseline, control, variant, delta, blocked versus rejected, read-back and the confirmation bar.
Who writes: The repo author; maintenance proposes changes.
Who reads: prompts/web/03-test.md, prompts/web/02-characterize.md and the validation prompts.
Wired into: prompts/web/02-characterize.md, prompts/web/02_5-map-classes.md, prompts/web/03-test.md, prompts/web/FINDING_VALIDATION.md, prompts/web/VALIDATE_REPORT.md, prompts/web/WEB_LOOP.md, prompts/README.md, AGENTS.md

## The four requests

1. Baseline: a normal request and its normal response, saved first.
2. Control: a request that must work, to prove the test can work at all (for example your own object with your own account).
3. Variant: the baseline with exactly one thing changed.
4. Delta: the difference between the variant response and the baseline. The delta is the evidence, not the variant alone.

Change one thing at a time. If two things changed, the delta says nothing.

## Blocked versus rejected

- Blocked: stopped before the application answered (firewall, login wall, timeout, rate limit, hook deny). Blocked proves nothing about the weakness. Record status blocked and what would unblock it.
- Rejected: the application answered and its answer shows the protection works (a clear refusal that depends on the object, no data of another user returned). Record rejected with the evidence path.

## Read-back

A 200 on a write is not proof. After a change, send a separate read request that shows the state. Compare it to the baseline read. No read-back, no confirmation.

## The confirmation bar

A row may be set to confirmed only when all hold:

1. The control worked and the variant produced a delta.
2. The delta shows impact on data or state that the account used should not reach (state who, what, whose).
3. A read-back, where the case involves a write, shows the change.
4. The request, response and delta are saved under the target's evidence folder with secrets redacted (`python3 tools/redact.py`), and the row's evidence column holds that path.
5. The false-positive file was consulted (see the trigger table in `prompts/web/02_5-map-classes.md`), and the result is not explained by a catch-all page, a cached response or a shared object.

Anything short of that is a candidate. A candidate is worth a closer look, not a report.

## Three lists

Keep apart: observed (facts with a path), guessed (hypotheses), next checks (single requests that would settle a guess). Do not write a guess into an observed list.

## Every claim gets a path

A claim with no path is a guess. Evidence paths in ledger rows, findings and skill files must exist on disk; the audit checks.

## Secrets

Never save a token, cookie or credential. Redact before saving. An evidence file with a secret-shaped string fails the secret scan at closeout.

## Wire it in

Named by every phase prompt through its Consult block. It is read through the Consult block of `prompts/web/01-triage.md`, `prompts/web/02-characterize.md`, `prompts/web/02_5-map-classes.md`, `prompts/web/03-test.md`, `prompts/web/FINDING_VALIDATION.md` and `prompts/web/VALIDATE_REPORT.md`, and loaded by `prompts/web/WEB_LOOP.md`. A change here is felt in all of them; edit them together.
