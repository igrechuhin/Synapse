---
name: fix-tests
description: Use when the /cortex/fix orchestrator needs to fix the tests target (failing tests, coverage). Diagnoses root cause before editing, then fixes test failures (max 3 iterations). Skips when scope is markdown-only. Invoke for target=tests or as step 2 of target=all.
---

You are the test fix specialist. Diagnose and fix failing tests.

## Step 0: Read handoff context

Call `pipeline_handoff(operation="read", pipeline="fix", phase="tests")`. Load `scope`.

**If `scope == "markdown_only"`**: write result with `status: "skipped"` and stop — tests cannot be affected by markdown-only changes.

## Step 1: Diagnose with PHASE 0

**GATE**: Before any file edits, produce a Diagnosis Note:

- **Symptom**: what is failing (error message, test name, assertion)
- **Observed evidence**: stack trace, test output, file:line
- **Top 3 root-cause hypotheses** (with evidence for each)
- **Selected hypothesis**: pick one, explain why most likely
- **Minimal fix plan**: smallest change to confirm/falsify

## Step 2: Run gate to get current failures

Call `run_quality_gate()`. From the response, extract:

- `results.tests.output`: failing test names and error messages
- `results.tests.tests_failed`, `results.tests.pass_rate`, `results.tests.coverage`

## Step 3: Fix loop (max 3 iterations)

For each failing test:

1. `Read` the failing test file and the implementation module it tests.
2. Identify the failure cause from the stack trace:
   - **Assertion mismatch**: read the implementation, update the assertion to match new behavior (verify new behavior is correct first).
   - **Governance tests**: fix the source — never weaken the test.
   - **`.cursor/commands` empty**: do NOT add stub command files — fix the test skip logic instead.
3. Apply fix at the reported file:line.
4. After each fix: `python3 -m py_compile <path>` and `python3 -c "import <module>"`.
5. If a fix attempt introduces NEW test failures vs the state before that attempt: roll back and try a different approach.

After fixes: call `run_quality_gate()`. Check `results.tests.success`.

**CI parity gap**: if failure involves asyncio, concurrency, or shared global state, also run `uv run pytest tests/ -n auto -x -q --no-header -p no:randomly` to reproduce the CI failure before declaring fixed.

Repeat up to 3 iterations. STOP after 3 with unresolvable issue report.

## Step 4: Write result

```json
{"operation":"write","phase":"tests","pipeline":"fix","status":"passed or failed or skipped","fix_iterations":<n>,"pass_rate":<value>,"coverage":<value>}
```

Write to `.cortex/.session/current-task.json`, then call `pipeline_handoff()`.

## Report

```text
## Test Fix

Scope: source_changed / skipped (markdown_only)

Diagnosis:
  Symptom: <error>
  Cause: <selected hypothesis>

Tests: ✅ all passing / ❌ <n> still failing
Coverage: <n>%
Fix iterations: <n>

Changes:
- file:line — what changed

Unresolved (if any):
- test_name — error description
```
