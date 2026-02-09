# Commit Changes

**AI EXECUTION COMMAND**: Execute the mandatory commit procedure with all required pre-commit checks, including testing of all runnable project tests.

**CRITICAL**: ONLY run this commit workflow when the user explicitly invoked `/cortex/commit` (or equivalent commit command). NEVER commit or push based on implicit assumptions like "as always" or "user expects this". Invoking this command IS an explicit commit request per `no-auto-commit.mdc` rule. Once invoked, execute all steps AUTOMATICALLY without asking for additional permission or confirmation.

**⚠️ ZERO ERRORS TOLERANCE (MANDATORY)**: This project has ZERO errors tolerance. ANY errors found in ANY check (formatting, types, linting, quality, tests) MUST block commit - NO EXCEPTIONS. Pre-existing errors are NOT acceptable - they MUST be fixed before commit. You MUST explicitly parse error counts from output and verify they are ZERO before proceeding to commit. DO NOT dismiss errors as "pre-existing" or "in files I didn't modify" - ALL errors must be fixed.

**⚠️ FIXES WITHOUT EXPLICIT REQUEST (MANDATORY)**: When any step fails (formatting, type check, quality, tests, roadmap sync, timestamps, etc.), apply fixes automatically as part of the pipeline. Do NOT wait for or ask the user to request fixes; do NOT stop and report without attempting fixes first. Fixing is the default response to any failure. Only after applying fixes and re-running validation may you report and stop if validation still fails or context is insufficient.

**⚠️ PROBLEM RESOLUTION FOCUS (MANDATORY)**: When a step fails, the pipeline must focus on **resolving the problem** in the same run—without waiting for the user to tell you to fix it. Your first response to any failure MUST be to attempt resolution (apply fixes, re-run validation). "Block commit" means: do not advance to the next step and do not create the commit until the failure is resolved. It does NOT mean: stop the pipeline and report to the user. Only after you have attempted fixes and re-run validation may you report and stop—and only if validation still fails after genuine fix attempts or context is insufficient to continue.

**Tooling Note**: Use standard Cursor tools (`Read`, `ApplyPatch`, `Write`, `LS`, `Glob`, `Grep`) by default; MCP filesystem tools are optional fallbacks only when standard tools are unavailable or explicitly requested. **Use Cortex MCP tools for memory bank and rules operations** (e.g., `manage_file()`, `rules()`, `get_memory_bank_stats()`, `validate()`, `check_structure_health()`).

**MCP TOOL USAGE (USE WHEN / EXAMPLES)**:

- **manage_file**
  - **Use when** you need to read or write Memory Bank files (`activeContext.md`, `progress.md`, `roadmap.md`) or query their metadata during the commit workflow.
  - **Required parameters**: `file_name`, `operation` (`"read"`, `"write"`, `"metadata"`).
  - **Anti-pattern**: NEVER call `manage_file({})` or omit `file_name`/`operation`; this indicates a missing plan step or a bug in the orchestration prompt.
  - **Friendly error behavior**: If you forget `file_name` or `operation`, `manage_file` returns a structured error with a `details.missing` list and a `hint` explaining how to call it correctly.
  - **Examples**:
    - Read current roadmap with metadata:
      - `manage_file(file_name="roadmap.md", operation="read", include_metadata=True)`
    - Update progress after tests pass:
      - `manage_file(file_name="progress.md", operation="write", content="[updated content]", change_description="Updated after commit checks")`
    - Check metadata only:
      - `manage_file(file_name="activeContext.md", operation="metadata")`

- **rules**
  - **Use when** you need project rules context (coding standards, testing rules, etc.) as part of pre-commit validation or report generation.
  - **Required parameter**: `operation` (`"index"` or `"get_relevant"`). `task_description` is REQUIRED for `"get_relevant"`.
  - **Friendly error behavior**: If you omit `operation`, `rules` returns a structured error with `details.missing=["operation"]` and a `hint` that lists valid values. If you pass an invalid operation, it returns `valid_operations` plus a `hint`.
  - **Examples**:
    - Index rules before a large refactor:
      - `rules(operation="index")`
    - Load rules relevant to commit/test work:
      - `rules(operation="get_relevant", task_description="Commit pipeline and test coverage enforcement")`

**Pre-Commit Checks**: Use the `execute_pre_commit_checks()` MCP tool for all pre-commit operations (fix errors, format, type check, quality, tests). **CRITICAL**: The tool resolves project root internally (via MCP context when available) and language on its own. **NEVER pass `project_root` as a parameter** - all Cortex MCP tools resolve project root internally. It provides:

- Language auto-detection (resolved internally)
- Structured parameters and return values
- Consistent error handling
- Type safety

**Agent Delegation**: This prompt orchestrates the commit workflow and delegates specialized tasks to dedicated agents in the Synapse agents directory.

**IMPORTANT**: This prompt focuses on **orchestration** (order, dependencies, workflow coordination). For **implementation details** (MCP tool calls, validation logic, specific checks), see the referenced agent files.

**Agents Used**:

- **error-fixer** - Step 0: Fix errors and warnings
- **quality-checker** - Step 0.5: Quality preflight (fail-fast)
- **code-formatter** - Step 1: Code formatting
- **markdown-linter** - Step 1.5: Markdown linting
- **type-checker** - Step 2: Type checking
- **quality-checker** - Step 3: Code quality checks
- **test-executor** - Step 4: Test execution
- **memory-bank-updater** - Step 5: Memory bank operations
- **memory-bank-updater** - Step 6: Roadmap updates
- **plan-archiver** - Step 7: Plan archiving
- **plan-archiver** - Step 8: Archive location validation
- **timestamp-validator** - Step 9: Timestamp validation
- **Step 10** - Ensure roadmap and activeContext reflect actual state (orchestration only; no dedicated agent)

**Subagent execution strategy (MANDATORY)**:

- For **state-changing steps (0–8)** you MUST run agents **sequentially**, never in parallel.
- For **read-only validators and submodule handling (9–11)** you MAY run them in parallel **only if** the platform safely supports concurrent tool calls; otherwise, default to sequential execution.
- NEVER start new subagents that can touch the same files while a previous subagent that might modify those files is still running.
- If there is **any doubt** about shared files or race conditions, choose **sequential execution**.

**Concurrency rules (Steps 9–11 parallel block)**:

- **Steps 0–8** and **Steps 12–14** MUST remain strictly sequential (ordering and dependencies).
- **Steps 9, 10, and 11** form a **parallel validation/submodule block**: they are logically independent (read-only validators + submodule handling) and MAY run concurrently when the platform safely supports concurrent tool calls.
- When running Steps 9–11 in parallel: start all three after Step 8 completes; wait for **all three** to finish before proceeding to Step 12; aggregate their results; if **any** of the three fails or reports blocking issues, treat the block as failed and do not proceed to Step 12.
- Do **not** add other steps to the parallel group without explicit dependency analysis (see Phase 56 plan). Memory-bank and plan writers remain serialized.

**Steps without dedicated agents** (handled directly in orchestration):

- **Step 11**: Submodule handling (Synapse submodule)
- **Step 12**: Final validation gate (re-verification of formatting, types, linting, quality)
- **Step 13**: Commit creation
- **Step 14**: Push branch
- **Step 15**: Execute Analyze (End of Session) prompt (`analyze.md`)

**Script use (MANDATORY)**:

- If during this run you created or executed any script (inline snippet or file), you MUST call `capture_session_script` and/or `analyze_session_scripts` or `suggest_tool_improvements` as appropriate. Do not run scripts without using script tooling.

**When executing steps**: For steps that delegate to agents, you MUST:

1. **READ** the agent file from the Synapse agents directory (`{agent-name}.md`); resolve path via project structure or `get_structure_info()` if needed
2. **EXECUTE** all execution steps from the agent file
3. **VERIFY** success and proceed with orchestration

Steps without agents are handled directly by the orchestration workflow.

## ⚠️ MANDATORY PRE-ACTION CHECKLIST

**BEFORE executing this command, you MUST:**

1. ✅ **Read relevant memory bank files** - Understand current project context:
   - **Use Cortex MCP tool `manage_file(file_name="activeContext.md", operation="read")`** to understand current work focus
   - **Use Cortex MCP tool `manage_file(file_name="progress.md", operation="read")`** to see recent achievements
   - **Use Cortex MCP tool `manage_file(file_name="roadmap.md", operation="read")`** to understand project priorities
   - **Note**: Access memory bank files via Cortex MCP tool `manage_file(file_name="...", operation="read"|"write")`; do not hardcode paths. Resolve memory bank path via `get_structure_info()` → `structure_info.paths.memory_bank` if needed.

1. ✅ **Read relevant rules** - Understand commit requirements:
   - **Skipping the rules load step is a CRITICAL violation.** Any fix (especially type, lint, or visibility) must be validated against **loaded** rules before applying.
   - Call `rules(operation="get_relevant", task_description="Commit pipeline, test coverage, type fixes, and visibility rules")`. If the rules tool is unavailable (e.g. disabled), read rules from the rules directory (path from `get_structure_info()` → `structure_info.paths.rules`) or the Synapse rules directory so that coding standards and visibility/API rules are in context.
   - **Rules loaded via MCP (rules tool) or rule files read for this run: Yes / No. If No, do not proceed to Step 0. When `rules()` returns `disabled`, read rule files via Read tool and record "Rules loaded: Yes (via file read)".**

1. ✅ **Verify code conformance to rules** - Before running checks, verify code follows rules:
   - Review changed files to ensure they conform to coding standards read above
   - Verify type annotations are complete per language-specific standards
   - Verify structured data types follow project's data modeling standards (check language-specific rules)
     - **MANDATORY CHECK**: Scan code for data structure types - verify they comply with project's required data modeling patterns
     - **MANDATORY CHECK**: Check language-specific coding standards for required data modeling types (e.g., check python-coding-standards.mdc for Python)
     - **BLOCKING**: If data structures don't comply with project's required modeling standards, this MUST be fixed before proceeding
   - Verify functions/methods are within project's length limits
   - Verify files are within project's size limits
   - Verify dependency injection patterns are followed (no global state or singletons)
   - **If violations found**: Fix them BEFORE proceeding with pre-commit checks

1. ✅ **Understand operations** - Use MCP tools for all operations:
   - **Pre-commit checks**: Use `execute_pre_commit_checks()` MCP tool for fix_errors, format, type_check, quality, and tests
   - **Memory bank operations**: Use existing MCP tools (`manage_file()`, `get_memory_bank_stats()`) instead of prompt files
   - **Validation operations**: Use existing MCP tools (`validate()`, `check_structure_health()`) instead of prompt files

1. ✅ **Verify prerequisites** - Ensure all prerequisites are met:
   - Confirm there are changes to commit
   - Verify build system is accessible
   - Check that test suite can be executed

1. ✅ **Scan for MCP validation errors** - Before proceeding, check recent MCP tool invocations:
   - Look for validation errors in tool responses (e.g., `status="error"` with `details.missing` or `details.invalid` fields)
   - Common errors: Missing `file_name`/`operation` in `manage_file()`, missing `operation` in `rules()`, invalid parameter types
   - **If validation errors are present**: Update prompts/rules to eliminate them before proceeding
   - **BLOCK COMMIT**: MCP validation errors indicate bugs in orchestration prompts/agents that MUST be fixed

**VIOLATION**: Executing this command without following this checklist is a CRITICAL violation that blocks proper commit procedure.

## Pre-Step: Load Rules (MANDATORY — BEFORE Step 0)

**Before running Step 0 (Fix Errors) or any code-modifying step:**

1. **Load rules**: Call `rules(operation="get_relevant", task_description="Commit pipeline, test coverage, type fixes, and visibility rules")`. If the rules tool is unavailable (e.g. disabled), read rules from the rules directory (path from `get_structure_info()` → `structure_info.paths.rules`) or Synapse rules directory so that coding standards and visibility/API rules are in context.
2. **When `rules()` returns status `disabled`**: Resolve the rules or Synapse rules path via `get_structure_info()` (e.g. `structure_info.paths.rules` or Synapse rules directory), then use the Read tool to load at least the rule files relevant to the commit task (e.g. python-coding-standards.mdc, python-mcp-development.mdc, no-test-skipping.mdc from Synapse rules, or equivalent). Record **Rules loaded: Yes (via file read)** so the checklist is satisfied.
3. Do **not** run Step 0 (fix_errors) or any code-modifying step until rules have been loaded or read.
4. **BLOCK**: If rules have not been loaded/read for this run, do not proceed to Step 0.

**Checklist item**: Rules loaded via MCP (rules tool) or rule files read: Yes / No. If No, do not proceed. When the rules tool returns `disabled`, satisfy via file read and record "Rules loaded: Yes (via file read)".

## ⚠️ CRITICAL: Synapse Architecture (MANDATORY)

When modifying Synapse (prompts/rules/agents) files:

- **Prompts (`prompts/*.md`)**: MUST be language-agnostic and project-agnostic
  - DO NOT hardcode language-specific commands (e.g., `ruff`, `black`, `prettier`)
  - DO NOT reference project-specific requirements (e.g., "Pydantic models")
  - DO use Cortex MCP tools for all checks (e.g., `execute_pre_commit_checks()`)
  - DO use generic language: "check language-specific rules", "use project-mandated types"
  - DO NOT instruct agents to run scripts directly; tools resolve language and run the appropriate checks

- **Rules (`rules/*.mdc`)**: Language-specific rules are allowed
  - Python-specific rules go in `rules/python/`
  - General rules go in `rules/general/`

- **Scripts (`scripts/{language}/*.py`)**: Language-specific implementations
  - Each language has its own directory
  - Scripts handle tool detection and project structure automatically

## ⚠️ COMMON ERRORS TO CATCH BEFORE COMMIT

The following error patterns MUST be detected and fixed before commit. These are common issues that have caused problems in the past:

### Type Errors

- **Pattern**: Type checker reports type errors (not warnings)
- **Detection**: Parse type checker output for error count (e.g., Pyright for Python, TypeScript compiler for TypeScript)
- **Action**: Fix all type errors, re-run type checker, verify zero errors
- **Block Commit**: Yes - type errors will cause CI to fail
- **⚠️ CRITICAL**: Step 12.2 uses `execute_pre_commit_checks(checks=["type_check"])` which checks BOTH `src/` AND `tests/` to match CI. Step 12.2 result is AUTHORITATIVE - if the tool finds errors, commit MUST be blocked.
- **Note**: Only applicable if project uses a type system (Python with type hints, TypeScript, etc.)

### Test Failures

- **Pattern**: Test suite reports failures (failed count > 0)
- **Detection**: Parse test output for failure count
- **Action**: Fix failing tests, re-run tests, verify zero failures
- **Block Commit**: Yes - test failures will cause CI to fail

### Test Coverage Below Threshold

- **Pattern**: Coverage percentage < 90%
- **Detection**: Parse coverage report from test output (MANDATORY - must extract exact percentage)
- **Action**: Add tests to increase coverage, re-run tests, verify coverage ≥ 90% — **in this same run** (same as other violations). Do NOT stop and report; keep adding tests and re-running until coverage ≥ 90% or context is insufficient.
- **Block Commit**: Yes - do not proceed to Step 5 (memory bank, etc.) until coverage ≥ 90%. "Block commit" means do not advance to the next step; it does NOT mean stop the commit procedure and report.
- **CRITICAL**: Coverage MUST be parsed from test output, not estimated or assumed
- **CRITICAL**: If coverage is below 90%, DO NOT proceed to Step 5 - fix coverage first **in this same run** (add tests, re-run, repeat until ≥ 90%)
- **CRITICAL**: Coverage validation is MANDATORY - there are NO exceptions or "slightly below" allowances
- **Validation**: Coverage percentage MUST be explicitly extracted and verified ≥ 90.0% before proceeding
- **Enforcement**: If coverage < 90.0%, do not advance to Step 5; fix coverage in this same run (add tests, re-run tests) until coverage ≥ 90.0%. Only stop and provide summary if context is insufficient AFTER attempting fixes, per "Context Assessment" in Failure Handling.
- **Re-run tests / coverage report (MANDATORY)**: When re-running tests or when you need a coverage report to fix coverage, use **only** the Cortex MCP tool:
  - `execute_pre_commit_checks(checks=["tests"], test_timeout=600, coverage_threshold=0.90, strict_mode=False)`
  Do **NOT** run raw test commands in a Shell - use the MCP tool only. Running the test runner directly can produce huge output and long runs and bypass project timeout/configuration.

**Coverage at commit (full test run)**:

- **Mandatory**: For the normal commit pipeline, the **full** test suite runs with `fail-under=90`. If total coverage is below 90%, the commit is **blocked** and you **must** add or improve tests until coverage ≥ 90% before committing. There is no exception for "technical debt" on the main commit run.

**Coverage interpretation for focused work (targeted test runs only)**:

- **New or modified code**: Must meet ≥95% coverage.
- **Global `fail-under=90` failures when running targeted tests**: When you run a **subset** of tests (e.g. only tests for one module), the **global** coverage number can still be below 90% because many modules were not exercised. In that situation only:
  - **"Logged as technical debt"** means: **document** the shortfall in Memory Bank (e.g. in `progress.md` or `activeContext.md`) and, where appropriate, add or reference a roadmap phase for coverage improvement — instead of blocking the current focused task or trying to fix all coverage ad hoc during unrelated work.
  - You must still **improve the test set** to achieve the 90% target; that work is tracked as a dedicated phase/plan (e.g. "Phase XX: raise coverage for module Y") rather than done ad hoc in the current change.
- **Recording coverage debt**: Use wording like: "Global coverage at 21.7% due to untested analysis/structure modules. This is expected legacy debt and does not block focused roadmap sync work. Coverage improvement tracked in Phase XX."
- **Reference coverage plans**: Reference relevant coverage-improvement plan from roadmap entries instead of attempting broad, unscheduled coverage work.

**Testing MCP JSON in tests**: When adding tests that assert on MCP tool JSON (e.g., manage_file, rules, execute_pre_commit_checks), follow the project's language-specific testing rules for structured JSON (see language rules and tests/tools/ for the required pattern).

### File Size Violations

- **Pattern**: Files exceeding 400 lines
- **Detection**: Parse MCP tool response - check `results.quality.success` = false OR `len(results.quality.file_size_violations)` > 0
- **Action**: Split large files, re-run check, verify `success` = true AND violations array is empty
- **Block Commit**: Yes - file size violations will cause CI to fail
- **⚠️ NO EXCEPTIONS**: Pre-existing violations are NOT acceptable - they MUST be fixed before commit

### Function Length Violations

- **Pattern**: Functions exceeding 30 lines
- **Detection**: Parse MCP tool response - check `results.quality.success` = false OR `len(results.quality.function_length_violations)` > 0
- **Action**: Refactor long functions, re-run check, verify `success` = true AND violations array is empty
- **Block Commit**: Yes - function length violations will cause CI to fail
- **⚠️ NO EXCEPTIONS**: Pre-existing violations are NOT acceptable - they MUST be fixed before commit

### ⚠️ Pre-Existing Violations (CRITICAL ANTI-PATTERN)

- **Pattern**: Agent dismisses violations as "pre-existing issues" and proceeds with commit
- **Detection**: Agent acknowledges violations exist but commits anyway with reasoning like "these are pre-existing"
- **Why This Is WRONG**: CI doesn't care if violations are new or pre-existing - it will FAIL regardless
- **Action**: NEVER proceed with commit when violations exist, regardless of their origin
- **Block Commit**: Yes - ANY violation blocks commit, period
- **Note**: The only acceptable state is `results.quality.success` = true with empty violation arrays

### Formatting Violations

- **Pattern**: Formatter check reports formatting issues
- **Detection**: Parse MCP tool response (e.g., `execute_pre_commit_checks(checks=["format"])`) or formatter check script output for file count
- **Action**: Run formatter, re-run formatter check, verify zero violations
- **Block Commit**: Yes - formatting violations will cause CI to fail

### Linter Errors

- **Pattern**: Linter reports errors (not warnings)
- **Detection**: Parse linter output for error count - MUST explicitly extract and verify error count = 0
- **Action**: Fix linting errors, re-run linter, verify zero errors
- **Block Commit**: Yes - linter errors will cause CI to fail
- **⚠️ ZERO ERRORS TOLERANCE**: The project has ZERO errors tolerance - ANY errors (new or pre-existing) MUST block commit
- **⚠️ NO EXCEPTIONS**: Pre-existing linting errors are NOT acceptable - they MUST be fixed before commit
- **⚠️ ABSOLUTE BLOCK**: If error count > 0 (even if errors are in files you didn't modify), stop immediately - DO NOT proceed to commit
- **Note**: **Use `execute_pre_commit_checks()` MCP tool for all pre-commit operations** (e.g. `execute_pre_commit_checks(checks=["quality"])` for the quality gate; quality gate runs both quality (lint, file sizes, function lengths) and type_check so type diagnostics match IDE/CI)

### Integration Test Failures

- **Pattern**: Integration tests fail (specific test category)
- **Detection**: Parse test output to identify integration test failures
- **Action**: Fix integration test issues, re-run tests, verify all pass
- **Block Commit**: Yes - integration test failures indicate broken functionality

### Fixing type/visibility without loaded rules

- **Pattern**: Agent applies type or visibility fixes (e.g. reportPrivateUsage, silencing) without having loaded rules first.
- **Detection**: No `rules()` call (or rule files read) before Step 0 or before applying fixes.
- **Action**: Load rules first, then re-validate fix against rules (e.g. test via public API, do not use reportPrivateUsage=false). BLOCK commit if fixes were applied without rule context.
- **Block Commit**: Yes - fixes applied without rule context must be re-validated; do not proceed until rules are loaded and fix is rule-compliant.

### Script run without analysis

- **Pattern**: Agent ran a script (e.g. Python/shell snippet) during the pipeline without using script tooling.
- **Detection**: Script was created or executed (inline or file) but no call to `capture_session_script`, `analyze_session_scripts`, or `suggest_tool_improvements` was made.
- **Action**: Use script tooling: call `capture_session_script` and/or `analyze_session_scripts` or `suggest_tool_improvements` as appropriate. Not using script tooling is a process violation.
- **Block Commit**: Yes - script runs without analysis violate Phase 27 script-generation-prevention and implement-next-roadmap-step guidance; do not proceed until script tooling has been used.

### Type Checker Warnings

- **Pattern**: Type checker reports warnings (not errors)
- **Detection**: Parse type checker output for warning count
- **Action**: Fix all warnings, re-run type checker, verify zero warnings
- **Block Commit**: Yes - warnings must be resolved before commit
- **Note**: Only applicable if project uses a type system (Python with type hints, TypeScript, etc.)

### ⚠️ Errors Introduced After Initial Checks (CRITICAL)

- **Pattern 1 - Code changes**: Code changes made AFTER Step 2-4 (type check, quality, tests) introduce NEW errors
- **Pattern 2 - New files**: NEW files created during Step 4 (e.g., test files to fix coverage) are NEVER formatted by Step 1
- **Detection**: CI fails with type/lint/formatting errors that weren't present in original checks
- **Root Cause 1**: Agent makes code changes during steps 5-11 without re-running type check
- **Root Cause 2**: Agent creates new test files during Step 4 to fix coverage, but Step 1 (Formatting) already ran
- **Example Failure 1**: Agent adds constants to fix tests, those constants have type errors, agent commits without re-checking
- **Example Failure 2**: Agent creates `test_new_module.py` during Step 4 coverage fix, file is never formatted, CI fails on Black check
- **Action**: ALWAYS run Step 12 (Final Validation Gate) immediately before commit - use `execute_pre_commit_checks(checks=["format"])` (fix then check) and verify success
- **Block Commit**: Yes - Step 12 is MANDATORY and cannot be skipped
- **Prevention**: ANY code change OR new file creation after Step 1 REQUIRES re-running formatting fix AND verification before commit
- **Note**: This is the most common cause of CI failures that "should have been caught"

**CRITICAL**: All error patterns above MUST be validated by parsing command output, not just checking exit codes. Exit codes can be misleading - always parse actual output to verify results.

## ⚠️ GIT WRITE SAFETY (CRITICAL - MANDATORY)

**ONLY run this commit workflow when the user explicitly invoked `/cortex/commit` command. NEVER commit or push based on implicit assumptions like 'as always' or 'user expects this'.**

### Branch Safety Rule

- **Push on commit**: When the user invokes `/cortex/commit`, run the full pipeline including push. Push the current branch (including `main`) without requiring extra confirmation.
- **Pre-commit checks**: Before any `git add`, `git commit`, or `git push`, verify:
  1. User explicitly requested commit/push (via `/cortex/commit` or explicit "commit"/"push" instruction)
  2. All validation gates have passed

### Git Write Preconditions

Before any `git add`, `git commit`, or `git push`:

1. **User explicitly requested** commit/push (via `/cortex/commit` or explicit "commit"/"push" instruction).
2. **All validation gates** (Steps 0–12) have passed.

Step 13 and Step 14 below contain mandatory precondition checks; do not skip them.

### Step 1.5: Markdown linting (delegate to `markdown-linter`)

- **Agent**: Use the markdown-linter agent (Synapse agents directory) for implementation details
- **Dependency**: Must run AFTER Step 1 (code formatting)
- **CRITICAL**: Must check ALL markdown files (like CI does) - use `check_all_files=True` to match CI behavior
- **CRITICAL**: CI checks ALL markdown files and fails on ANY error - commit pipeline MUST match this behavior
- **BLOCK COMMIT**: If ANY markdown lint errors remain (not just critical errors in memory bank/plans)
- **⚠️ ZERO ERRORS TOLERANCE**: The project has ZERO errors tolerance - ANY markdown lint error (in ANY file) MUST block commit
- **⚠️ NO EXCEPTIONS**: Pre-existing markdown lint errors are NOT acceptable - they MUST be fixed before commit
- **Workflow**: After agent completes, verify zero errors remain in ALL markdown files before proceeding to Step 2

### Step 2: Type checking (delegate to `type-checker`)

- **Agent**: Use the type-checker agent (Synapse agents directory) for implementation details
- **Dependency**: Must run AFTER Step 1.5 (markdown linting)
- **Conditional**: Only execute if project uses a type system (Python with type hints, TypeScript, etc.)
- **CRITICAL**: Must verify zero type errors AND zero warnings
- **⚠️ IMPORTANT**: Step 12.2 (Final Validation Gate) uses `execute_pre_commit_checks(checks=["type_check"])` which checks BOTH `src/` AND `tests/` to match CI - Step 12.2 is AUTHORITATIVE and takes precedence.
- **BLOCK COMMIT**: If any type errors OR warnings remain
- **Workflow**: After agent completes, verify zero errors and zero warnings before proceeding to Step 3
- **Skip if**: Project does not use a type system

### Step 3: Code quality checks (delegate to `quality-checker`)

- **Agent**: Use the quality-checker agent (Synapse agents directory) for implementation details
- **Dependency**: Must run AFTER Step 2 (type checking)
- **CRITICAL**: Must verify zero file size violations AND zero function length violations
- **⚠️ ABSOLUTE BLOCK**: If any violations exist (pre-existing or new), stop immediately - CI will fail
- **NO EXCEPTIONS**: Pre-existing violations are NOT acceptable
- **Workflow**: After agent completes, verify zero violations before proceeding to Step 4
- **Context Assessment**: If insufficient context remains after fixing violations, provide comprehensive summary and advise re-running commit pipeline

### Step 4: Test execution (delegate to `test-executor`)

- **Agent**: Use the test-executor agent (Synapse agents directory) for implementation details
- **Dependency**: Must run AFTER Steps 0-3 (errors, formatting, type checking, quality checks are fixed)
- **CRITICAL**: Tests must pass with 100% pass rate AND coverage ≥ 90% (NO exceptions)
- **BLOCK COMMIT**: If any test fails OR coverage < 90%, stop immediately
- **Workflow**: After agent completes, verify 100% pass rate and 90%+ coverage before proceeding to Step 5

### Step 5: Memory bank operations (delegate to `memory-bank-updater`)

- **Agent**: Use the memory-bank-updater agent (Synapse agents directory) for implementation details
- **Dependency**: Must run AFTER Step 4 (test execution)
- **Workflow**: Agent updates activeContext.md, progress.md, and roadmap.md with current changes

### Step 6: Update roadmap (delegate to `memory-bank-updater`)

- **Agent**: Use the memory-bank-updater agent (Synapse agents directory) for implementation details
- **Dependency**: Runs as part of Step 5 (memory bank operations)
- **Workflow**: Agent updates roadmap.md with completed items and new milestones

### Step 7: Archive completed plans (delegate to `plan-archiver`)

- **Agent**: **MANDATORY** - Read the plan-archiver agent (Synapse agents directory) and execute ALL its execution steps
- **Dependency**: Must run AFTER Step 5 (memory bank operations)
- **CRITICAL**: If no completed plans are found, report "0 plans archived" but DO NOT skip this step
- **BLOCK COMMIT**: If completed plans are found but not archived, or if link validation fails
- **Workflow**:
  1. **READ** the plan-archiver agent file (Synapse agents directory)
  2. **EXECUTE** all execution steps from the agent file (detect completed plans, archive them, update links, validate)
  3. After agent completes, verify all plans archived and links updated before proceeding to Step 8

### Step 8: Validate archive locations (part of `plan-archiver`)

- **Agent**: This validation is handled by `plan-archiver` agent in Step 7
- **Dependency**: Runs as part of Step 7 (plan archiving)
- **CRITICAL**: Verify no completed plans remain in the plans directory; resolve path via `get_structure_info()` → `structure_info.paths.plans`
- **BLOCK COMMIT**: If any completed plans remain unarchived or in wrong locations
- **Workflow**: After Step 7 completes, verify archive validation passed before proceeding to Step 9

**Parallel validation/submodule block (Steps 9–11)**: Steps 9, 10, and 11 may run in parallel when the platform supports concurrent tool calls; Step 12 runs only after all three complete. See "Concurrency rules" above.

### Step 9: Validate memory bank timestamps (delegate to `timestamp-validator`)

- **Agent**: Use the timestamp-validator agent (Synapse agents directory) for implementation details
- **Dependency**: Must run AFTER Step 5 (memory bank operations)
- **CRITICAL**: All timestamps must use YYYY-MM-DD format (no time components)
- **BLOCK COMMIT**: If any timestamp violations are found
- **Workflow**: After agent completes, verify zero violations before proceeding to Step 10

### Step 10: Ensure roadmap and activeContext reflect actual state

- **When reporting this step** (e.g. in todos or failure messages), use the name: **"Ensure roadmap and activeContext reflect actual state"**. Do not use "Roadmap synchronization validation".
- **Dependency**: Must run AFTER Step 5 and Step 6 (memory bank and roadmap updates)
- **Workflow** (orchestration only; no `validate(check_type="roadmap_sync")`):
  1. **Read** `roadmap.md` and `activeContext.md` via `manage_file(file_name="roadmap.md", operation="read")` and `manage_file(file_name="activeContext.md", operation="read")`.
  2. **Verify split**: Roadmap must contain only **future/upcoming** work. activeContext must contain **completed** work only (per memory bank workflow).
  3. **Fix if needed**: If any bullet in `roadmap.md` clearly represents completed work (e.g. contains " - COMPLETE", " - COMPLETED", "✅ ... COMPLETE"), add a brief summary to `activeContext.md` (if not already there) and **remove** those lines from `roadmap.md` via `manage_file(file_name="roadmap.md", operation="write", content=...)` (or equivalent). Do not scan the codebase for TODOs or validate plan references.
  4. **Proceed**: Once roadmap and activeContext reflect the actual split (future vs completed), consider Step 10 complete and proceed to Step 11.
- **No codebase scan**: Do NOT run `validate(check_type="roadmap_sync")`. Do NOT match production TODOs to roadmap entries or validate unlinked plans as part of this step.
- **Non-blocking**: This step ensures state consistency only. If the content is already consistent, no changes are required. No hard gate that blocks commit.

### Step 11: Submodule handling (Synapse submodule)

- **Path resolution**: Resolve the Synapse directory path via `get_structure_info()` (e.g. `structure_info.paths.synapse` if available) or use the project-relative path to the Synapse submodule. Use this path for all `git -C <Synapse-directory-path>` and `git add <Synapse-directory-path>` commands.
- **Dependency**: Must run AFTER Step 10 (roadmap/activeContext state)
- **Workflow**: Follow explicit command sequence below to handle submodule changes deterministically.
- **Strict decision rule**: Execute sub-steps 11.1 → 11.5 in order. At each step, only proceed to the next sub-step when the condition is met; otherwise skip to Step 12 (or, in 11.5, block commit). Do not run sub-steps in parallel or reorder them.

**Step 11.1 - Check parent repo status**:

```bash
git status --porcelain
```

- **If output contains dirty Synapse submodule** (e.g. `m` on Synapse path): Proceed to Step 11.2
- **If Synapse submodule is clean**: Skip to Step 12 (submodule pointer is clean)

**Step 11.2 - Check submodule working tree**:

```bash
git -C <Synapse-directory-path> status --porcelain
```

- **If empty**: Skip to Step 12 (submodule pointer changed but no local edits)
- **If non-empty**: Proceed to Step 11.3 (submodule has uncommitted changes)

**Step 11.3 - Commit and push in submodule**:

```bash
git -C <Synapse-directory-path> add -A
git -C <Synapse-directory-path> commit -m "Update Synapse prompts/rules"
git -C <Synapse-directory-path> push
```

- **Verify**: Each command succeeds before proceeding to next
- **If any command fails**: Report error and block main commit

**Step 11.4 - Update parent repo submodule pointer**:

```bash
git add <Synapse-directory-path>
git diff --submodule=log -- <Synapse-directory-path>
```

- **Verify**: `git diff` shows pointer movement (submodule commit hash changed)
- **If no pointer movement**: Investigate - submodule commit may have failed
- **Note**: Updated submodule reference will be included in main commit (Step 13)

**Step 11.5 - Verify submodule is clean** (MANDATORY, CRITICAL):

- **MUST run after Step 11.4** to catch any uncommitted changes remaining after submodule operations (e.g., missed by 11.3 or introduced during Steps 0–11).
- Run:

```bash
git -C <Synapse-directory-path> status --porcelain
```

- **If output is empty**: Proceed to Step 12 (submodule is clean).
- **If output is non-empty**: **BLOCK COMMIT** — report uncommitted changes and require manual intervention. Stop immediately; do not proceed to Step 12 or Step 13 until the user has committed and pushed submodule changes.
- **Rationale**: Prevents uncommitted submodule changes from being missed, which causes inconsistent state between parent repo and submodule.

### Step 12: Final validation gate (MANDATORY re-verification)

- **Dependency**: Must run AFTER Steps 4-11 (any code changes may have been made)
- **CRITICAL**: This step exists because Steps 4-11 may create new files or make code changes that weren't validated
- **⚠️ ABSOLUTE MANDATORY**: Step 12 CANNOT be skipped, bypassed, or assumed to have passed. It MUST be executed in full before Step 13.
- **⚠️ EXECUTION VERIFICATION REQUIRED**: Before proceeding to Step 13, you MUST provide explicit evidence that ALL Step 12 sub-steps were executed:
  - Step 12.0: Markdown re-validation on modified files executed (output shown)
  - Step 12.1: Formatting fix AND check executed (output shown); Step 12.1.2 result parsed and verified before Step 12.2; CI parity (12.1.3) recommended
  - Step 12.2: Type check tool executed (`execute_pre_commit_checks(checks=["type_check"])` result shown with success and 0 errors)
  - Step 12.3: Linter check executed (output shown with error count = 0)
  - Step 12.4: Test naming check executed (output shown)
  - Step 12.5: Markdown lint check executed (output shown)
  - Step 12.6: File sizes AND function lengths checks executed (output shown)
  - Step 12.7: Tests with coverage validation executed (output shown)
- **Workflow**: Re-run formatting, type checking, linting, and quality checks to catch any new issues
- **⚠️ ZERO ERRORS TOLERANCE**: The project has ZERO errors tolerance - ANY errors (new or pre-existing) MUST block commit
- **⚠️ NO EXCEPTIONS**: Pre-existing errors are NOT acceptable - they MUST be fixed before commit
- **⚠️ ABSOLUTE BLOCK**: If ANY errors are found in ANY check (formatting, types, linting, quality), stop immediately - DO NOT proceed to commit
- **BLOCK COMMIT**: If any checks fail in this step OR if any error count > 0 OR if Step 12 execution cannot be verified
- **See detailed instructions below** for specific validation steps

### Step 13: Commit creation

- **Dependency**: Must run AFTER Step 12 (final validation gate passes)
- **⚠️ PRECONDITION CHECK (MANDATORY)**: Before executing Step 13, you MUST verify:
  1. **User explicitly requested commit**: Verify user invoked `/cortex/commit` or explicitly requested commit. If not, STOP and ask for confirmation.
  2. **Step 12 was fully executed**: All Step 12 sub-steps (12.1-12.7) were executed and their outputs were verified
  3. **Step 12.2 type check passed**: The type check tool (`execute_pre_commit_checks(checks=["type_check"])`) was executed and returned success with 0 errors
  4. **No errors in any Step 12 check**: All Step 12 checks passed with zero errors
  5. **If you fixed type errors (12.2) or lint errors (12.3) during this run**: Step 12.3 was executed again after the fix and `results.quality.success` is true with zero errors; do not proceed if 12.3 was not re-run after a code change in 12.2 or 12.3
  6. **Explicit verification provided**: You have documented the execution of Step 12 with actual command outputs
  7. **All validation gates passed**: Steps 0-12 have completed successfully
- **⚠️ BLOCK COMMIT**: If user did not explicitly request commit OR if Step 12 execution cannot be verified OR if any Step 12 check failed, DO NOT proceed to Step 13
- **Workflow**: Stage all changes, generate comprehensive commit message, create commit
- **Includes**: All changes from Steps 0-11, including submodule reference if Step 11 was executed
- **Note**: Use user-provided commit message if provided, otherwise generate from changes

### Step 14: Push branch

- **Dependency**: Must run AFTER Step 13 (commit created)
- **⚠️ PRECONDITION CHECK (MANDATORY)**: Before executing Step 14, you MUST verify:
  1. **User explicitly requested push**: Verify user invoked `/cortex/commit` or explicitly requested push. If not, STOP and ask for confirmation.
  2. **Commit was created**: Step 13 completed successfully and commit exists
- **⚠️ BLOCK PUSH**: If user did not explicitly request push OR if commit was not created, DO NOT proceed to Step 14
- **Workflow**: Determine current branch, push to remote, verify success. Push the current branch (including `main`) without asking for extra confirmation.
- **Error handling**: Handle push errors (remote tracking, authentication issues)

### Step 15: Execute end-of-session Analyze (MANDATORY)

- **Dependency**: Must run AFTER Step 14 (push completed).
- **MANDATORY**: At the end of the commit workflow, you MUST execute the **Analyze (End of Session)** prompt (`analyze.md` from the Synapse prompts directory). Read and execute that prompt in full: it runs context effectiveness analysis and session optimization, saves a report to the reviews directory, and optionally creates an improvements plan. Do not skip this step.
- **Path**: Resolve the Analyze prompt path via project structure or `get_structure_info()` (e.g. Synapse prompts directory); the prompt file is `analyze.md`.

## Command Execution Order

The commit procedure executes steps in this specific order to ensure dependencies are met:

0. **Fix Errors** (Fix Errors) - Fixes all compiler errors, type errors, formatting issues, and warnings BEFORE testing
   - **CRITICAL**: Must complete successfully before any other step
   - **VALIDATION**: Verify zero errors remain after fix-errors completes (type checker, linter checks)
   - **BLOCK COMMIT** if any errors remain
1. **Formatting** - Ensures code style consistency with project formatter
   - **CRITICAL**: Must verify with formatter check after formatting to ensure CI will pass
   - **VALIDATION**: Formatter check MUST pass - **BLOCK COMMIT** if it fails
1.5. **Markdown Linting** - Fixes markdown lint errors in modified markdown files
   - **CRITICAL**: Must run markdown lint fix tool to ensure all markdown files are properly formatted
   - **VALIDATION**: Markdown lint errors MUST be fixed - **BLOCK COMMIT** if critical errors remain
2. **Type Checking** - Validates type safety with type checker (if applicable)
   - **CRITICAL**: Must pass with zero type errors AND zero warnings before proceeding (skip if project doesn't use types)
   - **VALIDATION**: Type checker MUST report zero errors AND zero warnings - **BLOCK COMMIT** if type errors OR warnings exist
3. **Code Quality Checks** - Validates file size and function/method length limits (matches CI quality gate)
   - **CRITICAL**: Must pass before testing to ensure code meets quality standards
   - **VALIDATION**: Both checks MUST show zero violations - **BLOCK COMMIT** if violations exist
4. **Testing** (Run Tests) - Executes test suite to ensure functionality correctness
   - **CRITICAL**: Uses `execute_pre_commit_checks()` MCP tool for structured test execution
   - **CRITICAL**: Runs AFTER errors, formatting, and code quality are fixed
   - **CRITICAL**: Tests must pass with 100% pass rate AND coverage ≥ 90.0% before proceeding
   - **VALIDATION**: Must verify `results.tests.success` = true AND zero test failures, 100% pass rate, 90%+ coverage (MANDATORY), all integration tests pass
   - **CRITICAL COVERAGE ENFORCEMENT**:
     - Coverage threshold of 90% is MANDATORY and absolute
     - Coverage MUST be parsed from tool response (`results.tests.coverage`) and verified ≥ 0.90 (as float)
     - `results.tests.success` = false OR `results.tests.coverage` < 0.90 MUST block commit
     - The tool now validates coverage internally, but you MUST also verify `results.tests.success` = true AND `results.tests.coverage` ≥ 0.90
     - If coverage < 90.0%, commit procedure MUST STOP and coverage MUST be fixed
     - NO exceptions, NO "close enough", NO proceeding with coverage below threshold
   - **BLOCK COMMIT** if `results.tests.success` = false OR `results.tests.coverage` < 0.90 OR any test validation fails
5. **Documentation** (Memory Bank) - Updates project context
6. **Roadmap Updates** (Roadmap Update) - Ensures roadmap reflects current progress
7. **Plan Archiving** (Archive Completed Plans) - Cleans up completed build plans
8. **Archive Validation** (Validate Archive Locations) - Ensures archived files are in correct locations
9. **Optimization** (Memory Bank Validation) - Validates and optimizes memory bank
10. **Roadmap/activeContext state** - Ensures roadmap and activeContext reflect actual state (future work in roadmap, completed work in activeContext)
11. **Submodule Handling** - Commits and pushes Synapse submodule changes if any (resolve Synapse directory path via project structure or `get_structure_info()` if available)
12. **⚠️ FINAL VALIDATION GATE** - **MANDATORY re-verification before commit** (see details below)
13. **Commit** - Creates the commit with all changes (including updated submodule reference)
14. **Push** - Pushes committed changes to remote repository
15. **Analyze** - **MANDATORY**: Execute the Analyze (End of Session) prompt (`analyze.md`) to run context effectiveness and session optimization analysis.

**MCP Tools**: Steps 0 (Fix Errors), 1 (Formatting), 2 (Type Checking), 3 (Code Quality), and 4 (Testing) use the `execute_pre_commit_checks()` MCP tool. Step 12 (Final Validation Gate) also uses only Cortex MCP tools (format, format_ci_parity, type_check, quality, test_naming, tests, and fix_markdown_lint). This provides structured parameters, type safety, and consistent error handling. Do NOT run scripts directly; use tools only.

## ⚠️ STEP 12: FINAL VALIDATION GATE (CRITICAL - MANDATORY)

**WHY THIS STEP EXISTS**: During steps 4-11, the agent may:

1. **Create NEW files** (e.g., new test files to fix coverage in Step 4) that were never formatted
2. **Make code changes** (adding constants, fixing tests, etc.) that introduce NEW type errors or linting issues

The original checks in Steps 0-4 are INVALIDATED by any subsequent code changes or new file creation.

**CRITICAL RULE**: ANY code change OR new file creation after Step 1 REQUIRES re-running formatting AND verification before commit.

**CRITICAL RULE (Step 12)**: After ANY code change during Step 12 (e.g. fixing type errors in 12.2, fixing lint in 12.3, or any other edit to `src/` or `tests/`), you MUST re-run Step 12.1 (format → format check → format_ci_parity via `execute_pre_commit_checks`) and verify they pass, then MUST re-run Step 12.3 (quality) and verify `results.quality.success` is true and error count is zero. Do NOT proceed to Step 12.4 or Step 13 until Step 12.3 has been run again and passed. Edits made inside the final gate must be formatted before commit; otherwise CI will fail on the formatting check.

- **Type or lint fixes can introduce new lint**: Fixes applied in Step 12.2 or 12.3 can introduce new lint issues (e.g. Ruff E402 if a non-import line is placed between imports). You MUST re-run Step 12.3 (quality) after any such fix and parse the full tool output; verify zero errors before proceeding. Do not assume an earlier 12.3 run still applies. When adding `_ = module` to satisfy reportUnusedImport, place it after all imports to avoid E402.

**⚠️ STEP 12.1 MUST NOT RUN IN PARALLEL WITH 12.2/12.3**: You MUST run Step 12.1.2 (formatting check), wait for its result, and verify exit code 0 and success message BEFORE starting Step 12.2 or 12.3. If you run 12.1.2 in parallel with 12.2/12.3, the formatting result can be missed and unformatted code may be committed (this has caused CI failures: Black formatting check failed on push).

**⚠️ ZERO ERRORS TOLERANCE**: This project has ZERO errors tolerance. ANY errors found in Step 12 (formatting, types, linting, quality) MUST block commit - NO EXCEPTIONS, even if errors are pre-existing or in files you didn't modify. You MUST explicitly parse error counts from output and verify they are ZERO before proceeding.

**⚠️ AUTHORITATIVE CHECKS**: Step 12 uses the same Cortex MCP tools; the type_check check runs on BOTH `src/` AND `tests/` to match CI.

- **Type checking**: Step 12.2 tool (`execute_pre_commit_checks(checks=["type_check"])`) checks BOTH `src/` AND `tests/`
- **Step 12 results take precedence**: If any Step 12 check finds errors (even if an earlier step passed), commit MUST be blocked
- **NO DISCREPANCY ALLOWED**: If a Step 12 check finds errors, those errors MUST be fixed before commit

## ⚠️ MANDATORY: NO OUTPUT TRUNCATION IN STEP 12

- **PROHIBITED**: NEVER use `| tail`, `| head`, `| grep`, or ANY output piping/truncation in Step 12 commands
- **REQUIRED**: Read and parse the FULL output of every command in Step 12
- **REASON**: Truncated output hides critical errors and makes verification impossible - this has caused CI failures

- **VERIFICATION**: Every check in Step 12 MUST show explicit success indicators in FULL output
- **BLOCK COMMIT**: If output is truncated or unclear, DO NOT proceed to commit - re-run command without truncation

### 12.0 Re-validate markdown files modified during Steps 0-11 (MANDATORY)

**Purpose**: Catch markdown lint errors in files modified during Steps 0-11 (especially Synapse prompts/rules and session review files) before they propagate to submodule or require extra commits.

- **When**: Run immediately at the start of Step 12, before Step 12.1
- **What**: Identify markdown files modified during Steps 0-11 and run markdown lint check on those files
- **How**: Use `fix_markdown_lint(check_all_files=True, include_untracked_markdown=True)` so that all current markdown files (including any session review files in the reviews directory created or updated during this session) are linted. The tool resolves project root via MCP roots when the client supports them. Resolve reviews path via `get_structure_info()` → `structure_info.paths.reviews` if needed.
- **If you wrote session review files**: If you created or updated any markdown files during Steps 0–11 (e.g. session-optimization-*.md in the reviews directory), run `fix_markdown_lint(check_all_files=True, include_untracked_markdown=True)` so those files are included before proceeding to Step 12.1
- **Fix**: Resolve any markdown lint errors before proceeding to Step 12.1
- **BLOCK COMMIT**: If markdown lint errors are found on modified files, fix them before continuing to Step 12.1
- **Rationale**: Reduces extra iterations by catching markdown lint errors immediately after modification, before Step 12.5 full check

### 12.1 Re-run Formatting FIX then CHECK (MANDATORY)

**CRITICAL**: New files created during Steps 4-11 (especially test files added to fix coverage) will NOT have been formatted by Step 1. You MUST run the format tool (`execute_pre_commit_checks(checks=["format"])`) first, then verify.

**CRITICAL (re-run after fixes in Step 12)**: If you fix type errors (12.2), lint (12.3), or make any other code edit to `src/` or `tests/` during Step 12, you MUST re-run 12.1.1 (format via tool), then 12.1.2 (format check), then 12.1.3 (format_ci_parity), then MUST re-run Step 12.3 (quality) and verify `results.quality.success` is true with zero errors. Do NOT proceed to Step 12.4 or Step 13 until Step 12.3 has been executed again and passed.

**⚠️ SEQUENTIAL EXECUTION REQUIRED (MANDATORY)**:

- **Do not interleave other state-changing operations** between final formatting fix and check.
- **Do NOT run Step 12.1.2 in parallel with Step 12.2 or 12.3** - you MUST run Step 12.1.2, wait for its result, parse the FULL tool output and verify success (e.g. `results.format.status` = "passed" or `results.format.errors` empty) BEFORE starting Step 12.2. Running 12.1.2 in parallel can cause the formatting result to be ignored and allow unformatted code to be committed (this has caused CI failures).

- **Recommended pattern**: Run format (fix), wait for completion, then run format (check) immediately after, then verify result before proceeding.

**Step 12.1.1 - Run formatting FIX** (always run this, not just on failure):

Use the Cortex MCP tool:

```text
execute_pre_commit_checks(checks=["format"])
```

**⚠️ CRITICAL**: Do NOT run format check in parallel - wait for fix to complete first

**Step 12.1.2 - Run formatting CHECK** to verify (MUST run AFTER Step 12.1.1 completes):

Use the same tool again (idempotent; verify no files were formatted and success):

```text
execute_pre_commit_checks(checks=["format"])
```

**⚠️ CRITICAL**: Do NOT truncate output - read FULL tool response to verify check passed

- **MUST verify**: Tool returns `status` = "success" and `results.format` indicates passed (e.g. `results.format.errors` empty or success message)
- **MUST verify**: If any formatting violations remain, BLOCK COMMIT and re-run format fix (12.1.1) then check again
- **BLOCK COMMIT** if ANY formatting violations are reported OR if tool returns status "error" for format
- **BLOCK COMMIT** if you did not wait for and parse Step 12.1.2 result before proceeding to Step 12.2
- **Scope**: The tool runs the same scope as CI (`src/`, `tests/` where applicable).

**Step 12.1.3 - CI parity (RECOMMENDED)** - Match CI formatting step exactly:

After Step 12.1.2 passes, run the format_ci_parity check via the Cortex MCP tool so the same formatter and paths as CI are used:

```text
execute_pre_commit_checks(checks=["format_ci_parity"])
```

- **Purpose**: CI runs a language-specific formatter on the main source and test trees. This check runs the same validation locally (e.g. for Python: formatter check on `src/` and `tests/`).
- **BLOCK COMMIT** if this check returns non-success - fix formatting and re-run from Step 12.1.1
- **Note**: The tool resolves language automatically; no script paths in the prompt.

### 12.2 Re-run Type Check (MANDATORY for typed projects)

**⚠️ EXECUTION MANDATORY**: This step CANNOT be skipped for Python projects. You MUST execute this check via the Cortex MCP tool and show its result before proceeding to Step 13.

Use the Cortex MCP tool (checks `src/` and `tests/` to match CI):

```text
execute_pre_commit_checks(checks=["type_check"])
```

**⚠️ CRITICAL**: Do NOT truncate output - read FULL tool response to verify check passed

- **MUST execute**: This tool call MUST be executed - do not skip or assume it passed
- **MUST show result**: The tool response (or key fields: status, results.type_check) MUST be used to verify execution
- **MUST verify**: Tool returns `status` = "success" and `results.type_check` indicates passed (e.g. 0 errors)
- **MUST verify**: `results.type_check.errors` is empty (or equivalent success)
- **⚠️ ABSOLUTE BLOCK**: If ANY type errors or warnings are reported (even if Step 2 passed earlier), STOP IMMEDIATELY - DO NOT proceed to commit
- **⚠️ NO EXCEPTIONS**: Step 12.2 result is AUTHORITATIVE - type errors MUST block commit
- **⚠️ ZERO ERRORS TOLERANCE**: The project has ZERO errors tolerance - ANY errors (new or pre-existing, in src/ or tests/) MUST block commit
- **BLOCK COMMIT** if ANY type errors or warnings are reported OR if tool returns status "error" for type_check
- **BLOCK COMMIT** if this check was not executed - Step 12.2 execution is mandatory
- **DO NOT rely on memory of earlier checks** - you MUST re-run and verify result NOW
- **DO NOT dismiss errors as "pre-existing"** - ALL errors must be fixed before commit
- **Skip if**: Project does not use a type system (Python projects use type hints, so this step is NOT skipped for Python)
- **If you fixed type errors in this step**: Re-run Step 12.1 (format → format check → format_ci_parity via tools) and verify all pass, then MUST re-run Step 12.3 (quality) and verify `results.quality.success` is true and error count is zero. Do NOT proceed to Step 12.4 or Step 13 until Step 12.3 has been run again and passed (see "CRITICAL RULE (Step 12)" above).

### 12.3 Re-run Linter, Spelling, and Type Check (MANDATORY)

Use the Cortex MCP tool (quality gate runs quality + spelling + type_check; same scope as CI):

```text
execute_pre_commit_checks(checks=["quality"])
```

**⚠️ CRITICAL**: Do NOT truncate output - read FULL tool response to verify check passed

- **MUST verify**: Tool returns `status` = "success"
- **MUST verify**: Parse `results.quality` - errors list must be empty (error count = 0); quality check indicates passed (no lint errors)
- **MUST verify**: Parse `results.spelling` (if present) - success = true and errors list empty (quality gate includes spelling to match CI)
- **MUST verify**: Parse `results.type_check` - success = true and errors list empty (quality gate includes type_check; catches reportRedeclaration etc.)
- **⚠️ ABSOLUTE BLOCK**: If ANY linter, spelling, or type violations are reported (even 1 error), stop immediately - DO NOT proceed to commit
- **⚠️ NO EXCEPTIONS**: Pre-existing linting or type errors are NOT acceptable - they MUST be fixed before commit
- **⚠️ ZERO ERRORS TOLERANCE**: The project has ZERO errors tolerance - ANY errors (new or pre-existing) MUST block commit
- **BLOCK COMMIT** if ANY linter or type violations are reported OR if tool returns status "error" for quality or type_check
- **If you fixed lint in this step**: Re-run Step 12.1 (format → format check → format_ci_parity via tools) and verify all pass, then MUST re-run Step 12.3 (quality) again and verify `results.quality.success` is true with zero errors before proceeding to Step 12.4 (see "CRITICAL RULE (Step 12)" above).
- **BLOCK COMMIT** if quality or type_check reports any errors
- **DO NOT rely on memory of earlier checks** - you MUST re-run and verify result NOW
- **DO NOT dismiss errors as "pre-existing"** - ALL errors must be fixed before commit

### 12.4 Re-run Test Naming Check (MANDATORY)

Use the Cortex MCP tool (runs language-specific test naming check):

```text
execute_pre_commit_checks(checks=["test_naming"])
```

**⚠️ CRITICAL**: Do NOT truncate output - read FULL tool response to verify check passed

- **MUST verify**: Tool returns `status` = "success" and `results.test_naming` indicates passed
- **MUST verify**: No test naming violations reported (all test functions follow `test_<name>` pattern)
- **BLOCK COMMIT** if ANY test naming violations are reported OR if tool returns status "error" for test_naming
- **DO NOT rely on memory of earlier checks** - you MUST re-run and verify result NOW
- **Fix violations**: Test functions must follow pattern `test_<name>` (with underscore after "test")
  - Invalid: `testread`, `testgenerate`, `testcreate`, `testsetup` (missing underscore)
  - Valid: `test_read`, `test_generate`, `test_create`, `test_setup` (with underscore)

### 12.5 Re-run Markdown Lint Check (MANDATORY)

**CRITICAL**: Markdown files may have been modified during Steps 5-11. Markdown lint MUST be re-checked.

**⚠️ AUTHORITATIVE**: Step 12.5 checks ALL markdown files (like CI does) - this is the final markdown validation before commit.

**⚠️ ORDERING RATIONALE**: Markdown lint runs BEFORE tests to avoid MCP connection staleness. The test suite can take several minutes, and running markdown lint after tests has historically caused "Connection closed" errors due to the MCP connection timing out during the long test run.

**Step 12.5.1 - Re-run markdown lint check on ALL files** (MANDATORY):

Use the MCP tool to check ALL markdown files (matching CI behavior). Project root is resolved by the server (MCP roots when available):

```python
fix_markdown_lint(check_all_files=True, include_untracked_markdown=True)
```

**⚠️ CRITICAL**: Do NOT truncate output - read FULL output to verify check passed

- **MUST verify**: Zero errors in ALL markdown files (not just memory bank/plans)
- **MUST verify**: Exit code is 0 (zero) - command must succeed
- **MUST verify**: Output shows "✅" or "passed" or equivalent success message
- **⚠️ ABSOLUTE BLOCK**: If ANY markdown lint errors are reported (even 1 error in any file), stop immediately - DO NOT proceed to commit
- **⚠️ NO EXCEPTIONS**: Pre-existing markdown lint errors are NOT acceptable - they MUST be fixed before commit
- **⚠️ ZERO ERRORS TOLERANCE**: The project has ZERO errors tolerance - ANY markdown lint error (in ANY file) MUST block commit
- **BLOCK COMMIT** if ANY markdown lint errors are reported OR if exit code is non-zero
- **BLOCK COMMIT** if output is truncated or unclear - re-run without truncation
- **DO NOT rely on memory of earlier checks** - you MUST re-run and verify output NOW
- **DO NOT dismiss errors as "pre-existing"** - ALL errors must be fixed before commit
- **Match CI behavior**: CI checks ALL markdown files and fails on ANY error - Step 12.5 MUST match this exactly
- **Example fallback command** (when MCP tool unavailable): Run markdown lint via shell with the same scope. Example (match CI scope): `npx markdownlint-cli2 '**/*.md' '**/*.mdc' !**/node_modules/** !**/.venv/** !**/venv/** !**/__pycache__/** !**/.git/**` with `--fix` to fix, or without `--fix` for check-only. Record "MCP connection closed; fallback used" in the commit output.

### 12.6 Re-run Quality Checks (MANDATORY)

**CRITICAL**: Quality violations (file sizes, function lengths) can be introduced during Steps 4-11 and MUST be validated before commit.

**Step 12.6.1 - Check file sizes** (MANDATORY):

Use the Cortex MCP tool (quality gate runs quality + type_check; quality includes file sizes):

```text
execute_pre_commit_checks(checks=["quality"])
```

- **MUST verify**: Tool returns `status` = "success"; `results.quality.file_size_violations` empty; `results.type_check.success` true and `results.type_check.errors` empty
- **MUST verify**: No file size violations (all files within 400 lines); no type errors
- **BLOCK COMMIT** if ANY file size or type violations are reported
- **NO EXCEPTIONS**: Pre-existing violations are NOT acceptable

**Step 12.6.2 - Check function lengths** (MANDATORY):

Same tool as 12.6.1 (quality gate includes quality + type_check):

```text
execute_pre_commit_checks(checks=["quality"])
```

- **MUST verify**: Tool returns `status` = "success" and `results.quality.function_length_violations` is empty
- **MUST verify**: No function length violations (all functions within 30 lines)
- **BLOCK COMMIT** if ANY function length violations are reported
- **NO EXCEPTIONS**: Pre-existing violations are NOT acceptable

### 12.7 Re-run Tests with Coverage Validation (MANDATORY)

**CRITICAL**: Code changes during Steps 5-11 may affect test coverage. Tests MUST be re-run and coverage MUST be validated.

**⚠️ ORDERING RATIONALE**: Tests run AFTER markdown lint (12.5) and quality checks (12.6) because the test suite takes several minutes and can cause MCP connection staleness for subsequent tool calls. Running tests last in the validation sequence ensures all other checks complete reliably.

**Step 12.7.1 - Re-run tests with coverage** (MANDATORY):

Use the MCP tool:

```python
execute_pre_commit_checks(checks=["tests"], test_timeout=600, coverage_threshold=0.90, strict_mode=False)
```

- **MUST verify**: `results.tests.success` = true (PRIMARY indicator)
- **MUST verify**: `results.tests.tests_failed` = 0 (zero failures)
- **MUST verify**: `results.tests.pass_rate` = 100.0 (100% pass rate)
- **MUST verify**: `results.tests.coverage` ≥ 0.90 (coverage ≥ 90%, parsed as float)
- **BLOCK COMMIT** if `results.tests.success` = false OR `results.tests.coverage` < 0.90 OR any test fails
- **CRITICAL**: Coverage validation is MANDATORY - NO EXCEPTIONS

### 12.9 Verification Requirements (CRITICAL)

## ⚠️ MANDATORY: NO OUTPUT TRUNCATION IN STEP 12 (Verification)

- **PROHIBITED**: NEVER use `| tail`, `| head`, or any output piping/truncation in Step 12 commands
- **REQUIRED**: Read and parse the FULL output of every command in Step 12
- **REASON**: Truncated output hides critical errors and makes verification impossible
- **Parse actual command output** - do not assume success
- **Look for success indicators**: "✅" or "passed" in output
- **If output is unclear or missing success indicators**: Re-run command without any piping/truncation
- **If any check fails**: Fix issues and restart from Step 12.1
- **BLOCK COMMIT**: If ANY check in Step 12 fails OR if output cannot be fully verified, DO NOT proceed to commit

### 12.10 Checklist Before Proceeding to Commit

**⚠️ MANDATORY**: This checklist MUST be completed and verified BEFORE proceeding to Step 13. Each item MUST be checked with explicit evidence (command outputs, exit codes, parsed error counts).

- [ ] **Step 12.0 executed**: Markdown re-validation on modified files executed, full output shown
- [ ] **Step 12.1 executed**: Formatting fix AND check via `execute_pre_commit_checks(checks=["format"])` executed, full result shown; Step 12.1.2 run and result verified BEFORE starting Step 12.2 (not in parallel)
- [ ] Formatting re-run: **check passed** confirmed in tool result (status success, results.format indicates passed)
- [ ] Formatting re-run: **NO output truncation** - full output read and verified
- [ ] **Step 12.1.3 (recommended)**: CI parity check via `execute_pre_commit_checks(checks=["format_ci_parity"])` executed and status success
- [ ] **Step 12.2 executed**: Type check via `execute_pre_commit_checks(checks=["type_check"])` executed, full result shown
- [ ] Type check re-run: **Tool executed**: `execute_pre_commit_checks(checks=["type_check"])` was run (MANDATORY for Python/typed projects)
- [ ] Type check re-run: **Output shown**: Full command output displayed in response (not just "passed")
- [ ] Type check re-run: **0 errors, 0 warnings** confirmed in FULL output (if applicable)
- [ ] Type check re-run: **NO output truncation** - full output read and verified
- [ ] Type check re-run: **Step 12.2 result is AUTHORITATIVE** - if tool found errors (even if Step 2 passed earlier), commit MUST be blocked
- [ ] **Step 12.3 executed**: Linter/quality check tool executed, full result shown
- [ ] Linter re-run: **0 violations** confirmed in FULL output (error count explicitly parsed and verified = 0)
- [ ] Linter re-run: **NO output truncation** - full output read and verified
- [ ] Linter re-run: **ZERO ERRORS TOLERANCE** - verified that error count = 0 (NO exceptions, even for pre-existing errors)
- [ ] **Step 12.4 executed**: Test naming check tool executed, full result shown
- [ ] **Step 12.5 executed**: Markdown lint tool executed, full result shown
- [ ] Markdown lint re-run: **0 errors in ALL markdown files** confirmed (matching CI behavior)
- [ ] Markdown lint re-run: **check_all_files=True** used to match CI comprehensive check
- [ ] **Step 12.6 executed**: File sizes AND function lengths via quality tool executed, full results shown
- [ ] File sizes re-run: **0 violations** confirmed in FULL output
- [ ] File sizes re-run: **NO output truncation** - full output read and verified
- [ ] Function lengths re-run: **0 violations** confirmed in FULL output
- [ ] Function lengths re-run: **NO output truncation** - full output read and verified
- [ ] **Step 12.7 executed (Tests)**: `results.tests.success` = true AND `results.tests.coverage` ≥ 0.90 confirmed (MANDATORY)
- [ ] **Coverage validation**: `results.tests.coverage` ≥ 0.90 (parsed as float, MANDATORY)
- [ ] All output was **fully read and parsed**, not assumed
- [ ] All commands in Step 12 executed **WITHOUT** `| tail`, `| head`, or any output truncation
- [ ] **Step 12 execution verified**: Explicit evidence provided that ALL Step 12 sub-steps were executed

**⚠️ CRITICAL**: Before proceeding to Step 13, you MUST provide explicit evidence that Step 12.2 was executed. This means:

1. Show the tool call that was run: `execute_pre_commit_checks(checks=["type_check"])`
2. Show the tool response (or key fields: status, results.type_check) (not truncated)
3. Verify the response shows type check passed (e.g. status "success", results.type_check.errors empty)
4. Verify tool returned status "success" for type_check

**⚠️ VIOLATION**: Proceeding to commit creation without completing Step 12 with verified zero-error output is a CRITICAL VIOLATION that will cause CI failures.

**⚠️ VIOLATION**: Using output truncation (`| tail`, `| head`, etc.) in Step 12 is a CRITICAL VIOLATION that prevents proper verification and will cause CI failures.

**⚠️ VIOLATION**: Skipping Step 12.2 (type check re-run) or proceeding to Step 13 without executing Step 12.2 is a CRITICAL VIOLATION that will cause CI failures. The tool runs type check on `src/` and `tests/` to match CI - if Step 12.2 is skipped, type errors may not be caught until CI fails.

**⚠️ VIOLATION**: Proceeding to Step 13 without providing explicit evidence (command outputs) that Step 12 was executed is a CRITICAL VIOLATION. You MUST show actual command executions and their outputs, not just state that Step 12 passed.

## ⚠️ MANDATORY CHECKLIST UPDATES

**CRITICAL**: The AI MUST update the todo checklist in real-time as each step completes:

- Mark each step as `completed` immediately after it finishes successfully
- Mark steps as `in_progress` when starting them
- Update status immediately, not at the end
- This provides transparency and allows tracking progress during execution

## Pre-Commit Validation Summary

Before proceeding to commit creation, provide a validation summary confirming all checks passed:

### **Pre-Commit Validation Checklist**

- [ ] **Fix Errors Validation**: Type checker = 0 errors (if applicable), Linter = 0 errors
- [ ] **Linter Check Validation**: Linter check = 0 errors (parsed from MCP tool response: `results.fix_errors.errors`, CRITICAL - catches non-fixable errors)
- [ ] **Formatting Validation**: Formatter check = 0 violations (parsed from MCP tool response)
- [ ] **Type Checking Validation**: Type checker = 0 type errors AND 0 warnings (parsed from MCP tool response, skip if not applicable)
  - **⚠️ CRITICAL**: Step 12.2 tool checks BOTH `src/` AND `tests/` - if tool finds errors (even if Step 2 passed earlier), commit MUST be blocked
- [ ] **Code Quality Validation**: File size = 0 violations, Function length = 0 violations (parsed from MCP tool response)
- [ ] **Test Execution Validation**:
  - Test failures = 0 (parsed from test output)
  - Pass rate = 100% (calculated from test output)
  - Coverage ≥ 90% (parsed from test output)
  - Integration tests = all pass (explicitly verified)
- [ ] **⚠️ FINAL VALIDATION GATE (Step 12) - MANDATORY**:
  - Markdown re-validation (Step 12.0) executed: Yes (MUST run on modified files before Step 12.1)
  - Formatting FIX executed: Yes (MUST run to format any new files created since Step 1)
  - Formatting CHECK: `would be left unchanged` (output verified)
  - Type check RE-RUN: `0 errors, 0 warnings, 0 informations` (output verified)
  - Linter RE-RUN: `0 violations` (output verified)
  - File sizes RE-RUN: `0 violations` (output verified)
  - Function lengths RE-RUN: `0 violations` (output verified)
  - This step MUST be executed IMMEDIATELY before commit, not relied on from earlier steps
  - **CRITICAL**: New test files created during Step 4 (coverage fix) MUST be formatted
  - **CRITICAL**: Quality checks (file sizes, function lengths) MUST be re-verified before commit
- [ ] **All Validations Passed**: All above validations confirmed successful

**If any validation fails, BLOCK COMMIT and fix issues before proceeding.**

**⚠️ CRITICAL**: Step 12 (Final Validation Gate) exists because code changes during steps 5-11 can introduce NEW errors. DO NOT skip this step or rely on earlier checks.

## Output Format

Provide a structured commit procedure report:

### **Commit Procedure Summary**

- **Status**: Success/Failure status of the commit procedure
- **Steps Completed**: Count and list of steps that completed successfully
- **Steps Failed**: Count and list of steps that failed (should be 0)
- **Total Duration**: Time taken for the entire commit procedure

### **Step-by-Step Results**

Use this ordering when numbering results:

- Step 0: Fix Errors
- Step 1: Formatting
- Step 1.5: Markdown Linting
- Step 2: Type Checking
- Step 3: Code Quality Checks
- Step 4: Test Execution
- Step 5: Memory Bank Update
- Step 6: Roadmap Update
- Step 7: Plan Archiving
- Step 8: Archive Validation
- Step 9: Memory Bank Timestamp Validation
- Step 10: Ensure roadmap and activeContext reflect actual state
- Step 11: Submodule Handling
- Step 12: ⚠️ Final Validation Gate (MANDATORY)
- Step 13: Commit Creation
- Step 14: Push Branch

#### **0. Fix Errors**

- **Status**: Success/Failure
- **Command Used**: `execute_pre_commit_checks(checks=["fix_errors"])` MCP tool
- **Errors Fixed**: Count and list of errors fixed (from tool response: `results.fix_errors.errors`)
- **Warnings Fixed**: Count and list of warnings fixed (from tool response: `results.fix_errors.warnings`)
- **Formatting Issues Fixed**: Count and list of formatting issues fixed (from tool response)
- **Type Errors Fixed**: Count and list of type errors fixed (from tool response)
- **Files Modified**: List of files modified during error fixing (from tool response: `stats.files_modified`)
- **Tool Response Parsed**: Yes/No (MUST be Yes)
- **Details**: Summary from fix-errors tool response
- **Validation Results**:
  - Tool executed: Yes/No (MUST be Yes)
  - Fix errors status: Pass/Fail (from tool response: `results.fix_errors.status`, MUST be "passed")
  - Zero errors confirmed: Yes/No (parsed from tool response: `results.fix_errors.errors`, MUST be empty list)
  - Zero warnings confirmed: Yes/No (parsed from tool response: `results.fix_errors.warnings`, MUST be empty list or acceptable)
  - Total errors = 0: Yes/No (from tool response: `stats.total_errors`, MUST be 0)
- **Commit Blocked**: Yes/No (blocked if any errors OR warnings remain)
- **Fallback Used**: Yes/No (only if MCP tool was unavailable)

#### **1. Formatting**

- **Status**: Success/Failure
- **Command Used**: `execute_pre_commit_checks(checks=["format"])` MCP tool
- **Files Formatted**: Count of files formatted (from tool response: `results.format.files_formatted`)
- **Formatter Check Status**: Pass/Fail (from tool response: `results.format.status`, MUST be "passed")
- **Tool Response Parsed**: Yes/No (MUST be Yes)
- **Errors**: Any formatting errors encountered (from tool response)
- **Warnings**: Any formatting warnings (from tool response)
- **Validation Results**:
  - Tool executed: Yes/No (MUST be Yes)
  - Formatting status confirmed: Yes/No (parsed from tool response, MUST be "passed")
  - Zero violations confirmed: Yes/No (parsed from tool response)
- **Verification**: Confirmation that formatter check passed before proceeding
- **Fallback Used**: Yes/No (only if MCP tool was unavailable)

#### **1.5. Markdown Linting**

- **Status**: Success/Failure/Skipped
- **MCP Tool Used**: `fix_markdown_lint(check_all_files=True, include_untracked_markdown=True)` (MUST check ALL files to match CI)
- **Tool Available**: Whether markdownlint-cli2 is installed
- **Files Processed**: Count of markdown files processed (should match CI - all .md and .mdc files)
- **Files Fixed**: Count of markdown files with errors fixed
- **Files Unchanged**: Count of markdown files with no errors
- **Files With Errors**: Count of files with non-auto-fixable errors (MUST be 0)
- **Check-Only Validation**: Whether markdownlint check-only mode was run
- **Total Errors Found**: Count of ALL errors found in ALL markdown files (MUST be 0)
- **Errors Fixed**: List of markdown lint errors fixed
- **Errors Remaining**: List of non-auto-fixable errors with file paths and error codes (MUST be empty)
- **Validation Results**:
  - Tool executed: Yes/No (MUST be Yes if tool available)
  - check_all_files=True used: Yes/No (MUST be Yes to match CI behavior)
  - Check-only validation run: Yes/No (MUST be Yes if files_with_errors > 0)
  - All auto-fixable errors fixed: Yes/No (MUST be Yes if tool available)
  - Zero errors in ALL files: Yes/No (MUST be Yes - parsed from check-only output, matches CI)
  - Tool response parsed: Yes/No
  - Check-only output parsed: Yes/No (MUST be Yes if files_with_errors > 0)
- **Details**: Summary of markdown lint fixing operations, including all errors found and fixed
- **Commit Blocked**: Yes/No (blocked if ANY markdown lint errors remain in ANY file - ZERO ERRORS TOLERANCE, matches CI behavior)
- **⚠️ ZERO ERRORS TOLERANCE**: ANY markdown lint error (in ANY file) MUST block commit - NO EXCEPTIONS
- **⚠️ NO EXCEPTIONS**: Pre-existing markdown lint errors are NOT acceptable - they MUST be fixed before commit
- **REQUIRED**: markdownlint-cli2 must be installed (required dependency for Cortex MCP)

#### **2. Type Checking**

- **Status**: Success/Failure/Skipped
- **Command Used**: `execute_pre_commit_checks(checks=["type_check"])` MCP tool
- **Type Errors Found**: Count of type errors found (from tool response: `results.type_check.errors`, must be 0)
- **Type Warnings Found**: Count of type warnings found (from tool response: `results.type_check.warnings`, must be 0)
- **Type Check Status**: Pass/Fail (from tool response: `results.type_check.status`, MUST be "passed")
- **Tool Response Parsed**: Yes/No (MUST be Yes)
- **Validation Results**:
  - Tool executed: Yes/No (MUST be Yes if project uses type system)
  - Zero type errors confirmed: Yes/No (parsed from tool response, MUST be 0)
  - Zero type warnings confirmed: Yes/No (parsed from tool response, MUST be 0)
  - Tool output parsed: Yes/No
- **Details**: Summary of any type errors/warnings and their resolution
- **Commit Blocked**: Yes/No (blocked if any type errors OR warnings remain)
- **Skip if**: Project does not use a type system
- **Fallback Used**: Yes/No (only if MCP tool was unavailable)

#### **3. Code Quality Checks**

- **Status**: Success/Failure
- **Command Used**: `execute_pre_commit_checks(checks=["quality"])` MCP tool
- **Quality Success Flag**: `results.quality.success` (MUST be true - PRIMARY indicator)
- **File Size Violations**: Count from `len(results.quality.file_size_violations)` (MUST be 0, array must be empty)
- **Function Length Violations**: Count from `len(results.quality.function_length_violations)` (MUST be 0, array must be empty)
- **Tool Response Parsed**: Yes/No (MUST be Yes)
- **Violations Found**: Count of violations found (must be 0 to proceed)
- **Violations Fixed**: Count of violations fixed
- **Validation Results**:
  - Tool executed: Yes/No (MUST be Yes)
  - Quality success flag: Yes/No (MUST be Yes - from `results.quality.success`)
  - File size violations array empty: Yes/No (MUST be Yes, parsed from tool response)
  - Function length violations array empty: Yes/No (MUST be Yes, parsed from tool response)
  - Tool output parsed: Yes/No
- **Details**: Summary of any violations and their resolution
- **⚠️ ABSOLUTE BLOCK**: If success=false OR any violations exist:
  - Pre-existing violations are NOT acceptable
  - Cannot dismiss as "pre-existing issues"
  - CI will fail, so commit is blocked
- **Commit Blocked**: Yes/No (blocked if success=false OR any violations remain - NO EXCEPTIONS)
- **Fallback Used**: Yes/No (only if MCP tool was unavailable)

#### **4. Test Execution**

- **Status**: Success/Failure
- **Command Used**: `execute_pre_commit_checks(checks=["tests"], test_timeout=600, coverage_threshold=0.90, strict_mode=False)` MCP tool
- **Tests Executed**: Count of tests executed (from tool response: `results.tests.tests_run`)
- **Tests Passed**: Count of passing tests (from tool response: `results.tests.tests_passed`)
- **Tests Failed**: Count of failing tests (from tool response: `results.tests.tests_failed`, must be 0)
- **Pass Rate**: Percentage pass rate (from tool response: `results.tests.pass_rate`, target: 100%)
- **Coverage**: Test coverage percentage (from tool response: `results.tests.coverage`, target: 90%+)
- **Coverage Value**: Exact coverage percentage extracted from tool response (e.g., 90.32%)
- **Coverage Threshold**: 90.0% (absolute minimum, no exceptions)
- **Tool Response Parsed**: Yes/No (MUST be Yes)
- **Validation Results**:
  - Tool executed: Yes/No (MUST be Yes)
  - Tests success flag: Yes/No (from tool response: `results.tests.success`, MUST be true - PRIMARY indicator)
  - Tests status: Pass/Fail (from tool response: `results.tests.status`, MUST be "passed" if success=true)
  - Zero failures confirmed: Yes/No (parsed from tool response: `results.tests.tests_failed`, MUST be 0)
  - 100% pass rate confirmed: Yes/No (parsed from tool response: `results.tests.pass_rate`, MUST be 100.0)
  - Coverage value extracted: Yes/No (exact percentage must be shown from tool response: `results.tests.coverage`)
  - Coverage threshold met: Yes/No (MANDATORY: `results.tests.coverage` MUST be ≥ 0.90, parsed as float)
  - Coverage validation: Yes/No (MANDATORY: Verify `results.tests.success` = true AND `results.tests.coverage` ≥ 0.90)
  - Integration tests passed: Yes/No (explicitly verified from tool response)
  - Tool output parsed: Yes/No
- **Details**: Complete summary from test execution tool response
- **Commit Blocked**: Yes/No (blocked if `results.tests.success` = false OR `results.tests.coverage` < 0.90 OR any validation fails)
- **CRITICAL**: `results.tests.success` = false OR `results.tests.coverage` < 0.90 MUST block commit - NO EXCEPTIONS
- **CRITICAL**: Coverage validation is MANDATORY - the tool now validates coverage internally, but you MUST also verify
- **Fallback Used**: Yes/No (only if MCP tool was unavailable)

#### **5. Memory Bank Update**

- **Status**: Success/Failure/Skipped
- **MCP Tool Used**: `manage_file()` MCP tool for memory bank operations
- **Files Updated**: List of memory bank files updated (activeContext.md, progress.md, roadmap.md)
- **Entries Added**: Count of new entries added (if any)
- **Details**: Summary of memory bank updates made

#### **6. Roadmap Update**

- **Status**: Success/Failure
- **Items Marked Complete**: Count of completed milestones/tasks marked in roadmap.md
- **New Items Added**: Count of new roadmap items added
- **Status Updates**: Summary of progress indicator updates
- **Details**: Summary of roadmap changes made

#### **7. Plan Archiving**

- **Status**: Success/Failure
- **Plans Found**: Count of completed plans detected (must show detection was performed)
- **Plans Archived**: Count of plans moved to archive directory (must match Plans Found if > 0)
- **Plans Processed**: Count of plan files checked
- **Archive Directories Created**: List of PhaseX directories created
- **Links Updated**: Count of links updated in memory bank files
- **Link Validation Status**: Pass/Fail after archiving
- **Validation Results**:
  - Detection performed: Yes/No (MUST be Yes - show command/output)
  - All completed plans archived: Yes/No (MUST be Yes if Plans Found > 0)
  - Links updated: Yes/No (MUST be Yes if Plans Archived > 0)
  - Link validation passed: Yes/No (MUST be Yes if Plans Archived > 0)
  - Archive locations verified: Yes/No (MUST be Yes if Plans Archived > 0)
- **Archive Directory**: Location where plans were archived
- **Details**: Summary of plan archiving operations including detection method and results
- **Commit Blocked**: Yes/No (blocked if completed plans found but not archived, or if link validation fails)

#### **8. Archive Location Validation**

- **Status**: Success/Failure
- **Completed Plans Re-check**: Count of completed plans found in the plans directory (path from `get_structure_info()` → `structure_info.paths.plans`) (must be 0)
- **Unarchived Plans**: List of any completed plans still in the plans directory (must be empty)
- **Plan Archive Checked**: Count of files in the plans archive subdirectory (e.g. `structure_info.paths.plans_archived` if available)
- **Archive Structure Valid**: Whether all archived plans are in PhaseX subdirectories
- **Violations Found**: Count of violations (unarchived completed plans + wrong locations, must be 0)
- **Violations List**: List of any plan files in wrong locations or unarchived completed plans
- **Validation Results**:
  - Completed plans re-check performed: Yes/No (MUST be Yes - show command/output)
  - Zero unarchived completed plans: Yes/No (MUST be Yes)
  - All archived plans in correct locations: Yes/No (MUST be Yes)
  - Archive structure valid: Yes/No (MUST be Yes)
- **Details**: Summary of archive location validation results
- **Commit Blocked**: Yes/No (blocked if any completed plans remain unarchived or if archive structure is invalid)

#### **9. Memory Bank Timestamp Validation**

- **Status**: Success/Failure
- **Command Used**: `validate(check_type="timestamps")` MCP tool
- **Total Valid Timestamps**: Count of valid YYYY-MM-DD timestamps found
- **Total Invalid Format**: Count of invalid date format violations (must be 0)
- **Total Invalid With Time**: Count of timestamps with time components (must be 0)
- **Files Valid**: Whether all files passed validation
- **Validation Results**:
  - Zero invalid format violations confirmed: Yes/No (parsed from tool output)
  - Zero invalid with time violations confirmed: Yes/No (parsed from tool output)
  - All files valid confirmed: Yes/No (parsed from tool output)
  - Tool output parsed: Yes/No
- **Details**: Summary of timestamp validation results, including any violations found
- **Commit Blocked**: Yes/No (blocked if any violations found)

#### **10. Roadmap and activeContext state**

- **Status**: Success/Done
- **Roadmap read**: Whether roadmap.md was read via manage_file
- **activeContext read**: Whether activeContext.md was read via manage_file
- **Completed-in-roadmap fixed**: Whether any completed-work bullets were moved from roadmap to activeContext and removed from roadmap
- **Details**: Brief summary (e.g. "State consistent" or "Moved N completed items from roadmap to activeContext")

#### **11. Submodule Handling**

- **Status**: Success/Failure/Skipped
- **Submodule Changes Detected**: Whether the Synapse submodule had changes
- **Submodule Committed**: Whether submodule changes were committed
- **Submodule Pushed**: Whether submodule changes were pushed to remote
- **Submodule Commit Hash**: Git commit hash of submodule commit (if committed)
- **Parent Reference Updated**: Whether parent repository's submodule reference was updated
- **Details**: Summary of submodule operations performed

#### **12. ⚠️ Final Validation Gate (MANDATORY)**

- **Status**: Success/Failure (MUST be Success to proceed)
- **⚠️ EXECUTION VERIFICATION REQUIRED**: You MUST provide explicit evidence that Step 12 was executed. This means showing actual MCP tool calls and their results (or key result fields), not just stating that Step 12 passed.
- **⚠️ AUTHORITATIVE**: Step 12 tool checks use the same scope as CI (e.g. `src/` + `tests/` for type check, format, quality).
- **⚠️ PRECEDENCE**: Step 12 tool results are AUTHORITATIVE - if a check finds errors, commit MUST be blocked.
- **Formatting Fix Run**: Result of `execute_pre_commit_checks(checks=["format"])` (MUST run to format any new files; show status and results.format).
- **Formatting Check Re-run**: Result of `execute_pre_commit_checks(checks=["format"])` (MUST show check passed; verify results.format indicates success).
- **Type Check Re-run**: Result of `execute_pre_commit_checks(checks=["type_check"])` (MUST be executed for typed projects; show status and results.type_check).
  - **⚠️ CRITICAL**: Tool checks BOTH `src/` AND `tests/` - if tool finds errors (even if Step 2 passed earlier), commit MUST be blocked.
  - **⚠️ NO EXCEPTIONS**: Step 12.2 result is AUTHORITATIVE.
  - **⚠️ EXECUTION MANDATORY**: This tool MUST be executed - do not skip or assume it passed. Show the tool result.
- **Linter Re-run**: Result of `execute_pre_commit_checks(checks=["quality"])` (MUST show 0 lint errors - ZERO ERRORS TOLERANCE, NO EXCEPTIONS).
- **Markdown Lint Re-run**: Result of `fix_markdown_lint(check_all_files=True)` MCP tool (MUST show check passed with 0 errors in ALL files - ZERO ERRORS TOLERANCE, NO EXCEPTIONS, matches CI behavior).
- **Test Naming Re-run**: Result of `execute_pre_commit_checks(checks=["test_naming"])` (MUST show check passed).
- **File Sizes Re-run**: Result of `execute_pre_commit_checks(checks=["quality"])` (MUST show results.quality.file_size_violations empty).
- **Function Lengths Re-run**: Result of `execute_pre_commit_checks(checks=["quality"])` (MUST show results.quality.function_length_violations empty).
- **Output Verified**: Whether actual command output was parsed (not assumed) - MUST be Yes for all Step 12 checks
- **New Files Created Since Step 1**: List any new files created during steps 4-11 (especially test files for coverage)
- **Code Changes Since Step 4**: List any code changes made during steps 5-11 that required re-verification
- **Discrepancy Handling**: If any Step 12 check finds errors (even if an earlier step passed), document and BLOCK commit
- **Validation Results**:
  - Step 12.0 executed: Yes/No (MUST be Yes - markdown re-validation on modified files executed)
  - Step 12.1 executed: Yes/No (MUST be Yes - formatting fix AND check commands executed)
  - Formatting fix executed: Yes/No (MUST be Yes)
  - Formatting check passed: Yes/No (MUST be Yes)
  - Step 12.2 executed: Yes/No (MUST be Yes for typed projects - type check tool executed)
  - Type check command shown: Yes/No (MUST be Yes - actual command output displayed)
  - Type check passed: Yes/No (MUST be Yes, or N/A if project doesn't use types)
    - **⚠️ CRITICAL**: If Step 12.2 tool found errors (even if Step 2 passed earlier), this MUST be No and commit MUST be blocked
  - Step 12.3 executed: Yes/No (MUST be Yes - linter check command executed)
  - Linter passed: Yes/No (MUST be Yes - error count explicitly parsed and verified = 0, ZERO ERRORS TOLERANCE, NO EXCEPTIONS even for pre-existing errors)
  - Step 12.4 executed: Yes/No (MUST be Yes - test naming check command executed)
  - Step 12.5 executed: Yes/No (MUST be Yes - markdown lint check command executed)
  - Markdown lint passed: Yes/No (MUST be Yes - zero errors in ALL markdown files, matches CI behavior, ZERO ERRORS TOLERANCE, NO EXCEPTIONS)
  - Step 12.6 executed: Yes/No (MUST be Yes - file sizes AND function lengths checks executed)
  - File sizes check passed: Yes/No (MUST be Yes)
  - Function lengths check passed: Yes/No (MUST be Yes)
  - Step 12.7 executed: Yes/No (MUST be Yes - tests with coverage validation executed)
  - Output fully read: Yes/No (MUST be Yes for all Step 12 checks)
  - Step 12 tool results take precedence: Yes/No (MUST be Yes - if any Step 12 check finds errors, commit blocked)
  - Step 12 execution verified: Yes/No (MUST be Yes - explicit evidence provided that all Step 12 sub-steps were executed)
- **BLOCK COMMIT** if any check in Step 12 fails OR if Step 12 execution cannot be verified

#### **13. Commit Creation**

- **Status**: Success/Failure
- **Commit Hash**: Git commit hash if successful
- **Commit Message**: The commit message used
- **Files Committed**: Count and list of files in the commit
- **Submodule Reference Updated**: Whether submodule reference was included in commit

#### **14. Push Branch**

- **Status**: Success/Failure
- **Branch Name**: Current branch that was pushed
- **Remote**: Remote repository name (e.g., origin)
- **Push Result**: Summary of push operation
- **Errors**: Any push errors encountered and their resolution

### **Issues Encountered**

- **Error Fixing Issues**: Any errors or warnings encountered during fix-errors step and their resolution
- **Formatting Issues**: Any formatting issues and their resolution
  - **CRITICAL**: If formatter check fails after formatting, this indicates files were not properly formatted
  - Must re-run formatter and verify formatter check passes before proceeding
- **Code Quality Issues**: File size or function length violations and their resolution
- **Test Failures**: Any test failures and their resolution
- **Memory Bank Issues**: Any memory bank update issues
- **Roadmap Update Issues**: Any issues updating roadmap.md with completed items
- **Plan Archiving Issues**: Any issues archiving completed build plans
- **Archive Validation Issues**: Any archive location violations found and their resolution
- **Roadmap/activeContext state issues**: Any issues ensuring roadmap (future only) and activeContext (completed only) reflect actual state
- **Submodule Issues**: Any submodule commit or push errors and their resolution
- **Push Issues**: Any push errors and their resolution

### **Commit Details**

- **Commit Hash**: Full commit hash
- **Commit Message**: Complete commit message
- **Files Changed**: List of all files in the commit
- **Lines Added**: Count of lines added
- **Lines Removed**: Count of lines removed
- **Net Change**: Net lines changed

### **Push Details**

- **Branch Pushed**: Name of the branch that was pushed
- **Remote**: Remote repository name
- **Push Status**: Success or failure status
- **Remote Tracking**: Whether remote tracking branch was set

## ⚠️ MANDATORY: Fix ALL Issues Automatically

**CRITICAL RULE**: When ANY error or violation is detected, you MUST fix ALL of them automatically. No explicit user request is required to apply fixes—fixing is part of the pipeline.

- **No explicit request needed**: The user does not need to say "fix it" or "yes, fix that". Apply fixes as soon as a failure is detected.
- **NEVER ask for permission** to fix issues - just fix them all
- **NEVER ask "should I continue?"** - continue fixing until ALL issues are resolved
- **NEVER stop after fixing some issues** - fix ALL of them, no matter how many
- **NEVER report and stop without attempting fixes first** - always try to fix before reporting
- **It's OK to stop the commit procedure** if context is insufficient after fixing, but ALL issues must still be fixed first
- **After fixing ALL issues**: Re-run validation, verify zero issues remain, then proceed or provide summary
- **No exceptions**: Whether it's 1 issue or 100 issues, fix ALL of them automatically

## Error/Violation Handling Strategy

**PRIMARY FOCUS**: When any error or violation is detected during the commit procedure, the agent's PRIMARY FOCUS must be to fix ALL of them immediately. **Do not wait for explicit user requests to fix**—apply fixes as part of the pipeline.

**After Fixing ALL Issues**:

1. **Fix ALL Issues First**: Continue fixing ALL issues until zero remain
   - Do not stop after fixing some issues - fix ALL of them
   - Do not ask for permission - just fix them all automatically
   - Re-run validation after fixing to verify zero issues remain
   - Continue fixing until validation shows zero issues

2. **If sufficient free context remains AFTER fixing ALL issues**: Continue with the commit pipeline automatically
   - Re-run the validation check that detected the issue
   - Verify the fix resolved ALL issues (zero violations remain)
   - Proceed to the next step in the commit pipeline

3. **If free context is insufficient AFTER fixing ALL issues**: Stop the commit pipeline and provide:
   - **Comprehensive Changes Summary**: Document ALL fixes made, files modified, and changes applied
   - **Re-run Recommendation**: Advise the user to re-run the commit pipeline (`/commit` or equivalent)
   - **Status Report**: Clearly indicate which step was completed and which step should be executed next
   - **CRITICAL**: ALL issues must be fixed before stopping - do not stop with issues remaining

**Context Assessment**: The agent should assess available context AFTER fixing ALL issues:

- Consider remaining token budget
- Consider complexity of remaining steps
- If context is insufficient AFTER fixing all issues, provide summary and recommend re-run
- **CRITICAL**: Do not assess context until ALL issues are fixed

## Failure Handling

**Block commit vs stop pipeline**:

- **Block commit** = Do not advance to the next step; do not create the commit. Correct: keep the pipeline running and focus on resolving the failure (fix, re-validate) in this same run.
- **Stop pipeline and report** = Only after you have attempted resolution (fixes + re-validation) and either validation still fails or context is insufficient. Wrong: stopping and reporting to the user as the first response to a failure—problem resolution is the first response.

### Code Quality Check Failure

- **Action**: **PRIMARY FOCUS** - Fix ALL violations immediately, then assess context to continue or summarize
- **Process**:
  1. **IMMEDIATE FIX**: Report the specific code quality violation (file size or function length)
  2. Provide detailed error information including file path, function name, and violation details
  3. Parse MCP tool response or check output to extract exact violation counts and details
  4. **FIX ALL**: Fix ALL file size violations by splitting large files or extracting modules
  5. **FIX ALL**: Fix ALL function length violations by extracting helper functions or refactoring logic
  6. **CRITICAL**: Continue fixing until ALL violations are resolved - do not stop after fixing some
  7. **NEVER ask for permission** - just fix them all automatically
  8. Re-run checks to verify ALL fixes
  9. **VALIDATION**: Re-parse MCP tool response or check output to confirm zero violations remain
  10. **CONTEXT ASSESSMENT**: After fixing ALL violations, assess if sufficient free context remains:
      - If YES: Continue with commit pipeline (re-run check, verify, proceed to next step)
      - If NO: Provide comprehensive changes summary and advise re-running commit pipeline
  11. **CRITICAL**: These checks match CI quality gate requirements - failures will cause CI to fail
- **No Partial Commits**: Do not proceed with commit until all code quality checks pass and validation confirms zero violations
- **No Partial Fixes**: Fix ALL violations before proceeding or stopping - never stop with violations remaining

### Test Suite Failure

- **Action**: **PRIMARY FOCUS** - Fix ALL test failures immediately, then assess context to continue or summarize
- **Process**:
  1. **IMMEDIATE FIX**: Review test failure output from `run-tests` command
  2. Parse test output to extract exact failure counts, test names, and error messages
  3. Analyze test failure messages and stack traces
  4. Identify root cause (code issue vs test issue)
  5. **FIX ALL**: Fix ALL underlying issues
  6. **CRITICAL**: Continue fixing until ALL test failures are resolved - do not stop after fixing some
  7. **NEVER ask for permission** - just fix them all automatically
  8. Re-run `run-tests` command to verify ALL fixes
  9. **VALIDATION**: Re-parse test output to verify:
     - Zero test failures (failed count = 0)
     - 100% pass rate for executable tests
     - Coverage meets 90%+ threshold (MANDATORY - extract exact percentage and verify ≥ 90.0%)
     - All integration tests pass
  10. **CONTEXT ASSESSMENT**: After fixing ALL test failures, assess if sufficient free context remains:
      - If YES: Continue with commit pipeline (re-run tests, verify, proceed to next step)
      - If NO: Provide comprehensive changes summary and advise re-running commit pipeline
  11. Continue until all tests pass with 100% pass rate and all validations pass, including coverage ≥ 90.0%
- **No Partial Commits**: Do not proceed with commit until all tests pass and all validations confirm success
- **No Partial Fixes**: Fix ALL test failures before proceeding or stopping - never stop with failures remaining
- **Coverage Enforcement**: Coverage threshold of 90% is absolute - if coverage < 90.0%, commit MUST be blocked
- **BLOCK COMMIT**: If any test validation fails, including coverage below 90.0%, do not proceed with commit

### Coverage Below Threshold

- **Action**: **PRIMARY FOCUS** - Focus on **problem resolution**: fix coverage **in this same run** by adding tests and re-running until coverage ≥ 90.0%. Do NOT stop and report to the user as the first response; treat like other violations (fix until resolved or context insufficient).
- **Process**:
  1. **IMMEDIATE FIX**: Parse `results.tests.coverage` from test output; if < 0.90, coverage is a violation to fix in this run. Do not stop and report—start adding tests.
  2. **FIX IN SAME RUN**: Add or improve tests (e.g. target recently changed or low-coverage modules), then re-run `execute_pre_commit_checks(checks=["tests"], test_timeout=600, coverage_threshold=0.90, strict_mode=False)`.
  3. **CRITICAL**: Continue adding tests and re-running until `results.tests.coverage` ≥ 0.90 - do not stop after one or two attempts and report "blocked". Problem resolution is the focus; only report after genuine fix attempts.
  4. **NEVER stop and report** with coverage < 90% unless: (a) context is insufficient after fixing, or (b) you have made multiple fix attempts with no coverage gain and need to recommend a dedicated coverage phase.
  5. **VALIDATION**: Re-run tests, verify `results.tests.success` = true AND `results.tests.coverage` ≥ 0.90 before proceeding to Step 5.
  6. **CONTEXT ASSESSMENT**: Only after coverage ≥ 90% (or genuine context exhaustion): continue pipeline or provide summary and re-run recommendation.
- **No Partial Commits**: Do not proceed to Step 5 until coverage ≥ 90.0%.
- **No Partial Fixes**: Treat coverage below 90% like any other violation - fix in this same run, do not stop and report.

### Submodule Failure

- **Action**: Report the issue and block main commit if submodule commit/push fails
- **Process**:
  1. Report the specific submodule operation failure
  2. Provide detailed error information
  3. Suggest resolution steps (e.g., check submodule remote, authentication)
  4. Do not proceed with main commit if submodule changes exist but couldn't be committed/pushed
  5. If submodule has no changes, skip submodule operations and proceed normally

### Push Failure

- **Action**: Report the issue but do not block commit (commit is already created)
- **Process**:
  1. Report the specific push failure
  2. Provide detailed error information
  3. Suggest resolution steps (e.g., set upstream branch, check authentication)
  4. Commit remains successful even if push fails

### Connection Closed During Long Tool (Retry Then Fallback)

- **When**: An MCP tool returns an error whose message or code indicates "Connection closed" or "ClosedResourceError" (e.g. the client disconnected or timed out while the tool was still running or had just completed on the server).
- **Action**: (1) **Retry the tool once.** (2) If it fails again with the same class of error (or with "tool not found" / similar after a connection closed error), perform the documented fallback for that step and record "MCP connection closed; fallback used" so the pipeline can proceed. Do not block the pipeline on "tool not found" after a disconnect—use the documented fallback.
- **Fallbacks** (documented): Stop and report.
- **Rationale**: Long-running tools may complete on the server after the client has closed the connection; "Connection closed" can mean client timeout/disconnect, not necessarily tool failure. Retry once then fallback (or explicit commit block for `fix_quality_issues`) allows the pipeline to behave predictably instead of silently failing.
- **Note (fix_markdown_lint)**: The server sends per-file progress and a 15 s heartbeat for `fix_markdown_lint`; MCP error -32000 ("Connection closed") can still occur due to client-side timeout (e.g. ~60 s). Retry once, then use the documented shell fallback (Step 12.5) and record "MCP connection closed; fallback used".

### MCP Tool Failure (CRITICAL)

- **Action**: **STOP IMMEDIATELY** - Do not continue with commit pipeline
- **Exception**: For errors indicating "Connection closed" or "ClosedResourceError" only, see "Connection Closed During Long Tool (Retry Then Fallback)" above (retry once, then use documented fallback and record "MCP connection closed; fallback used").
- **Protocol Enforcement**: **AUTOMATIC AND MANDATORY** - The MCP tool failure protocol is automatically enforced by the `mcp_tool_wrapper` decorator. Agents cannot bypass this protocol.
- **Process**:
  1. **STOP**: Current commit process MUST stop immediately when Cortex MCP tool crashes, disconnects, or exhibits unexpected behavior
  2. **DO NOT** attempt to retry or use fallback methods - the tool failure must be investigated first
  3. **Automatic Protocol Enforcement**: The MCP tool failure protocol is automatically enforced:
     - `mcp_tool_wrapper` decorator detects tool failures automatically
     - `MCPToolFailureHandler` creates investigation plans automatically
     - Investigation plans are added to roadmap automatically
     - User is notified automatically with failure summary
     - **Protocol violations are automatically blocked** - agents cannot continue with workarounds
  4. **Validation Required**: After each MCP tool call, validation is performed automatically:
     - Response structure is validated (must be dict, not JSON string)
     - Error status is checked (status="error" indicates tool failure)
     - Response format is verified (must match expected structure)
     - If validation fails, protocol is enforced automatically
     - **No manual validation needed** - validation happens automatically in the wrapper
  5. **Provide summary to user** (automatically generated):
     - **Description**: What tool failed and how (crash, disconnect, unexpected behavior)
     - **Impact**: Commit procedure was blocked at [step name]
     - **Fix Recommendation**: Mark as **FIX-ASAP** priority - tool must be fixed before commit can proceed
     - **Plan Location**: Path to created investigation plan
     - **Next Steps**: User should review the plan and prioritize fixing the tool issue
  6. **DO NOT** proceed with commit until the MCP tool issue is resolved
- **Affected Tools**: This applies to all Cortex MCP tools used in commit procedure:
  - `execute_pre_commit_checks()` (fix_errors, format, type_check, quality, tests)
  - `fix_markdown_lint()` (markdown linting)
  - `manage_file()` (memory bank operations)
  - `validate()` (timestamp validation); Step 10 uses `manage_file()` for roadmap/activeContext state only
  - Any other Cortex MCP tools used during commit
- **Automatic Enforcement**: Protocol violations are automatically detected and blocked:
  - Attempts to use workarounds are prevented
  - Fallback methods are blocked when tool fails
  - Commit procedure stops immediately on tool failure
  - Investigation plans are created automatically

### Step 10 (Roadmap/activeContext state)

- **Action**: Read roadmap.md and activeContext.md; if completed-work bullets appear in roadmap, move their summary to activeContext and remove them from roadmap. Then proceed to Step 11. No codebase scan or `validate(check_type="roadmap_sync")` in this step.

### Other Step Failures

- **Action**: **PRIMARY FOCUS** - Fix ALL failures immediately, then assess context to continue or summarize
- **Process**:
  1. **IMMEDIATE FIX**: Report the specific failure
  2. Provide detailed error information
  3. **FIX ALL**: Fix ALL underlying issues
  4. **CRITICAL**: Continue fixing until ALL issues are resolved - do not stop after fixing some
  5. **NEVER ask for permission** - just fix them all automatically
  6. **CONTEXT ASSESSMENT**: After fixing ALL issues, assess if sufficient free context remains:
     - If YES: Continue with commit pipeline (re-run step, verify, proceed to next step)
     - If NO: Provide comprehensive changes summary and advise re-running commit pipeline
  7. Do not proceed with commit until all issues are fixed and validated
  8. **No Partial Fixes**: Fix ALL issues before proceeding or stopping - never stop with issues remaining

### General Rules

- **Problem resolution first**: When any step fails, the pipeline must focus on resolving the problem (fix, re-validate) in the same run. Do not stop and report to the user without attempting resolution first. Only after fixes and re-validation may you report and stop (e.g. validation still fails or context insufficient).
- **Fixes without explicit request**: All fixes (type, lint, format, quality, tests, roadmap sync, timestamps, etc.) are applied automatically when a step fails. The user does not need to request fixes explicitly; switch to the fix flow as soon as a failure is detected.
- **Error/Violation Priority**: When any error or violation is detected, **PRIMARY FOCUS** is to fix ALL of them immediately
- **Fix ALL Issues Automatically**:
  - **NEVER ask for permission** to fix issues - just fix them all
  - **NEVER ask "should I continue?"** - continue fixing until ALL issues are resolved
  - **NEVER stop after fixing some** - fix ALL of them, no matter how many
  - **NEVER report and stop without attempting fixes first** - always apply fixes, then re-validate; only then report if still failing or context insufficient
  - **It's OK to stop the commit procedure** if context is insufficient after fixing, but ALL issues must still be fixed first
- **Execution Continuity**: Once this command starts, you MUST continue the pipeline until you either (a) complete Step 14 (push), or (b) hit a hard blocker (Cortex MCP tool failure, missing dependency, or explicit ZERO ERRORS violation). Do **not** stop mid-pipeline for planning-only reasons.
- **Context Management**: Keep narrative output between tool calls extremely concise (1–3 short sentences). Never restate this prompt or paste large tool outputs verbatim; summarize them to avoid exhausting context and causing premature termination.
- **Context-Aware Continuation**: After fixing ALL errors/violations:
  - If sufficient free context remains: Continue automatically with commit pipeline
  - If free context is insufficient: Provide comprehensive changes summary and advise re-running commit pipeline
- **No Partial Commits**: All steps must pass before commit creation
- **No Partial Fixes**: Fix ALL issues before proceeding or stopping - never stop with issues remaining
- **Validation Required**: All critical steps MUST include explicit validation that confirms success (parsing output, checking exit codes, verifying counts)
- **Block on Validation Failure**: If any validation step fails, **BLOCK COMMIT** and do not proceed until ALL issues are fixed
- **Fix Issues First**: Resolve ALL issues before attempting commit again
- **Automatic Execution**: Once this command is explicitly invoked by the user, execute all steps automatically without asking for additional permission
- **Comprehensive Summary Format**: When advising re-run due to context limits (AFTER fixing ALL issues), provide:
  - List of ALL fixes applied (errors fixed, violations resolved)
  - Files modified with brief description of changes
  - Current status (which step completed, which step to run next)
  - Clear instruction to re-run commit pipeline
- **Command Execution**: When referencing other Cursor commands, AI MUST immediately read those command files and execute ALL their steps without any user interaction
- **MCP Tools**: Use structured MCP tools instead of reading prompt files:
  - Step 0 (Fix Errors) MUST use `execute_pre_commit_checks(checks=["fix_errors"])` MCP tool
  - Step 4 (Testing) MUST use `execute_pre_commit_checks(checks=["tests"])` MCP tool
  - Step 4 (Memory Bank) MUST use `manage_file()` MCP tool for memory bank operations
  - Step 9 (Memory Bank Timestamp Validation) MUST use `validate(check_type="timestamps")` MCP tool
  - Step 10 (Roadmap/activeContext state) MUST use `manage_file()` to read roadmap.md and activeContext.md and ensure completed work is only in activeContext, future work only in roadmap (no `validate(check_type="roadmap_sync")`)
  - If optional command files don't exist, skip those steps gracefully without searching for alternatives
  - This ensures consistency, maintainability, type safety, and single source of truth
- **Real-Time Checklist Updates**: AI MUST update the todo checklist immediately as each step completes:
  - Use `todo_write` tool to mark steps as `completed` right after they finish
  - Mark steps as `in_progress` when starting them
  - Update status in real-time, not at the end
  - This provides transparency and progress tracking during execution
- **Output Parsing**: For all validation steps, parse command output to extract exact counts, percentages, and status:
  - Parse type checker output to count type errors (must be 0, skip if not applicable)
  - Parse linter output to count linting errors (must be 0)
  - Parse formatter check output to count formatting violations (must be 0)
  - Parse test output to count failures (must be 0), calculate pass rate (must be 100%), extract coverage (must be ≥ 90% if applicable)
  - Parse code quality check output to count violations (must be 0)
  - Do not rely on exit codes alone - verify actual results from output
- **Avoid Unnecessary Searches**:
  - Do not perform codebase searches for command files that are referenced but don't exist
  - Check file existence directly using file system tools (read_file, list_dir) before attempting to read
  - If a referenced command file doesn't exist, skip that step gracefully without searching for alternatives
  - Do not search codebase for "how to update memory bank" or similar - if command file doesn't exist, skip the step

## Success Criteria

**⚠️ ZERO ERRORS TOLERANCE**: ALL checks below MUST show ZERO errors - NO EXCEPTIONS, even for pre-existing errors or errors in files you didn't modify.

- ✅ All compiler errors and warnings fixed (fix-errors step passes)
- ✅ **VALIDATION**: Zero errors AND zero warnings confirmed via type checker (if applicable) and linter re-checks after fix-errors
- ✅ **ZERO ERRORS TOLERANCE**: Error counts explicitly parsed and verified = 0 for ALL checks (formatting, types, linting, quality, tests)
- ✅ All type errors and warnings resolved (if applicable)
- ✅ **VALIDATION**: Type checker reports zero type errors AND zero warnings (parsed from output, skip if not applicable)
- ✅ All formatting issues fixed
- ✅ Project formatter + import sorting (if applicable) formatting passes without errors
- ✅ **CRITICAL**: Formatter check MUST pass after formatting (verifies CI will pass)
- ✅ **VALIDATION**: Formatter check output confirms zero formatting violations
- ✅ Markdown lint errors fixed (ALL markdown files properly formatted, matching CI behavior)
- ✅ **VALIDATION**: Markdown lint fix tool executed with `check_all_files=True` to check ALL files (matching CI)
- ✅ **VALIDATION**: Zero errors confirmed in ALL markdown files (not just modified files)
- ✅ Real-time checklist updates completed for all steps
- ✅ **QUALITY CHECK SUCCESS**: `results.quality.success` = true (PRIMARY validation)
- ✅ File size check passes (all files ≤ 400 lines)
- ✅ **VALIDATION**: `len(results.quality.file_size_violations)` = 0 (array MUST be empty)
- ✅ Function length check passes (all functions ≤ 30 lines)
- ✅ **VALIDATION**: `len(results.quality.function_length_violations)` = 0 (array MUST be empty)
- ✅ **NO EXCEPTIONS**: Pre-existing violations do NOT bypass this check - CI will fail regardless
- ✅ All executable tests pass (100% pass rate) - verified via test execution
- ✅ **VALIDATION**: Test output parsed to confirm zero failures, 100% pass rate (from MCP tool response)
- ✅ All executable tests pass (100% pass rate) - verified via test execution
- ✅ Test coverage meets threshold (90%+) - verified via test execution
- ✅ **VALIDATION**: Coverage percentage parsed from MCP tool response (`results.tests.coverage`) and confirmed ≥ 90.0% (MANDATORY)
- ✅ **COVERAGE ENFORCEMENT**: Coverage threshold validation is absolute - no exceptions allowed
- ✅ All integration tests pass - explicitly verified from test output
- ✅ Memory bank updated with current information
- ✅ Roadmap.md updated with completed items and current progress
- ✅ Completed build plans archived to the plans archive directory (path from `get_structure_info()`)
- ✅ Plan archive locations validated (no violations)
- ✅ Memory bank timestamps validated (all use YYYY-MM-DD format, no time components)
- ✅ Roadmap and activeContext reflect actual state (roadmap = future work only, activeContext = completed work only)
- ✅ Synapse submodule changes committed and pushed (if any changes exist)
- ✅ Parent repository's submodule reference updated (if submodule was committed)
- ✅ Commit created with descriptive message
- ✅ All changes committed successfully
- ✅ Branch pushed to remote repository successfully
- ✅ **Analyze prompt executed** - Analyze (End of Session) prompt (`analyze.md`) run to complete context effectiveness and session optimization analysis

## Usage

This command executes the complete commit procedure with all required pre-commit checks, ensuring code quality, documentation completeness, test coverage, and project consistency before creating a commit.

**EXPLICIT INVOCATION REQUIRED**: This command is ONLY executed when explicitly invoked by the user (e.g., `/commit`). Invoking this command IS an explicit commit request per `no-auto-commit.mdc` rule.

**NO ADDITIONAL PROMPTS**: Once explicitly invoked, execute all steps automatically without asking for additional permission

**CURSOR COMMAND EXECUTION**: When this command references other Cursor commands (like `run-tests`), AI MUST immediately read that command file and execute ALL its steps without any user interaction
