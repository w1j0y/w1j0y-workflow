# Tools needed
What: The external tools the workflow uses, why, how to install them and what limits our code applies.
Who writes: The repo author; the intake prompt adds rows for approved tools.
Who reads: You, before the first recon run.
Wired into: GETTING_STARTED.md, docs/TOOL_WIRING.md, prompts/intake/INTAKE_TOOL.md, tools/install_tools.sh (one-way: script owned by another part), tools/recon.py (one-way: script owned by another part)

Exact install lines marked "verify" must be checked against each tool's own README on the day you install; module paths and commands move. Nothing here is installed by the tests.

| Tool | Needed for | Install | API key | Rate limit our code applies |
|---|---|---|---|---|
| subfinder (ProjectDiscovery) | passive subdomains | `go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest` (verify) | none required; optional provider keys live in the tool's own config file, never on a command line | none beyond tool defaults; `tools/recon.py` caps total rate |
| httpx (ProjectDiscovery binary, not the Python package of the same name) | live probe with header and rate applied | `go install github.com/projectdiscovery/httpx/cmd/httpx@latest` (verify); check that `httpx -version` mentions ProjectDiscovery | none | rate limit set from the scope file rate |
| gau | archive URLs | `go install github.com/lc/gau/v2/cmd/gau@latest` (verify) | none | threads capped at 5 |
| jq, curl, git, python3 (3.10 or newer) | scripts | your system package manager | none | none |
| claude (Claude Code) | digest, organizer, prompts | the official install steps in the Claude Code documentation (verify) | subscription login; no key is stored in this repo | none |
| Burp Suite (Community or Professional) with the MCP Server extension | tool wiring | BApp Store inside Burp (verify; see `docs/TOOL_WIRING.md`) | none | the hook's request-rate window |
| Chrome with the Claude extension | tool wiring | Chrome Web Store (verify; see `docs/TOOL_WIRING.md`) | none | the hook's navigation rate window |

`bash tools/install_tools.sh` prints the commands for the Go tools and checks what is present; it installs into a local tools/bin only when given its run flag, edits no shell profile and uses no sudo.

Optional and not installed by default: gowitness, nuclei, ffuf. Add any of them through the intake prompt, one at a time (`prompts/intake/INTAKE_TOOL.md`).

## Where data leaves your machine

- subfinder queries public sources; archive tools query public archives.
- Claude Code sends what it reads to the model provider. This repo's scripts do not send saved page content to a model API on their own; the digest calls the model on summaries you wrote.
- Burp and Chrome send requests to the program's hosts, and only after the hook and your own approvals allow it.
