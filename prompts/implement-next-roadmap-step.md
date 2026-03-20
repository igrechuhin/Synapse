# Implement Next Roadmap Step

**CRITICAL**: Execute ALL phases below AUTOMATICALLY. Do NOT pause, summarize, or ask for confirmation between phases. Start with Selection immediately. When a roadmap item is too large to finish in one session, make concrete, high-impact partial progress and update plans/status accordingly instead of stopping with no changes.

This is part of the **compound-engineering loop** (Plan → Work → Review → Compound). The Finalize phase is the Compound step.

## Sequential Execution Order

Each phase must complete before the next begins:

1. **Selection** (inline) → 2. **Implementation** (subagent) → 3. **Finalize** (inline) → 4. **Verify** (inline) → 5. **Fix** (inline)

---

## Pipeline Initialization

Before starting, call:

```text
pipeline_handoff(operation="init", pipeline="implement")
```

---

## Selection — run inline (no subagent)

**IMPORTANT**: Run Selection inline in the orchestrator — do NOT use the `implement-select` subagent. Subagents in Cursor may not have reliable MCP access.

Steps to run inline:

1. Call `session()` to verify MCP health. If unhealthy, STOP.
2. Read the roadmap: `manage_file(file_name="roadmap.md", operation="read")`. If Cursor strips args, read `.cortex/memory-bank/roadmap.md` directly.
3. If the user provided an explicit plan hint (e.g. `/cortex/implement @.cortex/plans/<slug>.md`):
   - Read the referenced plan file directly.
   - Verify the plan exists and is not archived/COMPLETE.
   - If eligible, use it as the selected step.
   - If ineligible, fall back to roadmap priority selection below.
4. When no eligible explicit plan: identify the next pending step by priority:
   - Blockers (ASAP Priority) — first item
   - Active Work (in progress) — first item
   - Pending plans — first item
   - If no pending steps exist: report "Roadmap complete" and STOP.
5. Read the `cortex://context` resource for implementation context (zero-arg, reads task from session config). Non-blocking if unavailable.
6. Read the `cortex://rules` resource for coding standards. Non-blocking if unavailable.
7. If the selected step references a plan file, read it directly. Extract implementation steps, success criteria, testing strategy, and which steps are already done.
8. Write result:

```text
pipeline_handoff(operation="write", pipeline="implement", phase="select",
  data='{"status":"complete","selected_step":"<title>","plan_file":"<path or null>","selection_source":"explicit_plan"|"roadmap_priority","roadmap_section":"<section>"}')
```

**GATE**: Read `pipeline_handoff(operation="read", pipeline="implement")` and verify `phases.select.status == "complete"`. If `phases.select.status == "roadmap_complete"`: report "Roadmap complete" and STOP.

---

## Implementation — use the `implement-code` subagent

This is the only phase that uses a subagent (for context isolation during heavy coding work).

Before invoking, write the task:

```text
pipeline_handoff(operation="write", pipeline="implement", phase="code",
  data='{"selected_step": "<from select>", "plan_file": "<from select>", "roadmap_section": "<from select>"}')
```

Use the `implement-code` subagent to scope the smallest meaningful subtask, implement it with tests, and run the quality gate.

**GATE**: Read state and verify `phases.code.status == "passed"` before proceeding to Finalize.

---

## Finalize — run inline (no subagent)

**IMPORTANT**: Run Finalize inline in the orchestrator.

Read the implementation result from pipeline state:

```text
pipeline_handoff(operation="read", pipeline="implement")
```

Extract: `phases.code.step_fully_complete`, `phases.code.subtask`, `phases.code.files_changed`, `phases.code.coverage`, `phases.select.plan_file`, `phases.select.selected_step`.

**If the roadmap step is fully completed**:

Call `plan(operation="complete", plan_title="{exact roadmap title}", summary="{summary}", plan_file_name="{filename}.md", progress_entry="**{step_title}** - COMPLETE. {summary}", completion_date="YYYY-MM-DD")`.

This single call atomically:

- Removes the roadmap entry
- Appends to activeContext under Completed Work
- Appends to progress.md
- Moves the plan file to `.cortex/plans/archive/`

**Rule**: Never call `update_memory_bank` for roadmap/activeContext/progress when completing a step — `plan(complete)` handles all of it.

**If only part of the step was completed**:

1. Call `update_memory_bank(operation="progress_append", date_str="YYYY-MM-DD", entry_text="**{step_title}** - PARTIAL. {summary}")`.
2. Call `update_memory_bank(operation="active_context_append", date_str="YYYY-MM-DD", title="{step_title} (PARTIAL)", summary="{summary}")` only if the partial work materially affects active behavior.
3. Do NOT remove the roadmap entry.
4. If a plan file was used: update its status to `IN_PROGRESS` with notes on what's done vs. remaining.

Write result:

```text
pipeline_handoff(operation="write", pipeline="implement", phase="finalize",
  data='{"status":"complete","memory_bank_updated":true,"roadmap_entry":"removed"|"kept","plan_file":"archived"|"updated"|"none"}')
```

**GATE**: Verify `phases.finalize.status == "complete"` before Verify.

---

## Verify — run inline (no subagent)

**IMPORTANT**: Run Verify inline. Read-only checks only.

1. Read `.cortex/memory-bank/roadmap.md`.
   - If fully completed: verify the step's entry is absent.
   - If partial: verify the entry is still present.
2. Read `.cortex/memory-bank/progress.md`.
   - Verify a new entry for today exists.
3. Call `plan(operation="archive_completed")` to archive any remaining plans with `status: COMPLETE`.
4. Write result:

```text
pipeline_handoff(operation="write", pipeline="implement", phase="verify",
  data='{"status":"passed","roadmap_check":"passed","progress_check":"passed","stray_complete_plans":[]}')
```

**GATE**: Verify `phases.verify.status == "passed"`.

---

## Fix — run inline (no subagent)

**IMPORTANT**: Run Fix inline. This ensures all quality, test, and docs issues are resolved before the session ends. Follow the **fix.md** prompt logic (`target=all`):

1. **Quality**: call `fix_quality_issues()`, then `run_quality_gate()`. If issues remain, fix inline and retry (max 3 iterations).
2. **Tests**: if `run_quality_gate()` reports test failures, diagnose and fix them (max 3 iterations).
3. **Docs**: call `run_docs_gate()`. If timestamps or roadmap_sync fail, fix via `manage_file()` and retry (max 3 iterations).

Write result:

```text
pipeline_handoff(operation="write", pipeline="implement", phase="fix",
  data='{"status":"passed"|"failed","quality_passed":<bool>,"tests_passed":<bool>,"docs_passed":<bool>,"fix_iterations":<n>}')
```

**GATE**: `phases.fix.status == "passed"` is recommended but non-blocking — if fix fails after 3 iterations per target, log remaining issues and proceed to Cleanup. The subsequent `/cortex/commit` pipeline will catch any remaining problems.

---

## Cleanup

After successful Verify and Fix:

```text
pipeline_handoff(operation="clear", pipeline="implement")
```

## Resuming After Context Compression

If context is lost mid-pipeline, call:

```text
pipeline_handoff(operation="read", pipeline="implement")
```

This restores the full record of completed phases — continue from the first phase not yet present.

## Error Handling

- **Selection fails (MCP unhealthy)**: STOP immediately
- **Selection returns roadmap_complete**: Report "Roadmap complete" and STOP
- **Quality gate fails after 3 iterations**: STOP, report unresolvable issues
- **Finalize fails (memory bank crash)**: STOP, report with FIX-ASAP priority
- **Quality gate unavailable (doc-only sessions)**: Record "Quality gate skipped" and proceed to Finalize

## Success Criteria

- Implementation complete and all tests pass
- Quality gate passed (zero lint, file-size, function-length, type_check violations)
- Coverage >= 90% global, >= 95% for new/modified code
- Memory bank updated (roadmap entry removed or retained correctly, progress added, activeContext updated)
- Completed plans archived; partial plans marked IN_PROGRESS
- Fix phase executed (quality + tests + docs all green, or remaining issues logged)
- Pipeline state cleared
