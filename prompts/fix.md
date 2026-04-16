# Fix (Helper Command)

**AI EXECUTION COMMAND**: Fix issues in a targeted domain using Cortex MCP tools, outside of the full commit pipeline. This is a unified entry point for quality, test, and documentation fixes.

## Clean Semantics

For `/cortex/fix`, **clean** means **issue-clean for the active fix target(s)** (quality/tests/docs), not git-clean working tree. See "Submodule `clean` semantics for `/fix`" below for required submodule behavior.

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
- **NO-GO — synthetic roadmap backlog**: NEVER fabricate generic `PENDING` roadmap bullets (for example, “follow-up reconciliation/normalization”) solely to satisfy docs gates. Only add backlog items that map to concrete, implementation-ready unfinished work.
- **NO-GO — Cursor command stubs**: NEVER create, track, or widen `.gitignore` for `.cursor/commands/*.md` to pass tests or the quality gate. Workflows are **canonical under `.cortex/synapse/prompts/`** (and project `.cortex/prompts/`); duplicating them as Cursor commands **pollutes the user’s command picker** and fights `.gitignore` (`/.cursor/`). If `tests/integration/test_synapse_final_report_prompt_alignment.py` complains about empty `.cursor/commands/`, fix the **test or prompt expectations** (optional skip when no `*.md` is correct) — do **not** add stub command files.

**Post-fix validation** (before treating the quality target as ✅ for changed Python modules): run `.venv/bin/python -m py_compile <path/to/file.py>` and `PYTHONPATH=src .venv/bin/python -c "import <module_import_path>"` for each changed module (use the package import path, e.g. `cortex.tools.foo`, not a filesystem path). `.venv/bin/python` is mandatory here; using any other interpreter is a critical error. If either command fails, fix the cause or revert — do not proceed to success.

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

- `autofix()` — auto-fix formatting, linting, type errors, markdown (does NOT run tests)
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

**Why this matters**: `run_quality_gate()` spawns a full language-specific build + test run (e.g. `swift build` + `swift test`, `pytest`, `go test`). On large projects this takes **5–15+ minutes**. When only markdown files changed, language tests are provably irrelevant — but `run_quality_gate()` is still required for `markdown_only` scope because it runs the markdown lint check. Do NOT substitute `run_docs_gate()` for quality verification: `run_docs_gate()` only checks timestamps and roadmap sync, not markdown lint, which would produce a false green that `commit` Phase A would then fail.

## Submodule-First Fix Routing (MANDATORY)

⛔ **GATE**: Before root quality/tests/docs gates, check for dirty submodules and treat them as fix targets.

### Submodule "clean" semantics for `/fix`

For this prompt, a submodule is **clean** when there are **no remaining fixable issues** for the active target(s) (quality/tests/docs). A submodule may still contain intentional local edits and still be considered clean for `/fix`.

Do **not** use commit-pipeline cleanliness semantics here. In `/cortex/commit`, "clean" means git-clean working tree (changes committed/discarded); in `/fix`, "clean" means issue-clean for the requested gates.

1. Detect dirty submodules with `git submodule foreach 'git status --short'` (or equivalent).
2. If a submodule has uncommitted/untracked changes:
   - Run the same diagnose-first + fix loop inside that submodule first (quality/tests/docs as applicable).
   - Keep iterating until the submodule is green (or max 3 iterations for that submodule target).
3. Only after all dirty submodules are green, return to the superproject and continue root `/fix`.

**Interpretation rule**: Uncommitted submodule changes are not automatically "dirty state to reject" — they are work that must be fixed first. `submodule_hygiene` failure at the superproject level should trigger submodule-first remediation, not immediate stop.

**Submodule commit authority**: The Submodule-First routing in this prompt has authority to commit inside a submodule when required. This is not a violation of the "No commit" goal because (a) the superproject is not committed and (b) without the submodule commit the gate cannot proceed at all. See the exception note in **Goals (All Targets)** above.

## Sequential Execution (`all` target)

When `target=all`, run targets **one at a time in order**: quality → tests → docs. Do NOT launch concurrent subagents.

Steps:

1. Perform Change-Scope Assessment (above) once; reuse the result for all targets.
2. Run Submodule-First Fix Routing (above) and complete required submodule fixes.
3. Run `fix quality` — complete the full quality workflow below before proceeding.
4. Run `fix tests` — complete the full tests workflow below before proceeding.
5. Run `fix docs` — complete the full docs workflow below.
6. Report a combined summary with emoji status: ✅/⚠️/❌ per target (quality/tests/docs), plus the single highest-signal failure snippet if anything is ❌.

## Goals (All Targets)

- Use structured MCP tools instead of ad-hoc shell commands.
- Do NOT commit or push as part of this command; `/cortex/commit` is responsible for the full pipeline.
- **Exception — submodule commit**: A commit *inside* `.cortex/synapse` (or another submodule) IS allowed when `submodule_hygiene` blocks `run_quality_gate` and the only alternatives are discarding valid in-progress submodule changes or leaving the gate permanently broken. The *superproject* must NOT be committed. After the submodule commit, stage the updated gitlink (`git add .cortex/synapse`) so the next `run_quality_gate` sees a clean, in-sync submodule.

## Pre-Action Checklist

Before making changes, complete PHASE 0, load rules, and classify the change scope. Then **immediately apply fixes**.

1. **Load rules** (background, no output to user):
   - Read the `cortex://rules` resource (zero-arg, reads task from session config).
   - If `cortex://rules` returns `status: "disabled"`: proceed without rules AND record a ⚠️ warning for the final report: "Rules indexing is disabled — set `rules.enabled` to `true` in `.cortex/config/optimization.json` to get rules-aware fixes." Do NOT surface this inline; add it to the "Next" section of the final report only.
   - If resource access fails for any other reason (connection error, timeout): proceed without rules, no warning needed.
2. **Classify change scope**: Run Change-Scope Assessment above.
3. **Start fixing immediately (after PHASE 0)**: Do NOT produce a summary. The moment a tool returns errors, start editing files.

## Execution Steps

⛔ **GATE**: Fix loops are limited to **3 iterations** per target. After 3 failed fix-and-verify cycles, STOP and report unresolvable issues.

### Post-Exhaustion Analysis (required when limit reached)

(a) Root-cause hypothesis: Write one paragraph explaining why the loop did not converge. Focus on the failed approach, incorrect constraint, or missing prerequisite instead of restating the latest error.

(b) Reformulated brief: Write a short replacement brief that states the corrected constraint, dependency, or alternative approach the next session should start with.

(c) Directive: State this verbatim: `Do NOT retry in this session.` Open a new session with the reformulated brief instead of repeating the same approach.

### 🛠️ quality Target

Use @fix-quality to handle this target. If the subagent is unavailable, run inline:

Route based on change scope:

**Path A — markdown_only** (no source files changed):

1. Call `autofix()` to auto-fix markdown lint issues.
2. Verify with `run_quality_gate()` — this is the same gate `commit` runs in Phase A, ensuring markdown lint (MD036, MD057, etc.) in all files (including new untracked plan files) is clean before commit.
3. If markdown lint errors remain, fix them manually per rule code and re-run `autofix()`. Repeat (max 3 iterations).

> **Why not `run_docs_gate()` here?** `run_docs_gate()` only checks timestamps and roadmap sync — it does NOT run markdown lint. Using it as the quality gate for `markdown_only` scope produces a false green: `fix` passes while `commit` Phase A later fails on markdown lint violations (MD036 etc.) in the same files.

**Path B — source_changed or mixed** (source or test files changed):

1. Call `autofix()`. This runs format, lint, type, and markdown auto-fix (does NOT run tests).
2. Verify with `run_quality_gate()`. Parse the result for `preflight_passed` and per-check results.
3. **CI parity structural checks (mandatory before ✅)**: after a green `run_quality_gate()`, run parity scripts across **all** language subfolders. These checks mirror exactly what the commit pipeline runs in Phase A — **if any script exits non-zero here, fix must be treated as failed, same as commit would.**

   ⛔ **HARD GATE**: You MUST run these scripts as actual subprocesses and check their exit codes. A glob-based Python fallback or manual file inspection is **not** a valid substitute. If the shell does not support the `find … | while read` pattern, use `python3 -c` with `subprocess` or `pathlib.Path.glob` to enumerate and invoke each script individually.

   Run in two passes:

   **Pass 1 — changed-files check** (catches violations introduced by the current diff):

   ```bash
   CHANGED_FILES=$(git diff --name-only HEAD && git diff --name-only)
   for script in check_file_sizes.py check_function_lengths.py build.py; do
     find .cortex/synapse/scripts -mindepth 2 -maxdepth 2 -name "$script" | sort | \
       while read -r s; do FILES="$CHANGED_FILES" python3 "$s" || exit 1; done
   done
   ```

   **Pass 2 — full-repo file-size scan** (catches pre-existing violations in unchanged files that commit would also catch; `check_function_lengths.py` is delta-only so skip it here):

   ```bash
   find .cortex/synapse/scripts -mindepth 2 -maxdepth 2 -name "check_file_sizes.py" | sort | \
     while read -r s; do python3 "$s" || exit 1; done
   ```

   Each script's `_get_files_from_env()` filters by its own extension (`.py`, `.swift`, `.ts`, …). When `FILES` contains no files matching the script's language, it exits 0 immediately — no directory-scan fallback is triggered.

   Treat any non-zero exit as a hard failure — fix the violation and re-run both passes (max 3 iterations).
4. If checks still fail, parse the result — `results.type_check.output` and `results.quality.output` contain full error output. Fix each error:
   - **Type errors**: fix import, type annotation, or cast at the reported line.
   - **File too long** (> 400 lines): extract helpers or split into a new module.
   - **Function too long** (> 30 lines): extract helper functions.
   - **Markdown lint**: fix manually per rule code (MD057, MD046, MD051, MD076, MD022, MD047). For `.cortex/memory-bank/*.md` use `manage_file()`. **Generated files**: if violations are in generated files (e.g. `.cortex/wiki/**`), the fix must go into the generator code, not just the generated file — otherwise violations will reappear on the next ingest run.
5. Re-verify with `run_quality_gate()`. Repeat from step 4 (max 3 iterations).
6. Before declaring the 🛠️ quality target ✅ for Python edits: apply **Post-fix validation** and **Rollback on regressions** from [Fix-loop integrity (NO-GO)](#fix-loop-integrity-no-go) — `py_compile`, import check, and bounded retry with revert on new failures.

### 🧪 tests Target

Use @fix-tests to handle this target. If the subagent is unavailable, run inline:

Route based on change scope:

**markdown_only**: Skip this target entirely — no source changed, tests cannot be affected.

**source_changed or mixed**:

1. Call `run_quality_gate()` to get test results alongside quality checks.
2. Locate failing tests: open failing test files and implementation modules using `Grep`/`Read`.
3. Debug and fix in small, focused steps. Follow AAA pattern:
   - **Assertion count mismatch**: read the implementation, update the assertion.
   - **Governance tests**: fix the source — never weaken the test.
   - **Final-report alignment / `.cursor/commands`**: If the failure is `expected at least one *.md under .cursor/commands` (or similar), the repository policy is **no tracked Cursor command markdown** — alignment checks **skip** when that folder has no `*.md`. Fix the **integration test** (or restore the skip path), not the working tree with new command stubs. See **NO-GO — Cursor command stubs** above.
4. **Coverage-only failure handling (mandatory)**: if `tests_failed == 0` and quality still fails because coverage is below threshold:
   - Parse gate output for coverage details (current %, required %, and any uncovered-module hints).
   - Identify the highest-impact uncovered or under-covered modules touched by current work (or core hot paths if no hints are available).
   - Add focused tests that exercise missing branches/edge cases in those modules (AAA style; deterministic).
   - Re-run `run_quality_gate()` immediately and keep iterating coverage uplift (max 3 iterations total for this target).
   - Do **not** stop with a policy-only recommendation while there are obvious missing tests you can add in this run.
   - Emit a bounded evidence contract in the tests-phase handoff payload:
     - `coverage_only_failure: true`
     - `coverage_attempt_evidence`: concise summary of tests added/updated
     - `coverage_attempt_count`: integer in `[0,3]`
     - `coverage_delta`: numeric delta between last two measured coverage values
     - `blocker_reason`: required only when no further in-session uplift is feasible
   - The tests target is ✅ only when either:
     - coverage reaches threshold after at least one uplift attempt (`coverage_attempt_evidence` present), or
     - status is explicitly `BLOCKED` with a concrete `blocker_reason`.
   - Exiting without `coverage_attempt_evidence` or `BLOCKED` classification is a hard failure.
5. Re-run `run_quality_gate()` after fixes. Repeat (max 3 iterations).

⚠️ **CI parity gap — parallel test execution**: The local `run_quality_gate()` may run tests single-threaded, while CI always runs `pytest -n auto` (parallel xdist workers). Tests that only fail under parallel execution (e.g. asyncio cross-loop bugs, shared module-level state, concurrent resource races) will pass locally but fail CI. If a test failure involves asyncio, concurrency, event loops, or shared global state, **also run** `uv run pytest tests/ -n auto -x -q --no-header -p no:randomly` locally to reproduce the CI failure before declaring the target ✅.

### 📝 docs Target

Use @fix-docs to handle this target. If the subagent is unavailable, run inline:

(Fast — never invokes the language build or test runner regardless of scope.)

1. Analyze roadmap and plans: cross-check `roadmap.md` against plan files. Use `manage_file()` and `Glob` on `.cortex/plans/*.md`.
2. Align activeContext and progress: ensure completed work in `activeContext.md`, ongoing work in `roadmap.md`.
3. Fix timestamp and sync issues: read `cortex://validation` resource. Apply targeted fixes.
4. Re-run docs validation: call `run_docs_gate()`. If not passing, go back to step 1 (max 3 iterations).

`roadmap_progress_consistency` handling rule:

- If this check fails, do **not** create generic placeholder `PENDING` bullets.
- Only add a roadmap `PENDING` entry when you can point to a concrete unfinished deliverable with implementation-ready wording.
- If no concrete unfinished deliverable exists, treat the check as a validation mismatch to be addressed in validator logic (or by truthfully resolving stale PARTIAL history), not by backlog fabrication.

## Failure Handling

**DO NOT stop to describe issues or ask the user if they want fixes applied.** Fix immediately and re-run.

- Type errors → edit the source file at the reported line.
- File/function too long → extract helpers; split if needed. **`autofix()` returning `files_modified: []` does NOT mean this is unresolvable — `autofix()` only handles format/lint/type errors, never structural refactors. You MUST perform function extraction manually by editing the source file.**
- Markdown lint failures → fix manually per rule code, then re-run `autofix()`.
- Test assertion mismatches → update the assertion (verify new behavior is correct first).
- Docs sync failures → edit memory bank files via `manage_file()`.
- **`submodule_hygiene` failure in `run_quality_gate`**: Follow **Submodule-First Fix Routing** above. Commit dirty changes inside the submodule, remove any ephemeral untracked files (e.g. `.cache/`), then `git add <submodule>` in the superproject. Retry `run_quality_gate`. This does NOT violate the "No commit" goal — see exception in **Goals (All Targets)**.
- **Empty `.cursor/commands` vs alignment test**: Do **not** add `.cursor/commands/*.md` — see **NO-GO — Cursor command stubs** and the tests-target bullet on final-report alignment.

Only stop after **3 complete fix-and-verify iterations per target** have all failed.

⛔ **MANDATORY RE-VERIFY AFTER EDITS**: After making ANY file edits, you MUST complete a full re-verification pass (run all applicable gates and parity scripts) before writing the final report. Do NOT end the session or emit a conversational summary after edits — loop back to the verification step and only stop when all targets are ✅ or the 3-iteration limit is reached. Offering to run further checks ("If you want, I can now...") after edits is a violation — just run them.

If an attempt worsens the tree (new failures, duplicate defs, invalid syntax), **roll back that attempt** and retry with a different strategy — see **Rollback on regressions** under [Fix-loop integrity (NO-GO)](#fix-loop-integrity-no-go).

## Step 10: Post-Prompt Hook (Self-Improvement)

After writing the final report for this fix run, invoke the post-prompt self-improvement hook:

- Read `.cortex/synapse/prompts/post-prompt-hook.md` and execute it to analyze the session and emit any applicable Skills, Plans, or Rules.
- Treat this hook as **non-blocking**: if it fails or is unavailable (for example, MCP connection issues), record a brief note in the final report `## Next` section and consider the fix workflow complete.

## Final report (required format)

**MANDATORY**: Use the **Diagnostic** report type from `docs/guides/synapse-final-report-templates.md`.

```markdown
## Result

✅ Fixed <targets> (<n> iterations)

## Diagnosis

**Symptom**: <error message or failing check>
**Cause**: <root cause from PHASE 0>

## Iterations

| Target | Status | Count |
|--------|--------|-------|
| Quality | ✅/❌ | <n> |
| Tests | ✅/❌/⏭️ | <n OR skipped> |
| Docs | ✅/❌/⏭️ | <n OR skipped> |

## Changes

- <file:line> — <what changed>
- ...

## Next

<remaining failures OR None>
```

**Rules**:

- Diagnosis section promotes PHASE 0 findings to top level
- ⏭️ for skipped targets (e.g., markdown-only scope)
- Changes list: file:line format for each edit
- If a ⚠️ rules-disabled warning was recorded in step 1 of Pre-Action Checklist, include it as the first item under `## Next`

## Success Criteria

| Target | Criteria |
|--------|----------|
| 🛠️ quality ✅ | Zero type errors, clean formatting/linting, zero markdown errors |
| 🧪 tests ✅ | All tests passing (skipped when markdown_only) |
| 📝 docs ✅ | `docs_phase_passed: true`, all sync issues resolved |
