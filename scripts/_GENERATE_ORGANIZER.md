What: Prompt that creates scripts/organize_scope_[harness].sh, a scope organizer launcher for another harness, from the template.
Who writes: The repo author.
Who reads: You, pasting it into Claude Code.
Wired into: scripts/_TEMPLATE_ORGANIZER.md, scripts/organize_scope_claude.sh

Read scripts/_TEMPLATE_ORGANIZER.md and scripts/organize_scope_claude.sh.
Create scripts/organize_scope_[harness].sh for [harness and its non-interactive command].
Keep the five duties. Use the harness's own allowlist options, never a flag that skips permissions.
Reuse scripts/lib/organize_scope_common.sh. Do not edit the Claude launcher.
Then run python3 tools/wiring_check.py and fix what it reports.
