# Implement Next Roadmap Step

**CRITICAL**: Execute ALL phases below AUTOMATICALLY. Do NOT pause, summarize, or ask for confirmation between phases. Start with Selection immediately. When a roadmap item is too large to finish in one session, make concrete, high-impact partial progress and update plans/status accordingly instead of stopping with no changes.

This is part of the **compound-engineering loop** (Plan → Work → Review → Compound). The Finalize phase is the Compound step.

## Sequential Execution Order

Each phase must complete before the next begins:

1. **Selection** → 2. **Implementation** → 3. **Finalize** → 4. **Verify**

---

## Pipeline Initialization

Before invoking Selection, call:
```
pipeline_handoff(operation="init", pipeline="implement")
```

This creates `.cortex/.session/{session_id}/implement/` where all phase inputs and outputs are stored for the lifetime of this run.

---

## Selection — use the `implement-select` subagent

Before invoking, write the task (include any explicit plan hint if the user provided one):
```
pipeline_handoff(operation="write_task", pipeline="implement", phase="select",
  data='{"explicit_plan_path": "<slug or null>"}')
```

Use the `implement-select` subagent to:

- Honor any explicit plan reference when `/user-cortex/implement` is invoked with a targeted plan (for example, `/user-cortex/implement @.cortex/plans/<slug>.md`), by reading `explicit_plan_path` from its task and preferring that plan **when it exists and is eligible**.
- When an explicit plan is missing, archived/COMPLETE, or otherwise ineligible, record a short note or error and fall back to normal roadmap priority selection.
- When no explicit plan hint is provided, read the roadmap, identify the next pending step by priority (Blockers first, then Active Work, then Pending plans), load implementation context and rules, and read the plan file if one exists.

**GATE**: Read `pipeline_handoff(operation="read_state", pipeline="implement")` and verify `phases.select.status == "complete"` before proceeding. If `phases.select.status == "roadmap_complete"`: report "Roadmap complete" and STOP.

---

## Implementation — use the `implement-code` subagent

Before invoking, read the state and forward what `implement-code` needs:
```
pipeline_handoff(operation="write_task", pipeline="implement", phase="code",
  data='{"selected_step": "<from phases.select.selected_step>",
         "plan_file": "<from phases.select.plan_file>",
         "roadmap_section": "<from phases.select.roadmap_section>"}')
```

Use the `implement-code` subagent to scope the smallest meaningful subtask, implement it with tests, and run the quality gate via the job-based API (start + poll).

**GATE**: Read state and verify `phases.code.status == "passed"` before proceeding to Finalize.

---

## Finalize — use the `implement-finalize` subagent

Before invoking, forward the implementation result:
```
pipeline_handoff(operation="write_task", pipeline="implement", phase="finalize",
  data='{"step_fully_complete": <bool from phases.code.step_fully_complete>,
         "subtask": "<from phases.code.subtask>",
         "files_changed": <from phases.code.files_changed>,
         "coverage": <from phases.code.coverage>,
         "plan_file": "<from phases.select.plan_file>",
         "selected_step": "<from phases.select.selected_step>"}')
```

Use the `implement-finalize` subagent to update the memory bank (activeContext.md, progress.md, roadmap.md) and handle the plan file (archive if complete, mark IN_PROGRESS if partial).

**GATE**: Read state and verify `phases.finalize.status == "complete"` before proceeding to Verify.

---

## Verify — use the `implement-verify` subagent

Before invoking:
```
pipeline_handoff(operation="write_task", pipeline="implement", phase="verify",
  data='{"selected_step": "<from phases.select.selected_step>",
         "step_fully_complete": <bool from phases.code.step_fully_complete>}')
```

Use the `implement-verify` subagent to confirm the roadmap and progress entries are correct and no stray COMPLETE plans remain in the plans root. Read-only.

**GATE**: Read state and verify `phases.verify.status == "passed"`. If stray COMPLETE plans are reported: archive them before declaring the pipeline complete.

---

## Cleanup

After successful Verify:
```
pipeline_handoff(operation="clear", pipeline="implement")
```

## Resuming After Context Compression

If context is lost mid-pipeline, call:
```
pipeline_handoff(operation="read_state", pipeline="implement")
```
This restores the full record of completed phases — continue from the first phase not yet present in `phases`.

## Error Handling

- **Selection fails (MCP unhealthy)**: STOP immediately
- **Selection returns roadmap_complete**: Report "Roadmap complete" and STOP
- **Quality gate fails after 3 iterations**: STOP, report unresolvable issues
- **Finalize fails (memory bank crash)**: STOP, report with FIX-ASAP priority
- **Quality gate unavailable (doc-only sessions)**: Record "Quality gate skipped — doc-only session" and proceed to Finalize

## Success Criteria

- Implementation complete and all tests pass
- Quality gate passed (zero lint, file-size, function-length, type_check violations)
- Coverage >= 90% global, >= 95% for new/modified code
- Memory bank updated (roadmap entry removed or retained correctly, progress added, activeContext updated)
- Completed plans archived; partial plans marked IN_PROGRESS
- Pipeline state cleared
