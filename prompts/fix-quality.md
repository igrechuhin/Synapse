## Fix Quality (Helper Command)

**AI EXECUTION COMMAND**: Fix type errors, formatting, linting, and related quality issues using Cortex MCP tools, outside of the full commit pipeline. This command is typically called when `/cortex/commit` or `run_preflight_checks` reports non-test quality failures.

**CURSOR COMMAND**: This is a Cursor command from the Synapse prompts directory, NOT a terminal command.

### Goals

- Drive the codebase toward zero type errors and clean formatting/linting.
- Use structured MCP tools instead of ad-hoc shell commands.
- Avoid running git operations or the full `/cortex/commit` pipeline.

### Tooling Requirements (MANDATORY)

- Prefer these Cortex MCP tools:
  - `fix_quality_issues(include_untracked_markdown=True)` for automated quality fixes.
  - `execute_pre_commit_checks(checks=["type_check", "quality", "format"], test_timeout=300, coverage_threshold=0.90, strict_mode=False)` for targeted quality verification.
- **Do NOT** run `black`, `ruff`, `isort`, or other formatters/linters directly; rely on Cortex MCP tools.

### Pre-Action Checklist

Before making changes, you MUST:

1. ✅ **Load relevant rules**:
   - Call `rules(operation="get_relevant", task_description="Type, lint, and formatting fixes")`.
   - If `rules()` is disabled, discover the rules directory using `get_structure_info()` and read the relevant rules files via standard tools.

2. ✅ **Understand current quality status**:
   - If recent `run_preflight_checks` or `/cortex/commit` output is available, review which checks failed (type_check, quality, markdown_lint, format).
   - If no recent context is available, run:
     - `execute_pre_commit_checks(checks=["type_check", "quality", "format"], test_timeout=300, coverage_threshold=0.90, strict_mode=False)`
     - And inspect the structured response for failures.

3. ✅ **Scope changes**:

- Focus on the files and modules relevant to the current work (especially recently modified files).
- Avoid large-scale refactors unless clearly necessary to resolve quality issues.

### Execution Steps

1. **Run automatic quality fixes**
   - Call `fix_quality_issues(include_untracked_markdown=True)` to apply automated fixes.
   - Inspect the response:
     - Note which files were modified.
     - Note any remaining type errors or issues that could not be auto-fixed.

2. **Address remaining issues manually**
   - For remaining type errors or lint violations:
     - Open the affected files and locations using standard IDE tools.
     - Apply precise, minimal fixes that respect project rules (e.g., strict typing, no use of `Any`, proper dependency injection).
   - For markdown issues:
     - Use `manage_file()` or standard tools to open the relevant docs.
     - Fix structural or content problems while preserving DRY linking and memory bank patterns.

3. **Re-run targeted quality checks**

   - After fixes, run:
     `execute_pre_commit_checks(checks=["type_check", "quality", "format"], test_timeout=300, coverage_threshold=0.90, strict_mode=False)`
   - Verify that:
     - Type errors are resolved.
     - Quality checks pass.
     - Formatting checks (including markdown) are clean.

4. **Summarize results**
   - List the main classes of issues that were fixed (e.g., type mismatches, unused imports, markdown heading structure).
   - Note any remaining non-blocking warnings and suggested future cleanups.

### Failure Handling

- If some quality issues cannot be fixed without broader refactoring or unclear requirements:
  - Clearly describe the blocking issues and why they cannot be resolved within this command.
  - Suggest creating or updating a plan (via `/cortex/plan`) to track larger refactors.
- Do **not** run git commit or push as part of this command; `/cortex/commit` remains responsible for the full commit pipeline.
