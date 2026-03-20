# Fix (Helper Command)

**AI EXECUTION COMMAND**: Fix issues in a targeted domain using Cortex MCP tools, outside of the full commit pipeline. This is a unified entry point for quality, test, and documentation fixes.

## Target Parameter

This prompt accepts an optional `target` parameter:

- **quality** -- Fix type errors, formatting, linting
- **tests** -- Diagnose and fix failing tests
- **docs** -- Synchronize documentation and memory bank
- **all** -- Run all three targets sequentially (see Sequential Execution below)

**GATE**: If `target` is **omitted**, you MUST behave as if `target=all` and run all three targets sequentially. Do **not** ask the user which target they need when the command is invoked without parameters.

## Zero-Arg Tools (all tools work with no arguments)

All MCP tools work when called with empty `{}` arguments. Use these zero-arg tools:

- `fix_quality_issues()` — auto-fix formatting, linting, type errors, markdown
- `run_quality_gate()` — run Phase A quality gate end-to-end
- `run_docs_gate()` — run Phase B docs/memory-bank validation

**CRITICAL: After calling any fix/gate tool, you MUST apply all remaining fixes inline. Do NOT produce a list of "required fixes" and stop. Just apply them immediately.**

## Sequential Execution (`all` target)

When `target=all`, run targets **one at a time in order**: quality → tests → docs. Do NOT launch concurrent subagents.

Steps:

1. Run `fix quality` — complete the full quality workflow below before proceeding.
2. Run `fix tests` — complete the full tests workflow below before proceeding.
3. Run `fix docs` — complete the full docs workflow below.
4. Report a combined summary: which targets passed, which had remaining issues.

## Goals (All Targets)

- Use structured MCP tools instead of ad-hoc shell commands.
- Do NOT commit or push as part of this command; `/cortex/commit` is responsible for the full pipeline.

## Pre-Action Checklist

Before making changes, load rules and run the first check. Then **immediately apply fixes**.

1. **Load rules** (background, no output to user):
   - Read the `cortex://rules` resource (zero-arg, reads task from session config).
   - If resource access fails, proceed without rules — fix based on error output.
2. **Start fixing immediately**: Do NOT produce a summary. The moment a tool returns errors, start editing files.

## Execution Steps

**GATE**: Fix loops are limited to **3 iterations** per target. After 3 failed fix-and-verify cycles, STOP and report unresolvable issues.

### quality Target

1. **Run automatic quality fixes**: Call `fix_quality_issues()`. This runs format, lint, type, and markdown auto-fix. Note any remaining issues.
2. **Verify**: Call `run_quality_gate()`. Parse the result for `preflight_passed` and per-check results.
3. **Get detailed errors**: If checks still fail, parse the `run_quality_gate()` result — fields `results.type_check.output` and `results.quality.output` contain full pyright/ruff error output.
4. **Fix remaining issues manually**: For each error, open the file and apply a precise fix:
   - **Type errors**: fix import, type annotation, or cast at the reported line.
   - **File too long** (> 400 lines): extract helpers or split into a new module.
   - **Function too long** (> 30 lines): extract helper functions.
   - **Governance test failures**: update `TOOL_CATEGORIES` in `categories.py`, add `EXAMPLES:` to MCP docstrings, or edit prompt files.
   - **Markdown lint**: fix manually per rule code (MD057, MD046, MD051, MD076, MD022, MD047). For `.cortex/memory-bank/*.md` use `manage_file()`.
5. **Re-verify**: Call `run_quality_gate()` again. Repeat from step 3 (max 3 iterations).

### tests Target

1. **Run quality gate**: Call `run_quality_gate()` to get test results alongside quality checks.
2. **Locate failing tests**: Open failing test files and implementation modules using `Grep`/`Read`.
3. **Debug and fix**: Apply changes in small, focused steps. Follow AAA pattern. Common patterns:
   - **Assertion count mismatch**: read the implementation, update the assertion.
   - **Governance tests**: fix the source (categories.py, prompt file, docstring) — never weaken the test.
4. **Re-run**: Call `run_quality_gate()` after fixes. Repeat (max 3 iterations).

### docs Target

1. **Analyze roadmap and plans**: Cross-check `roadmap.md` against plan files. Use `manage_file()` and `Glob` on `.cortex/plans/*.md`.
2. **Align activeContext and progress**: Ensure completed work in `activeContext.md`, ongoing work in `roadmap.md`.
3. **Fix timestamp and sync issues**: Read `cortex://validation` resource (defaults to timestamps). Apply targeted fixes.
4. **Re-run docs validation**: Call `run_docs_gate()`. If not passing, go back to step 1 (max 3 iterations).

## Failure Handling

**DO NOT stop to describe issues or ask the user if they want fixes applied.** Fix immediately and re-run.

- Type errors → edit the source file at the reported line.
- File/function too long → extract helpers; split if needed.
- Governance test failures → update `TOOL_CATEGORIES`, prompt files, or MCP docstrings.
- Test assertion mismatches → update the assertion (verify new behavior is correct first).
- Docs sync failures → edit memory bank files via `manage_file()`.

Only stop after **3 complete fix-and-verify iterations per target** have all failed.

## Success Criteria

| Target | Criteria |
|--------|----------|
| quality | Zero type errors, clean formatting/linting, zero markdown errors |
| tests | All tests passing, coverage >= threshold |
| docs | `docs_phase_passed: true`, all sync issues resolved |
