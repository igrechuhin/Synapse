# Review Code

**AI EXECUTION COMMAND**: Comprehensive code review to find bugs, inconsistencies, and incomplete implementations.

**CRITICAL**: These steps are for the AI to execute AUTOMATICALLY. DO NOT ask the user for permission or confirmation. Execute immediately.

**CURSOR COMMAND**: This is a Cursor command located in `.cortex/synapse/prompts/` directory, NOT a terminal command.

**Tooling Note**: Use standard Cursor tools (`Read`, `ApplyPatch`, `Write`, `LS`, `Glob`, `Grep`) by default; MCP filesystem tools are optional fallbacks only when standard tools are unavailable or explicitly requested. Use Cortex MCP tools for memory bank operations when appropriate (e.g., `manage_file()` for reading memory bank files, `validate()` for validation checks).

## ⚠️ MANDATORY PRE-ACTION CHECKLIST

**BEFORE executing this command, you MUST:**

1. ✅ **Read relevant memory bank files** - Understand current project context:
   - **Use Cortex MCP tool `manage_file()`** to read `.cursor/memory-bank/activeContext.md` to understand current work focus
   - **Use Cortex MCP tool `manage_file()`** to read `.cursor/memory-bank/progress.md` to see recent achievements
   - **Use Cortex MCP tool `manage_file()`** to read `.cursor/memory-bank/roadmap.md` to understand project priorities
   - **Use Cortex MCP tool `manage_file()`** to read `.cursor/memory-bank/systemPatterns.md` to understand architectural patterns
   - **Use Cortex MCP tool `manage_file()`** to read `.cursor/memory-bank/techContext.md` to understand technical context

2. ✅ **Read relevant rules** - Understand project requirements:
   - Read `.cursor/rules/coding-standards.mdc` for core coding standards
   - Read `.cursor/rules/maintainability.mdc` for architecture rules
   - Read `.cursor/rules/testing-standards.mdc` for testing requirements
   - Read any other rules relevant to the code being reviewed

3. ✅ **Understand review scope** - Determine what needs to be reviewed:
   - Identify the module, directory, or files to review
   - Understand the context and purpose of the code
   - Check for previous reviews of the same scope

4. ✅ **Verify prerequisites** - Ensure all prerequisites are met:
   - Confirm review scope is clear and actionable
   - Verify access to all necessary files
   - Check that build system is accessible for validation

**VIOLATION**: Executing this command without following this checklist is a CRITICAL violation that blocks proper code review.

## Steps

1. **Static analysis** - Run linter and type checker:
   - Run Pyright type checker: `.venv/bin/pyright src/ tests/` or `python -m pyright src/ tests/` to identify type errors and warnings
   - Run ruff linter: `.venv/bin/ruff check src/ tests/` to identify code quality issues
   - Check for compiler warnings and errors
   - Identify deprecated API usage
   - Check for unused imports and variables
   - Verify code follows best practices
2. **Bug detection** - Search for potential bugs and logic errors:
   - Search for force unwraps (`!`) and analyze safety
   - Check for null pointer dereferences
   - Identify potential race conditions in concurrent code
   - Look for logic errors in business logic
   - Check for off-by-one errors in loops
   - Verify array bounds checking
   - Check for integer overflow possibilities
3. **Consistency check** - Verify naming conventions and code style:
   - Check naming consistency (camelCase, PascalCase)
   - Verify file organization (one type per file, file naming)
   - Check code style consistency across files
   - Verify error handling patterns are consistent
   - Check architectural pattern consistency
   - Verify API design patterns are consistent
4. **Rules compliance check** - Verify all @rules/ requirements are met:
   - **Coding Standards**: SOLID principles, DRY, YAGNI compliance
   - **File Organization**: One type per file, max 400 lines per file, max 30 lines per function
   - **Performance Rules**: O(n) algorithms, no blocking I/O on main thread
   - **Testing Standards**: Public API test coverage, AAA pattern
   - **Error Handling**: No fatalError in production, typed errors
   - **Dependency Injection**: No singletons, proper injection
5. **Completeness verification** - Identify incomplete implementations:
   - Search for `TODO:` and `FIXME:` comments in production code
   - Identify placeholder implementations (`fatalError("Not implemented")`)
   - Check for missing error handling
   - Verify all protocol requirements are implemented
   - Check for incomplete test coverage
   - Identify missing documentation
6. **Test coverage review** - Check that all public APIs have adequate test coverage:
   - Identify all public APIs (public/open declarations)
   - Check for corresponding test files
   - Verify test coverage for critical business logic
   - Check for edge case coverage
   - Verify test quality (AAA pattern, descriptive names)
   - Identify gaps in test coverage
7. **Security assessment** - Look for potential security vulnerabilities:
   - Check for hardcoded secrets or credentials
   - Verify input validation at boundaries
   - Verify secure logging (no secrets in logs)
   - Check for proper authentication/authorization
8. **Performance review** - Identify potential performance bottlenecks:
   - Check for O(n²) algorithms on large collections
   - Identify unnecessary memory allocations
   - Check for blocking I/O on main thread
   - Verify efficient data structures are used
   - Check for unnecessary iterations
   - Identify potential memory leaks
   - Check for inefficient string operations

## Review Criteria

### Bugs to Find

- **Null pointer dereferences**: Force unwraps (`!`) that may fail
- **Race conditions**: Concurrent access to shared mutable state
- **Logic errors**: Incorrect business logic implementation
- **Memory leaks**: Retain cycles, unclosed resources
- **Incorrect error handling**: Missing error handling, wrong error types
- **Off-by-one errors**: Array bounds, loop indices
- **Integer overflow**: Unsafe arithmetic operations

### Inconsistencies to Check

- **Naming conventions**: Inconsistent naming patterns
- **Coding styles**: Mixed coding styles and patterns
- **Error handling**: Inconsistent error handling approaches
- **Architectural violations**: Dependency injection bypasses, singleton usage
- **API design**: Inconsistent API design patterns
- **Rules violations**: Mandatory @rules/ non-compliance

### Incomplete Implementations

- **TODO/FIXME comments**: In production code (should be in issues/tickets)
- **Placeholder implementations**: `fatalError("Not implemented")` in production
- **Missing error handling**: Operations without proper error handling
- **Incomplete test coverage**: Public APIs without tests
- **Missing documentation**: Public APIs without documentation
- **Unimplemented protocol requirements**: Missing protocol implementations

## Output Format

**ALWAYS provide a detailed report** with comprehensive analysis. Every review must include either improvement suggestions or code quality estimates (or both).

Provide a structured report with:

### Code Quality Assessment

- **Overall Score**: Code quality score/rating (0-10 scale)
- **Detailed Reasoning**: Explanation of the score with specific examples
- **Strengths**: What the codebase does well
- **Weaknesses**: Areas needing improvement

### Detailed Metrics Scoring (MANDATORY)

Every report MUST include a detailed breakdown with scores (0-10) for each metric:

- **Architecture (X/10)**: Separation of concerns, design patterns, dependency injection, SOLID principles
- **Test Coverage (X/10)**: Test coverage percentage, test quality, edge case coverage, AAA pattern compliance
- **Documentation (X/10)**: Documentation completeness, quality, clarity, examples
- **Code Style (X/10)**: Consistency, naming conventions, formatting, Best practices
- **Error Handling (X/10)**: Error propagation, typed errors, no fatalError, proper error messages
- **Performance (X/10)**: Algorithm complexity, memory efficiency, optimization, bottlenecks
- **Security (X/10)**: Input validation, no secrets, secure logging, vulnerability assessment
- **Maintainability (X/10)**: Code organization, file structure, function length, readability, complexity
- **Rules Compliance (X/10)**: Adherence to project rules (file size, function length, one-type-per-file, etc.)

### Critical Issues (Must-Fix)

- **Bugs**: List of critical bugs with severity levels (Critical/High/Medium/Low)
- **Security Vulnerabilities**: Security issues with severity levels
- **Data Loss Risks**: Issues that could cause data loss
- **System Crashes**: Issues that could cause system failures

### Consistency Issues

- **Naming Inconsistencies**: Examples of inconsistent naming with fixes
- **Style Violations**: Code style inconsistencies with examples
- **Pattern Violations**: Architectural pattern inconsistencies
- **API Design Issues**: Inconsistent API design patterns

### Rules Violations

- **Coding Standards**: SOLID, DRY, YAGNI violations with references
- **File Organization**: File size, function length, one-type-per-file violations
- **Performance Rules**: O(n²) algorithms, blocking I/O violations
- **Security Rules**: Secrets, input validation, logging violations
- **Testing Standards**: Missing tests, test quality issues
- **Error Handling**: fatalError usage, missing error handling

### Completeness Issues

- **TODO/FIXME Comments**: List with locations and context
- **Placeholder Implementations**: Unimplemented code with impact
- **Missing Error Handling**: Operations without error handling
- **Incomplete Test Coverage**: APIs without tests with coverage gaps
- **Missing Documentation**: APIs without documentation

### Improvement Suggestions

- **Specific Recommendations**: Actionable suggestions with examples
- **Before/After Examples**: Code examples showing improvements
- **Estimated Effort**: Time estimate for each improvement (Low/Medium/High)
- **Impact Assessment**: Expected impact of each improvement (Low/Medium/High)
- **Priority**: Suggested priority order for improvements

## Success Criteria

- ✅ Comprehensive review completed
- ✅ All critical issues identified and documented
- ✅ Rules violations identified with specific references
- ✅ Improvement suggestions provided with examples
- ✅ Code quality assessed with detailed reasoning
- ✅ **Detailed metrics scoring included** - All 9 metrics scored (0-10) with reasoning
- ✅ Overall score calculated as average of metric scores
- ✅ Actionable recommendations provided

## Failure Handling

- If critical bugs are found → create todo items to fix them immediately
- If inconsistencies are found → standardize the codebase
- If rules violations are found → fix them immediately to comply with @rules/ requirements
- If incomplete implementations exist → complete them or add proper TODOs with context
- Continue review process until all issues are identified and addressed
- **NO USER PROMPTS**: Execute all steps automatically without asking for permission

## Usage

This command provides comprehensive code quality assurance before commits and releases, ensuring high code quality, consistency, and completeness.

**NO USER PROMPTS**: Execute all steps automatically without asking for permission
