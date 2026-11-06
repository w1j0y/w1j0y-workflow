# Prompts: index
What: The index of every prompt in the repo: what it does, who runs it and where its shared rules live.
Who writes: The repo author; updated when a prompt is added.
Who reads: You, to find the prompt for a job.
Wired into: STRUCTURE.md, AGENTS.md, prompts/organize_scope.md, prompts/web/WEB_LOOP.md, prompts/reference/routing_and_handoff.md, prompts/reference/evidence_rules.md, prompts/maintenance/AUDIT.md, prompts/maintenance/MAINTENANCE.md, prompts/intake/INTAKE_TOOL.md

## Scope

- `prompts/organize_scope.md`: turns a raw program page into five scope files with the four program rules. Run through `scripts/organize_scope_claude.sh`.

## Web assessment (run by the orchestrator)

- `prompts/web/WEB_LOOP.md`: the orchestrator.
- `prompts/web/01-triage.md`, `prompts/web/02-characterize.md`, `prompts/web/02_5-map-classes.md`, `prompts/web/03-test.md`: the four phases.
- `prompts/web/FINDING_VALIDATION.md`: a fresh reader's verdict on one finding.
- `prompts/web/VALIDATE_REPORT.md`: a fresh reader's audit of a drafted report.

## Shared rules

- `prompts/reference/routing_and_handoff.md`: seed preamble, parameters, ROUTING values, refusals, repair.
- `prompts/reference/evidence_rules.md`: baseline, control, variant, delta, read-back, confirmation bar.
- `prompts/reference/ledger_schema.md`: the schema the gate reads (statuses, blocks, required columns per phase).

## Maintenance and intake (human-started, end at an approval step)

- `prompts/maintenance/AUDIT.md`: the wiring audit, via the audit slash command.
- `prompts/maintenance/MAINTENANCE.md`: the learning pass, via the maintenance slash command.
- `prompts/intake/INTAKE_TOOL.md`: the three-stage tool intake, via the intake slash command.

## Meta files: templates and generators

Meta files start with an underscore. A template shows the shape of one finished file; a generator is a short prompt that makes or regenerates that file from your own resource. They are for building, never for content, and are listed here only so you can find them.

- Setup: `prompts/setup/_TEMPLATE_AGENTS.md` with `prompts/setup/_GENERATE_AGENTS.md`; `prompts/setup/_TEMPLATE_FRONTDOOR.md` with `prompts/setup/_GENERATE_FRONTDOOR.md`; `prompts/setup/_TEMPLATE_TOOL_WIRING.md` with `prompts/setup/_GENERATE_TOOL_WIRING.md`.
- Phases: `prompts/web/_TEMPLATE_PHASE.md` and `prompts/web/_TEMPLATE_LOOP.md` with `prompts/web/_GENERATE_PHASES.md`.
- Reference: `prompts/reference/_TEMPLATE_REFERENCE.md` with `prompts/reference/_GENERATE_REFERENCE.md`.
- Maintenance: `prompts/maintenance/_TEMPLATE_MAINTENANCE.md` with `prompts/maintenance/_GENERATE_MAINTENANCE.md`.
- Intake decision record: `prompts/intake/_TEMPLATE_DECISION.md`, the shape of each file in `docs/decisions/`.
- Knowledge: `knowledge/_TEMPLATE_KNOWLEDGE.md` with `knowledge/_GENERATE_KNOWLEDGE.md`.
- Memory skill files: `memory/_TEMPLATE_SKILL.md` with `memory/_GENERATE_SKILL.md`.

Each generator is at most ten lines. It names its template, its input, its output path and the check command that must pass.
