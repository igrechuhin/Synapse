---
name: commit-phase-a
description: Use when the /cortex/commit orchestrator reaches Phase A (pre-commit checks) after Preflight passes. Runs run_quality_gate(); on failure delegates fixes to @fix-quality (or @fix-tests) subagent rather than fixing inline. Pipeline must not continue if this agent reports failed.
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
2. **Fix via fix workflow** (delegate, do NOT fix inline): if `preflight_passed: false`, invoke the fix workflow quality target:
   - Write pipeline handoff: `{"operation":"write","phase":"quality","pipeline":"fix","scope":"<scope>"}` to `.cortex/.session/current-task.json`, call `pipeline_handoff()`.
   - Spawn `@fix-quality` subagent (or run `/cortex/fix quality` inline from `fix.md` if subagent unavailable). The subagent owns the autofix + gate loop (max 3 iterations).
   - After the subagent completes, call `run_quality_gate()` once to confirm `preflight_passed: true`.
   - If still failing after the fix workflow, report `status:"failed"` with the fix workflow's last error summary.
3. **Write result** to `.cortex/.session/current-task.json` then call `pipeline_handoff()`:

```json
{"operation":"write","phase":"checks","pipeline":"commit","status":"passed","coverage":<actual>,"fix_iterations":<n>,"preflight_passed":true}
```

Gate rule: parse `preflight_passed` from tool response only — never infer from banners.

Report: Gate ✅/❌ · Coverage `<n>%` · Fix iterations `<n>`
