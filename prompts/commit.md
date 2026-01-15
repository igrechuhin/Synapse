# Commit Changes

**AI EXECUTION COMMAND**: Execute the mandatory commit procedure with all required pre-commit checks, including testing of all runnable project tests.

**CRITICAL**: This command is ONLY executed when explicitly invoked by the user (e.g., `/commit` or user explicitly requests commit). Invoking this command IS an explicit commit request per `no-auto-commit.mdc` rule. Once invoked, execute all steps AUTOMATICALLY without asking for additional permission or confirmation.

**Tooling Note**: Use standard Cursor tools (`Read`, `ApplyPatch`, `Write`, `LS`, `Glob`, `Grep`) by default; MCP filesystem tools are optional fallbacks only when standard tools are unavailable or explicitly requested. **Use Cortex MCP tools for memory bank operations** (e.g., `manage_file()`, `get_memory_bank_stats()`, `validate()`, `check_structure_health()`).

**Pre-Commit Checks**: Use the `execute_pre_commit_checks()` MCP tool for all pre-commit operations (fix errors, format, type check, quality, tests). This tool provides:

- Language auto-detection
- Structured parameters and return values
- Consistent error handling
- Type safety

## ⚠️ MANDATORY PRE-ACTION CHECKLIST

**BEFORE executing this command, you MUST:**

1. ✅ **Read relevant memory bank files** - Understand current project context:
   - **Use Cortex MCP tool `manage_file()`** to read `.cursor/memory-bank/activeContext.md` to understand current work focus
   - **Use Cortex MCP tool `manage_file()`** to read `.cursor/memory-bank/progress.md` to see recent achievements
   - **Use Cortex MCP tool `manage_file()`** to read `.cursor/memory-bank/roadmap.md` to understand project priorities

1. ✅ **Read relevant rules** - Understand commit requirements:
   - Read `.cursor/rules/no-auto-commit.mdc` for commit procedure requirements
   - Read `.cursor/rules/coding-standards.mdc` and language-specific coding standards (e.g., `.cursor/rules/python-coding-standards.mdc` for Python) for code quality standards
   - Read `.cursor/rules/memory-bank-workflow.mdc` for memory bank update requirements

1. ✅ **Understand operations** - Use MCP tools for all operations:
   - **Pre-commit checks**: Use `execute_pre_commit_checks()` MCP tool for fix_errors, format, type_check, quality, and tests
   - **Memory bank operations**: Use existing MCP tools (`manage_file()`, `get_memory_bank_stats()`) instead of prompt files
   - **Validation operations**: Use existing MCP tools (`validate()`, `check_structure_health()`) instead of prompt files

1. ✅ **Verify prerequisites** - Ensure all prerequisites are met:
   - Confirm there are changes to commit
   - Verify build system is accessible
   - Check that test suite can be executed

**VIOLATION**: Executing this command without following this checklist is a CRITICAL violation that blocks proper commit procedure.

## ⚠️ COMMON ERRORS TO CATCH BEFORE COMMIT

The following error patterns MUST be detected and fixed before commit. These are common issues that have caused problems in the past:

### Type Errors

- **Pattern**: Type checker reports type errors (not warnings)
- **Detection**: Parse type checker output for error count (e.g., Pyright for Python, TypeScript compiler for TypeScript)
- **Action**: Fix all type errors, re-run type checker, verify zero errors
- **Block Commit**: Yes - type errors will cause CI to fail
- **Note**: Only applicable if project uses a type system (Python with type hints, TypeScript, etc.)

### Test Failures

- **Pattern**: Test suite reports failures (failed count > 0)
- **Detection**: Parse test output for failure count
- **Action**: Fix failing tests, re-run tests, verify zero failures
- **Block Commit**: Yes - test failures will cause CI to fail

### Test Coverage Below Threshold

- **Pattern**: Coverage percentage < 90%
- **Detection**: Parse coverage report from test output (MANDATORY - must extract exact percentage)
- **Action**: Add tests to increase coverage, re-run tests, verify coverage ≥ 90%
- **Block Commit**: Yes - coverage below threshold violates project standards
- **CRITICAL**: Coverage MUST be parsed from test output, not estimated or assumed
- **CRITICAL**: If coverage is below 90%, DO NOT proceed with commit - fix coverage first
- **CRITICAL**: Coverage validation is MANDATORY - there are NO exceptions or "slightly below" allowances
- **Validation**: Coverage percentage MUST be explicitly extracted and verified ≥ 90.0% before proceeding
- **Enforcement**: If coverage < 90.0%, the commit procedure MUST stop immediately and coverage MUST be fixed before continuing

### File Size Violations

- **Pattern**: Files exceeding 400 lines
- **Detection**: Parse MCP tool response (`results.quality.file_size_violations`) or file size check output
- **Action**: Split large files, re-run check, verify zero violations
- **Block Commit**: Yes - file size violations will cause CI to fail

### Function Length Violations

- **Pattern**: Functions exceeding 30 lines
- **Detection**: Parse MCP tool response (`results.quality.function_length_violations`) or function length check output
- **Action**: Refactor long functions, re-run check, verify zero violations
- **Block Commit**: Yes - function length violations will cause CI to fail

### Formatting Violations

- **Pattern**: Formatter check reports formatting issues
- **Detection**: Parse formatter check output for file count (e.g., `black --check` for Python, `prettier --check` for JavaScript/TypeScript)
- **Action**: Run formatter, re-run formatter check, verify zero violations
- **Block Commit**: Yes - formatting violations will cause CI to fail

### Linter Errors

- **Pattern**: Linter reports errors (not warnings)
- **Detection**: Parse linter output for error count (e.g., ruff for Python, ESLint for JavaScript/TypeScript)
- **Action**: Fix linting errors, re-run linter, verify zero errors
- **Block Commit**: Yes - linter errors will cause CI to fail
- **Note**: For Python, ensure code is compatible with Python 3.13+ (CI checks Python 3.13 compatibility). Use `TypeAlias` from `typing` instead of `type` alias statement (Python 3.13+ only). **Use `execute_pre_commit_checks()` MCP tool for all pre-commit operations** - scripts are fallbacks only if MCP tool is unavailable

### Integration Test Failures

- **Pattern**: Integration tests fail (specific test category)
- **Detection**: Parse test output to identify integration test failures
- **Action**: Fix integration test issues, re-run tests, verify all pass
- **Block Commit**: Yes - integration test failures indicate broken functionality

### Type Checker Warnings

- **Pattern**: Type checker reports warnings (not errors)
- **Detection**: Parse type checker output for warning count
- **Action**: Fix all warnings, re-run type checker, verify zero warnings
- **Block Commit**: Yes - warnings must be resolved before commit
- **Note**: Only applicable if project uses a type system (Python with type hints, TypeScript, etc.)

**CRITICAL**: All error patterns above MUST be validated by parsing command output, not just checking exit codes. Exit codes can be misleading - always parse actual output to verify results.

## Steps

0. **Fix errors and warnings** - Use `execute_pre_commit_checks()` MCP tool:
   - **Call MCP tool**: `execute_pre_commit_checks(checks=["fix_errors"], strict_mode=False)`
   - The tool will automatically:
     - Detect project language
     - Fix all compiler errors, type errors, formatting issues, and warnings
     - Return structured results with error counts and files modified
   - **CRITICAL**: This step MUST run before testing to ensure code contains no errors
   - **CRITICAL**: This prevents committing/pushing poor code that would fail CI checks
   - **PRIMARY FOCUS**: If errors are detected, fix them immediately
   - **VALIDATION**: Parse tool response to verify:
     - `total_errors` = 0 (MUST be zero)
     - `results.fix_errors.success` = true
     - **BLOCK COMMIT** if any errors remain after fix-errors step
   - **CONTEXT ASSESSMENT**: After fixing errors, if insufficient context remains, provide comprehensive summary and advise re-running commit pipeline
   - **CRITICAL**: After fix-errors, verify all linting issues are resolved by checking the tool response:
     - The `execute_pre_commit_checks()` tool already runs linter checks as part of fix_errors
     - Parse tool response: `results.fix_errors.errors` must be empty list
     - **CRITICAL**: If linting errors remain, fix remaining issues and re-run fix-errors until check passes
     - **MANDATORY**: Linter check MUST pass before proceeding to next step
     - **VALIDATION**: Parse tool response to verify zero errors - **BLOCK COMMIT** if any linting errors remain
     - **Note**: The fix-errors step runs linter with --fix which fixes auto-fixable issues, but some errors (like syntax errors, undefined names, Python version compatibility) cannot be auto-fixed and must be manually resolved
     - **Fallback**: If MCP tool is unavailable, run linter manually: `.venv/bin/ruff check src/ tests/` (for Python) or equivalent for other languages

1. **Code formatting** - Use `execute_pre_commit_checks()` MCP tool:
   - **Call MCP tool**: `execute_pre_commit_checks(checks=["format"], strict_mode=False)`
   - The tool will automatically:
     - Detect project language
     - Run project formatter (e.g., Black for Python) and import sorting tools
     - Auto-detect directories (src/, tests/) matching CI workflow
     - Return structured results with files formatted count
   - **CRITICAL**: After formatting, verify all files pass formatting check:
     - Parse tool response: `results.format.status` must be "passed"
     - Parse tool response: `results.format.files_formatted` shows count of files formatted
     - **PRIMARY FOCUS**: If formatting violations are detected, fix them immediately
     - **CRITICAL**: If formatter check fails, re-run format check until it passes
     - **MANDATORY**: Formatter check MUST pass before proceeding to next step
     - **VALIDATION**: Parse tool response to verify formatting passed - **BLOCK COMMIT** if formatting fails
     - **CONTEXT ASSESSMENT**: After fixing formatting issues, if insufficient context remains, provide comprehensive summary and advise re-running commit pipeline
   - **Fallback**: If MCP tool is unavailable, run formatter manually: `.venv/bin/black src/ tests/` (for Python) or equivalent for other languages
1.5. **Markdown linting** - Fix markdown lint errors in all markdown files:
   - **MANDATORY**: Run markdown lint fix tool to automatically fix markdownlint errors
   - **CRITICAL**: Check ALL markdown files, not just modified ones, to catch existing errors
   - Execute: `.venv/bin/python scripts/fix_markdown_lint.py --check-all` (or equivalent)
   - The script automatically:
     - Finds all markdown files (`.md` and `.mdc`) in the project when `--check-all` is used
     - Runs markdownlint-cli2 with `--fix` to auto-fix errors
     - Reports files fixed and errors resolved
   - **CRITICAL**: markdownlint-cli2 is a REQUIRED dependency for Cortex MCP. If not installed:
     - **BLOCK COMMIT** and report error: "markdownlint-cli2 not found. Install it with: npm install -g markdownlint-cli2"
     - Installation is required because `fix_markdown_lint` MCP tool depends on it
     - See README.md for installation instructions
   - **VALIDATION**: After fixing, verify markdown lint errors are resolved:
     - **Step 1**: Check tool response for `files_with_errors` count
     - **Step 2**: If `files_with_errors > 0`, run markdownlint in check-only mode to get detailed error report:
       - Execute: `markdownlint-cli2 "**/*.md" "**/*.mdc" --config .markdownlint.json 2>&1` (or equivalent)
       - Parse output to extract error codes (MD024, MD032, MD031, MD036, etc.) and file paths
     - **Step 3**: Categorize errors by severity:
       - **Critical errors** (BLOCK COMMIT for memory bank files): 
         - MD024 (duplicate headings) - especially in `.cortex/memory-bank/*.md` files
         - MD032 (blanks around lists) - formatting issue
         - MD031 (blanks around fences) - formatting issue
       - **Critical errors** (BLOCK COMMIT for all files):
         - MD001 (heading increment) - structural issue
         - MD003 (heading style) - consistency issue
         - MD009 (trailing spaces) - formatting issue
       - **Non-critical errors** (warn but don't block):
         - MD036 (emphasis as heading) - may be intentional formatting
         - MD013 (line length) - may be acceptable for code blocks
     - **Step 4**: For each file with critical errors:
       - If file is in `.cortex/memory-bank/` directory: **BLOCK COMMIT** - memory bank files must be error-free
       - If file is in `.cortex/plans/` directory: **BLOCK COMMIT** - plan files must be error-free
       - For other files: Review and fix manually or add markdownlint disable comments if appropriate
     - **Step 5**: Re-run validation after manual fixes:
       - Run fix tool again: `.venv/bin/python scripts/fix_markdown_lint.py --check-all`
       - Run check-only mode again: `markdownlint-cli2 "**/*.md" "**/*.mdc" --config .markdownlint.json 2>&1`
       - Verify zero critical errors remain
     - **BLOCK COMMIT** if:
       - Any critical errors remain in `.cortex/memory-bank/*.md` files
       - Any critical errors remain in `.cortex/plans/*.md` files
       - More than 5 critical errors remain in other markdown files
     - **Note**: Some errors (like duplicate headings) require changing heading text, not just formatting
     - **Note**: Memory bank files (progress.md, activeContext.md, roadmap.md, etc.) must be error-free
   - **PRIMARY FOCUS**: If markdown lint errors are detected, fix them immediately
   - **Note**: This step runs after code formatting to ensure markdown files are also properly formatted
   - **Note**: Using `--check-all` ensures all markdown files are checked, not just those modified in the current commit
2. **Type checking** - Use `execute_pre_commit_checks()` MCP tool (if applicable):
   - **Conditional**: Only execute if project uses a type system (Python with type hints, TypeScript, etc.)
   - **Call MCP tool**: `execute_pre_commit_checks(checks=["type_check"], strict_mode=False)`
   - The tool will automatically:
     - Detect project language and type checker (e.g., pyright for Python, tsc for TypeScript)
     - Run type checker on appropriate directories (e.g., src/ for Python, matches CI workflow)
     - Return structured results with error and warning counts
   - **CRITICAL**: Capture and parse type checker output to verify zero errors AND zero warnings
   - **VALIDATION**: Parse tool response to verify:
     - `results.type_check.status` = "passed"
     - `results.type_check.errors` = 0 (MUST be zero)
     - `results.type_check.warnings` = 0 (MUST be zero)
   - **BLOCK COMMIT** if type checker reports any type errors OR warnings
   - **PRIMARY FOCUS**: If type errors/warnings are detected, fix them immediately
   - Fix any type errors and warnings before proceeding
   - Re-run type checker after fixes to verify zero errors AND zero warnings remain
   - **CONTEXT ASSESSMENT**: After fixing type issues, if insufficient context remains, provide comprehensive summary and advise re-running commit pipeline
   - **Skip if**: Project does not use a type system
   - **Fallback**: If MCP tool is unavailable, run type checker manually: `.venv/bin/pyright src/` (for Python) or equivalent for other languages
3. **Code quality checks** - Use `execute_pre_commit_checks()` MCP tool:
   - **Call MCP tool**: `execute_pre_commit_checks(checks=["quality"], strict_mode=False)`
   - The tool will automatically:
     - Detect project language
     - Run file size checks (verifies all files ≤ 400 lines)
     - Run function/method length checks (verifies all functions ≤ 30 lines)
     - Auto-detect directories (src/, tests/) matching CI workflow
     - Return structured results with violation counts
   - **VALIDATION**: Parse tool response to verify:
     - `results.quality.status` = "passed"
     - `results.quality.file_size_violations` = 0 (MUST be zero)
     - `results.quality.function_length_violations` = 0 (MUST be zero)
   - **BLOCK COMMIT** if any violations are found
   - **PRIMARY FOCUS**: If violations are detected, fix them immediately (split files, extract functions)
   - Fix any file size or function/method length violations before proceeding
   - Re-run quality check after fixes to verify zero violations remain
   - **CONTEXT ASSESSMENT**: After fixing violations, if insufficient context remains, provide comprehensive summary and advise re-running commit pipeline
   - Note: These checks match CI quality gate requirements and MUST pass
   - **Fallback**: If MCP tool is unavailable, run quality checks manually using scripts: `.cortex/synapse/scripts/{language}/check_file_sizes.py` and `.cortex/synapse/scripts/{language}/check_function_lengths.py` (or equivalent)
4. **Test execution** - Use `execute_pre_commit_checks()` MCP tool:
   - **Call MCP tool**: `execute_pre_commit_checks(checks=["tests"], timeout=300, coverage_threshold=0.90)`
   - The tool will automatically:
     - Detect project language and test framework
     - Execute test suite with timeout protection
     - Calculate coverage and verify threshold
     - Return structured results with test counts and coverage
   - **CRITICAL**: This step runs AFTER errors, formatting, and code quality checks are fixed
   - **CRITICAL**: Tests must pass with 100% pass rate before proceeding to commit
   - **VALIDATION**: Parse tool response to verify:
     - `results.tests.success` = true
     - `results.tests.tests_failed` = 0 (MUST be zero)
     - `results.tests.pass_rate` = 100.0 (MUST be 100%)
     - `results.tests.coverage` ≥ 0.90 (MUST meet threshold - NO exceptions)
     - **BLOCK COMMIT** if any of the above validations fail
   - **CRITICAL COVERAGE VALIDATION**:
     - Coverage MUST be extracted from `results.tests.coverage` field
     - Coverage MUST be compared to 0.90 threshold
     - If coverage < 0.90, commit procedure MUST STOP immediately
     - DO NOT proceed with "slightly below" or "close enough" - threshold is absolute
     - Coverage must be fixed by adding tests before commit can proceed
   - If tests fail or coverage is below threshold, fix issues and re-run tool until all pass
   - Re-verify all validation criteria after fixes, including coverage threshold
5. **Memory bank operations** - **Should use existing MCP tools**:
   - **Use MCP tool `manage_file()`** to update memory bank files (e.g., `activeContext.md`, `progress.md`, `roadmap.md`)
   - **Use MCP tool `get_memory_bank_stats()`** to check current state
   - **Do NOT** read prompt files - use structured MCP tools instead
   - Update all relevant memory bank files with current changes using `manage_file(operation="write", ...)`
6. **Update roadmap** - Update roadmap.md with completed items and new milestones:
   - **Use Cortex MCP tool `manage_file()`** to read and update roadmap.md
   - Review recent changes and completed work
   - Mark completed milestones and tasks in roadmap.md using `manage_file(operation="write", ...)`
   - Add new roadmap items if significant new work is identified
   - Update completion status and progress indicators
   - Ensure roadmap accurately reflects current project state
7. **Archive completed plans** - Archive any completed build plans:
   - **MANDATORY**: Scan `.cursor/plans/` directory (or `.cortex/plans/` if `.cursor/plans` is a symlink) for plan files with status "COMPLETED" or "Complete"
   - **Detection Method**: Use `grep -l "Status.*COMPLETED\|Status.*Complete" .cursor/plans/*.md` (or `.cortex/plans/*.md`) to find completed plans
   - **CRITICAL**: If no completed plans are found, report "0 plans archived" but DO NOT skip this step - the check MUST be performed
   - For each completed plan found:
     - Extract phase number from filename (e.g., `phase-18-*.md` → Phase18)
     - Create archive directory: `mkdir -p .cursor/plans/archive/PhaseX/` (or `.cortex/plans/archive/PhaseX/`)
     - Move plan file: `mv .cursor/plans/phase-X-*.md .cursor/plans/archive/PhaseX/`
     - Update all links in memory bank files (activeContext.md, roadmap.md, progress.md) to point to archive location: `../plans/archive/PhaseX/phase-X-*.md`
     - Run `validate_links()` MCP tool to verify all links are valid after archival
     - Fix any broken links found
   - **VALIDATION**: After archiving, verify:
     - Count of plans archived (must match count found in detection step)
     - All archived plans are in `.cursor/plans/archive/PhaseX/` directories (not in `.cursor/plans/`)
     - All links in memory bank files point to archive locations
     - Link validation passes with zero broken links for archived plans
   - **BLOCK COMMIT** if:
     - Completed plans are found but not archived
     - Links are not updated after archiving
     - Link validation fails for archived plan links
   - **CRITICAL**: Plan files MUST be archived in `.cursor/plans/archive/PhaseX/`, never left in `.cursor/plans/`
8. **Validate archive locations** - Validate that all archived files are in correct locations and no completed plans remain unarchived:
   - **MANDATORY**: Re-check for completed plans in `.cursor/plans/` (or `.cortex/plans/`) that were not archived
   - Use `grep -l "Status.*COMPLETED\|Status.*Complete" .cursor/plans/*.md` to detect any remaining completed plans
   - **CRITICAL**: If any completed plans are found in `.cursor/plans/`, this is a violation - they MUST be archived
   - Check `.cursor/plans/archive/` directory structure - should contain PhaseX subdirectories with plan files
   - Validate that all plan files in archive are in correct PhaseX subdirectories
   - Report any plan files found outside `.cursor/plans/archive/PhaseX/` and require manual correction
   - **BLOCK COMMIT** if:
     - Any completed plans remain in `.cursor/plans/` directory
     - Any archived plans are in wrong locations (not in PhaseX subdirectories)
     - Archive location violations are found
9. **Validate memory bank timestamps** - Use MCP tool `validate(check_type="timestamps")`:
   - **Call MCP tool**: `validate(check_type="timestamps", project_root="<project_root>")`
   - The tool will automatically:
     - Scan all Memory Bank files for timestamps
     - Validate that all timestamps use YYYY-MM-DD date-only format (no time components)
     - Report any violations with file names, line numbers, and issue descriptions
     - Return structured results with violation counts and details
   - **CRITICAL**: This step runs as part of pre-commit validation
   - **VALIDATION**: Parse tool response to verify:
     - `valid` = true (MUST be true)
     - `total_invalid_format` = 0 (MUST be zero)
     - `total_invalid_with_time` = 0 (MUST be zero)
     - **BLOCK COMMIT** if any timestamp violations are found
   - If violations are found, fix timestamp formats and re-run validation until all pass
   - Re-verify all validation criteria after fixes
10. **Roadmap synchronization validation** - Execute Cursor command: `validate-roadmap-sync` (if available):

- Check if `.cortex/synapse/prompts/validate-roadmap-sync.md` exists
- If file exists:
  - Read `.cortex/synapse/prompts/validate-roadmap-sync.md`
  - Execute ALL steps from that command automatically
  - Validate roadmap.md is synchronized with Sources/ directory
  - Ensure all production TODOs are properly tracked
  - Verify line numbers and file references are accurate
- If file does not exist:
  - Skip this step (command file not available)
  - Note: Roadmap synchronization can be validated manually if needed

1. **Submodule handling** - Commit and push `.cortex/synapse` submodule changes if any:

- Check if `.cortex/synapse` submodule has uncommitted changes using `git -C .cortex/synapse status --porcelain`
- If submodule has changes:
  - Stage all changes in the submodule using `git -C .cortex/synapse add .`
  - Create commit in submodule with descriptive message (use same message format as main commit or append " [synapse submodule]")
  - Push submodule changes to remote using `git -C .cortex/synapse push`
  - Verify submodule push completes successfully
  - Update parent repository's submodule reference using `git add .cortex/synapse`
  - Note: This stages the updated submodule reference for the main commit

1. **Commit creation** - Create commit with descriptive message:

- Stage ALL changes in the working directory using `git add .` (this includes the updated submodule reference if submodule was committed)
- Analyze all changes made during the commit procedure
- Generate comprehensive commit message summarizing:
  - Features added or modified
  - Refactors performed
  - Tests added or updated
  - Documentation updates
  - Rules compliance fixes
  - Memory bank updates
  - Roadmap updates
  - Plan archiving
  - Submodule updates (if `.cortex/synapse` submodule was updated)
- Create commit with `git commit` using the generated message
- If user provided custom commit message, use that exact message instead

1. **Push branch** - Push committed changes to remote repository:
    - Determine current branch name using `git branch --show-current`
    - Push current branch to remote using `git push`
    - Verify push completes successfully
    - Handle any push errors (e.g., remote tracking not set, authentication issues)

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
   - **CRITICAL**: Tests must pass with 100% pass rate before proceeding
   - **VALIDATION**: Must verify zero test failures, 100% pass rate, 90%+ coverage (MANDATORY), all integration tests pass
   - **CRITICAL COVERAGE ENFORCEMENT**:
     - Coverage threshold of 90% is MANDATORY and absolute
     - Coverage MUST be parsed from test output and verified ≥ 90.0%
     - If coverage < 90.0%, commit procedure MUST STOP and coverage MUST be fixed
     - NO exceptions, NO "close enough", NO proceeding with coverage below threshold
   - **BLOCK COMMIT** if any test validation fails, including coverage below threshold
5. **Documentation** (Memory Bank) - Updates project context
6. **Roadmap Updates** (Roadmap Update) - Ensures roadmap reflects current progress
7. **Plan Archiving** (Archive Completed Plans) - Cleans up completed build plans
8. **Archive Validation** (Validate Archive Locations) - Ensures archived files are in correct locations
9. **Optimization** (Memory Bank Validation) - Validates and optimizes memory bank
10. **Roadmap Sync** (Roadmap-Codebase Synchronization) - Ensures roadmap.md matches Sources/ codebase
11. **Submodule Handling** - Commits and pushes `.cortex/synapse` submodule changes if any
12. **Commit** - Creates the commit with all changes (including updated submodule reference)
13. **Push** - Pushes committed changes to remote repository

**MCP Tools**: Steps 0 (Fix Errors), 1 (Formatting), 2 (Type Checking), 3 (Code Quality), and 4 (Testing) use the `execute_pre_commit_checks()` MCP tool instead of scripts. This provides structured parameters, type safety, and consistent error handling. Scripts are fallbacks only if the MCP tool is unavailable.

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
- [ ] **Code Quality Validation**: File size = 0 violations, Function length = 0 violations (parsed from MCP tool response)
- [ ] **Test Execution Validation**:
  - Test failures = 0 (parsed from test output)
  - Pass rate = 100% (calculated from test output)
  - Coverage ≥ 90% (parsed from test output)
  - Integration tests = all pass (explicitly verified)
- [ ] **All Validations Passed**: All above validations confirmed successful

**If any validation fails, BLOCK COMMIT and fix issues before proceeding.**

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
- Step 10: Roadmap Synchronization Validation
- Step 11: Submodule Handling
- Step 12: Commit Creation
- Step 13: Push Branch

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
- **Command Used**: `.venv/bin/python scripts/fix_markdown_lint.py --check-all`
- **Tool Available**: Whether markdownlint-cli2 is installed
- **Files Processed**: Count of markdown files processed
- **Files Fixed**: Count of markdown files with errors fixed
- **Files Unchanged**: Count of markdown files with no errors
- **Files With Errors**: Count of files with non-auto-fixable errors
- **Check-Only Validation**: Whether markdownlint check-only mode was run
- **Critical Errors Found**: Count of critical errors found (MD024, MD032, MD031, MD001, MD003, MD009)
- **Critical Errors in Memory Bank**: Count of critical errors in `.cortex/memory-bank/*.md` files (MUST be 0)
- **Critical Errors in Plans**: Count of critical errors in `.cortex/plans/*.md` files (MUST be 0)
- **Critical Errors in Other Files**: Count of critical errors in other markdown files
- **Non-Critical Errors**: Count of non-critical errors (MD036, MD013, etc.)
- **Errors Fixed**: List of markdown lint errors fixed
- **Errors Remaining**: List of non-auto-fixable errors with file paths and error codes
- **Validation Results**:
  - Tool executed: Yes/No (MUST be Yes if tool available)
  - Check-only validation run: Yes/No (MUST be Yes if files_with_errors > 0)
  - All auto-fixable errors fixed: Yes/No (MUST be Yes if tool available)
  - Zero critical errors in memory bank: Yes/No (MUST be Yes - parsed from check-only output)
  - Zero critical errors in plans: Yes/No (MUST be Yes - parsed from check-only output)
  - Critical errors in other files ≤ 5: Yes/No (MUST be Yes or commit blocked)
  - Tool response parsed: Yes/No
  - Check-only output parsed: Yes/No (MUST be Yes if files_with_errors > 0)
- **Details**: Summary of markdown lint fixing operations, including critical error breakdown
- **Commit Blocked**: Yes/No (blocked if critical markdown lint errors remain in memory bank/plans, or >5 in other files)
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
- **File Size Check**: Status of file size validation (from tool response: `results.quality.file_size_violations`, max 400 lines, MUST be 0)
- **Function Length Check**: Status of function length validation (from tool response: `results.quality.function_length_violations`, max 30 lines, MUST be 0)
- **Quality Check Status**: Pass/Fail (from tool response: `results.quality.status`, MUST be "passed")
- **Tool Response Parsed**: Yes/No (MUST be Yes)
- **Violations Found**: Count of violations found (must be 0)
- **Violations Fixed**: Count of violations fixed
- **Validation Results**:
  - Tool executed: Yes/No (MUST be Yes)
  - File size violations after fixes: Count (MUST be 0, parsed from tool response)
  - Function length violations after fixes: Count (MUST be 0, parsed from tool response)
  - Tool output parsed: Yes/No
- **Details**: Summary of any violations and their resolution
- **Commit Blocked**: Yes/No (blocked if any violations remain)
- **Fallback Used**: Yes/No (only if MCP tool was unavailable)

#### **4. Test Execution**

- **Status**: Success/Failure
- **Command Used**: `execute_pre_commit_checks(checks=["tests"], timeout=300, coverage_threshold=0.90)` MCP tool
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
  - Tests status: Pass/Fail (from tool response: `results.tests.status`, MUST be "passed")
  - Zero failures confirmed: Yes/No (parsed from tool response: `results.tests.tests_failed`, MUST be 0)
  - 100% pass rate confirmed: Yes/No (parsed from tool response: `results.tests.pass_rate`, MUST be 100.0)
  - Coverage threshold met: Yes/No (parsed from tool response: `results.tests.coverage`, MUST be ≥ 90.0%)
  - Coverage value extracted: Yes/No (exact percentage must be shown from tool response)
  - Integration tests passed: Yes/No (explicitly verified from tool response)
  - Tool output parsed: Yes/No
- **Details**: Complete summary from test execution tool response
- **Commit Blocked**: Yes/No (blocked if any validation fails, including coverage < 90.0%)
- **CRITICAL**: If coverage < 90.0%, commit MUST be blocked regardless of other results
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
- **Completed Plans Re-check**: Count of completed plans found in `.cursor/plans/` (must be 0)
- **Unarchived Plans**: List of any completed plans still in `.cursor/plans/` (must be empty)
- **Plan Archive Checked**: Count of files in `.cursor/plans/archive/`
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

#### **10. Roadmap Synchronization Validation**

- **Status**: Success/Failure/Skipped
- **Command File Available**: Whether validate-roadmap-sync.md exists
- **Roadmap TODOs Validated**: Count of TODOs checked in roadmap.md (if command executed)
- **Codebase TODOs Scanned**: Count of production TODOs found in Sources/ (if command executed)
- **Synchronization Issues**: Count of issues found (must be 0 if command executed)
- **Details**: Summary from validate-roadmap-sync command (if executed) or reason for skipping

#### **11. Submodule Handling**

- **Status**: Success/Failure/Skipped
- **Submodule Changes Detected**: Whether `.cortex/synapse` submodule had changes
- **Submodule Committed**: Whether submodule changes were committed
- **Submodule Pushed**: Whether submodule changes were pushed to remote
- **Submodule Commit Hash**: Git commit hash of submodule commit (if committed)
- **Parent Reference Updated**: Whether parent repository's submodule reference was updated
- **Details**: Summary of submodule operations performed

#### **12. Commit Creation**

- **Status**: Success/Failure
- **Commit Hash**: Git commit hash if successful
- **Commit Message**: The commit message used
- **Files Committed**: Count and list of files in the commit
- **Submodule Reference Updated**: Whether submodule reference was included in commit

#### **13. Push Branch**

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
- **Roadmap Sync Issues**: Any roadmap-codebase synchronization problems and their resolution
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

## Error/Violation Handling Strategy

**PRIMARY FOCUS**: When any error or violation is detected during the commit procedure, the agent's PRIMARY FOCUS must be to fix it immediately.

**After Fixing**:

1. **If sufficient free context remains**: Continue with the commit pipeline automatically
   - Re-run the validation check that detected the issue
   - Verify the fix resolved the issue
   - Proceed to the next step in the commit pipeline

2. **If free context is insufficient**: Stop the commit pipeline and provide:
   - **Comprehensive Changes Summary**: Document all fixes made, files modified, and changes applied
   - **Re-run Recommendation**: Advise the user to re-run the commit pipeline (`/commit` or equivalent)
   - **Status Report**: Clearly indicate which step was completed and which step should be executed next

**Context Assessment**: The agent should assess available context after each fix:

- Consider remaining token budget
- Consider complexity of remaining steps
- Consider number of additional fixes that may be needed
- If uncertain, err on the side of providing a summary and recommending re-run

## Failure Handling

### Code Quality Check Failure

- **Action**: **PRIMARY FOCUS** - Fix violations immediately, then assess context to continue or summarize
- **Process**:
  1. **IMMEDIATE FIX**: Report the specific code quality violation (file size or function length)
  2. Provide detailed error information including file path, function name, and violation details
  3. Parse MCP tool response or check output to extract exact violation counts and details
  4. **FIX**: Fix file size violations by splitting large files or extracting modules
  5. **FIX**: Fix function length violations by extracting helper functions or refactoring logic
  6. Re-run checks to verify fixes
  7. **VALIDATION**: Re-parse MCP tool response or check output to confirm zero violations remain
  8. **CONTEXT ASSESSMENT**: After fixing, assess if sufficient free context remains:
     - If YES: Continue with commit pipeline (re-run check, verify, proceed to next step)
     - If NO: Provide comprehensive changes summary and advise re-running commit pipeline
  9. **CRITICAL**: These checks match CI quality gate requirements - failures will cause CI to fail
- **No Partial Commits**: Do not proceed with commit until all code quality checks pass and validation confirms zero violations

### Test Suite Failure

- **Action**: **PRIMARY FOCUS** - Fix test failures immediately, then assess context to continue or summarize
- **Process**:
  1. **IMMEDIATE FIX**: Review test failure output from `run-tests` command
  2. Parse test output to extract exact failure counts, test names, and error messages
  3. Analyze test failure messages and stack traces
  4. Identify root cause (code issue vs test issue)
  5. **FIX**: Fix the underlying issues
  6. Re-run `run-tests` command to verify fixes
  7. **VALIDATION**: Re-parse test output to verify:
     - Zero test failures (failed count = 0)
     - 100% pass rate for executable tests
     - Coverage meets 90%+ threshold (MANDATORY - extract exact percentage and verify ≥ 90.0%)
     - All integration tests pass
  8. **CONTEXT ASSESSMENT**: After fixing, assess if sufficient free context remains:
     - If YES: Continue with commit pipeline (re-run tests, verify, proceed to next step)
     - If NO: Provide comprehensive changes summary and advise re-running commit pipeline
  9. Continue until all tests pass with 100% pass rate and all validations pass, including coverage ≥ 90.0%
- **No Partial Commits**: Do not proceed with commit until all tests pass and all validations confirm success
- **Coverage Enforcement**: Coverage threshold of 90% is absolute - if coverage < 90.0%, commit MUST be blocked
- **BLOCK COMMIT**: If any test validation fails, including coverage below 90.0%, do not proceed with commit

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

### Other Step Failures

- **Action**: **PRIMARY FOCUS** - Fix the failure immediately, then assess context to continue or summarize
- **Process**:
  1. **IMMEDIATE FIX**: Report the specific failure
  2. Provide detailed error information
  3. **FIX**: Fix the underlying issue
  4. **CONTEXT ASSESSMENT**: After fixing, assess if sufficient free context remains:
     - If YES: Continue with commit pipeline (re-run step, verify, proceed to next step)
     - If NO: Provide comprehensive changes summary and advise re-running commit pipeline
  5. Do not proceed with commit until all issues are fixed and validated

### General Rules

- **Error/Violation Priority**: When any error or violation is detected, **PRIMARY FOCUS** is to fix it immediately
- **Context-Aware Continuation**: After fixing errors/violations:
  - If sufficient free context remains: Continue automatically with commit pipeline
  - If free context is insufficient: Provide comprehensive changes summary and advise re-running commit pipeline
- **No Partial Commits**: All steps must pass before commit creation
- **Validation Required**: All critical steps MUST include explicit validation that confirms success (parsing output, checking exit codes, verifying counts)
- **Block on Validation Failure**: If any validation step fails, **BLOCK COMMIT** and do not proceed until fixed
- **Fix Issues First**: Resolve all issues before attempting commit again
- **Automatic Execution**: Once this command is explicitly invoked by the user, execute all steps automatically without asking for additional permission
- **Comprehensive Summary Format**: When advising re-run due to context limits, provide:
  - List of all fixes applied (errors fixed, violations resolved)
  - Files modified with brief description of changes
  - Current status (which step completed, which step to run next)
  - Clear instruction to re-run commit pipeline
- **Command Execution**: When referencing other Cursor commands, AI MUST immediately read those command files and execute ALL their steps without any user interaction
- **MCP Tools**: Use structured MCP tools instead of reading prompt files:
  - Step 0 (Fix Errors) MUST use `execute_pre_commit_checks(checks=["fix_errors"])` MCP tool
  - Step 4 (Testing) MUST use `execute_pre_commit_checks(checks=["tests"])` MCP tool
  - Step 4 (Memory Bank) MUST use `manage_file()` MCP tool for memory bank operations
  - Step 8 (Memory Bank Timestamp Validation) MUST use `validate(check_type="timestamps")` MCP tool
  - Step 9 (Roadmap Sync) MUST use `validate-roadmap-sync.md` command if it exists
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

- ✅ All compiler errors and warnings fixed (fix-errors step passes)
- ✅ **VALIDATION**: Zero errors AND zero warnings confirmed via type checker (if applicable) and linter re-checks after fix-errors
- ✅ All type errors and warnings resolved (if applicable)
- ✅ **VALIDATION**: Type checker reports zero type errors AND zero warnings (parsed from output, skip if not applicable)
- ✅ All formatting issues fixed
- ✅ Project formatter + import sorting (if applicable) formatting passes without errors
- ✅ **CRITICAL**: Formatter check MUST pass after formatting (verifies CI will pass)
- ✅ **VALIDATION**: Formatter check output confirms zero formatting violations
- ✅ Markdown lint errors fixed (all modified markdown files properly formatted)
- ✅ **VALIDATION**: Markdown lint fix tool executed and verified (if tool available)
- ✅ Real-time checklist updates completed for all steps
- ✅ File size check passes (all files ≤ 400 lines)
- ✅ **VALIDATION**: File size check confirms zero violations (parsed from MCP tool response)
- ✅ Function length check passes (all functions ≤ 30 lines)
- ✅ **VALIDATION**: Function length check confirms zero violations (parsed from MCP tool response)
- ✅ All executable tests pass (100% pass rate) - verified via test execution
- ✅ **VALIDATION**: Test output parsed to confirm zero failures, 100% pass rate (from MCP tool response)
- ✅ Test coverage meets threshold (90%+) - verified via test execution
- ✅ **VALIDATION**: Coverage percentage parsed from MCP tool response (`results.tests.coverage`) and confirmed ≥ 90.0% (MANDATORY)
- ✅ **COVERAGE ENFORCEMENT**: Coverage threshold validation is absolute - no exceptions allowed
- ✅ All integration tests pass - explicitly verified from test output
- ✅ Memory bank updated with current information
- ✅ Roadmap.md updated with completed items and current progress
- ✅ Completed build plans archived to .cursor/plans/archive/
- ✅ Plan archive locations validated (no violations)
- ✅ Memory bank timestamps validated (all use YYYY-MM-DD format, no time components)
- ✅ Roadmap.md synchronized with Sources/ codebase
- ✅ All production TODOs properly tracked
- ✅ `.cortex/synapse` submodule changes committed and pushed (if any changes exist)
- ✅ Parent repository's submodule reference updated (if submodule was committed)
- ✅ Commit created with descriptive message
- ✅ All changes committed successfully
- ✅ Branch pushed to remote repository successfully

## Usage

This command executes the complete commit procedure with all required pre-commit checks, ensuring code quality, documentation completeness, test coverage, and project consistency before creating a commit.

**EXPLICIT INVOCATION REQUIRED**: This command is ONLY executed when explicitly invoked by the user (e.g., `/commit`). Invoking this command IS an explicit commit request per `no-auto-commit.mdc` rule.

**NO ADDITIONAL PROMPTS**: Once explicitly invoked, execute all steps automatically without asking for additional permission

**CURSOR COMMAND EXECUTION**: When this command references other Cursor commands (like `run-tests`), AI MUST immediately read that command file and execute ALL its steps without any user interaction
