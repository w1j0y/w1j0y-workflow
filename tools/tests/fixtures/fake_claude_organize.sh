#!/usr/bin/env bash
# Fake claude for the organizer test. Records its arguments, reads the prompt on stdin,
# and writes the five scope files from the good fixture into the target folder.
set -euo pipefail
printf '%s\n' "$@" > "$FAKE_ARGS_FILE"
prompt="$(cat)"
target_dir="$(printf '%s\n' "$prompt" | sed -n 's/^- target_dir (absolute; write all five output files here): //p')"
rel="$(printf '%s\n' "$prompt" | sed -n 's/^- target_dir (repo-relative): //p')"
case "${FAKE_MODE:-ok}" in
  fail) exit 1 ;;
  nowrite) exit 0 ;;
esac
for f in scope.json scope.txt guidelines.json guidelines.txt README.md; do
  sed "s#scope_good/#$rel/#g" "$FAKE_FIXTURE/$f" > "$target_dir/$f"
done
[ "${FAKE_MODE:-ok}" = "tamper" ] && echo "more" >> "$target_dir/scope_raw.txt"
[ "${FAKE_MODE:-ok}" = "extra" ] && echo "x" > "$target_dir/notes.tmp"
exit 0
