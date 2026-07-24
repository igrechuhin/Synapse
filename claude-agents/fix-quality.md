---
name: fix-quality
description: Use when the /cortex/fix orchestrator needs to fix the quality target (type errors, formatting, linting, markdown). Runs autofix() then run_quality_gate() in a fix loop (max 3 iterations). Invoke for target=quality or as step 1 of target=all.
tools: mcp__cortex__*, Bash, Read, Edit, Grep
---

Read scope from handoff; fix quality; write result.

## Resume Check (required)

Before Step 1, call `pipeline_handoff(operation="status", pipeline="fix")`.

- If `phases.quality == "completed"`: skip execution, return prior result.
- If `phases.quality == "failed"` or `phases.quality == "running"`: continue and re-run this phase.
- If `phases.quality == "pending"` or missing: continue normally.

Immediately before Step 1, call `pipeline_handoff(operation="mark_running", pipeline="fix", phase="quality")`.

1. **Read scope**: call `pipeline_handoff(operation="read", pipeline="fix", phase="quality")`. Extract `scope` (source_changed / markdown_only / mixed).
2. **Fix loop** (max 3 iterations; ABORT if violation count does not decrease iteration-over-iteration):
   - Call `autofix()` then `run_quality_gate()`.
   - Fix remaining errors at reported `file:line`: type errors (fix annotation/cast/import); file >400 lines (split); function >30 lines (extract); markdown (fix per rule code).
   - Note: for `markdown_only` scope use `run_quality_gate()` (not `run_docs_gate()`) — it catches markdown lint that commit Phase A checks.
   - **No-progress check** (before each retry): append `{"target":"<file:line or rule-code>","outcome_signature":"<error type + message shape, no line numbers/timestamps>","attempt_number":<n>}` to this phase's `attempt_history` list (read prior list via `pipeline_handoff(operation="read", pipeline="fix", phase="quality")`, append, write full list back via `operation="write"`). If the last 3 records share the same `target` and identical `outcome_signature`, this is a **task-level no-progress trip** — distinct from the MCP circuit breaker (shared-conventions.md): STOP retrying, write `status:"BLOCKED"`, `blocker_reason:"no_progress_monitor_tripped"`, and report: "No-progress monitor tripped after 3 consecutive attempts with identical outcome on target '<target>'. Pausing for orchestrator re-plan/human check-in." Do not attempt a 4th iteration.
3. **Write result** to `.cortex/.session/current-task.json` then call `pipeline_handoff()`:

```json
{"operation":"write","phase":"quality","pipeline":"fix","status":"passed or failed","fix_iterations":<n>,"preflight_passed":<bool>}
```

Report: Scope `<scope>` · Gate ✅/❌ · Fix iterations `<n>` · Issues fixed: `file:line — change`
