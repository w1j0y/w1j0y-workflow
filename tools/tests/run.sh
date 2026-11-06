#!/usr/bin/env bash
# What: Runs every unit test of the tools with the standard library test runner.
# Who writes: the repo author.
# Who reads: the human, GETTING_STARTED.md, and the closeout step.
# Wired into: GETTING_STARTED.md (one-way: first command a new reader runs)
set -eu
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 -B -m unittest discover -s "$HERE" -t "$HERE" -v
