# Fix (Helper Command)

**AI EXECUTION COMMAND**: Fix issues in a targeted domain using Cortex MCP tools, outside of the full commit pipeline. This is a unified entry point for quality, test, and documentation fixes.

## Target Parameter

This prompt accepts an optional `target` parameter:

- **quality** -- Fix type errors, formatting, linting (formerly fix-quality.md)
- **tests** -- Diagnose and fix failing tests (formerly fix-tests.md)
- **docs** -- Synchronize documentation and memory bank (formerly docs-sync.md)
- **all** -- Run all three targets concurrently in parallel (see Parallel Execution below)

**GATE**: If `target` is **omitted**, you MUST behave as if `target=all` and run all three targets concurrently in parallel. Do **not** ask the user which target they need when the command is invoked without parameters.

## Parallel Execution (`all` target)

When `target=all`, launch **three independent subagents simultaneously** — one per target — rather than running them sequentially. Each subagent executes this same prompt with its specific target.

**MANDATORY**: All three agents must start at the same time. Do NOT wait for one to finish before starting another.

Steps:

1. Launch Agent 1: `fix quality` — runs the quality target workflow below.
2. Launch Agent 2: `fix tests` — runs the tests target workflow below.
3. Launch Agent 3: `fix docs` — runs the docs target workflow below.
4. Collect and merge all three results. Report a combined summary: which targets passed, which had remaining issues, and any cross-target interactions (e.g. quality fixes that affect test outcomes).

## Conventions

Per `shared-conventions.md`. Severity: GATE/CHECK/PREFER. Memory bank writes: per `memory-bank-contract.md`.

## Goals (All Targets)

- Use structured MCP tools instead of ad-hoc shell commands.
- Avoid running git operations or the full `/cortex/commit` pipeline.
- Do NOT commit or push as part of this command; `/cortex/commit` is responsible for the full pipeline.

### Target-Specific Goals

| Target | Goal |
|--------|------|
| quality | Drive codebase toward zero type errors, clean formatting/linting, and zero markdown lint errors |
| tests | Identify and fix failing tests; maintain or improve coverage |
| docs | Fix discrepancies between roadmap, activeContext, progress, and plans (does NOT cover markdown lint — use `quality` for that) |

## Tooling Requirements (MANDATORY)

### quality

- `execute_pre_commit_checks(checks=["fix_quality"], include_untracked_markdown=True)` for automated fixes (includes rumdl auto-fix for markdown).
- `execute_pre_commit_checks(checks=["type_check", "quality", "format", "markdown"], test_timeout=300, coverage_threshold=0.90, strict_mode=False)` for verification.
- **Do NOT** run `black`, `ruff`, `isort`, or other formatters/linters directly.
- For remaining non-autofixable markdown issues (`[MD057]` broken links, `[MD046]` unclosed code blocks, `[MD051]` missing fragments): use `Grep`/`Read`/`Edit` tools to locate and fix each issue manually.

### tests

- `execute_pre_commit_checks(checks=["tests"], test_timeout=600, coverage_threshold=0.90, strict_mode=False)` for test execution.
- `execute_pre_commit_checks(checks=["fix_errors", "format", "quality", "type_check"])` if type/quality issues block test fixes.
- **Do NOT** run raw test commands in Shell.

### docs

- `execute_pre_commit_checks(phase="B")` for aggregated docs/memory validation.
- `validate(check_type="timestamps")` and `validate(check_type="roadmap_sync")` for deeper inspection.
- `manage_file()` for reading/writing memory bank files via Cortex MCP.
- `get_structure_info()` for path resolution; do **not** hardcode `.cortex/` paths.

## Pre-Action Checklist

Before making changes, you MUST:

1. **Load relevant rules**:
   - quality: `rules(operation="get_relevant", task_description="Type, lint, and formatting fixes")`
   - tests: `rules(operation="get_relevant", task_description="Test debugging and coverage improvements")`
   - docs: `get_structure_info()` for paths, then `manage_file()` to read roadmap.md, activeContext.md, progress.md
   - If `rules()` is disabled, use `get_structure_info()` to discover the rules directory and read relevant rule files directly.

2. **Understand current status**:
   - quality: Review recent Phase A output or run `execute_pre_commit_checks(checks=["type_check", "quality", "format"], ...)`
   - tests: Review recent Phase A output or run `execute_pre_commit_checks(checks=["tests"], ...)`
   - docs: Review recent Phase B output or run `execute_pre_commit_checks(phase="B")`

3. **Scope changes**:
   - Focus on files and modules relevant to current work (especially recently modified files).
   - Avoid large-scale refactors unless clearly necessary.

Once the checklist is satisfied, **proceed directly through execution steps without pausing for user confirmation.**

## Execution Steps

**GATE**: Fix loops are limited to **3 iterations** per target (see `shared-conventions.md` Max-Retry Limits). After 3 failed fix-and-verify cycles, STOP and report unresolvable issues.

### quality Target

1. **Run automatic quality fixes**: Call `execute_pre_commit_checks(checks=["fix_quality"], include_untracked_markdown=True)`. This runs rumdl auto-fix for markdown alongside Python formatter/linter fixes. Note which files were modified and any remaining issues.
2. **Address remaining Python issues manually**: For remaining type errors or lint violations, open affected files and apply precise, minimal fixes (respect strict typing, no `Any`, proper DI).
3. **Address remaining markdown issues manually**: Run `execute_pre_commit_checks(checks=["markdown"])` to get the current rumdl output. For each remaining non-autofixable issue:
   - `[MD057]` broken relative links — use `Grep`/`Read` to verify whether the target file exists; if the link is stale (file was moved/deleted), update the link to the correct path or remove it. History files (`.cortex/history/`) may be excluded from fixes since they are read-only archives.
   - `[MD046]` unclosed code blocks — open the file, find the mismatched fence, and close it correctly.
   - `[MD051]` missing link fragments — either correct the fragment anchor or remove the anchor from the link.
   - Other non-autofixable rules — apply the minimal targeted edit to bring the file into compliance.
4. **Re-run targeted quality checks**: `execute_pre_commit_checks(checks=["type_check", "quality", "format", "markdown"], test_timeout=300, coverage_threshold=0.90, strict_mode=False)`. Verify zero errors.
5. **Summarize results**: List main classes of issues fixed. Note any remaining non-blocking warnings.

### tests Target

1. **Run or reuse test results**: If recent results exist from `execute_pre_commit_checks(checks=["tests"], ...)`, reuse them. Otherwise run tests fresh.
2. **Locate failing tests and code under test**: Open failing test files and implementation modules using standard IDE tools (`Grep`, `Read`).
3. **Debug and fix**: Apply changes in small, focused steps. Fix assertion logic, implementation bugs, or test setup. Follow AAA pattern, no skipped tests without justification.
4. **Re-run tests iteratively**: After fixes, re-run until all tests pass with coverage >= 90% global, >= 95% for new/modified code.
5. **Summarize outcomes**: List key fixes. Note any remaining risks or follow-up work.

### docs Target

1. **Analyze roadmap and plans**: Cross-check `roadmap.md` entries against plan files. Identify missing or renamed plans. Create missing plan stubs when roadmap references exist without corresponding files.
2. **Align activeContext and progress**: Ensure completed work is in `activeContext.md`, ongoing/future work in `roadmap.md`, recent achievements in `progress.md`. Use `manage_file()` for edits.
3. **Fix timestamp and sync issues**: Use `validate(check_type="timestamps")` and `validate(check_type="roadmap_sync")`. Apply targeted fixes for mismatched timestamps and invalid references.
4. **Re-run docs validation**: Call `execute_pre_commit_checks(phase="B")`. Confirm `status="success"` and `docs_phase_passed: true`.
5. **Summarize outcomes**: Describe specific fixes applied (roadmap corrections, plan stubs, timestamp fixes). Note any follow-up work.

## Failure Handling

For all targets: If issues cannot be fully resolved within this command:

- Clearly describe blocking issues and why they cannot be resolved.
- Suggest creating or updating a plan via `/cortex/plan` to track larger refactors.
- Do **not** run git commit or push.

## Success Criteria

| Target | Criteria |
|--------|----------|
| quality | Zero type errors, clean formatting/linting, zero rumdl markdown errors |
| tests | All tests passing, coverage >= threshold |
| docs | `docs_phase_passed: true`, all sync issues resolved |
