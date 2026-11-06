# Closed: unknown paths return 200

What: The reason one example lead was closed instead of reported.
Who writes: the validation prompt.
Who reads: the phase prompts and the human.
Wired into: recon_output/example-program/coverage_ledger.md, memory/playbook/spa_catch_all.md

Lead: /static/missing-page on shop.example-shop.test returned 200.
Reason closed: the single-page app returns its shell with 200 for any unknown path. A random path returns the same body, so the 200 carries no information.
Evidence: control request to /static/zzz-random returned the identical body length.
Ledger row: S-003 (rejected).
