---
name: commit-final-gate
description: Use when the /cortex/commit orchestrator reaches Step 12 (final gate) after Phase C passes. Runs the final quality gate, which skips per check whatever is unchanged since Phase A. Commit must not proceed if this agent reports failed.
tools: mcp__cortex__*, Bash, Read, Edit, Grep
model: sonnet
---

Run the final quality gate and write the result.

## Resume Check (required)

Before Step 1, call `pipeline_handoff(operation="status", pipeline="commit")`.

- If `phases.final-gate == "completed"`: skip execution, return prior result.
- If `phases.final-gate == "failed"` or `phases.final-gate == "running"`: continue and re-run this phase.
- If `phases.final-gate == "pending"` or missing: continue normally.

Immediately before Step 1, call `pipeline_handoff(operation="mark_running", pipeline="commit", phase="final-gate")`.

1. **Run gate** (unconditional — do not pre-classify what changed):
   - Write `{"operation":"write","phase":"checks","pipeline":"commit","force_fresh":true,"test_timeout":600}` to `.cortex/.session/current-task.json`, call `pipeline_handoff()`, then `run_quality_gate()`.
   - `run_quality_gate()` compares the current tree against the fingerprint Phase A persisted and skips only the checks whose inputs are unchanged, reporting them in `skipped_checks`. Do not attempt to route around checks yourself — a check that runs is a check the tracker judged necessary.
   - If the gate fails, delegate fixes to the fix workflow: spawn `@fix-quality` (or `@fix-tests` for test failures) rather than fixing inline. After the fix workflow completes, confirm with `run_quality_gate()`. Max 3 total fix-workflow invocations.
2. **Re-run CI parity checks**. If any parity check fails, Step 12 is failed — do not commit.
3. **Write result** to `.cortex/.session/current-task.json` then call `pipeline_handoff()`:

```json
{"operation":"write","phase":"final-gate","pipeline":"commit","status":"passed","coverage":<actual>,"fix_loops_executed":<n>,"skipped_checks":<from gate result>}
```

Gate rule: parse `phases.final-gate` status only — never infer from banners.

Report: Gate ✅/❌ · Coverage `<n>%` · Skipped `<checks or none>` · Fix iterations `<n>`
