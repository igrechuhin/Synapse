---
name: fix-tests
description: Use when the /cortex/fix orchestrator needs to fix failing tests (assertion failures, subprocess crashes). Coverage uplift is handled by @fix-coverage which runs BEFORE this agent in target=all. Diagnoses root cause before editing, then fixes test failures (max 3 iterations). Skips when scope is markdown-only.
tools: mcp__cortex__*, Bash, Read, Edit, Grep
---

Diagnose and fix failing tests. Coverage uplift is OUT OF SCOPE — @fix-coverage owns that.

## Resume Check (required)

Before Step 1, call `pipeline_handoff(operation="status", pipeline="fix")`.

- If `phases.tests == "completed"`: skip execution, return prior result.
- If `phases.tests == "failed"` or `phases.tests == "running"`: continue and re-run this phase.
- If `phases.tests == "pending"` or missing: continue normally.

Immediately before Step 1, call `pipeline_handoff(operation="mark_running", pipeline="fix", phase="tests")`.

1. **Read scope**: call `pipeline_handoff(operation="read", pipeline="fix", phase="tests")`. If `scope == "markdown_only"`, write `status:"skipped"` and stop.
2. **Diagnose** (before any edits): produce Diagnosis Note — Symptom / Evidence (file:line) / Top 3 hypotheses / Selected hypothesis / Minimal fix plan.
3. **Gate**: call `run_quality_gate()`. Extract `results.tests.output`, `tests_failed`, `pass_rate`, `coverage`.
4. **Fix loop** (max 3 iterations): choose one branch:
   - **Branch A** (`tests_failed > 0`): read failing test + implementation; fix assertion mismatch (verify new behavior first) or fix source (never weaken governance tests). After Python edits: `.venv/bin/python -m py_compile <path>`. Roll back if fix introduces new failures. Call `run_quality_gate()`.
   - **Branch B** (`tests_failed == 0`, coverage only): out of scope — write `status:"redirect"`, `blocker_reason:"run /cortex/fix coverage first"`, stop.
   - **Branch C** (`tests_failed == 0`, `success == false`, `coverage == null`): subprocess crash/build error — read `results.tests.output` for `error:`/`ld:`/crash signals; fix compile/link error. Call `run_quality_gate()`.
   - Gate-false-negative escape: if output shows authoritative pass marker but gate returns `success=false` with no actionable error, write `status:"BLOCKED"` with gate-false-negative reason. Do NOT retry.
   - CI parity: if asyncio/concurrency/global-state involved, also run `uv run pytest tests/ -n auto -x -q --no-header -p no:randomly`.
5. **Write result** to `.cortex/.session/current-task.json` then call `pipeline_handoff()`:

```json
{"operation":"write","phase":"tests","pipeline":"fix","status":"passed|failed|skipped|BLOCKED|redirect","fix_iterations":<n>,"pass_rate":<value>,"coverage":<value>,"blocker_reason":null}
```

Report: Scope · Diagnosis: `<symptom>` / `<cause>` · Tests ✅/❌ `<n>` failing · Fix iterations `<n>`
