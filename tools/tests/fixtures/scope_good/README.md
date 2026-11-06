# Example Shop Bounty Target Scope

## Files
- `scope.json`: machine-readable scope
- `scope.txt`: one value per line
- `guidelines.json`: program rules
- `guidelines.txt`: program rules as text
- Source: scope_raw.txt

## Recon command
Header required by the program: X-Research: tester-a

python3 tools/recon.py --scope-json scope_good/scope.json --target-name example-program --dry-run

## Validation summary
- JSON parsed successfully: yes
- Recon targets found: 2
- Non-recon in-scope entries: 0
- Out-of-scope entries found: 1
- Review-required entries: 0
- Required header detected: yes
- Raw-source coverage: 3 asset tokens and 7 list items checked against the generated JSON; 0 recorded as non-asset references
- Unresolved items: none
