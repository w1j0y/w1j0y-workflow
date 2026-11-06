#!/usr/bin/env bash
# What: Launcher that has Claude Code turn a raw program scope page into the five organized scope files, then validates them.
# Who writes: the repo author.
# Who reads: the human runs it once per target; docs and the series show it.
# Wired into: scripts/lib/organize_scope_common.sh, prompts/organize_scope.md, tools/validate_scope.py
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)/lib/organize_scope_common.sh"

CLAUDE_BIN="${CLAUDE_BIN:-claude}"

organize_scope_prepare "$@" || exit 1
command -v "$CLAUDE_BIN" >/dev/null 2>&1 || { echo "REFUSED: missing $CLAUDE_BIN" >&2; exit 1; }

status=0
# The prompt goes in on stdin because the tool lists take several values.
# acceptEdits plus the allow list means no skip-permissions flag is needed.
printf '%s' "$PROMPT_CONTENT" | "$CLAUDE_BIN" -p \
  --permission-mode acceptEdits \
  --allowedTools "${ALLOWED_TOOLS[@]}" \
  --disallowedTools "${DISALLOWED_TOOLS[@]}" || status=$?

organize_scope_finish "$status"
