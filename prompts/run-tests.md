# Run Tests

**AI EXECUTION COMMAND**: Execute build and test suite with pytest-timeout protection to detect and handle hangs.

**CRITICAL**: These steps are for the AI to execute AUTOMATICALLY. DO NOT ask the user for permission or confirmation. Execute immediately.

**CURSOR COMMAND**: This is a Cursor command located in `.cortex/synapse/prompts/` directory, NOT a terminal command.

**Tooling Note**: Use standard Cursor tools (`Read`, `ApplyPatch`, `LS`, `Glob`, `Grep`) by default; MCP filesystem tools are optional fallbacks only when standard tools are unavailable or explicitly requested.

**Lint Note**: When using `read_lints`, pass absolute file paths to avoid path resolution errors during lint checks.

## ⚠️ MANDATORY PRE-ACTION CHECKLIST

**BEFORE executing this command, you MUST:**

1. ✅ **Read relevant memory bank files** - Understand current project context:
   - Read `.cursor/memory-bank/activeContext.md` to understand current work focus
   - Read `.cursor/memory-bank/progress.md` to see recent test-related achievements
   - Read `.cursor/memory-bank/techContext.md` to understand test environment

2. ✅ **Read relevant rules** - Understand testing requirements:
   - Read `.cursor/rules/testing-standards.mdc` for testing requirements
   - Read `.cursor/rules/no-test-skipping.mdc` for test skipping rules
   - Read `.cursor/rules/coding-standards.mdc` for code quality standards

3. ✅ **Verify prerequisites** - Ensure all prerequisites are met:
   - Confirm build system is accessible
   - Verify test suite can be executed
   - Ensure `python` resolves to the project virtualenv (prefer `.venv/bin/python` or set `PATH` accordingly) so pytest is available
   - Check that test environment is ready
   - Verify pytest-timeout plugin is installed and available
   - Check that pytest-timeout is configured in pytest.ini

**VIOLATION**: Executing this command without following this checklist is a CRITICAL violation that blocks proper test execution.

## Steps

1. **Build verification with hang detection** - Python import/build sanity check with pytest-timeout protection:
   - Execute `.venv/bin/pytest --maxfail=1 --collect-only --session-timeout=180` (180-second session timeout prevents hangs during collection)
   - Capture build/collection output for analysis
   - Record execution time
   - Detect if collection hangs and terminate automatically via pytest-timeout
   - Verify collection completes with no errors or warnings
2. **Test coverage verification** - Check that all new/updated functionality has comprehensive test coverage:
   - Identify all modified source files
   - Verify corresponding test files exist
   - Check that new public APIs have test coverage
   - Verify critical business logic has tests
   - Ensure edge cases are covered
3. **Test suite execution with hang protection** - Run tests with pytest-timeout control:
   - Execute `.venv/bin/pytest -q --session-timeout=300` (300-second session timeout prevents test suite hangs, per-test timeout of 10s from pytest.ini)
   - Capture full test output for analysis
   - Record execution time
   - Note any tests that are skipped
   - Detect and handle test hangs automatically via pytest-timeout (signal-based termination)
4. **Pass rate verification** - Ensure 100% pass rate for all executable tests:
   - Count total tests executed (excluding skipped tests)
   - Count passing tests
   - Count failing tests (must be 0)
   - Calculate pass rate percentage
   - Verify zero failures among tests that can run
5. **Failure investigation** - If tests fail, investigate and fix issues:
   - Analyze failure messages and stack traces
   - Identify root cause of each failure
   - Fix the underlying issues
   - Re-run tests to verify fixes
   - Continue until all tests pass
6. **Test results analysis** - Analyze test execution results:
   - Identify slow tests (performance bottlenecks)
   - **Flag tests exceeding 10 seconds** - Any test taking longer than 10 seconds MUST be flagged as a violation
   - Identify flaky tests (if any)
   - Verify test coverage metrics
   - Check for test quality issues
   - **Performance violation handling** - Tests exceeding 10 seconds MUST be investigated and optimized

## Test Execution Details

- **Build Command**: `.venv/bin/pytest --maxfail=1 --collect-only --session-timeout=180` (3-minute session timeout prevents hangs during collection)
- **Test Command**: `.venv/bin/pytest -q --session-timeout=300` (300-second session timeout prevents test suite hangs, per-test timeout of 10s from pytest.ini)
- **Preferred Runner**: When pytest is unavailable in the sandbox, use `make test-unit` (wraps `uv run python -m pytest tests/unit tests/integration/test_repository_fetching.py`) to ensure the uv-managed environment and pytest are available.
- **Timeout Protection**: pytest-timeout plugin provides signal-based hang detection and termination (configured in pytest.ini: timeout=10s per test, session_timeout=300s for entire suite)
- **Scope**: Collects and runs all Python tests with hang protection
- **Success Criteria**: Successful collection + all executable tests pass with 0 failures + no hangs detected
- **Coverage**: Verifies Python test suite without hanging

## Output Format

Provide a structured test execution report:

### **Build Results**

- **Build Status**: Success/Failure/Timeout
- **Build Time**: Total build execution duration in seconds
- **Build Output**: Summary of build results (errors, warnings, success)
- **Compilation Issues**: Any compilation errors or warnings detected
- **Hang Detection**: Whether build completed within pytest-timeout session timeout limits

### **Test Execution Summary**

- **Total Tests**: Count of all tests in the test suite
- **Executed Tests**: Count of tests that ran successfully
- **Skipped Tests**: Count of tests skipped (with reasons)
- **Passed Tests**: Count of passing tests
- **Failed Tests**: Count of failing tests (must be 0 for success)
- **Pass Rate**: Percentage of executed tests that passed (target: 100%)
- **Execution Time**: Total test execution duration in seconds
- **Timeout Status**: Whether tests completed within pytest-timeout session timeout (target: within 300 seconds)
- **Hang Prevention**: Whether pytest-timeout protection prevented any hangs

### **Test Results by Module**

For each module/target, provide:

- **Module Name**: Name of the module/target
- **Total Tests**: Count of tests in the module
- **Executed**: Count of tests executed
- **Passed**: Count of passing tests
- **Failed**: Count of failing tests
- **Skipped**: Count of skipped tests
- **Pass Rate**: Percentage pass rate for the module

### **Skipped Tests Details**

For each skipped test, provide:

- **Test Name**: Full test name
- **Module**: Module/target containing the test
- **Skip Reason**: Reason for skipping (if applicable)
- **Environment Constraint**: Specific constraint that prevented execution

### **Test Failures** (if any)

For each failure, provide:

- **Test Name**: Full test name with test class
- **Module**: Module/target containing the test
- **File Path**: Path to the test file
- **Line Number**: Line where the failure occurred
- **Error Message**: Complete error message and stack trace
- **Root Cause**: Analysis of the underlying issue
- **Fix Applied**: Description of the fix applied
- **Verification**: Confirmation that the test now passes

### **Timeout Events** (if any)

For each pytest-timeout event, provide:

- **Event Type**: Build timeout or Test timeout
- **Duration**: Time elapsed before timeout
- **Test/Command**: Test name or command that timed out
- **Root Cause**: Analysis of what caused the hang
- **Resolution**: How the timeout was handled (signal-based termination)
- **Hang Prevention**: Confirmation that the hang was detected and handled by pytest-timeout

### **Test Performance Analysis**

- **Slow Tests**: List of tests taking > 1 second (with execution times)
- **Performance Violations**: List of tests exceeding 10 seconds (MANDATORY violation - must be fixed)
- **Performance Bottlenecks**: Tests that may need optimization
- **Average Test Duration**: Average time per test
- **Total Execution Time**: Total time for all tests
- **10-Second Rule Compliance**: Verification that all tests complete in under 10 seconds
- **Timeout Compliance**: Verification that all operations complete within pytest-timeout limits (10s per test, 300s for session)

### **Test Coverage Analysis**

- **Coverage Status**: Overall test coverage assessment
- **New Code Coverage**: Coverage for newly added/modified code
- **Coverage Gaps**: Areas lacking test coverage
- **Critical Path Coverage**: Coverage for critical business logic

### **Test Quality Assessment**

- **Test Quality**: Overall assessment of test quality
- **Flaky Tests**: Any tests that may be flaky or non-deterministic
- **Test Maintenance**: Notes on test maintainability
- **Test Organization**: Assessment of test structure and organization

### **Actions Taken**

- **Build Issues Fixed**: Count and list of build issues that were resolved
- **Tests Fixed**: Count and list of tests that were fixed
- **Timeout Issues Resolved**: Count and list of pytest-timeout issues that were addressed
- **Hang Events Handled**: Count and list of hang events detected and resolved by pytest-timeout
- **Issues Resolved**: List of issues resolved during execution
- **Remaining Issues**: Any issues that couldn't be resolved

## Success Criteria

- ✅ Build completes successfully without errors or warnings
- ✅ All executable tests pass (100% pass rate)
- ✅ Zero test failures among tests that can run
- ✅ **No operations hang** - pytest-timeout protection prevents hangs
- ✅ **All operations complete within pytest-timeout limits** (build within 3 minutes, tests within 300 seconds, individual tests within 10 seconds)
- ✅ **All tests complete in under 10 seconds** (MANDATORY performance requirement)
- ✅ All new/updated functionality has test coverage
- ✅ Test execution completes successfully without hangs
- ✅ No compilation errors or warnings
- ✅ All test files compile and run correctly

## Failure Handling

- If build fails → investigate and fix compilation issues before proceeding
- If build times out → investigate build hang (infinite compilation, deadlock) and resolve before proceeding
- If test suite fails → investigate and fix issues before proceeding
- If tests fail due to code issues → fix the code and re-run tests
- If tests fail due to test issues → fix the tests and re-run
- If tests time out → investigate test hang, fix infinite loops or deadlocks, then re-run
- **If operations hang** → pytest-timeout will detect and terminate the test automatically via signal
- **If tests exceed 10 seconds** → pytest-timeout will timeout the test; optimize or refactor tests to meet performance requirement, then re-run
- **If operations exceed session timeout** → investigate root cause of hangs and fix before proceeding
- Continue until build succeeds, all executable tests pass with 0 failures, all operations complete within timeouts, all tests complete in under 10 seconds, and no hangs occur
- **NO USER PROMPTS**: Execute all steps automatically without asking for permission

## Usage

This command ensures the project builds correctly and all tests pass before proceeding with commits or other operations, with robust protection against hangs through pytest-timeout plugin (signal-based timeout mechanism).
