---
name: commit-phase-a
description: Use when the /cortex/commit orchestrator reaches Phase A (pre-commit checks) after Preflight passes. Runs run_quality_gate(), calls autofix() on failure, retries up to 3 times. Pipeline must not continue if this agent reports failed.
tools: mcp__cortex__*, Bash, Read, Edit, Grep
---

Run quality gate; fix failures; write result.

## Resume Check (required)

Before Step 1, call `pipeline_handoff(operation="status", pipeline="commit")`.

- If `phases.checks == "completed"`: skip execution, return prior result.
- If `phases.checks == "failed"` or `phases.checks == "running"`: continue and re-run this phase.
- If `phases.checks == "pending"` or missing: continue normally.

Immediately before Step 1, call `pipeline_handoff(operation="mark_running", pipeline="commit", phase="checks")`.

1. **Gate**: call `run_quality_gate()`. If `preflight_passed: true` → go to step 3.
2. **Fix loop** (max 3 iterations, ABORT if violation count does not decrease): call `autofix()` then `run_quality_gate()`. If still failing after 3 iterations, report `status:"failed"` with last error summary.
   - CI parity: if changed code touches asyncio/event loops/shared state, also run `uv run pytest tests/ -n auto -x -q --no-header -p no:randomly`.
3. **Write result** to `.cortex/.session/current-task.json` then call `pipeline_handoff()`:

```json
{"operation":"write","phase":"checks","pipeline":"commit","status":"passed","coverage":<actual>,"fix_iterations":<n>,"preflight_passed":true}
```

Gate rule: parse `preflight_passed` from tool response only — never infer from banners.

Report: Gate ✅/❌ · Coverage `<n>%` · Fix iterations `<n>`
