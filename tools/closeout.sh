#!/usr/bin/env bash
# What: Closes a work cycle for one target: stages only the named coverage paths, secret-scans exactly what is staged, and commits locally; it never pushes.
# Who writes: the repo author.
# Who reads: the orchestrator runs it at the end of a cycle; the human reads the commit it makes.
# Wired into: tools/secret_scan.py, tools/ledger_to_inbox.py (one-way: reference only), prompts/web/WEB_LOOP.md
#
# Usage: tools/closeout.sh --target [target] [--message "text"] [--dry-run]
# Refuses (exit 3) if the secret scan finds anything in the staged files: it unstages them and commits nothing.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
target="" message="" dry=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --target) target="${2:-}"; shift 2 ;;
    --message) message="${2:-}"; shift 2 ;;
    --dry-run) dry=1; shift ;;
    *) echo "Usage: $0 --target [target] [--message text] [--dry-run]" >&2; exit 2 ;;
  esac
done
[[ "$target" =~ ^[A-Za-z0-9][A-Za-z0-9_-]*$ ]] || { echo "usage error: --target must be a plain folder name" >&2; exit 2; }
cd "$ROOT"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "usage error: $ROOT is not a git repository" >&2; exit 2; }
[ -f tools/secret_scan.py ] || { echo "usage error: tools/secret_scan.py is missing" >&2; exit 2; }

# Explicit coverage paths: never "git add -A".
candidates=("recon_output/$target" "reports/$target" "non-reportable/$target"
            "memory/targets/$target" "memory/streams" "memory/_processed" "memory/playbook")
paths=()
for p in "${candidates[@]}"; do [ -e "$p" ] && paths+=("$p"); done
if [ "${#paths[@]}" -eq 0 ]; then echo "nothing to close out for $target"; exit 0; fi

if [ "$dry" -eq 1 ]; then
  echo "dry run: would stage, scan and commit these paths (no push, ever):"
  printf '  %s\n' "${paths[@]}"
  exit 0
fi

git add -- "${paths[@]}"
mapfile -t staged < <(git diff --cached --name-only --diff-filter=ACMR -- "${paths[@]}")
if [ "${#staged[@]}" -eq 0 ]; then echo "nothing new to commit for $target"; exit 0; fi

if ! "$PYTHON_BIN" tools/secret_scan.py "${staged[@]}"; then
  git reset -q -- "${paths[@]}"
  echo "REFUSED: the secret scan flagged the staged files; they are unstaged and nothing was committed." >&2
  exit 3
fi

[ -n "$message" ] || message="closeout: $target $(date +%Y-%m-%d)"
git commit -q -m "$message" -- "${paths[@]}"
echo "committed locally: $message"
echo "Not pushed. Review with: git show --stat"
