# Review Code

**AI EXECUTION COMMAND**: Comprehensive code review to find bugs, inconsistencies, and incomplete implementations.

**CRITICAL**: These steps are for the AI to execute AUTOMATICALLY. DO NOT ask the user for permission or confirmation. Execute immediately.

**CURSOR COMMAND**: This is a Cursor command from the Synapse prompts directory, NOT a terminal command.

**Agent Delegation**: This prompt orchestrates code review and delegates specialized analysis to dedicated agents in the Synapse agents directory:

- **static-analyzer** - Step 1: Static analysis (linting)
- **bug-detector** - Step 2: Bug detection
- **consistency-checker** - Step 3: Consistency check
- **rules-compliance-checker** - Step 4: Rules compliance check
- **completeness-verifier** - Step 5: Completeness verification
- **test-coverage-reviewer** - Step 6: Test coverage review
- **security-assessor** - Step 7: Security assessment
- **performance-reviewer** - Step 8: Performance review

When executing steps, delegate to the appropriate agent for specialized analysis, then aggregate results into the review report.

**Tooling Note**: **MANDATORY: All memory bank and structure operations MUST use Cortex MCP tools** - do NOT access files directly via hardcoded paths. Use standard Cursor tools (`Read`, `ApplyPatch`, `Write`, `LS`, `Glob`, `Grep`) for source files outside Cortex structure. For memory bank and structure paths:

- Use `manage_file(file_name="...", operation="read"|"write")` for memory bank files
- Use `rules(operation="get_relevant", task_description="...")` to obtain relevant rules context
- Use `get_structure_info()` to get directory paths dynamically (e.g. `structure_info.paths.reviews`, `structure_info.paths.plans`)
- For review reports: Use `Write` tool with path from `get_structure_info()` → `structure_info.paths.reviews`

**MCP TOOL USAGE (USE WHEN / EXAMPLES)**:

- **manage_file**
  - **Use when** you need project context from Memory Bank files (e.g., `activeContext.md`, `progress.md`, `roadmap.md`, `systemPatterns.md`, `techContext.md`) to guide the review.
  - **Required parameters**: `file_name`, `operation` (`"read"`, `"write"`, `"metadata"`).
  - **Friendly error behavior**: If `file_name` or `operation` is missing, `manage_file` returns a structured error with `details.missing` and a `hint` on correct usage instead of a raw validation trace.
  - **Examples**:
    - Load active context before reviewing:
      - `manage_file(file_name="activeContext.md", operation="read")`
    - Read roadmap for priority context:
      - `manage_file(file_name="roadmap.md", operation="read", include_metadata=True)`

- **rules**
  - **Use when** you want rules-aware reviews (e.g., “review this code against coding standards and testing rules”).
  - **Required parameter**: `operation` (`"index"` or `"get_relevant"`). `task_description` is REQUIRED for `"get_relevant"`.
  - **Friendly error behavior**: If `operation` is omitted, `rules` returns a structured error with `details.missing=["operation"]` and a `hint` that lists valid operations; invalid operations return `valid_operations` plus a `hint`.
  - **Examples**:
    - Index rules prior to a broad review:
      - `rules(operation="index")`
    - Fetch rules relevant to the current review task:
      - `rules(operation="get_relevant", task_description="Review new health-check and commit pipeline tooling")`

## ⚠️ MANDATORY PRE-ACTION CHECKLIST

**BEFORE executing this command, you MUST:**

1. ✅ **Read relevant memory bank files** - Understand current project context:
   - **Use Cortex MCP tool `manage_file(file_name="activeContext.md", operation="read")`** to understand current work focus
   - **Use Cortex MCP tool `manage_file(file_name="progress.md", operation="read")`** to see recent achievements
   - **Use Cortex MCP tool `manage_file(file_name="roadmap.md", operation="read")`** to understand project priorities
   - **Use Cortex MCP tool `manage_file(file_name="systemPatterns.md", operation="read")`** to understand architectural patterns
   - **Use Cortex MCP tool `manage_file(file_name="techContext.md", operation="read")`** to understand technical context

2. ✅ **Read relevant rules** - Understand project requirements:
   - Use Cortex MCP tool `rules(operation="get_relevant", task_description="Code review, coding standards, maintainability, testing")` or read from the rules directory (path from `get_structure_info()` → `structure_info.paths.rules`)
   - Ensure core coding standards, maintainability rules, testing standards, and other rules relevant to the code being reviewed are in context

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

1. **Static analysis** - **Delegate to `static-analyzer` agent**:
   - Use the `static-analyzer` agent (Synapse agents directory) for this step
   - The agent will run linter (type checking is handled separately by type-checker agent):
   - Use Cortex MCP tool `execute_pre_commit_checks(checks=["type_check"])` and `execute_pre_commit_checks(checks=["quality"])` (or the language-specific type/lint scripts from the Synapse scripts directory) to identify type errors and code quality issues. Do **NOT** run raw language-specific commands (e.g., `pyright`, `ruff`) in a Shell.
   - Check for compiler warnings and errors
   - Identify deprecated API usage
   - Check for unused imports and variables
   - Verify code follows best practices
2. **Bug detection** - **Delegate to `bug-detector` agent**:
   - Use the `bug-detector` agent (Synapse agents directory) for this step
   - The agent will search for potential bugs and logic errors:
   - Search for force unwraps (`!`) and analyze safety
   - Check for null pointer dereferences
   - Identify potential race conditions in concurrent code
   - Look for logic errors in business logic
   - Check for off-by-one errors in loops
   - Verify array bounds checking
   - Check for integer overflow possibilities
3. **Consistency check** - **Delegate to `consistency-checker` agent**:
   - Use the `consistency-checker` agent (Synapse agents directory) for this step
   - The agent will verify cross-file consistency (naming conventions, code style uniformity):
   - Check naming consistency (camelCase, PascalCase)
   - Verify file organization (one type per file, file naming)
   - Check code style consistency across files
   - Verify error handling patterns are consistent
   - Check architectural pattern consistency
   - Verify API design patterns are consistent
4. **Rules compliance check** - **Delegate to `rules-compliance-checker` agent**:
   - Use the `rules-compliance-checker` agent (Synapse agents directory) for this step
   - The agent will verify all @rules/ requirements are met:
   - **Coding Standards**: SOLID principles, DRY, YAGNI compliance
   - **File Organization**: One type per file, max 400 lines per file, max 30 lines per function
   - **Performance Rules**: O(n) algorithms, no blocking I/O on main thread
   - **Testing Standards**: Public API test coverage, AAA pattern
   - **Error Handling**: No fatalError in production, typed errors
   - **Dependency Injection**: No singletons, proper injection
5. **Completeness verification** - **Delegate to `completeness-verifier` agent**:
   - Use the `completeness-verifier` agent (Synapse agents directory) for this step
   - The agent will identify incomplete implementations:
   - Search for `TODO:` and `FIXME:` comments in production code
   - Identify placeholder implementations (`fatalError("Not implemented")`)
   - Check for missing error handling
   - Verify all protocol requirements are implemented
   - Check for incomplete test coverage
   - Identify missing documentation
6. **Test coverage review** - **Delegate to `test-coverage-reviewer` agent**:
   - Use the `test-coverage-reviewer` agent (Synapse agents directory) for this step
   - The agent will check that all public APIs have adequate test coverage:
   - Identify all public APIs (public/open declarations)
   - Check for corresponding test files
   - Verify test coverage for critical business logic
   - Check for edge case coverage
   - Verify test quality (AAA pattern, descriptive names)
   - **Pydantic v2 for JSON testing**: Verify that tests for MCP tool responses use Pydantic v2 `BaseModel` types and `model_validate_json()` / `model_validate()` instead of raw `dict` assertions. See `tests/tools/test_file_operations.py` for examples (e.g., `ManageFileErrorResponse` pattern).
   - Identify gaps in test coverage
7. **Security assessment** - **Delegate to `security-assessor` agent**:
   - Use the `security-assessor` agent (Synapse agents directory) for this step
   - The agent will look for potential security vulnerabilities:
   - Check for hardcoded secrets or credentials
   - Verify input validation at boundaries
   - Verify secure logging (no secrets in logs)
   - Check for proper authentication/authorization
8. **Performance review** - **Delegate to `performance-reviewer` agent**:
   - Use the `performance-reviewer` agent (Synapse agents directory) for this step
   - The agent will identify potential performance bottlenecks:
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

## CRITICAL: Report File Location

- All review reports MUST be saved to the reviews directory (configured in structure)
- File naming: `code-review-report-YYYY-MM-DDTHH-mm.md`. Suffix MUST be derived from real time (e.g. run `date +%Y-%m-%dT%H-%M`). NEVER use fallback or invented time (e.g. no `T00-00`).
- **MANDATORY: Use Cortex MCP tools to get the correct path**:
  1. Call `get_structure_info(project_root=None)` MCP tool to get structure information
  2. Extract the reviews directory path from the response: `structure_info.paths.reviews` (use the value returned by the Cortex tool; do not hardcode)
  3. Construct the full file path: `{reviews_path}/code-review-report-YYYY-MM-DDTHH-mm.md`
  4. Use the `Write` tool with this dynamically constructed path (it will create parent directories automatically)
- **NEVER use hardcoded paths** - Always use `get_structure_info()` to get the reviews path dynamically (`structure_info.paths.reviews`)
- Do NOT save review reports in the Cortex root or other locations; use the reviews directory path from the Cortex tool

**CRITICAL: Report Structure for Plan Creation**
The report structure MUST be optimized for use by `create-plan.md` prompt. Each issue and improvement MUST include:

- Clear, actionable implementation steps (numbered list)
- Dependencies and prerequisites
- Estimated effort and timeline
- Technical design considerations
- Success criteria (measurable)
- Risk assessment and mitigation
- File locations and code examples

This structure enables `create-plan.md` to automatically extract:

- Requirements and goals
- Implementation tasks
- Dependencies and prerequisites
- Estimated complexity and timeline
- Technical constraints
- Success criteria
- Risk mitigation strategies

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

For each critical issue, provide the following structure to enable efficient plan creation:

**Issue Template:**

- **Title**: Clear, descriptive issue name
- **Severity**: Critical/High/Medium/Low
- **Priority**: ASAP/High/Medium/Low
- **Impact**: Description of impact on system, users, or development
- **Location**: Specific file paths and line numbers
- **Current State**: What the code currently does (with code examples)
- **Expected State**: What the code should do (with code examples)
- **Root Cause**: Analysis of why this issue exists
- **Dependencies**: Other issues, files, or work that must be completed first
- **Prerequisites**: Required knowledge, tools, or setup
- **Implementation Steps**: Detailed, actionable steps to fix (numbered list)
- **Technical Design**: Architecture changes, refactoring approach, data model changes
- **Testing Strategy**: How to verify the fix (unit tests, integration tests, manual testing)
- **Success Criteria**: Measurable outcomes (e.g., "All tests pass", "File size < 400 lines")
- **Estimated Effort**: Time estimate (Low: 1-4h, Medium: 4-16h, High: 16-40h, Very High: 40h+)
- **Risks**: Potential risks during implementation and mitigation strategies
- **Related Issues**: Links to other issues that should be addressed together

**Issue Categories:**

- **Bugs**: Critical bugs with severity levels (Critical/High/Medium/Low)
- **Security Vulnerabilities**: Security issues with severity levels
- **Data Loss Risks**: Issues that could cause data loss
- **System Crashes**: Issues that could cause system failures
- **Rules Violations**: Mandatory rule violations that must be fixed

### Consistency Issues

- **Naming Inconsistencies**: Examples of inconsistent naming with fixes
- **Style Violations**: Code style inconsistencies with examples
- **Pattern Violations**: Architectural pattern inconsistencies
- **API Design Issues**: Inconsistent API design patterns

### Rules Violations

For each rules violation, provide the following structure to enable efficient plan creation:

**Violation Template:**

- **Rule**: Specific rule being violated (with reference to rule file)
- **Severity**: Critical/High/Medium/Low (based on rule importance)
- **Location**: File paths and line numbers
- **Current State**: What violates the rule (with code examples)
- **Required State**: What complies with the rule (with code examples)
- **Impact**: Impact of violation (maintainability, performance, security, etc.)
- **Implementation Steps**: Detailed steps to fix (numbered list)
- **Dependencies**: Other work that must be completed first
- **Estimated Effort**: Time estimate (Low: 1-4h, Medium: 4-16h, High: 16-40h, Very High: 40h+)
- **Success Criteria**: Measurable compliance (e.g., "File size ≤ 400 lines", "All functions ≤ 30 lines")
- **Risks**: Potential risks during fix and mitigation

**Violation Categories:**

- **Coding Standards**: SOLID, DRY, YAGNI violations with references
- **File Organization**: File size, function length, one-type-per-file violations
- **Performance Rules**: O(n²) algorithms, blocking I/O violations
- **Security Rules**: Secrets, input validation, logging violations
- **Testing Standards**: Missing tests, test quality issues
- **Error Handling**: fatalError usage, missing error handling

### Completeness Issues

For each completeness issue, provide the following structure to enable efficient plan creation:

**Completeness Issue Template:**

- **Type**: TODO/FIXME/Placeholder/Missing Error Handling/Missing Tests/Missing Documentation/Unimplemented Protocol
- **Severity**: Critical/High/Medium/Low
- **Location**: File paths and line numbers
- **Current State**: What's missing or incomplete (with code examples)
- **Required State**: What needs to be implemented (with code examples or specifications)
- **Impact**: Impact of incomplete implementation
- **Implementation Steps**: Detailed steps to complete (numbered list)
- **Dependencies**: Other work that must be completed first
- **Prerequisites**: Required knowledge, tools, or setup
- **Technical Design**: What needs to be implemented (architecture, API design, etc.)
- **Testing Strategy**: How to verify completion
- **Success Criteria**: Measurable completion criteria
- **Estimated Effort**: Time estimate (Low: 1-4h, Medium: 4-16h, High: 16-40h, Very High: 40h+)
- **Risks**: Potential risks and mitigation

**Issue Categories:**

- **TODO/FIXME Comments**: List with locations, context, and completion plan
- **Placeholder Implementations**: Unimplemented code with impact and implementation plan
- **Missing Error Handling**: Operations without error handling with implementation plan
- **Incomplete Test Coverage**: APIs without tests with coverage gaps and test plan
- **Missing Documentation**: APIs without documentation with documentation plan
- **Unimplemented Protocol Requirements**: Missing protocol implementations with implementation plan

### Improvement Suggestions

For each improvement suggestion, provide the following structure to enable efficient plan creation:

**Improvement Template:**

- **Title**: Clear, descriptive improvement name
- **Category**: Architecture/Security/Performance/Documentation/Maintainability/etc.
- **Priority**: High/Medium/Low
- **Current State**: What exists now (with examples)
- **Proposed State**: What should be improved (with examples)
- **Benefits**: Expected benefits (performance, maintainability, security, etc.)
- **Implementation Approach**: High-level strategy
- **Implementation Steps**: Detailed, actionable steps (numbered list)
- **Dependencies**: Other work that must be completed first
- **Prerequisites**: Required knowledge, tools, or setup
- **Technical Design**: Architecture changes, refactoring approach
- **Testing Strategy**: How to verify the improvement
- **Success Criteria**: Measurable outcomes
- **Estimated Effort**: Time estimate (Low: 1-4h, Medium: 4-16h, High: 16-40h, Very High: 40h+)
- **Risks**: Potential risks and mitigation strategies
- **Impact Assessment**: Expected impact (Low/Medium/High) with reasoning

**Grouping:**

- Group related improvements together
- Suggest implementation order based on dependencies
- Identify quick wins (low effort, high impact)

## After the review (MANDATORY): Execute Analyze prompt

- **MANDATORY**: After saving the review report, you MUST execute the **Analyze (End of Session)** prompt (`analyze.md` from the Synapse prompts directory). Read and execute that prompt in full: it runs context effectiveness analysis and session optimization, saves a report to the reviews directory, and optionally creates an improvements plan. Do not skip this step.
- **Path**: Resolve the Analyze prompt path via project structure or `get_structure_info()` (e.g. Synapse prompts directory); the prompt file is `analyze.md`.

## Success Criteria

- ✅ Comprehensive review completed
- ✅ All critical issues identified and documented
- ✅ Rules violations identified with specific references
- ✅ Improvement suggestions provided with examples
- ✅ Code quality assessed with detailed reasoning
- ✅ **Detailed metrics scoring included** - All 9 metrics scored (0-10) with reasoning
- ✅ Overall score calculated as average of metric scores
- ✅ Actionable recommendations provided
- ✅ **Report saved to reviews directory** - Report file location is correct (path obtained via `get_structure_info()`)
- ✅ **All issues include plan-ready structure** - Each issue/improvement has:
  - Implementation steps (numbered, actionable)
  - Dependencies and prerequisites
  - Estimated effort and timeline
  - Technical design considerations
  - Success criteria (measurable)
  - Risk assessment and mitigation
  - File locations and code examples
- ✅ **Report structure optimized for `create-plan.md`** - Report can be directly used to create comprehensive plans
- ✅ **Analyze prompt executed** - Analyze (End of Session) prompt (`analyze.md`) run after the review to complete context effectiveness and session optimization analysis

## Failure Handling

- If critical bugs are found → create todo items to fix them immediately
- If inconsistencies are found → standardize the codebase
- If rules violations are found → fix them immediately to comply with @rules/ requirements
- If incomplete implementations exist → complete them or add proper TODOs with context
- Continue review process until all issues are identified and addressed
- **NO USER PROMPTS**: Execute all steps automatically without asking for permission

## Usage

This command provides comprehensive code quality assurance before commits and releases, ensuring high code quality, consistency, and completeness.

**Report Output:**

- **MANDATORY: Use Cortex MCP tools to get the correct path**:
  1. Call `get_structure_info(project_root=None)` MCP tool to get structure information
  2. Extract the reviews directory path: `structure_info.paths.reviews`
  3. Construct file path: `{reviews_path}/code-review-report-YYYY-MM-DDTHH-mm.md`
  4. Use the `Write` tool with this dynamically constructed path (it will create parent directories automatically)
- Use format: `code-review-report-YYYY-MM-DDTHH-mm.md`; suffix MUST be derived from real time (e.g. `date +%Y-%m-%dT%H-%M`). NEVER use fallback or invented time.
- **NEVER use hardcoded paths** - Always use `get_structure_info()` to get the reviews path dynamically (`structure_info.paths.reviews`)
- Never save reports in the Cortex root or other locations; use the reviews directory from the Cortex tool

**Report Structure for Plan Creation:**
The review report MUST be structured to enable efficient plan creation by `create-plan.md`. Each section should provide:

1. **Actionable Information**: Every issue/improvement must have clear implementation steps
2. **Dependencies**: Clearly identify what must be done first
3. **Effort Estimates**: Provide time estimates for planning
4. **Success Criteria**: Define measurable outcomes
5. **Technical Details**: Include architecture, design, and code examples
6. **Risk Assessment**: Identify risks and mitigation strategies

When `create-plan.md` processes a review report, it should be able to:

- Extract requirements and goals from issues
- Create implementation steps from detailed issue breakdowns
- Identify dependencies and prerequisites
- Estimate timeline from effort estimates
- Define success criteria from measurable outcomes
- Assess risks from risk assessments
- Generate technical design from technical details

**NO USER PROMPTS**: Execute all steps automatically without asking for permission
