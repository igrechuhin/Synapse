# Commit Changes

**AI EXECUTION COMMAND**: Execute the mandatory commit procedure with all required pre-commit checks, including testing of all runnable project tests.

**CRITICAL**: This command is ONLY executed when explicitly invoked by the user (e.g., `/commit` or user explicitly requests commit). Invoking this command IS an explicit commit request per `no-auto-commit.mdc` rule. Once invoked, execute all steps AUTOMATICALLY without asking for additional permission or confirmation.

**CURSOR COMMANDS**: The commands referenced below (like `run-tests`, etc.) are Cursor commands located in `.cortex/synapse/prompts/` directory. AI MUST read each referenced command file and execute ALL its steps AUTOMATICALLY without asking user permission.

## ⚠️ MANDATORY PRE-ACTION CHECKLIST

**BEFORE executing this command, you MUST:**

1. ✅ **Read relevant memory bank files** - Understand current project context:
   - Read `.cursor/memory-bank/activeContext.md` to understand current work focus
   - Read `.cursor/memory-bank/progress.md` to see recent achievements
   - Read `.cursor/memory-bank/roadmap.md` to understand project priorities

1. ✅ **Read relevant rules** - Understand commit requirements:
   - Read `.cursor/rules/no-auto-commit.mdc` for commit procedure requirements
   - Read `.cursor/rules/coding-standards.mdc` and `.cursor/rules/python-coding-standards.mdc` for code quality standards
   - Read `.cursor/rules/memory-bank-workflow.mdc` for memory bank update requirements

1. ✅ **Read referenced command files** - Understand all sub-commands:
   - Read `.cortex/synapse/prompts/fix-errors.md` before executing it (CRITICAL: Must run before testing)
   - Read `.cortex/synapse/prompts/run-tests.md` before executing it
   - Read `.cortex/synapse/prompts/update-memory-bank.md` before executing it
   - Read `.cortex/synapse/prompts/validate-memory-bank-timestamps.md` before executing it
   - Read `.cortex/synapse/prompts/validate-roadmap-sync.md` before executing it

1. ✅ **Verify prerequisites** - Ensure all prerequisites are met:
   - Confirm there are changes to commit
   - Verify build system is accessible
   - Check that test suite can be executed

**VIOLATION**: Executing this command without following this checklist is a CRITICAL violation that blocks proper commit procedure.

## Steps

0. **Fix errors and warnings (Python)** - Execute Cursor command: `fix-errors`:
   - Read `.cortex/synapse/prompts/fix-errors.md`
   - Execute ALL steps from that command automatically
   - Fix all compiler errors, type errors, formatting issues, and warnings
   - Verify all fixes are applied and code is error-free
   - **CRITICAL**: This step MUST run before testing to ensure code contains no errors
   - **CRITICAL**: This prevents committing/pushing poor code that would fail CI checks

1. **Code formatting (Python)** - Run Black and isort:
   - Execute `./.venv/bin/black .` and `./.venv/bin/ruff check --fix --select I .`
   - **CRITICAL**: After formatting, run `./.venv/bin/black --check .` to verify all files pass Black check
   - **CRITICAL**: If `black --check` fails, re-run `black .` and verify again until check passes
   - Verify formatting completes successfully with no errors or warnings
   - Fix any formatting issues if they occur
   - Verify no files were left in inconsistent state
   - **MANDATORY**: Black check MUST pass before proceeding to next step
2. **Type checking (Python)** - Run Pyright type checker:
   - Execute `.venv/bin/pyright src/ tests/` or `python -m pyright src/ tests/`
   - Verify type checking completes with zero errors (warnings are acceptable but should be reviewed)
   - Fix any critical type errors before proceeding
   - Note: Pyright is required for type safety validation
3. **Code quality checks (Python)** - Run file size and function length checks:
   - Execute `./.venv/bin/python .cortex/synapse/scripts/python/check_file_sizes.py` to verify all files are within 400 line limit
   - Execute `./.venv/bin/python .cortex/synapse/scripts/python/check_function_lengths.py` to verify all functions are within 30 line limit
   - Verify both checks complete successfully with no violations
   - Fix any file size or function length violations before proceeding
   - Note: These checks match CI quality gate requirements and MUST pass
   - Note: Scripts are located in `.cortex/synapse/scripts/python/` and are shared across projects using the same Synapse repository
4. **Test execution (Python)** - Execute Cursor command: `run-tests`:
   - Read `.cortex/synapse/prompts/run-tests.md`
   - Execute ALL steps from that command automatically
   - **CRITICAL**: This step runs AFTER errors, formatting, and code quality checks are fixed
   - **CRITICAL**: Tests must pass with 100% pass rate before proceeding to commit
   - If tests fail, fix issues and re-run `run-tests` command until all pass
   - **DRY Principle**: Reuse `run-tests.md` command instead of duplicating test execution logic
5. **Memory bank operations** - Execute Cursor command: `update-memory-bank`:
   - Read `.cortex/synapse/prompts/update-memory-bank.md`
   - Execute ALL steps from that command automatically
   - Update all relevant memory bank files with current changes
6. **Update roadmap** - Update roadmap.md with completed items and new milestones:
   - Review recent changes and completed work
   - Mark completed milestones and tasks in roadmap.md
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
9. **Optimize memory bank** - Execute Cursor command: `validate-memory-bank-timestamps`:
   - Read `.cortex/synapse/prompts/validate-memory-bank-timestamps.md`
   - Execute ALL steps from that command automatically
   - Validate timestamp format and optimize memory bank
   - Ensure all timestamps use YY-MM-DD format (no HH-mm)
10. **Roadmap synchronization validation** - Execute Cursor command: `validate-roadmap-sync`:
   - Read `.cortex/synapse/prompts/validate-roadmap-sync.md`
   - Execute ALL steps from that command automatically
   - Validate roadmap.md is synchronized with Sources/ directory
   - Ensure all production TODOs are properly tracked
   - Verify line numbers and file references are accurate
11. **Submodule handling** - Commit and push `.cortex/synapse` submodule changes if any:
   - Check if `.cortex/synapse` submodule has uncommitted changes using `git -C .cortex/synapse status --porcelain`
   - If submodule has changes:
     - Stage all changes in the submodule using `git -C .cortex/synapse add .`
     - Create commit in submodule with descriptive message (use same message format as main commit or append " [synapse submodule]")
     - Push submodule changes to remote using `git -C .cortex/synapse push`
     - Verify submodule push completes successfully
     - Update parent repository's submodule reference using `git add .cortex/synapse`
     - Note: This stages the updated submodule reference for the main commit

12. **Commit creation** - Create commit with descriptive message:

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
1. **Formatting** - Ensures code style consistency with Black and ruff import sorting
   - **CRITICAL**: Must verify with `black --check` after formatting to ensure CI will pass
2. **Code Quality Checks** - Validates file size and function length limits (matches CI quality gate)
   - **CRITICAL**: Must pass before testing to ensure code meets quality standards
3. **Testing** (Run Tests) - Executes `run-tests.md` command to ensure functionality correctness
   - **CRITICAL**: Reuses `run-tests.md` command (DRY principle) - do not duplicate test logic
   - **CRITICAL**: Runs AFTER errors, formatting, and code quality are fixed
   - **CRITICAL**: Tests must pass with 100% pass rate before proceeding
4. **Documentation** (Memory Bank) - Updates project context
5. **Roadmap Updates** (Roadmap Update) - Ensures roadmap reflects current progress
6. **Plan Archiving** (Archive Completed Plans) - Cleans up completed build plans
7. **Archive Validation** (Validate Archive Locations) - Ensures archived files are in correct locations
8. **Optimization** (Memory Bank Validation) - Validates and optimizes memory bank
9. **Roadmap Sync** (Roadmap-Codebase Synchronization) - Ensures roadmap.md matches Sources/ codebase
10. **Submodule Handling** - Commits and pushes `.cortex/synapse` submodule changes if any
11. **Commit** - Creates the commit with all changes (including updated submodule reference)
12. **Push** - Pushes committed changes to remote repository

**DRY Principle**: Step 3 (Testing) reuses the `run-tests.md` command instead of duplicating test execution logic. This ensures consistency and maintainability.

## ⚠️ MANDATORY CHECKLIST UPDATES

**CRITICAL**: The AI MUST update the todo checklist in real-time as each step completes:
- Mark each step as `completed` immediately after it finishes successfully
- Mark steps as `in_progress` when starting them
- Update status immediately, not at the end
- This provides transparency and allows tracking progress during execution

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

#### **1. Formatting**

- **Status**: Success/Failure
- **Files Formatted**: Count of files formatted
- **Black Check Status**: Pass/Fail (MUST pass - verified with `black --check`)
- **Black Check Output**: Output from `black --check` command
- **Errors**: Any formatting errors encountered
- **Warnings**: Any formatting warnings
- **Verification**: Confirmation that `black --check` passed before proceeding

#### **2. Code Quality Checks**

- **Status**: Success/Failure
- **File Size Check**: Status of file size validation (max 400 lines)
- **Function Length Check**: Status of function length validation (max 30 lines)
- **Violations Found**: Count of violations found (must be 0)
- **Violations Fixed**: Count of violations fixed
- **Details**: Summary of any violations and their resolution

#### **3. Test Execution**

- **Status**: Success/Failure
- **Command Used**: `run-tests` (reused from `.cortex/synapse/prompts/run-tests.md`)
- **Tests Executed**: Count of tests executed
- **Tests Passed**: Count of passing tests
- **Tests Failed**: Count of failing tests (must be 0)
- **Pass Rate**: Percentage pass rate (target: 100%)
- **Coverage**: Test coverage percentage (target: 90%+)
- **Details**: Complete summary from run-tests command (see run-tests.md output format)
- **Note**: This step reuses `run-tests.md` command to avoid duplication (DRY principle)

#### **4. Memory Bank Update**

- **Status**: Success/Failure
- **Files Updated**: List of memory bank files updated
- **Entries Added**: Count of new entries added
- **Details**: Summary from update-memory-bank command

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

- **Status**: Success/Failure
- **Timestamp Validation**: Status of timestamp format validation
- **Optimization**: Summary of optimization performed
- **Details**: Summary from validate-memory-bank-timestamps command

#### **9. Roadmap Synchronization Validation**

- **Status**: Success/Failure
- **Roadmap TODOs Validated**: Count of TODOs checked in roadmap.md
- **Codebase TODOs Scanned**: Count of production TODOs found in Sources/
- **Synchronization Issues**: Count of issues found (must be 0)
- **Details**: Summary from validate-roadmap-sync command

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
  - **CRITICAL**: If `black --check` fails after formatting, this indicates files were not properly formatted
  - Must re-run `black .` and verify `black --check` passes before proceeding
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
  3. Fix file size violations by splitting large files or extracting modules
  4. Fix function length violations by extracting helper functions or refactoring logic
  5. Re-run checks to verify fixes
  6. Do not proceed with commit until all checks pass
  7. **CRITICAL**: These checks match CI quality gate requirements - failures will cause CI to fail
- **No Partial Commits**: Do not proceed with commit until all code quality checks pass

### Test Suite Failure

- **Action**: Investigate and fix issues before proceeding
- **Process**:
  1. Review test failure output from `run-tests` command
  2. Analyze test failure messages and stack traces
  3. Identify root cause (code issue vs test issue)
  4. Fix the underlying issues
  5. Re-run `run-tests` command to verify fixes
  6. Continue until all tests pass with 100% pass rate
- **No Partial Commits**: Do not proceed with commit until all tests pass
- **Reuse Command**: Always use `run-tests.md` command, do not duplicate test execution logic

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
- **Fix Issues First**: Resolve all issues before attempting commit again
- **Automatic Execution**: Once this command is explicitly invoked by the user, execute all steps automatically without asking for additional permission
- **Command Execution**: When referencing other Cursor commands, AI MUST immediately read those command files and execute ALL their steps without any user interaction
- **DRY Principle**: Reuse existing commands instead of duplicating logic:
  - Step 3 (Testing) MUST use `run-tests.md` command - do not duplicate test execution logic
  - Step 0 (Fix Errors) MUST use `fix-errors.md` command - do not duplicate error fixing logic
  - Step 4 (Memory Bank) MUST use `update-memory-bank.md` command - do not duplicate memory bank update logic
  - This ensures consistency, maintainability, and single source of truth
- **Real-Time Checklist Updates**: AI MUST update the todo checklist immediately as each step completes:
  - Use `todo_write` tool to mark steps as `completed` right after they finish
  - Mark steps as `in_progress` when starting them
  - Update status in real-time, not at the end
  - This provides transparency and progress tracking during execution

## Success Criteria

- ✅ All compiler errors and warnings fixed (fix-errors step passes)
- ✅ All type errors resolved
- ✅ All formatting issues fixed
- ✅ Black + ruff import sorting formatting passes without errors
- ✅ **CRITICAL**: `black --check .` MUST pass after formatting (verifies CI will pass)
- ✅ Real-time checklist updates completed for all steps
- ✅ File size check passes (all files ≤ 400 lines)
- ✅ Function length check passes (all functions ≤ 30 lines)
- ✅ All executable tests pass (100% pass rate) - verified via `run-tests.md` command
- ✅ Test coverage meets threshold (90%+) - verified via `run-tests.md` command
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
