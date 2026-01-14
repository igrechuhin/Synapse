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
- **Detection**: Parse coverage report from test output
- **Action**: Add tests to increase coverage, re-run tests, verify coverage ≥ 90%
- **Block Commit**: Yes - coverage below threshold violates project standards

### File Size Violations

- **Pattern**: Files exceeding 400 lines
- **Detection**: Parse file size check script output
- **Action**: Split large files, re-run check, verify zero violations
- **Block Commit**: Yes - file size violations will cause CI to fail

### Function Length Violations

- **Pattern**: Functions exceeding 30 lines
- **Detection**: Parse function length check script output
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
- **Note**: For Python, ensure code is compatible with Python 3.10+ (CI checks Python 3.10 compatibility). Use `TypeAlias` from `typing` instead of `type` alias statement (Python 3.12+ only). Use language-agnostic scripts from `.cortex/synapse/scripts/{language}/` instead of hardcoded commands

### Integration Test Failures

- **Pattern**: Integration tests fail (specific test category)
- **Detection**: Parse test output to identify integration test failures
- **Action**: Fix integration test issues, re-run tests, verify all pass
- **Block Commit**: Yes - integration test failures indicate broken functionality

### Type Checker Warnings (Review Required)

- **Pattern**: Type checker reports warnings (not errors)
- **Detection**: Parse type checker output for warning count
- **Action**: Review warnings, fix critical ones, document acceptable warnings
- **Block Commit**: No - warnings don't block commit but should be reviewed
- **Note**: Only applicable if project uses a type system

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
   - **VALIDATION**: Parse tool response to verify:
     - `total_errors` = 0 (MUST be zero)
     - `results.fix_errors.success` = true
     - **BLOCK COMMIT** if any errors remain after fix-errors step
   - **CRITICAL**: After fix-errors, run linter check script in check-only mode to verify all linting issues are resolved
     - Execute language-specific linting check script: `.cortex/synapse/scripts/{language}/check_linting.py` (or equivalent for non-Python)
     - The script runs linter in check-only mode (without --fix flag) to catch non-fixable errors
     - Scripts auto-detect directories (src/, tests/, .cortex/synapse/scripts/) matching CI workflow
     - **CRITICAL**: If linter check fails, fix remaining issues and re-run fix-errors until check passes
     - **MANDATORY**: Linter check MUST pass before proceeding to next step
     - **VALIDATION**: Parse linter check output to verify zero errors - **BLOCK COMMIT** if any linting errors remain
     - **Note**: The fix-errors step runs linter with --fix which fixes auto-fixable issues, but some errors (like syntax errors, undefined names, Python version compatibility) cannot be auto-fixed and must be manually resolved

1. **Code formatting** - Run project formatter:
   - Execute language-specific formatting script: `.cortex/synapse/scripts/{language}/format_code.py` (or equivalent)
   - The script should run the project formatter and import sorting tools
   - Scripts auto-detect directories (src/, tests/, .cortex/synapse/scripts/) matching CI workflow
   - **CRITICAL**: After formatting, run formatter check script to verify all files pass formatting check
     - Execute language-specific formatter check script: `.cortex/synapse/scripts/{language}/check_formatting.py` (or equivalent)
     - If script doesn't exist, run formatter in check-only mode manually (e.g., `black --check` for Python)
     - Scripts auto-detect directories matching CI workflow
   - **CRITICAL**: If formatter check fails, re-run formatter and verify again until check passes
   - Verify formatting completes successfully with no errors or warnings
   - Fix any formatting issues if they occur
   - Verify no files were left in inconsistent state
   - **MANDATORY**: Formatter check MUST pass before proceeding to next step
   - **VALIDATION**: Parse formatter check output to verify zero violations - **BLOCK COMMIT** if any violations remain
2. **Type checking** - Run type checker (if applicable):
   - **Conditional**: Only execute if project uses a type system (Python with type hints, TypeScript, etc.)
   - Execute language-specific type checker script: `.cortex/synapse/scripts/{language}/check_types.py` (or equivalent)
   - If script doesn't exist, run type checker manually (e.g., `pyright src/` for Python - matches CI which only checks src/, not tests/)
   - Scripts auto-detect directories matching CI workflow
   - **CRITICAL**: Capture and parse type checker output to verify zero errors
   - **VALIDATION**: Verify type checking completes with zero errors (warnings are acceptable but should be reviewed)
   - **BLOCK COMMIT** if type checker reports any type errors (not warnings)
   - Fix any critical type errors before proceeding
   - Re-run type checker after fixes to verify zero errors remain
   - **Skip if**: Project does not use a type system
3. **Code quality checks** - Run file size and function/method length checks:
   - Execute language-specific code quality check scripts:
     - File size check: `.cortex/synapse/scripts/{language}/check_file_sizes.py` (or equivalent)
     - Function length check: `.cortex/synapse/scripts/{language}/check_function_lengths.py` (or equivalent)
   - Verify all files are within project's line limit (typically 400 lines)
   - **VALIDATION**: Parse check output to verify zero violations - **BLOCK COMMIT** if any files exceed limit
   - Verify all functions/methods are within project's length limit (typically 30 lines)
   - **VALIDATION**: Parse check output to verify zero violations - **BLOCK COMMIT** if any functions/methods exceed limit
   - Verify both checks complete successfully with no violations
   - Fix any file size or function/method length violations before proceeding
   - Re-run checks after fixes to verify zero violations remain
   - Note: These checks match CI quality gate requirements and MUST pass
   - Note: Scripts are located in `.cortex/synapse/scripts/{language}/` and are shared across projects using the same Synapse repository
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
     - `results.tests.coverage` ≥ 0.90 (MUST meet threshold)
     - **BLOCK COMMIT** if any of the above validations fail
   - If tests fail, fix issues and re-run tool until all pass
   - Re-verify all validation criteria after fixes
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
   - Check `.cursor/plans/` directory for completed plan files
   - Use standard tools (`mv` or equivalent) to move completed plans to `.cursor/plans/archive/` directory
   - Create `.cursor/plans/archive/` directory with standard tools if it doesn't exist
   - Update plan status to "archived" if not already done
   - Ensure no active plans remain in the plans directory
   - **CRITICAL**: Plan files MUST be archived in `.cursor/plans/archive/`, never in `.cursor/plans/archive/`
8. **Validate archive locations** - Validate that all archived files are in correct locations:
   - Check `.cursor/plans/archive/` directory - should contain plan files only
   - Validate that plan files are archived in `.cursor/plans/archive/`
   - Report any plan files found outside `.cursor/plans/archive/` and require manual correction
   - Block commit if archive location violations are found
9. **Optimize memory bank** - Execute Cursor command: `validate-memory-bank-timestamps` (if available):
   - Check if `.cortex/synapse/prompts/validate-memory-bank-timestamps.md` exists
   - If file exists:
     - Read `.cortex/synapse/prompts/validate-memory-bank-timestamps.md`
     - Execute ALL steps from that command automatically
     - Validate timestamp format and optimize memory bank
     - Ensure all timestamps use YY-MM-DD format (no HH-mm)
   - If file does not exist:
     - Skip this step (command file not available)
     - Note: Memory bank optimization can be done manually if needed
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

11. **Submodule handling** - Commit and push `.cortex/synapse` submodule changes if any:

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
2. **Type Checking** - Validates type safety with type checker (if applicable)
   - **CRITICAL**: Must pass with zero type errors before proceeding (skip if project doesn't use types)
   - **VALIDATION**: Type checker MUST report zero errors - **BLOCK COMMIT** if type errors exist
3. **Code Quality Checks** - Validates file size and function/method length limits (matches CI quality gate)
   - **CRITICAL**: Must pass before testing to ensure code meets quality standards
   - **VALIDATION**: Both checks MUST show zero violations - **BLOCK COMMIT** if violations exist
4. **Testing** (Run Tests) - Executes `run-tests.md` command to ensure functionality correctness
   - **CRITICAL**: Reuses `run-tests.md` command (DRY principle) - do not duplicate test logic
   - **CRITICAL**: Runs AFTER errors, formatting, and code quality are fixed
   - **CRITICAL**: Tests must pass with 100% pass rate before proceeding
   - **VALIDATION**: Must verify zero test failures, 100% pass rate, 90%+ coverage (if applicable), all integration tests pass
   - **BLOCK COMMIT** if any test validation fails
5. **Documentation** (Memory Bank) - Updates project context
6. **Roadmap Updates** (Roadmap Update) - Ensures roadmap reflects current progress
7. **Plan Archiving** (Archive Completed Plans) - Cleans up completed build plans
8. **Archive Validation** (Validate Archive Locations) - Ensures archived files are in correct locations
9. **Optimization** (Memory Bank Validation) - Validates and optimizes memory bank
10. **Roadmap Sync** (Roadmap-Codebase Synchronization) - Ensures roadmap.md matches Sources/ codebase
11. **Submodule Handling** - Commits and pushes `.cortex/synapse` submodule changes if any
12. **Commit** - Creates the commit with all changes (including updated submodule reference)
13. **Push** - Pushes committed changes to remote repository

**MCP Tools**: Steps 0 (Fix Errors) and 4 (Testing) use the `execute_pre_commit_checks()` MCP tool instead of reading prompt files. This provides structured parameters, type safety, and consistent error handling.

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
- [ ] **Linter Check Validation**: Linter check (without --fix) = 0 errors (parsed from output, CRITICAL - catches non-fixable errors)
- [ ] **Formatting Validation**: Formatter check = 0 violations (parsed from output)
- [ ] **Type Checking Validation**: Type checker = 0 type errors (parsed from output, skip if not applicable)
- [ ] **Code Quality Validation**: File size = 0 violations, Function length = 0 violations (parsed from script output)
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
- Step 2: Code Quality Checks
- Step 3: Test Execution
- Step 4: Memory Bank Update
- Step 5: Roadmap Update
- Step 6: Plan Archiving
- Step 7: Archive Validation
- Step 8: Memory Bank Optimization
- Step 9: Roadmap Synchronization Validation
- Step 10: Submodule Handling
- Step 11: Commit Creation
- Step 12: Push Branch

#### **0. Fix Errors**

- **Status**: Success/Failure
- **Errors Fixed**: Count and list of errors fixed
- **Warnings Fixed**: Count and list of warnings fixed
- **Formatting Issues Fixed**: Count and list of formatting issues fixed
- **Type Errors Fixed**: Count and list of type errors fixed
- **Files Modified**: List of files modified during error fixing
- **Details**: Summary from fix-errors command
- **Validation Results**:
  - Type checker re-check: Pass/Fail with error count (MUST be 0, skip if not applicable)
  - Linter re-check (after fix): Pass/Fail with error count (MUST be 0)
  - Linter check (without --fix): Pass/Fail with error count (MUST be 0, CRITICAL - catches non-fixable errors)
- **Commit Blocked**: Yes/No (blocked if any errors remain)

#### **1. Formatting**

- **Status**: Success/Failure
- **Files Formatted**: Count of files formatted
- **Formatter Check Status**: Pass/Fail (MUST pass - verified with formatter check command)
- **Formatter Check Output**: Output from formatter check command
- **Errors**: Any formatting errors encountered
- **Warnings**: Any formatting warnings
- **Verification**: Confirmation that formatter check passed before proceeding

#### **2. Code Quality Checks**

- **Status**: Success/Failure
- **File Size Check**: Status of file size validation (max 400 lines)
- **Function Length Check**: Status of function length validation (max 30 lines)
- **Violations Found**: Count of violations found (must be 0)
- **Violations Fixed**: Count of violations fixed
- **Validation Results**:
  - File size violations after fixes: Count (MUST be 0)
  - Function length violations after fixes: Count (MUST be 0)
  - Script output parsed: Yes/No
- **Details**: Summary of any violations and their resolution
- **Commit Blocked**: Yes/No (blocked if any violations remain)

#### **3. Test Execution**

- **Status**: Success/Failure
- **Command Used**: `run-tests` (reused from `.cortex/synapse/prompts/run-tests.md`)
- **Tests Executed**: Count of tests executed
- **Tests Passed**: Count of passing tests
- **Tests Failed**: Count of failing tests (must be 0)
- **Pass Rate**: Percentage pass rate (target: 100%)
- **Coverage**: Test coverage percentage (target: 90%+)
- **Validation Results**:
  - Zero failures confirmed: Yes/No (parsed from test output)
  - 100% pass rate confirmed: Yes/No (calculated from test output)
  - Coverage threshold met: Yes/No (coverage ≥ 90% confirmed)
  - Integration tests passed: Yes/No (explicitly verified)
  - Test output parsed: Yes/No
- **Details**: Complete summary from run-tests command (see run-tests.md output format)
- **Commit Blocked**: Yes/No (blocked if any validation fails)
- **Note**: This step reuses `run-tests.md` command to avoid duplication (DRY principle)

#### **4. Memory Bank Update**

- **Status**: Success/Failure/Skipped
- **Command File Available**: Whether update-memory-bank.md exists
- **Files Updated**: List of memory bank files updated (if command executed)
- **Entries Added**: Count of new entries added (if command executed)
- **Details**: Summary from update-memory-bank command (if executed) or reason for skipping

#### **5. Roadmap Update**

- **Status**: Success/Failure
- **Items Marked Complete**: Count of completed milestones/tasks marked in roadmap.md
- **New Items Added**: Count of new roadmap items added
- **Status Updates**: Summary of progress indicator updates
- **Details**: Summary of roadmap changes made

#### **6. Plan Archiving**

- **Status**: Success/Failure
- **Plans Archived**: Count of plans moved to archive directory
- **Plans Processed**: Count of plan files checked
- **Archive Directory**: Location where plans were archived
- **Details**: Summary of plan archiving operations

#### **7. Archive Location Validation**

- **Status**: Success/Failure
- **Plan Archive Checked**: Count of files in `.cursor/plans/archive/`
- **Violations Found**: Count of plan files outside `.cursor/plans/archive/` (must be 0)
- **Violations List**: List of any plan files in wrong locations
- **Details**: Summary of archive location validation results

#### **8. Memory Bank Optimization**

- **Status**: Success/Failure/Skipped
- **Command File Available**: Whether validate-memory-bank-timestamps.md exists
- **Timestamp Validation**: Status of timestamp format validation (if command executed)
- **Optimization**: Summary of optimization performed (if command executed)
- **Details**: Summary from validate-memory-bank-timestamps command (if executed) or reason for skipping

#### **9. Roadmap Synchronization Validation**

- **Status**: Success/Failure/Skipped
- **Command File Available**: Whether validate-roadmap-sync.md exists
- **Roadmap TODOs Validated**: Count of TODOs checked in roadmap.md (if command executed)
- **Codebase TODOs Scanned**: Count of production TODOs found in Sources/ (if command executed)
- **Synchronization Issues**: Count of issues found (must be 0 if command executed)
- **Details**: Summary from validate-roadmap-sync command (if executed) or reason for skipping

#### **10. Submodule Handling**

- **Status**: Success/Failure/Skipped
- **Submodule Changes Detected**: Whether `.cortex/synapse` submodule had changes
- **Submodule Committed**: Whether submodule changes were committed
- **Submodule Pushed**: Whether submodule changes were pushed to remote
- **Submodule Commit Hash**: Git commit hash of submodule commit (if committed)
- **Parent Reference Updated**: Whether parent repository's submodule reference was updated
- **Details**: Summary of submodule operations performed

#### **11. Commit Creation**

- **Status**: Success/Failure
- **Commit Hash**: Git commit hash if successful
- **Commit Message**: The commit message used
- **Files Committed**: Count and list of files in the commit
- **Submodule Reference Updated**: Whether submodule reference was included in commit

#### **12. Push Branch**

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

## Failure Handling

### Code Quality Check Failure

- **Action**: Report the issue and block commit if violations found
- **Process**:
  1. Report the specific code quality violation (file size or function length)
  2. Provide detailed error information including file path, function name, and violation details
  3. Parse script output to extract exact violation counts and details
  4. Fix file size violations by splitting large files or extracting modules
  5. Fix function length violations by extracting helper functions or refactoring logic
  6. Re-run checks to verify fixes
  7. **VALIDATION**: Re-parse script output to confirm zero violations remain
  8. Do not proceed with commit until all checks pass and validation confirms zero violations
  9. **CRITICAL**: These checks match CI quality gate requirements - failures will cause CI to fail
- **No Partial Commits**: Do not proceed with commit until all code quality checks pass and validation confirms zero violations

### Test Suite Failure

- **Action**: Investigate and fix issues before proceeding
- **Process**:
  1. Review test failure output from `run-tests` command
  2. Parse test output to extract exact failure counts, test names, and error messages
  3. Analyze test failure messages and stack traces
  4. Identify root cause (code issue vs test issue)
  5. Fix the underlying issues
  6. Re-run `run-tests` command to verify fixes
  7. **VALIDATION**: Re-parse test output to verify:
     - Zero test failures (failed count = 0)
     - 100% pass rate for executable tests
     - Coverage meets 90%+ threshold
     - All integration tests pass
  8. Continue until all tests pass with 100% pass rate and all validations pass
- **No Partial Commits**: Do not proceed with commit until all tests pass and all validations confirm success
- **Reuse Command**: Always use `run-tests.md` command, do not duplicate test execution logic
- **BLOCK COMMIT**: If any test validation fails, do not proceed with commit

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

- **Action**: Stop immediately and surface the issue
- **Process**:
  1. Report the specific failure
  2. Provide detailed error information
  3. Do not proceed with commit
  4. Fix issues first before attempting commit again

### General Rules

- **No Partial Commits**: All steps must pass before commit creation
- **Validation Required**: All critical steps MUST include explicit validation that confirms success (parsing output, checking exit codes, verifying counts)
- **Block on Validation Failure**: If any validation step fails, **BLOCK COMMIT** and do not proceed
- **Fix Issues First**: Resolve all issues before attempting commit again
- **Automatic Execution**: Once this command is explicitly invoked by the user, execute all steps automatically without asking for additional permission
- **Command Execution**: When referencing other Cursor commands, AI MUST immediately read those command files and execute ALL their steps without any user interaction
- **MCP Tools**: Use structured MCP tools instead of reading prompt files:
  - Step 0 (Fix Errors) MUST use `execute_pre_commit_checks(checks=["fix_errors"])` MCP tool
  - Step 4 (Testing) MUST use `execute_pre_commit_checks(checks=["tests"])` MCP tool
  - Step 4 (Memory Bank) MUST use `manage_file()` MCP tool for memory bank operations
  - Step 8 (Memory Bank Optimization) MUST use `validate-memory-bank-timestamps.md` command if it exists
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
- ✅ **VALIDATION**: Zero errors confirmed via type checker (if applicable) and linter re-checks after fix-errors
- ✅ All type errors resolved (if applicable)
- ✅ **VALIDATION**: Type checker reports zero type errors (parsed from output, skip if not applicable)
- ✅ All formatting issues fixed
- ✅ Project formatter + import sorting (if applicable) formatting passes without errors
- ✅ **CRITICAL**: Formatter check MUST pass after formatting (verifies CI will pass)
- ✅ **VALIDATION**: Formatter check output confirms zero formatting violations
- ✅ Real-time checklist updates completed for all steps
- ✅ File size check passes (all files ≤ 400 lines)
- ✅ **VALIDATION**: File size check script output confirms zero violations
- ✅ Function length check passes (all functions ≤ 30 lines)
- ✅ **VALIDATION**: Function length check script output confirms zero violations
- ✅ All executable tests pass (100% pass rate) - verified via `run-tests.md` command
- ✅ **VALIDATION**: Test output parsed to confirm zero failures, 100% pass rate
- ✅ Test coverage meets threshold (90%+) - verified via `run-tests.md` command
- ✅ **VALIDATION**: Coverage percentage parsed from test output and confirmed ≥ 90%
- ✅ All integration tests pass - explicitly verified from test output
- ✅ Memory bank updated with current information
- ✅ Roadmap.md updated with completed items and current progress
- ✅ Completed build plans archived to .cursor/plans/archive/
- ✅ Plan archive locations validated (no violations)
- ✅ Memory bank optimized and validated
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
