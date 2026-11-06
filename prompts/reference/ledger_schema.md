# Ledger schema
What: The one schema the ledger gate reads: statuses, table blocks, required columns per phase and handoff rules.
Who writes: the repo author; change it here and the gate follows, nothing is hard-coded in the script.
Who reads: tools/ledger_gate.py at run time, and every phase file that writes the ledger.
Wired into: tools/ledger_gate.py, prompts/web/WEB_LOOP.md

## What the ledger is

One file per target, `recon_output/[target]/coverage_ledger.md`. It holds three markdown tables, each under its own second-level heading:

- `## Surfaces`: one row per surface worth testing, with its class, status, evidence and next step.
- `## Phase handoff`: one row per hand-off from one phase to the next, OPEN until the next phase consumes it.
- `## Finding Validation`: one row per finding file, with a verdict and the reason.

Finding files live next to the ledger as `recon_output/[target]/[target]_finding_[name].md`.

## Rules the gate enforces

The gate (`tools/ledger_gate.py`) takes a snapshot before a phase and checks after it. It looks only at rows that are new or changed since the snapshot.

- Every touched Surfaces row has a status from the status list below.
- Every touched row has the columns this phase requires, non-blank.
- Every touched handoff row has a status (OPEN or CONSUMED).
- Every finding file that is new or changed since the snapshot has a Finding Validation row naming it, with a verdict from the verdict list.
- A report is submittable only when a finding has the ready verdict and, if the program requires AI disclosure, the report carries a line starting with "AI disclosure:".

A packet (the `packet` subcommand) shows only the open rows, capped at the row cap, so a phase never reads the whole ledger.

## Status meanings

- untested: listed, not touched yet.
- no-signal: tried with a baseline and a control, nothing differed.
- blocked: could not be tested (access, rate, scope); say why in evidence.
- needs-depth: something differed, more testing needed.
- candidate: a repeatable difference exists, not yet validated.
- confirmed: validated with read-back.
- rejected: shown to be a false positive.
- skip: out of scope or not worth the time; say why.

## The machine-readable block

The gate parses the fenced json block below. Edit it with care: it must stay valid JSON.

```json
{
  "statuses": ["untested", "no-signal", "blocked", "needs-depth", "candidate", "confirmed", "rejected", "skip"],
  "open_statuses": ["untested", "needs-depth", "candidate"],
  "phases": ["01", "02", "02.5", "03"],
  "packet_row_cap": 60,
  "blocks": {
    "Surfaces": {
      "columns": ["id", "surface", "class", "status", "evidence", "next"],
      "status_column": "status",
      "required_by_phase": {
        "01": ["id", "surface", "status"],
        "02": ["id", "surface", "class", "status"],
        "02.5": ["id", "surface", "class", "status", "next"],
        "03": ["id", "surface", "class", "status", "evidence"]
      }
    },
    "Phase handoff": {
      "columns": ["id", "from", "to", "status", "note"],
      "status_column": "status",
      "handoff_statuses": ["OPEN", "CONSUMED"],
      "open_statuses": ["OPEN"],
      "required_by_phase": {
        "01": ["id", "from", "to", "status"],
        "02": ["id", "from", "to", "status"],
        "02.5": ["id", "from", "to", "status"],
        "03": ["id", "from", "to", "status", "note"]
      }
    },
    "Finding Validation": {
      "columns": ["id", "finding_file", "verdict", "reason"],
      "verdicts": ["VALID_READY_TO_REPORT", "VALID_NEEDS_MORE_WORK", "NOT_VALID"],
      "ready_verdict": "VALID_READY_TO_REPORT",
      "required": ["id", "finding_file", "verdict"]
    }
  }
}
```
