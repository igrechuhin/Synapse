# Fix (Helper Command)

**AI EXECUTION COMMAND**: Fix issues in a targeted domain using Cortex MCP tools, outside of the full commit pipeline. This is a unified entry point for quality, test, and documentation fixes.

## Status legend (scan-friendly)

- ✅ **Success** (passed / complete)
- ⚠️ **Warning** (non-blocking; proceed but report)
- ❌ **Error** (blocking; must fix before proceeding)
- ⛔ **Hard gate** (rule violation if skipped)

**CRITICAL**: Execute ALL required gates automatically. Do NOT pause, summarize, or ask for confirmation unless clarification is genuinely needed.

⛔ **HARD GATE — VIOLATION IF BROKEN**: You MUST complete **PHASE 0 — Diagnose First** (including documenting hypotheses and selecting one) BEFORE making ANY file edits. Reading/searching the repo and running checks is allowed; editing files is prohibited until the PHASE 0 Diagnosis Note is written.

## Fix-loop integrity (NO-GO)

⛔ During **any** fix iteration, the following corrupt the tree and cause multi-session repair loops. **Do not** do these to “make the checker happy”:

- **NO-GO — duplicate definitions**: NEVER add duplicate function/class definitions in the same module.
- **NO-GO — `TYPE_CHECKING` workarounds**: NEVER use `TYPE_CHECKING` conditional imports; they violate project standards — use normal imports or refactor instead.
- **NO-GO — circular imports**: NEVER paper over import cycles; extract shared types/helpers to a new module instead.
- **NO-GO — invalid syntax**: NEVER commit syntax-invalid Python.

**Post-fix validation** (before treating the quality target as ✅ for changed Python modules): run `python3 -m py_compile <path/to/file.py>` and `python3 -c "import <module_import_path>"` for each changed module (use the package import path, e.g. `cortex.tools.foo`, not a filesystem path). If either command fails, fix the cause or revert — do not proceed to success.

**Rollback on regressions**: If a fix attempt introduces **new** test failures or **new** quality errors versus the state before that attempt, roll back that attempt and try a different approach. **Max 3 attempts** per target (same limit as the fix loop below).

## PHASE 0 — Diagnose First (MANDATORY — before any file edits)

🧠 **GOAL**: Identify the most likely root cause and a minimal, targeted fix plan before touching code.

⛔ **GATE**: No file edits are allowed until you produce the **Diagnosis Note** below.

### Diagnose-first checklist

- **Identify affected files**: List the top suspected files/modules based on symptoms and where the failure surfaces.
- **Trace an execution path / call stack**: Use stack traces, logs, request/CLI flow, or dependency graph reasoning to describe the likely path from input → failing point.
- **Check related recent changes**: Look for nearby changes in the same area (recent commits, recent edits, or adjacent modules) that could plausibly explain the symptom.
- **Check related known issues**: If the project has issue tracking or a bug log, quickly scan for similar symptoms to avoid duplicating a known root cause.

### Diagnosis Note (required output before edits)

Produce the following note in your response before making edits:

- **Symptom**: What is failing (error message, failing check, failing behavior).
- **Observed evidence**: Concrete evidence from the codebase (file paths, quoted snippets, config values) and/or failure output (logs, stack traces).
- **Top 3 root-cause hypotheses (with evidence)**:
  1. Hypothesis A — include 1–3 evidence bullets pointing to specific files/snippets or outputs.
  2. Hypothesis B — include 1–3 evidence bullets.
  3. Hypothesis C — include 1–3 evidence bullets.
- **Selected hypothesis**: Pick ONE hypothesis and explain why it is most likely (and why the others are less likely).
- **Minimal fix plan**: The smallest change(s) that would confirm/falsify the hypothesis and resolve the issue if confirmed.

## Target Parameter

This prompt accepts an optional `target` parameter:

- 🛠️ **quality** — Fix type errors, formatting, linting
- 🧪 **tests** — Diagnose and fix failing tests
- 📝 **docs** — Synchronize documentation and memory bank
- 🔁 **all** — Run all three targets sequentially (see Sequential Execution below)

⛔ **GATE**: If `target` is **omitted**, you MUST behave as if `target=all` and run all three targets sequentially. Do **not** ask the user which target they need when the command is invoked without parameters.

## Zero-Arg Tools (all tools work with no arguments)

All MCP tools work when called with empty `{}` arguments. Use these zero-arg tools:

- `fix_quality_issues()` — auto-fix formatting, linting, type errors, markdown (does NOT run tests)
- `run_quality_gate()` — run Phase A quality gate end-to-end (includes tests; may be long-running)
- `run_docs_gate()` — run Phase B docs/memory-bank validation (fast; does NOT run tests)

**CRITICAL**: After calling any fix/gate tool (and after completing PHASE 0), you MUST apply all remaining fixes inline. Do NOT produce a list of "required fixes" and stop. Just apply them immediately.

## Change-Scope Assessment (MANDATORY — run before any tool call)

**Before invoking any MCP tool**, classify what changed in the working tree:

1. Run `git diff --name-only HEAD` (or `git status --short`) to list modified files.
2. Classify each file:
   - **source_changed**: any file outside `.cortex/` that is a source or test file (`.swift`, `.py`, `.ts`, `.go`, `.rs`, `.java`, `.kt`, etc.)
   - **markdown_only**: all changes are `.md`/`.mdc` files (e.g. only `.cortex/` memory-bank or plan edits)
   - **mixed**: both source and markdown files changed
3. Record the scope and use it to select the right tool path below.

**Why this matters**: `run_quality_gate()` spawns a full language-specific build + test run (e.g. `swift build` + `swift test`, `pytest`, `go test`). On large projects this takes **5–15+ minutes**. When only markdown files changed, tests are provably irrelevant — running them wastes time and makes the prompt appear to hang.

## Sequential Execution (`all` target)

When `target=all`, run targets **one at a time in order**: quality → tests → docs. Do NOT launch concurrent subagents.

Steps:

1. Perform Change-Scope Assessment (above) once; reuse the result for all targets.
2. Run `fix quality` — complete the full quality workflow below before proceeding.
3. Run `fix tests` — complete the full tests workflow below before proceeding.
4. Run `fix docs` — complete the full docs workflow below.
5. Report a combined summary with emoji status: ✅/⚠️/❌ per target (quality/tests/docs), plus the single highest-signal failure snippet if anything is ❌.

## Goals (All Targets)

- Use structured MCP tools instead of ad-hoc shell commands.
- Do NOT commit or push as part of this command; `/cortex/commit` is responsible for the full pipeline.

## Pre-Action Checklist

Before making changes, complete PHASE 0, load rules, and classify the change scope. Then **immediately apply fixes**.

1. **Load rules** (background, no output to user):
   - Read the `cortex://rules` resource (zero-arg, reads task from session config).
   - If resource access fails, proceed without rules — fix based on error output.
2. **Classify change scope**: Run Change-Scope Assessment above.
3. **Start fixing immediately (after PHASE 0)**: Do NOT produce a summary. The moment a tool returns errors, start editing files.

## Execution Steps

⛔ **GATE**: Fix loops are limited to **3 iterations** per target. After 3 failed fix-and-verify cycles, STOP and report unresolvable issues.

### 🛠️ quality Target

Route based on change scope:

**Path A — markdown_only** (no source files changed):

1. Call `fix_quality_issues()` to auto-fix markdown lint issues.
2. Verify with `run_docs_gate()` (fast; confirms docs are clean without running tests).
3. If markdown lint errors remain in the quality result, fix them manually per rule code and re-run `fix_quality_issues()`. Repeat (max 3 iterations).

**Path B — source_changed or mixed** (source or test files changed):

1. Call `fix_quality_issues()`. This runs format, lint, type, and markdown auto-fix (does NOT run tests).
2. Verify with `run_quality_gate()`. Parse the result for `preflight_passed` and per-check results.
3. If checks still fail, parse the result — `results.type_check.output` and `results.quality.output` contain full error output. Fix each error:
   - **Type errors**: fix import, type annotation, or cast at the reported line.
   - **File too long** (> 400 lines): extract helpers or split into a new module.
   - **Function too long** (> 30 lines): extract helper functions.
   - **Markdown lint**: fix manually per rule code (MD057, MD046, MD051, MD076, MD022, MD047). For `.cortex/memory-bank/*.md` use `manage_file()`.
4. Re-verify with `run_quality_gate()`. Repeat from step 3 (max 3 iterations).
5. Before declaring the 🛠️ quality target ✅ for Python edits: apply **Post-fix validation** and **Rollback on regressions** from [Fix-loop integrity (NO-GO)](#fix-loop-integrity-no-go) — `py_compile`, import check, and bounded retry with revert on new failures.

### 🧪 tests Target

Route based on change scope:

**markdown_only**: Skip this target entirely — no source changed, tests cannot be affected.

**source_changed or mixed**:

1. Call `run_quality_gate()` to get test results alongside quality checks.
2. Locate failing tests: open failing test files and implementation modules using `Grep`/`Read`.
3. Debug and fix in small, focused steps. Follow AAA pattern:
   - **Assertion count mismatch**: read the implementation, update the assertion.
   - **Governance tests**: fix the source — never weaken the test.
4. Re-run `run_quality_gate()` after fixes. Repeat (max 3 iterations).

### 📝 docs Target

(Fast — never invokes the language build or test runner regardless of scope.)

1. Analyze roadmap and plans: cross-check `roadmap.md` against plan files. Use `manage_file()` and `Glob` on `.cortex/plans/*.md`.
2. Align activeContext and progress: ensure completed work in `activeContext.md`, ongoing work in `roadmap.md`.
3. Fix timestamp and sync issues: read `cortex://validation` resource. Apply targeted fixes.
4. Re-run docs validation: call `run_docs_gate()`. If not passing, go back to step 1 (max 3 iterations).

## Failure Handling

**DO NOT stop to describe issues or ask the user if they want fixes applied.** Fix immediately and re-run.

- Type errors → edit the source file at the reported line.
- File/function too long → extract helpers; split if needed.
- Markdown lint failures → fix manually per rule code, then re-run `fix_quality_issues()`.
- Test assertion mismatches → update the assertion (verify new behavior is correct first).
- Docs sync failures → edit memory bank files via `manage_file()`.

Only stop after **3 complete fix-and-verify iterations per target** have all failed.

If an attempt worsens the tree (new failures, duplicate defs, invalid syntax), **roll back that attempt** and retry with a different strategy — see **Rollback on regressions** under [Fix-loop integrity (NO-GO)](#fix-loop-integrity-no-go).

## Success Criteria

| Target | Criteria |
|--------|----------|
| 🛠️ quality ✅ | Zero type errors, clean formatting/linting, zero markdown errors |
| 🧪 tests ✅ | All tests passing (skipped when markdown_only) |
| 📝 docs ✅ | `docs_phase_passed: true`, all sync issues resolved |
