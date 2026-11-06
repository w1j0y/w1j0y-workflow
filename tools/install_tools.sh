#!/usr/bin/env bash
# What: Prints the commands that install subfinder, httpx and gau into tools/bin, and runs them only when asked.
# Who writes: the repo author.
# Who reads: the human, before the first recon run; GETTING_STARTED.md points here.
# Wired into: tools/recon.py, GETTING_STARTED.md (one-way: the guide names this script)
#
# Usage: tools/install_tools.sh          print the commands and check what is present
#        tools/install_tools.sh --run    run them (needs Go 1.21 or newer; no sudo, no profile edits)
# Binaries land in tools/bin only. recon.py looks there first, so PATH never changes.
# Verify the module paths against each tool's own README before running; they can move.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
BIN="$ROOT/tools/bin"
run=0
case "${1:-}" in "") ;; --run) run=1 ;; *) echo "Usage: $0 [--run]" >&2; exit 2 ;; esac

MODULES=(
  "subfinder|github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"
  "httpx|github.com/projectdiscovery/httpx/cmd/httpx@latest"
  "gau|github.com/lc/gau/v2/cmd/gau@latest"
)

echo "Install folder: tools/bin (nothing is written elsewhere, no sudo, no shell profile edits)"
for tool in git python3 curl jq go; do
  if command -v "$tool" >/dev/null 2>&1; then echo "  found: $tool"; else echo "  missing: $tool (install it with your system package manager)"; fi
done
echo
echo "Commands:"
echo "  mkdir -p tools/bin"
for m in "${MODULES[@]}"; do
  echo "  GOBIN=\"\$PWD/tools/bin\" go install ${m#*|}"
done
echo "Check after install: tools/bin/httpx -version   (it must say ProjectDiscovery; the Python package of the same name is a different tool)"
echo "Provider keys, if you want any, go in each tool's own config file, never on a command line."

if [ "$run" -eq 1 ]; then
  command -v go >/dev/null 2>&1 || { echo "go is missing; install Go first" >&2; exit 2; }
  mkdir -p "$BIN"
  for m in "${MODULES[@]}"; do
    echo "installing ${m%%|*} ..."
    GOBIN="$BIN" go install "${m#*|}"
  done
  echo "done: $(ls "$BIN" | tr '\n' ' ')"
else
  echo
  echo "Nothing was installed. Re-run with --run to execute the commands above."
fi
