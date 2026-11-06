# Template: recon tool

What: The contract any recon.py must keep, so it can be regenerated for a different set of passive tools.
Who writes: the repo author.
Who reads: tools/_GENERATE_RECON.md and whoever regenerates tools/recon.py.
Wired into: tools/_GENERATE_RECON.md, tools/recon.py

## Header block
The generated file starts with the four-line box (What, Who writes, Who reads, Wired into) as comments, then a docstring that lists the modes and the exit codes.

## Arguments (all required to exist)
- --scope-json [path]: the scope file. Required.
- --target-name [name]: required.
- --output [folder]: default recon_output/[target-name]. The tool always writes a [timestamp] folder under it.
- --rate [requests per minute]: required unless the scope states a rate. Refuse a value above the scope rate.
- --header ["Name: value"]: defaults to the scope's identification header. Refuse to run without one, unless --no-identifier-header is given and every target is localhost.
- --dry-run: print the in-scope hosts, the rate, the header and the exact commands. Send nothing, write nothing.
- --validate-scope-only: check the scope file shape and print the seeds. No tool runs.
- --fixture [folder]: offline. Read saved tool outputs from the folder, apply the same filters, write the run folder. Start no process.

## Contract
1. Scope filter at three points: after enumeration, after resolution, after probing (including redirect targets). Import host_in_scope from tools/scope_check.py through sys.path. Never keep a local copy.
2. Live mode only starts a tool with subprocess and an argument list (no shell). Each command that sends traffic to the target carries the header and a rate cap in the tool's own units.
3. Live mode refuses unless rules.confirmed_by_human is true, automation is not prohibited and AI use is not prohibited or restricted.
4. No credential or token ever appears on a command line. Provider keys live in each tool's own config file.
5. TLS verification stays on. No sudo, no profile edits, no absolute paths.
6. Exit codes: 0 ok, 1 scope file invalid, 2 usage or missing input, 3 refusal.

## Output
recon_output/[target]/[timestamp]/ holds the host list, the probe results, the archive URLs, a list of what was dropped as out of scope, and a small run summary.

## Wire it in
Name the tool set in tools/install_tools.sh. Name the tests in tools/tests/. Run the wiring check.
