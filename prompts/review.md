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
