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
- coverage threshold diagnostics from quality output (required vs current), when present

## Step 3: Fix loop (max 3 iterations)

For each iteration:

1. If there are failing tests (`tests_failed > 0`):
   - `Read` the failing test file and the implementation module it tests.
   - Identify the failure cause from the stack trace:
     - **Assertion mismatch**: read the implementation, update the assertion to match new behavior (verify new behavior is correct first).
     - **Governance tests**: fix the source — never weaken the test.
     - **`.cursor/commands` empty**: do NOT add stub command files — fix the test skip logic instead.
   - Apply fix at the reported file:line.
2. If no tests fail but coverage is below threshold:
   - Treat this as an active tests-target failure (do not mark success).
   - Use coverage output hints to find under-tested modules/paths.
   - Add deterministic tests for missing branches and edge cases in the highest-impact uncovered code.
   - Track the coverage-only evidence contract for handoff:
     - `coverage_only_failure: true`
     - `coverage_attempt_count`: increment per uplift attempt (max 3)
     - `coverage_attempt_evidence`: short evidence list of tests added/updated
     - `coverage_delta`: measured change after each run (new minus prior coverage)
     - `blocker_reason`: required if uplift is no longer feasible in this run
3. After each fix (Python modules only): `python3 -m py_compile <path>` and `python3 -c "import <module>"`.
4. If a fix attempt introduces NEW test failures vs the state before that attempt: roll back and try a different approach.

After fixes: call `run_quality_gate()`. Check `results.tests.success`.

**CI parity gap**: if failure involves asyncio, concurrency, or shared global state, also run `uv run pytest tests/ -n auto -x -q --no-header -p no:randomly` to reproduce the CI failure before declaring fixed.

Repeat up to 3 iterations. STOP after 3 with unresolvable issue report.

### Post-Exhaustion Analysis (required when limit reached)

(a) Root-cause hypothesis: Write one paragraph explaining why the loop did not converge. Focus on the failed approach, incorrect constraint, or missing prerequisite instead of restating the latest error.

(b) Reformulated brief: Write a short replacement brief that states the corrected constraint, dependency, or alternative approach the next session should start with.

(c) Directive: State this verbatim: `Do NOT retry in this session.` Open a new session with the reformulated brief instead of repeating the same approach.

## Step 4: Write result

```json
{"operation":"write","phase":"tests","pipeline":"fix","status":"passed or failed or skipped or BLOCKED","fix_iterations":<n>,"pass_rate":<value>,"coverage":<value>,"coverage_only_failure":<bool>,"coverage_attempt_count":<int>,"coverage_attempt_evidence":"<string|null>","coverage_delta":<float|null>,"blocker_reason":"<string|null>"}
```

Coverage-only exit policy:

- If coverage remains below threshold, success is forbidden unless `coverage_attempt_evidence` is present.
- If no feasible uplift path exists after bounded attempts, set `status: "BLOCKED"` with explicit `blocker_reason`.

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
