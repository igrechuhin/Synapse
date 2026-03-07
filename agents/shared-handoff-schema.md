---
name: shared-handoff-schema
description: Reference document defining typed JSON schemas for inter-agent communication. All agents MUST return results conforming to these schemas. Orchestrators MUST validate agent output against the relevant schema before passing data to the next agent.
---

# Shared Handoff Schema

This document defines **typed JSON schemas** for structured communication between orchestrator prompts and their delegated agents. Every agent MUST return a result conforming to the relevant schema in its `## Completion` section. Orchestrators MUST validate the structure before passing data downstream.

## Why Typed Handoffs

- **Eliminates state loss**: Explicit fields prevent the orchestrator from forgetting agent results mid-workflow
- **Enables validation**: Orchestrators can verify required fields are present before proceeding
- **Single source of truth**: Agents and orchestrators reference the same schema

## Usage

1. **Agents**: In your `## Completion` section, format your result as a JSON code block matching the schema for your agent type
2. **Orchestrators**: After an agent completes, parse the JSON result and verify all required fields are present. If a required field is missing, re-run the agent or STOP with an error.
3. **Downstream agents**: Reference specific fields from the upstream agent's handoff by name (e.g., `step_1_result.step_description`)

---

## CommonChecklistResult

**Produced by**: `common-checklist` agent
**Consumed by**: All orchestrator prompts (before delegating to specialized agents)

```json
{
  "agent": "common-checklist",
  "status": "complete | error",
  "structure_info": {
    "paths": {
      "plans": "/absolute/path/to/plans",
      "memory_bank": "/absolute/path/to/memory-bank",
      "reviews": "/absolute/path/to/reviews",
      "rules": "/absolute/path/to/rules"
    },
    "root": "/absolute/path/to/project",
    "plans_exist": true
  },
  "memory_bank_loaded": ["activeContext.md", "roadmap.md", "..."],
  "memory_bank_warnings": [],
  "rules_loaded": true,
  "primary_language": "Python 3.13",
  "error": null
}
```

**Required fields**: `agent`, `status`, `structure_info`, `memory_bank_loaded`, `primary_language`

**Note**: The `structure_info.paths.*` keys mirror `get_structure_info()` output for consistency.

---

## RoadmapImplementerResult

**Produced by**: `roadmap-implementer` agent
**Consumed by**: `implement-executor` agent (via orchestrator)

```json
{
  "agent": "roadmap-implementer",
  "status": "complete | no_pending_steps | error",
  "step_description": "Add response_format parameter to manage_file",
  "step_title": "Phase 95: manage_file response format",
  "plan_file_path": "/absolute/path/to/plan.md",
  "plan_file_basename": "phase-95-manage-file-response-format.md",
  "context_loaded": true,
  "rules_loaded": true,
  "dependencies": [],
  "error": null
}
```

**Required fields**: `agent`, `status`, `step_description`

---

## ImplementExecutorResult

**Produced by**: `implement-executor` agent
**Consumed by**: `implement-finalizer` agent (via orchestrator)

```json
{
  "agent": "implement-executor",
  "status": "complete | quality_gate_failed | error",
  "files_changed": ["src/cortex/tools/file_ops.py", "tests/tools/test_file_ops.py"],
  "tests_passed": true,
  "test_coverage": 94.2,
  "quality_gate_passed": true,
  "quality_issues_remaining": [],
  "implementation_summary": "Added response_format parameter with 'content' and 'summary' modes",
  "error": null
}
```

**Required fields**: `agent`, `status`, `quality_gate_passed`

---

## ImplementFinalizerResult

**Produced by**: `implement-finalizer` agent
**Consumed by**: Orchestrator (final step of implement workflow)

```json
{
  "agent": "implement-finalizer",
  "status": "complete | error",
  "memory_bank_updated": true,
  "roadmap_entry_removed": true,
  "progress_updated": true,
  "active_context_updated": true,
  "plan_archived": true,
  "roadmap_sync_passed": true,
  "error": null
}
```

**Required fields**: `agent`, `status`, `memory_bank_updated`, `roadmap_sync_passed`

---

## ContextEffectivenessResult

**Produced by**: `context-effectiveness-analyzer` agent
**Consumed by**: `analyze.md` orchestrator (report assembly)

```json
{
  "agent": "context-effectiveness-analyzer",
  "status": "complete | no_data | unavailable",
  "sessions_analyzed": { "new": 1, "total": 5 },
  "calls_analyzed": 3,
  "key_metrics": {
    "avg_token_utilization": 0.72,
    "precision": 0.85,
    "recall": 0.90,
    "feedback_types": {}
  },
  "role_recommendations": {},
  "zero_budget_warnings": [],
  "error": null
}
```

**Required fields**: `agent`, `status`

---

## SessionOptimizationResult

**Produced by**: `session-optimization-analyzer` agent
**Consumed by**: `analyze.md` orchestrator (report assembly)

```json
{
  "agent": "session-optimization-analyzer",
  "status": "complete | error",
  "mistake_patterns": [],
  "root_causes": [],
  "recommendations": [],
  "tool_anomalies": [],
  "error": null
}
```

**Required fields**: `agent`, `status`

---

## ToolsOptimizerResult

**Produced by**: `tools-optimizer` agent
**Consumed by**: `analyze.md` orchestrator (report assembly)

```json
{
  "agent": "tools-optimizer",
  "status": "complete | unavailable",
  "tool_budget": { "registered_count": 38, "target": 40, "hard_limit": 80, "status": "OK" },
  "dead_tools": [],
  "duplicates": [],
  "incomplete_consolidations": [],
  "consolidation_candidates": [],
  "total_reduction_potential": 0,
  "actionable_recommendation": "",
  "report_subsection": "",
  "error": null
}
```

**Required fields**: `agent`, `status`, `tool_budget`

---

## SessionCompactorResult

**Produced by**: `session-compactor` agent
**Consumed by**: `analyze.md` orchestrator (report assembly)

```json
{
  "agent": "session-compactor",
  "status": "complete | error",
  "compaction_status": "compacted",
  "session_id": "2026-03-06T14-30",
  "token_savings": 1200,
  "snapshot_paths": [],
  "lint_status": "clean | warnings",
  "error": null
}
```

**Required fields**: `agent`, `status`, `session_id`

---

## ImprovementsPlannerResult

**Produced by**: `improvements-planner` agent
**Consumed by**: `analyze.md` orchestrator (report assembly)

```json
{
  "agent": "improvements-planner",
  "status": "complete | skipped | error",
  "plan_file": "/absolute/path/to/plan.md",
  "roadmap_updated": true,
  "error": null
}
```

**Required fields**: `agent`, `status`

---

## PlanCreatorResult

**Produced by**: `plan-creator` agent
**Consumed by**: `create-plan.md` orchestrator

```json
{
  "agent": "plan-creator",
  "status": "complete | error",
  "plan_file_path": "/absolute/path/to/plan.md",
  "plan_title": "Phase 95: manage_file response format",
  "plan_reused": false,
  "enriched_existing": false,
  "similarity_decision": "create_new | enrich_existing",
  "similarity_table": [
    {
      "candidate": "phase-81-oversized-module-reduction.md",
      "component_match": 1,
      "keyword_overlap": 1,
      "action_verb_match": 0,
      "score": 2,
      "similar": true
    }
  ],
  "error": null
}
```

**Required fields**: `agent`, `status`, `plan_file_path`, `similarity_decision`

---

## MemoryBankUpdaterResult

**Produced by**: `memory-bank-updater` agent
**Consumed by**: Various orchestrators

```json
{
  "agent": "memory-bank-updater",
  "status": "complete | error",
  "roadmap_updated": true,
  "plan_registered": true,
  "entry_section": "pending",
  "error": null
}
```

**Required fields**: `agent`, `status`

---

## BugDetectorResult

**Produced by**: `bug-detector` agent
**Consumed by**: `review.md` orchestrator (report assembly)

```json
{
  "agent": "bug-detector",
  "status": "complete",
  "bugs": [
    {
      "severity": "Critical | High | Medium | Low",
      "location": "src/cortex/tools/file_ops.py:42",
      "description": "Unguarded None access on optional field",
      "suggestion": "Add None check before attribute access"
    }
  ],
  "counts": { "critical": 0, "high": 1, "medium": 2, "low": 0 },
  "language_checks_applied": "Python",
  "error": null
}
```

**Required fields**: `agent`, `status`, `bugs`, `counts`

---

## SubmoduleHandlerResult

**Produced by**: `submodule-handler` agent
**Consumed by**: `commit.md` orchestrator (Step 11)

```json
{
  "agent": "submodule-handler",
  "status": "clean | pointer_only | committed | dirty_after_commit | commit_failed | error",
  "submodule_path": "/absolute/path/to/synapse",
  "push_succeeded": true,
  "push_error": null,
  "pointer_updated": true,
  "error": null
}
```

**Required fields**: `agent`, `status`

---

## FinalGateValidatorResult

**Produced by**: `final-gate-validator` agent
**Consumed by**: `commit.md` orchestrator (Step 12 -> Step 13 gate)

```json
{
  "agent": "final-gate-validator",
  "status": "passed | failed | error",
  "phases_executed": {
    "markdown_revalidation": true,
    "formatting": true,
    "type_check": true,
    "quality": true,
    "spelling": true,
    "test_naming": true,
    "markdown_lint": true,
    "quality_recheck": true,
    "tests_coverage": true
  },
  "phases_passed": {
    "markdown_revalidation": true,
    "formatting": true,
    "type_check": true,
    "quality": true,
    "spelling": true,
    "test_naming": true,
    "markdown_lint": true,
    "quality_recheck": true,
    "tests_coverage": true
  },
  "coverage": 0.92,
  "fix_loops_executed": 0,
  "fallbacks_used": [],
  "connection_errors": [],
  "dirty_state_skips": [],
  "error": null
}
```

**Required fields**: `agent`, `status`, `phases_executed`, `phases_passed`, `coverage`

---

## CommitStateTrackerResult

**Produced by**: `commit-state-tracker` agent
**Consumed by**: `commit.md` orchestrator (state management across pipeline)

```json
{
  "agent": "commit-state-tracker",
  "status": "complete | error",
  "operation": "write | read | clear",
  "state": {
    "pipeline_id": "2026-03-07T14-30",
    "current_step": 12,
    "rules_loaded": true,
    "mcp_healthy": true,
    "phase_a": {
      "executed": true,
      "passed": true,
      "coverage": 0.92
    },
    "steps_completed": {},
    "final_gate": {
      "executed": false,
      "all_passed": false
    },
    "source_files_dirty_since_phase_a": false
  },
  "checkpoint_path": "/absolute/path/to/commit-pipeline-state.json",
  "error": null
}
```

**Required fields**: `agent`, `status`, `operation`

---

## AgentHealthCheckerResult

**Produced by**: `agent-health-checker` agent
**Consumed by**: All orchestrator prompts (pre-flight validation before any delegation)

```json
{
  "agent": "agent-health-checker",
  "status": "passed | failed | error",
  "pipeline_name": "commit",
  "agents_checked": 12,
  "found_agents": ["error-fixer.md", "quality-checker.md"],
  "missing_agents": [],
  "malformed_agents": [],
  "unregistered_agents": [],
  "error": null
}
```

**Required fields**: `agent`, `status`, `pipeline_name`, `agents_checked`, `missing_agents`

---

## PipelineStateTrackerResult

**Produced by**: `pipeline-state-tracker` agent
**Consumed by**: `review.md` and `analyze.md` orchestrators (state management)

```json
{
  "agent": "pipeline-state-tracker",
  "status": "complete | no_checkpoint | error",
  "operation": "write | read | clear",
  "pipeline_name": "review | analyze",
  "state": {
    "pipeline_name": "review",
    "pipeline_id": "2026-03-07T14-30",
    "current_step": "step_3_consistency",
    "steps": {
      "step_1_static_analysis": { "status": "complete", "result": {} },
      "step_2_bug_detection": { "status": "complete", "result": {} }
    }
  },
  "checkpoint_path": "/absolute/path/to/review-pipeline-state.json",
  "error": null
}
```

**Required fields**: `agent`, `status`, `operation`, `pipeline_name`

**Note**: The `state.steps.*.result` fields conform to the individual agent schemas defined earlier in this document (e.g., `BugDetectorResult` for step_2_bug_detection).

---

## Validation Rules

Orchestrators MUST check:

1. **`status` field exists** and is not `"error"` (unless the orchestrator has error-handling logic)
2. **All required fields are present** for the specific schema
3. **Downstream dependencies are met**: e.g., `quality_gate_passed` must be `true` before invoking `implement-finalizer`; `final-gate-validator.status` must be `"passed"` before Step 13

If validation fails, the orchestrator should:

- Log the missing/invalid fields
- Re-run the agent if the issue is transient
- STOP with a clear error message if the issue is persistent
