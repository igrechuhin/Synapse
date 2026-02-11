## Fix Tests (Helper Command)

**AI EXECUTION COMMAND**: Diagnose and fix failing tests using Cortex MCP tools, without running the full commit pipeline. This command is typically called **after** `/cortex/commit` (or `run_preflight_checks`) reports test failures.

**CURSOR COMMAND**: This is a Cursor command from the Synapse prompts directory, NOT a terminal command.

### Goals

- Identify and fix failing tests efficiently.
- Maintain or improve coverage to meet project thresholds.
- Avoid running the full commit pipeline or performing git operations.

### Tooling Requirements (MANDATORY)

- Use **Cortex MCP tools only** for tests and quality:
  - `execute_pre_commit_checks(checks=["tests"], test_timeout=..., coverage_threshold=0.90, strict_mode=False)`
  - `fix_quality_issues()` if type/quality issues block test fixes.
- **Do NOT** run raw test commands in a Shell. Always use `execute_pre_commit_checks` for test execution.

### Pre-Action Checklist

Before making changes, you MUST:

1. ✅ **Load relevant rules**:
   - Call `rules(operation="get_relevant", task_description="Test debugging and coverage improvements")`.
   - If `rules()` is disabled, use `get_structure_info()` to discover the rules directory and read the relevant rules files via standard tools.

2. ✅ **Understand recent failures**:
   - If available, inspect the most recent `run_preflight_checks` or `/cortex/commit` output to see which tests failed.
   - If that context is not available, run `execute_pre_commit_checks(checks=["tests"], test_timeout=600, coverage_threshold=0.90, strict_mode=False)` once to get a fresh baseline.

3. ✅ **Scope the task**:
   - Focus only on **test failures and coverage gaps** related to the current work.
   - Do **not** attempt to run memory-bank/roadmap sync or git operations.

### Execution Steps

1. **Run or reuse test results**
   - If you already have recent structured results from `execute_pre_commit_checks(checks=["tests"], ...)`, reuse them.
   - Otherwise, call `execute_pre_commit_checks(checks=["tests"], test_timeout=600, coverage_threshold=0.90, strict_mode=False)` to run tests.
   - Parse the structured response to identify:
     - Which tests failed.
     - Any coverage information provided (especially if below threshold).

2. **Locate failing tests and code under test**
   - Open the failing test files and the modules they exercise.
   - Use standard IDE tools (`Grep`, `Read`, `LS`) to navigate to:
     - The failing test functions.
     - The implementation that those tests cover.

3. **Debug and fix**
   - Apply changes in small, focused steps:
     - Fix assertion logic or expectations where incorrect.
     - Fix implementation bugs that cause failures.
     - Add or adjust fixtures and test setup/teardown as needed.
   - Follow project rules from AGENTS and shared rules (no skipped tests without justification, AAA pattern, etc.).

4. **Re-run tests iteratively**
   - After a set of fixes, re-run tests with:
     - `execute_pre_commit_checks(checks=["tests"], test_timeout=600, coverage_threshold=0.90, strict_mode=False)`.
   - Repeat the fix → re-run loop until:
     - All relevant tests pass, and
     - Coverage meets or exceeds thresholds (≥90% global, ≥95% for new/modified code) where reported.

5. **Summarize outcomes**
   - When tests are passing and coverage is acceptable:
     - Summarize key fixes that were made.
     - Note any remaining risks or follow-up work (e.g., refactors, additional tests).
   - Do **not** perform git commit or push in this command; `/cortex/commit` is responsible for the full pipeline.

### Failure Handling

- If repeated attempts to fix tests fail due to lack of context or unclear requirements:
  - Clearly explain what you tried and where you are blocked.
  - Suggest follow-up actions (e.g., add more logging, request clarification, create a focused plan).
