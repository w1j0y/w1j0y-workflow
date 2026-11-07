# example-program Target Scope
What: Generated summary of the organized scope for the example program.
Who writes: scripts/organize_scope_claude.sh through its agent.
Who reads: You, before running tools/recon.py.
Wired into: targets/example-program/scope_raw.txt (one-way: input), tools/validate_scope.py (one-way: validator)

# example-program Target Scope

## Files

- `scope_raw.txt`: original pasted program scope
- `scope.json`: structured machine-readable recon scope
- `scope.txt`: flat human-readable scope
- `guidelines.json`: structured testing rules
- `guidelines.txt`: human-readable testing rules

## Required header

`X-Research: tester-a`

## Recon command

```bash
python3 tools/recon.py --scope-json targets/example-program/scope.json --target-name example-program --output recon_output/example-program --dry-run
```

## Validation summary

- JSON parsed successfully: yes
- Recon targets found: 2
- Non-recon in-scope entries: 0
- Out-of-scope entries found: 3
- Review-required entries: 0
- Required header detected: yes
- Raw-source coverage: 3 asset tokens and 7 list items checked against the generated JSON; 0 recorded as non-asset references
- Unresolved items: none

## Notes

- payments.example-shop.test is excluded although the in-scope wildcard *.example-shop.test would cover it. The narrower exclusion wins.
- The wildcard does not cover the bare domain example-shop.test, which is not listed.
- Rules: automation limited, AI use requires disclosure, 60 requests per minute, header X-Research: tester-a.
