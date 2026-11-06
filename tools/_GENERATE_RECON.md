What: Prompt that regenerates tools/recon.py from the viewer's own scope file using the template.
Who writes: The repo author.
Who reads: You, pasting it into Claude Code.
Wired into: tools/_TEMPLATE_RECON.md
Read tools/_TEMPLATE_RECON.md.
Read my scope file targets/[target]/scope.json and tools/scope_check.py.
My tool set is: [list of passive tools, one line each: what it finds, how it takes a header and a rate].
Write tools/recon.py in the shape of the template. Keep every contract line in the template.
Add a test for each contract line in tools/tests/test_recon.py with files under tools/tests/fixtures/.
Run: python3 -B -m unittest discover -s tools/tests
Then run: python3 tools/recon.py --scope-json targets/[target]/scope.json --target-name [target] --dry-run
Fix every failure. Do not send a request to any host.
