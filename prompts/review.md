# Review Code

**CRITICAL**: Execute ALL steps below AUTOMATICALLY. Do NOT pause, summarize, or ask for confirmation. Start with Step 1 immediately.

## START HERE — Execute These Tool Calls Now

**Step 1**: Call `check_mcp_connection_health()`. If unhealthy, STOP.

**Step 2**: Call `load_context(task_description="Code review: bugs, consistency, completeness, security, performance", token_budget=4000)`.

**Step 3**: Call `rules(operation="get_relevant", task_description="Code review, coding standards")`. If `disabled`, read rules via `get_structure_info()`.

**Step 4**: Determine **review scope** — identify module, directory, or files to review. Check `git diff --name-only` for recently changed files.

After Step 4, continue to the analysis steps below.

---

## Step 5: Static Analysis

Call `execute_pre_commit_checks(checks=["type_check"])` and `execute_pre_commit_checks(checks=["quality"])`.

Record: compiler warnings, deprecated API usage, unused imports/variables, type errors.

## Step 6: Bug Detection

Review code in scope for language-specific bugs:

- **Python**: Unguarded `None`, mutable default args, bare `except:`, async/await misuse, unclosed resources
- **All**: Race conditions, logic errors, memory leaks, incorrect error handling, off-by-one

Use `Read` and `Grep` to inspect suspicious patterns.

## Step 7: Consistency Check

Review code for:

- Naming conventions, coding styles, error handling patterns
- DI bypasses, API design inconsistencies
- File organization and code style across related files

## Step 8: Rules Compliance

Check against loaded rules:

- SOLID/DRY/YAGNI principles
- File limits (400 lines), function limits (30 lines)
- Testing standards, dependency injection patterns

## Step 9: Completeness

Search for incomplete implementations:

- `Grep` for `TODO`, `FIXME`, `HACK` in production code
- Placeholder implementations, missing error handling
- Missing tests for public APIs

## Step 10: Test Coverage

Review test quality:

- Public API coverage, edge cases
- AAA pattern (Arrange, Act, Assert)
- Pydantic v2 for JSON testing

## Step 11: Security Assessment

Check for:

- Hardcoded secrets, input validation gaps
- Secure logging (no sensitive data in logs)
- Auth/authz issues

## Step 12: Performance Review

Check for:

- O(n^2) algorithms, unnecessary allocations
- Blocking I/O in async contexts
- Memory leaks, resource cleanup

---

## Report Assembly

1. Call `get_structure_info()` to get `structure_info.paths.reviews`.
2. Generate timestamp: run `date +%Y-%m-%dT%H-%M`.
3. Write report to `{reviews_path}/code-review-report-{timestamp}.md`.

### Report Format

Score all 9 metrics (0-10): Architecture, Test Coverage, Documentation, Code Style, Error Handling, Performance, Security, Maintainability, Rules Compliance. Overall = average.

Each metric score **MUST** cite specific tool output or concrete code evidence. Scores without evidence are invalid. Example: `Test Coverage: 7 — pytest shows 85% coverage, edge cases in test_parser_edge_cases.py`.

#### Architecture Calibration

| Score | Meaning | Evidence Required |
|---|---|---|
| 0-2 | Ad-hoc structure, no clear separation of concerns | Code examples showing god objects, tight coupling, or mixed responsibilities |
| 3-4 | Basic layering but frequent violations and tangling | References to files/functions where layers are crossed or responsibilities mixed |
| 5-6 | Reasonable modularity with some architectural smells | Specific modules with partial DI, unclear boundaries, or leaky abstractions |
| 7-8 | Well-structured architecture with clear boundaries and DI | Code locations demonstrating clean layering, DI usage, and cohesive modules |
| 9-10 | Exemplary architecture with strong patterns and extensibility | Concrete examples of patterns (e.g., ports/adapters), clear module contracts, and low coupling |

#### Test Coverage Calibration

| Score | Meaning | Evidence Required |
|---|---|---|
| 0-2 | No tests or < 30% coverage | `pytest --cov` output showing < 30% |
| 3-4 | Happy path only, 30-60% | Coverage report showing gaps |
| 5-6 | Good coverage 60-80%, some edge cases | Coverage report |
| 7-8 | Strong coverage 80-95%, edge cases covered | Coverage report + edge case test names |
| 9-10 | Exhaustive 95%+, mutation testing or property tests | Coverage report + mutation/property test evidence |

#### Documentation Calibration

| Score | Meaning | Evidence Required |
|---|---|---|
| 0-2 | Little or no documentation | Missing or empty `README`/docs paths, undocumented public APIs |
| 3-4 | Minimal docs, many gaps | Specific modules or APIs without docstrings or guides |
| 5-6 | Core flows documented, some gaps | References to existing docs plus examples of missing areas |
| 7-8 | Comprehensive docs for main components and workflows | Links to up-to-date guides, API docs, and inline docs for complex code |
| 9-10 | Exceptional docs with tutorials, diagrams, and change history | Evidence of end-to-end guides, architecture diagrams, and maintained changelogs |

#### Code Style Calibration

| Score | Meaning | Evidence Required |
|---|---|---|
| 0-2 | Style is chaotic and inconsistent | Examples of mixed naming, indentation, or formatter not applied |
| 3-4 | Some conventions, many violations | References to files with inconsistent style or formatter errors |
| 5-6 | Mostly consistent with occasional issues | Concrete examples of minor deviations from agreed style or linters |
| 7-8 | Strong consistency with rare minor nits | Linter/formatter outputs plus a few style observations |
| 9-10 | Near-perfect adherence to standards | Clean linter output and clear alignment with documented style guides |

#### Error Handling Calibration

| Score | Meaning | Evidence Required |
|---|---|---|
| 0-2 | Errors ignored or swallowed, no structure | Code showing bare `except`, silent failures, or missing checks |
| 3-4 | Some error handling, many gaps | Examples of unhandled failure paths or generic error handling |
| 5-6 | Reasonable handling with a few weak spots | Specific locations with structured errors but some missing propagation or context |
| 7-8 | Consistent, typed, and contextual error handling | Code showing structured errors, clear messages, and consistent propagation |
| 9-10 | Robust error model with domain-specific errors and recovery | Evidence of rich error types, recovery strategies, and clear error contracts |

#### Performance Calibration

| Score | Meaning | Evidence Required |
|---|---|---|
| 0-2 | Known bottlenecks or obviously inefficient code | Profiling output or code examples of O(n²+) hot paths without justification |
| 3-4 | Some inefficient paths with limited mitigation | Concrete examples of inefficiencies and their impact |
| 5-6 | Generally acceptable performance, some optimizations possible | Profiling data or reasoning showing moderate headroom |
| 7-8 | Optimized for common paths with measured behavior | Profiling traces or benchmarks showing good performance in key flows |
| 9-10 | Highly optimized with evidence-driven tuning | Benchmark/profiling evidence plus documented optimization decisions |

#### Security Calibration

| Score | Meaning | Evidence Required |
|---|---|---|
| 0-2 | Obvious security issues or missing basics | Examples of hardcoded secrets, missing validation, or insecure defaults |
| 3-4 | Some security measures, many gaps | Specific missing checks, unsafe patterns, or unclear trust boundaries |
| 5-6 | Reasonable baseline security with a few issues | References to validation, secret handling, and logging with some gaps |
| 7-8 | Strong security posture following best practices | Evidence of thorough validation, secret management, and safe logging |
| 9-10 | Exceptional security with defense-in-depth | Concrete examples of threat modeling, layered defenses, and audits |

#### Maintainability Calibration

| Score | Meaning | Evidence Required |
|---|---|---|
| 0-2 | Sprawling files, unclear structure, hard to change | Examples of very large files/functions or tangled dependencies |
| 3-4 | Some structure, still hard to navigate | References to areas with unclear ownership or mixed concerns |
| 5-6 | Generally maintainable with a few problem areas | Specific modules with moderate complexity or duplication |
| 7-8 | Well-organized, readable, and easy to modify | Code examples of small, focused functions and clear module boundaries |
| 9-10 | Highly maintainable with clear ownership and patterns | Evidence of consistent patterns, clear ownership docs, and low churn cost |

#### Rules Compliance Calibration

| Score | Meaning | Evidence Required |
|---|---|---|
| 0-2 | Frequent, severe rule violations | Concrete examples of file/function size violations or missing tests |
| 3-4 | Multiple medium-level violations | References to several rules not followed across the codebase |
| 5-6 | Mostly compliant with some exceptions | Specific, limited rule violations with locations |
| 7-8 | Strong compliance with minor edge cases | Evidence from checks (e.g., `execute_pre_commit_checks`) plus a few minor issues |
| 9-10 | Full compliance with documented standards | Clean check outputs and code examples showing consistent rule adherence |

For each issue found, include:

- Severity (Critical / High / Medium / Low)
- Location (file:line)
- Description and suggestion

## MCP Tool Usage

- `manage_file(file_name="...", operation="read")` — read memory bank for project context
- `rules(operation="get_relevant", ...)` — load review rules
- `get_structure_info()` — get reviews path dynamically
- `execute_pre_commit_checks(checks=[...])` — run automated checks

## Failure Handling

- Critical bugs found → create todo items to fix immediately
- Rules violations found → fix immediately
- Consecutive MCP failures → follow circuit-breaker pattern per `shared-conventions.md`

## Success Criteria

- All 8 analysis steps (5-12) completed
- All 9 metrics scored with reasoning
- Report saved to reviews directory
