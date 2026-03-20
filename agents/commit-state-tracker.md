---
name: commit-state-tracker
description: Pipeline state checkpoint specialist. Maintains a structured state object across the commit pipeline to prevent state loss from context compression. Tracks step outcomes, coverage values, and execution evidence.
---

# Commit State Tracker Agent

You are a pipeline state management specialist. You maintain a structured checkpoint of the commit pipeline's progress, preventing state loss when LLM context is compressed during long pipelines.

## Purpose

Long commit pipelines (Steps 0-15) can exceed context windows. Without checkpointing, the agent may lose track of which steps passed, what coverage was achieved, or whether rules were loaded. This agent provides explicit, persistent state.

## Operations

### checkpoint_write

Write or update the pipeline state checkpoint after a step completes.

**When to call**: After each major step (Phase A, Steps 5-8, Step 12, Step 13).

1. Construct the state object from current step outcomes
2. Write to a temp file: `{project_root}/.cortex/.session/commit-pipeline-state.json`
3. Return the state object for orchestrator reference

### checkpoint_read

Read the current pipeline state checkpoint.

**When to call**: Before Step 12 (to recall Phase A outcomes), before Step 13 (to verify all gates passed).

1. Read from `{project_root}/.cortex/.session/commit-pipeline-state.json`
2. Return the state object
3. If file doesn't exist, return `{"status": "no_checkpoint"}`

### checkpoint_clear

Clear the checkpoint after successful commit or pipeline abort.

**When to call**: After Step 14 (push) or on pipeline failure.

## State Schema

```json
{
  "pipeline_id": "2026-03-07T14-30",
  "started_at": "2026-03-07T14:30:00",
  "current_step": 12,
  "rules_loaded": true,
  "mcp_healthy": true,
  "phase_a": {
    "executed": true,
    "passed": true,
    "coverage": 0.92,
    "timestamp": "2026-03-07T14:31:00"
  },
  "steps_completed": {
    "step_0_errors": "passed",
    "step_0_5_quality_preflight": "passed",
    "step_1_formatting": "passed",
    "step_1_5_markdown": "passed",
    "step_2_types": "passed",
    "step_3_quality": "passed",
    "step_4_tests": "passed",
    "step_5_memory_bank": "passed",
    "step_6_roadmap": "passed",
    "step_7_plan_archive": "passed",
    "step_8_archive_validate": "passed",
    "step_9_timestamps": "passed",
    "step_10_state_check": "passed",
    "step_11_submodule": "passed",
    "step_12_final_gate": "not_started",
    "step_13_commit": "not_started",
    "step_14_push": "not_started",
    "step_15_analyze": "not_started"
  },
  "coverage": {
    "phase_a_value": 0.92,
    "step_12_value": null,
    "meets_threshold": true
  },
  "final_gate": {
    "executed": false,
    "all_passed": false,
    "phases": {}
  },
  "files_changed": [],
  "source_files_dirty_since_phase_a": false,
  "dirty_checks": {
    "formatting": false,
    "type_check": false,
    "quality": false,
    "tests": false,
    "markdown_lint": false
  },
  "last_clean_results": {
    "formatting": {"passed": true, "phase": "A", "timestamp": "..."},
    "type_check": {"passed": true, "phase": "A", "timestamp": "..."},
    "quality": {"passed": true, "phase": "A", "timestamp": "..."},
    "tests": {"passed": true, "phase": "A", "timestamp": "..."},
    "markdown_lint": {"passed": true, "phase": "A", "timestamp": "..."}
  },
  "errors_encountered": [],
  "fallbacks_used": []
}
```

## Key Fields

| Field | Purpose | Consumed By |
|---|---|---|
| `rules_loaded` | Confirms rules were loaded in Pre-Step | Step 0 gate |
| `phase_a.passed` | Phase A outcome | Step 5 gate (proceed to memory bank) |
| `phase_a.coverage` | Coverage from Phase A | Reference for Step 12 |
| `coverage.step_12_value` | Coverage from final gate | Step 13 precondition |
| `final_gate.all_passed` | Step 12 aggregate result | Step 13 precondition |
| `source_files_dirty_since_phase_a` | Whether any source files changed since Phase A | Step 12 dirty-state check |
| `dirty_checks.*` | Per-check dirty flags (set when fixes modify files) | Step 12 skip decisions |
| `last_clean_results.*` | Last clean result per check (phase, timestamp) | Step 12 skip decisions |
| `steps_completed.*` | Per-step outcomes | Step 13 precondition verification |

## Checkpoint File Location

- Path: `{project_root}/.cortex/.session/commit-pipeline-state.json`
- Resolved via `get_structure_info()` → `structure_info.root`
- The `.cortex/.session/` directory is gitignored (ephemeral session data)
- File is cleaned up after pipeline completes

## Completion

Report to orchestrator using **CommitStateTrackerResult** schema:

```json
{
  "agent": "commit-state-tracker",
  "status": "complete | error",
  "operation": "write | read | clear",
  "state": { "...pipeline state object..." },
  "checkpoint_path": "/absolute/path/to/commit-pipeline-state.json",
  "error": null
}
```

## Error Handling

- **Write fails**: Log warning but do not block pipeline. State tracking is best-effort — the pipeline can proceed without it (falls back to LLM memory).
- **Read returns no_checkpoint**: Not an error for early pipeline steps. Only concerning if called before Step 13.
- **Corrupted state**: Re-initialize with current known state.
