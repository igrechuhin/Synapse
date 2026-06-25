---
name: commit-final-gate
description: Use when the /cortex/commit orchestrator reaches Step 12 (final gate) after Phase C passes. Classifies what changed since Phase A, re-runs the minimal necessary quality gate. Commit must not proceed if this agent reports failed.
tools: mcp__cortex__*, Bash, Read, Edit, Grep
---

Classify scope of Phase B/C writes, run minimal gate, write result.

## Resume Check (required)

Before Step 1, call `pipeline_handoff(operation="status", pipeline="commit")`.

- If `phases.final-gate == "completed"`: skip execution, return prior result.
- If `phases.final-gate == "failed"` or `phases.final-gate == "running"`: continue and re-run this phase.
- If `phases.final-gate == "pending"` or missing: continue normally.

Immediately before Step 1, call `pipeline_handoff(operation="mark_running", pipeline="commit", phase="final-gate")`.

1. **Classify** (based on what Phases B/C actually wrote, not `git diff HEAD`):
   - `source_changed`: any `src/` or `tests/` file written by B/C.
   - `markdown_changed`: any `.md`/`.mdc` written by B/C (Phase B always touches memory-bank, so usually `true`).
   - `nothing`: no files written.
2. **Run gate**:
   - `source_changed`: write `{"operation":"write","phase":"checks","pipeline":"commit","force_fresh":true,"test_timeout":600}` to `.cortex/.session/current-task.json`, call `pipeline_handoff()`, then `run_quality_gate()`. If gate fails, delegate fixes to the fix workflow: spawn `@fix-quality` (or `@fix-tests` for test failures) rather than fixing inline. After fix workflow completes, confirm with `run_quality_gate()`. Max 3 total fix-workflow invocations.
   - `markdown_changed` only: same config write + `pipeline_handoff()` + `run_quality_gate()`. If markdown lint fails, spawn `@fix-quality` to fix. Timeout-only test failures pass if all non-test checks pass (Phase A proved tests green).
   - `nothing`: skip, set `skipped_checks:["all"]`.
3. **Write result** to `.cortex/.session/current-task.json` then call `pipeline_handoff()`:

```json
{"operation":"write","phase":"final-gate","pipeline":"commit","status":"passed","coverage":<actual>,"fix_loops_executed":<n>,"skipped_checks":[]}
```

Gate rule: parse `phases.final-gate` status only — never infer from banners.

Report: Scope source/markdown/nothing · Gate ✅/❌ · Coverage `<n>%` · Fix iterations `<n>`
