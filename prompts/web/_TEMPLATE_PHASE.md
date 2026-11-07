# Template: a phase prompt
What: The shape of one finished phase prompt in prompts/web.
Who writes: The repo author.
Who reads: prompts/web/_GENERATE_PHASES.md and anyone adding a phase.
Wired into: prompts/web/_GENERATE_PHASES.md, prompts/web/_TEMPLATE_LOOP.md

A phase prompt is run by a fresh subagent that starts from nothing but the files. Copy this shape.

~~~text
# Phase [P]: [name]
What: [one sentence]
Who writes: [who]
Who reads: [the phase subagent and the orchestrator]
Wired into: [the loop file, the routing reference, the evidence reference, others; each must list this file back]

Mode: [triage read-only, or test with approval for state change]

## Before Step 1
[Tools to load. Entry gate already passed. Scope decision line rule.]

## Step 1: your bounded state
python3 tools/ledger_gate.py packet --target [target] --phase [P]

## Consult
[knowledge/INDEX.md; the schema blocks this phase writes; evidence_rules.md; routing_and_handoff.md]

## Steps
[Numbered. One action each.]

## What this phase writes
[Which ledger blocks, which files, nothing else]

## The gate it must pass
python3 tools/ledger_gate.py check --target [target] --phase [P]
[Say that the orchestrator runs it after the phase, that a passing check deletes the snapshot, and that the phase must not run check itself]

## Refusals
[When to stop]

## ROUTING
[Allowed final lines for this phase]

## Write-back
[Pointer to the append-only rule]
~~~

## Wire it in

1. The loop file names the new phase by its exact path.
2. The routing reference lists its ROUTING values.
3. The schema lists its required columns under required_by_phase.
4. `prompts/README.md` and `STRUCTURE.md` list it.
5. `python3 tools/wiring_check.py` passes.
