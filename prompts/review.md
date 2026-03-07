# Review Code

**AI EXECUTION COMMAND**: Comprehensive code review to find bugs, inconsistencies, and incomplete implementations.

**CRITICAL**: Execute all steps AUTOMATICALLY. DO NOT ask the user for permission or confirmation.

## Conventions

Per `shared-conventions.md`. Severity: GATE/CHECK/PREFER.

## Architecture

### Prompts = Orchestration | Agents = Implementation

This prompt orchestrates code review and delegates specialized analysis to agents. Output format is defined in `review-output-schema.md`.

## Agents Used

| Step | Agent | Purpose |
|---|---|---|
| Pre-Step | common-checklist | Load structure, memory bank, rules, language |
| State | pipeline-state-tracker | Pipeline state checkpointing (review) |
| 1 | static-analyzer | Static analysis (linting) |
| 2 | bug-detector | Bug detection (language-aware) |
| 3 | consistency-checker | Cross-file consistency |
| 4 | rules-compliance-checker | Rules compliance |
| 5 | completeness-verifier | Incomplete implementations |
| 6 | test-coverage-reviewer | Test coverage review |
| 7 | security-assessor | Security assessment |
| 8 | performance-reviewer | Performance review |
| — | review-output-schema | Output format reference |

**Inter-agent communication**: All agents return structured results per `shared-handoff-schema.md`. Validate required fields before assembling the report. Pipeline state is persisted after each step via `pipeline-state-tracker` to prevent state loss during long reviews.

**When executing steps**: Agent availability is verified by the pre-flight health check. READ the agent file, EXECUTE its steps, VERIFY success.

**Language-Aware Review**: The `common-checklist` agent detects the project's primary language from `techContext.md`. Pass `primary_language` to all sub-agents so they filter checklists to relevant patterns.

## Pre-Action Checklist

Execute standard pre-flight protocol (see `shared-conventions.md`) with all agents from the "Agents Used" table.

After checklist, determine **review scope**:

- Identify module, directory, or files to review
- Understand context and purpose of the code
- Check for previous reviews of the same scope

**GATE**: Do not proceed without running common-checklist.

## Execution Steps

### Step 1: Static analysis — Delegate to `static-analyzer`

- **Agent**: static-analyzer (Synapse agents directory)
- Uses `execute_pre_commit_checks(checks=["type_check"])` and `execute_pre_commit_checks(checks=["quality"])`
- **CHECK**: Compiler warnings, deprecated API usage, unused imports/variables
- After agent completes, delegate to `pipeline-state-tracker` (checkpoint_write, step_name="step_1_static_analysis")

### Step 2: Bug detection — Delegate to `bug-detector`

- **Agent**: bug-detector (Synapse agents directory)
- **CHECK**: Pass `primary_language` from common-checklist result
- Language-specific checks (Python: None access, mutable defaults, async misuse; all: race conditions, off-by-one)
- After agent completes, delegate to `pipeline-state-tracker` (checkpoint_write, step_name="step_2_bug_detection")

### Step 3: Consistency check — Delegate to `consistency-checker`

- **Agent**: consistency-checker (Synapse agents directory)
- **CHECK**: Naming conventions, file organization, code style, error handling patterns, API design
- After agent completes, delegate to `pipeline-state-tracker` (checkpoint_write, step_name="step_3_consistency")

### Step 4: Rules compliance — Delegate to `rules-compliance-checker`

- **Agent**: rules-compliance-checker (Synapse agents directory)
- **CHECK**: SOLID/DRY/YAGNI, file limits (400 lines), function limits (30 lines), testing standards, DI
- After agent completes, delegate to `pipeline-state-tracker` (checkpoint_write, step_name="step_4_rules_compliance")

### Step 5: Completeness — Delegate to `completeness-verifier`

- **Agent**: completeness-verifier (Synapse agents directory)
- **CHECK**: TODO/FIXME in production code, placeholder implementations, missing error handling, missing tests
- After agent completes, delegate to `pipeline-state-tracker` (checkpoint_write, step_name="step_5_completeness")

### Step 6: Test coverage — Delegate to `test-coverage-reviewer`

- **Agent**: test-coverage-reviewer (Synapse agents directory)
- **CHECK**: Public API coverage, edge cases, AAA pattern, Pydantic v2 for JSON testing
- After agent completes, delegate to `pipeline-state-tracker` (checkpoint_write, step_name="step_6_test_coverage")

### Step 7: Security — Delegate to `security-assessor`

- **Agent**: security-assessor (Synapse agents directory)
- **CHECK**: Hardcoded secrets, input validation, secure logging, auth/authz
- After agent completes, delegate to `pipeline-state-tracker` (checkpoint_write, step_name="step_7_security")

### Step 8: Performance — Delegate to `performance-reviewer`

- **Agent**: performance-reviewer (Synapse agents directory)
- **CHECK**: O(n^2) algorithms, unnecessary allocations, blocking I/O, memory leaks
- After agent completes, delegate to `pipeline-state-tracker` (checkpoint_write, step_name="step_8_performance")

## Review Criteria

### Bugs (filtered by `primary_language`)

- **Python**: Unguarded `None`, mutable default args, bare `except:`, async/await misuse, unclosed resources
- **Swift**: Force unwraps, retain cycles, unclosed resources
- **All**: Race conditions, logic errors, memory leaks, incorrect error handling, off-by-one

### Inconsistencies

- Naming patterns, coding styles, error handling approaches, DI bypasses, API design

### Incomplete Implementations

- TODO/FIXME in production, placeholder implementations, missing error handling, missing tests, missing docs

## Report Assembly

Before assembling the report, delegate to `pipeline-state-tracker` (checkpoint_read) to recall all agent results from Steps 1-8. Use the persisted state to populate the report even if early step results have been compressed from context.

## Output Format

**Format per `review-output-schema.md`** in the Synapse agents directory. This schema defines:

- Report structure (Quality Assessment, Metrics, Issues, Violations, Improvements)
- Issue templates (all fields required for plan-ready output)
- Violation templates
- Completeness templates
- Improvement templates

### Report File Location

- **Path**: `{reviews_path}/code-review-report-YYYY-MM-DDTHH-mm.md`
- **GATE**: Use `get_structure_info()` -> `structure_info.paths.reviews` for path. Never hardcode.
- **GATE**: Timestamp from real time (`date +%Y-%m-%dT%H-%M`). Never use invented time.

### Detailed Metrics (MANDATORY — all 9 scored 0-10)

Architecture, Test Coverage, Documentation, Code Style, Error Handling, Performance, Security, Maintainability, Rules Compliance. Overall score = average. See `review-output-schema.md` for full definitions.

**PREFER**: Use `think` tool in full mode for large or complex reviews.

## MCP Tool Usage

- **manage_file**: Read memory bank files for project context (`manage_file(file_name="...", operation="read")`)
- **rules**: Load rules for review (`rules(operation="get_relevant", task_description="Code review, coding standards")`)
- **get_structure_info**: Get reviews path, plans path dynamically

## Failure Handling

- Critical bugs found -> create todo items to fix immediately
- Inconsistencies found -> standardize the codebase
- Rules violations found -> fix immediately
- Incomplete implementations -> complete or add proper TODOs with context
- Continue until all issues identified and addressed

## Success Criteria

- Comprehensive review completed with all 8 analysis steps
- All 9 metrics scored (0-10) with reasoning
- All issues include plan-ready structure (per `review-output-schema.md`)
- Report saved to reviews directory (path from `get_structure_info()`)
- Report structure optimized for `create-plan.md` consumption

After report is saved, delegate to `pipeline-state-tracker` (checkpoint_clear) to clean up session state.
