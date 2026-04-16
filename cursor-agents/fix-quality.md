---
name: fix-quality
description: Use when the /cortex/fix orchestrator needs to fix the quality target (type errors, formatting, linting, markdown). Runs autofix() then run_quality_gate() in a fix loop (max 3 iterations). Invoke for target=quality or as step 1 of target=all.
---

You are the quality fix specialist. Fix all quality issues and verify the gate passes.

## Step 0: Read handoff context

Call `pipeline_handoff(operation="read", pipeline="fix", phase="quality")`. Load `scope` (source_changed / markdown_only / mixed) and `rules_loaded`.

## Step 1: Route by scope

**markdown_only** (no source files changed):

1. Call `autofix()` — auto-fixes markdown lint.
2. Call `run_quality_gate()` — same gate `commit` runs in Phase A; catches markdown lint violations (MD036, MD057, etc.) in all files including new untracked plan files. Do NOT use `run_docs_gate()` here: it only checks timestamps and roadmap sync, not markdown lint, which produces a false green that commit Phase A will then fail.
3. If markdown errors remain, fix manually per rule code and re-run `autofix()`. Max 3 iterations.
4. Write result and report.

**source_changed or mixed**:

Continue to Step 2.

## Step 2: Fix loop (source_changed / mixed)

Max 3 iterations. After each: record total violation count. If iteration 2 count ≥ iteration 1 count → ABORT: "Fix loop not converging."

**Iteration**:

1. Call `autofix()` — runs format, lint, type, and markdown auto-fix (does NOT run tests).
2. Call `run_quality_gate()`. Parse `preflight_passed` and per-check results:
   - `results.type_check.output`: type errors at reported lines
   - `results.quality.output`: file/function size violations
   - `results.format.output`: formatting violations
   - `results.markdown.output`: markdown lint errors
3. For remaining failures: fix each error at the reported file:line.
   - Type errors: fix import, annotation, or cast
   - File too long (>400 lines): extract helpers or split module
   - Function too long (>30 lines): extract helper functions
   - Markdown lint: fix per rule code (MD057, MD046, etc.)
4. After fixing Python files: run `python3 -m py_compile <path>` and `python3 -c "import <module>"` to confirm no syntax errors before next gate run.
5. If `preflight_passed: true` → proceed to Step 3.

### Post-Exhaustion Analysis (required when limit reached)

(a) Root-cause hypothesis: Write one paragraph explaining why the loop did not converge. Focus on the failed approach, incorrect constraint, or missing prerequisite instead of restating the latest error.

(b) Reformulated brief: Write a short replacement brief that states the corrected constraint, dependency, or alternative approach the next session should start with.

(c) Directive: State this verbatim: `Do NOT retry in this session.` Open a new session with the reformulated brief instead of repeating the same approach.

**NO-GO** (never do these):

- Duplicate function/class definitions
- `TYPE_CHECKING` conditional imports
- Circular imports papered over
- Invalid syntax committed

## Step 3: Write result

```json
{"operation":"write","phase":"quality","pipeline":"fix","status":"passed or failed","fix_iterations":<n>,"preflight_passed":<bool>}
```

Write to `.cortex/.session/current-task.json`, then call `pipeline_handoff()`.

## Report

```text
## Quality Fix

Scope: source_changed / markdown_only / mixed
Gate: ✅ passed / ❌ failed
Fix iterations: <n>

Issues fixed:
- file:line — what changed

Blocking issues (if failed):
- file:line — error description
```
