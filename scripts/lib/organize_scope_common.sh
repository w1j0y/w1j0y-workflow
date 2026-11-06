#!/usr/bin/env bash
# What: Shared logic for the scope organizer launcher: path checks, prompt building, and the refusals after the agent runs.
# Who writes: the repo author (sanitized from an earlier private launcher).
# Who reads: scripts/organize_scope_claude.sh sources it; the human reads it to see what the organizer may and may not do.
# Wired into: scripts/organize_scope_claude.sh, tools/validate_scope.py, prompts/organize_scope.md
#
# Sourced, never executed. Two functions:
#   organize_scope_prepare "$@"   resolve and check paths, build PROMPT_CONTENT and the tool lists
#   organize_scope_finish STATUS  refuse unless every post-run check passes

organize_scope_prepare() {
  if [ "$#" -ne 1 ]; then
    echo "Usage: $0 targets/[target]/scope_raw.txt" >&2
    echo >&2
    echo "Optional environment:" >&2
    echo "  CLAUDE_BIN=claude   the Claude Code binary" >&2
    echo "  PYTHON_BIN=python3" >&2
    return 1
  fi

  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
  REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd -P)"
  PYTHON_BIN="${PYTHON_BIN:-python3}"
  VALIDATOR="$REPO_ROOT/tools/validate_scope.py"
  PROMPT_PATH="$REPO_ROOT/prompts/organize_scope.md"

  local given_raw="$1"
  [ -f "$PROMPT_PATH" ] || { echo "REFUSED: missing prompt: $PROMPT_PATH" >&2; return 1; }
  [ -f "$given_raw" ] || { echo "REFUSED: missing raw scope file: $given_raw" >&2; return 1; }
  [ -f "$VALIDATOR" ] || { echo "REFUSED: missing validator: $VALIDATOR" >&2; return 1; }
  command -v "$PYTHON_BIN" >/dev/null 2>&1 || { echo "REFUSED: missing $PYTHON_BIN" >&2; return 1; }

  RAW_SCOPE_ABS="$(readlink -f -- "$given_raw")"
  TARGET_DIR="$(dirname -- "$RAW_SCOPE_ABS")"
  case "$RAW_SCOPE_ABS" in
    "$REPO_ROOT"/targets/*/scope_raw.txt) ;;
    *) echo "REFUSED: the raw scope file must be targets/[target]/scope_raw.txt inside this repo (got $RAW_SCOPE_ABS)" >&2
       return 1 ;;
  esac
  RAW_SCOPE_REL="${RAW_SCOPE_ABS#"$REPO_ROOT"/}"
  TARGET_DIR_REL="${TARGET_DIR#"$REPO_ROOT"/}"
  if [ ! -s "$RAW_SCOPE_ABS" ]; then
    echo "REFUSED: the raw scope file is empty: $RAW_SCOPE_REL" >&2
    return 1
  fi

  RAW_SHA_BEFORE="$(sha256sum -- "$RAW_SCOPE_ABS" | cut -d' ' -f1)"
  LISTING_BEFORE="$(find "$TARGET_DIR" -mindepth 1 -maxdepth 1 -printf '%f\n' | sort)"
  # 1s leeway absorbs coarse filesystem timestamps; stale outputs are far older.
  START_NS=$(( $(date +%s%N) - 1000000000 ))

  # Tool lists. Read is open; Edit rules (they cover Write too) are limited to the target folder
  # (a leading double slash means an absolute path in Claude Code permission rules);
  # Bash is limited to the validator. Web and MCP tools are denied outright, so
  # "offline" is true by construction.
  ALLOWED_TOOLS=("Read" "Edit(/${TARGET_DIR}/**)"
                 "Bash(${PYTHON_BIN} tools/validate_scope.py:*)")
  DISALLOWED_TOOLS=("WebFetch" "WebSearch" "mcp__*")

  PROMPT_CONTENT="$(cat -- "$PROMPT_PATH")

## Task parameters (supplied by the launcher; authoritative)

- repo_root: $REPO_ROOT
- raw_scope_file (absolute): $RAW_SCOPE_ABS
- raw_scope_file (repo-relative; use verbatim as source_file): $RAW_SCOPE_REL
- target_dir (absolute; write all five output files here): $TARGET_DIR
- target_dir (repo-relative): $TARGET_DIR_REL
- scope_json (repo-relative; use in the README recon command): $TARGET_DIR_REL/scope.json
- validator: $PYTHON_BIN tools/validate_scope.py --raw-scope \"$RAW_SCOPE_ABS\"
- working directory: $REPO_ROOT

Read the raw scope file at the absolute path above in full, then follow every requirement in this prompt.
"
  if [ "${#PROMPT_CONTENT}" -gt 100000 ]; then
    echo "REFUSED: prompt too large (${#PROMPT_CONTENT} bytes)" >&2
    return 1
  fi
  cd "$REPO_ROOT"
}

organize_scope_finish() {
  local agent_status="$1" status=0
  if [ "$agent_status" -ne 0 ]; then
    echo "FAILED: the agent exited with status $agent_status; scope organization is NOT complete." >&2
    return "$agent_status"
  fi
  local sha_after listing_after unexpected
  sha_after="$(sha256sum -- "$RAW_SCOPE_ABS" | cut -d' ' -f1)"
  if [ "$sha_after" != "$RAW_SHA_BEFORE" ]; then
    echo "FAILED: the raw scope file was modified during the run: $RAW_SCOPE_REL" >&2
    status=1
  fi
  listing_after="$(find "$TARGET_DIR" -mindepth 1 -maxdepth 1 -printf '%f\n' | sort)"
  unexpected="$(comm -13 <(printf '%s\n' "$LISTING_BEFORE") <(printf '%s\n' "$listing_after") \
    | grep -vxF -e scope.json -e scope.txt -e guidelines.json -e guidelines.txt -e README.md || true)"
  if [ -n "$unexpected" ]; then
    echo "FAILED: unexpected new files left in $TARGET_DIR_REL:" >&2
    while IFS= read -r f; do echo "  $f" >&2; done <<<"$unexpected"
    status=1
  fi
  echo "Running offline validation..." >&2
  if ! "$PYTHON_BIN" "$VALIDATOR" --raw-scope "$RAW_SCOPE_ABS" --target-dir "$TARGET_DIR" \
        --repo-root "$REPO_ROOT" --require-fresh-since-ns "$START_NS"; then
    status=1
  fi
  if [ "$status" -ne 0 ]; then
    echo "FAILED: scope organization for $RAW_SCOPE_REL did NOT complete. Fix the problems above and re-run." >&2
    return 1
  fi
  echo "OK: organized scope files written to $TARGET_DIR_REL/ and validated."
  echo "Next: a human reads the four rules against the live program page, then runs: python3 tools/scope_check.py confirm --target [target]"
}
