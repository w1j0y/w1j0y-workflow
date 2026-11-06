#!/usr/bin/env bash
# Fake claude for the digest test. Records its arguments, drains stdin, prints a claude-style JSON envelope.
set -euo pipefail
printf '%s\n' "$@" > "${FAKE_ARGS_FILE:-/dev/null}"
cat >/dev/null
case "${FAKE_MODE:-ok}" in
  fail) echo "boom" >&2; exit 1 ;;
  refuse) echo '{"type":"result","is_error":false,"result":"I cannot help with that."}' ;;
  empty) echo '{"type":"result","is_error":false,"structured_output":{"learnings":[],"failures":[],"decision_rules":[],"knowledge_gaps":[],"target_notes":[]}}' ;;
  ok) echo '{"type":"result","is_error":false,"structured_output":{"learnings":["A control request separates a catch-all from a real 200."],"failures":[],"decision_rules":["Run the control first."],"knowledge_gaps":[],"target_notes":[{"target":"example-program","note":"api host answers 401 without a session."}]}}' ;;
esac
