Generator: a scope organizer launcher for another harness
What: Prompt that creates scripts/organize_scope_[harness].sh from the template.
Who writes: You, by sending the prompt below to Claude Code.
Who reads: Claude Code, once.
Wired into: scripts/_TEMPLATE_ORGANIZER.md, scripts/organize_scope_claude.sh

Read scripts/_TEMPLATE_ORGANIZER.md and scripts/organize_scope_claude.sh.
Create scripts/organize_scope_[harness].sh for [harness and its non-interactive command].
Keep the five duties. Use the harness's own allowlist options, never a flag that skips permissions.
Reuse scripts/lib/organize_scope_common.sh. Do not edit the Claude launcher.
Then run python3 tools/wiring_check.py and fix what it reports.
