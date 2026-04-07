# Review Code

**CRITICAL**: Execute ALL steps below AUTOMATICALLY. Do NOT pause, summarize, or ask for confirmation. Start with Step 1 immediately.

## Clean Semantics

For `/cortex/review`, **clean** means **review-clean for the scoped code**:

- Required review checks are executed for the selected scope.
- Findings are either absent or fully documented with severity and evidence.
- No unresolved hidden blockers remain in the reviewed scope.

Git-clean working tree is not required; review cleanliness is about issue detection and reporting quality.

## START HERE — Execute These Tool Calls Now

**Step 1**: Call `session()` to verify MCP health and get orientation.

**Step 2**: Determine **review scope** — identify module, directory, or files to review. Check `git diff --name-only` for recently changed files.

**Telemetry-only diffs**: If `git diff --name-only` lists *only* paths under `.cortex/.session/`, `.cortex/synapse/.cache/`, or other telemetry/metadata-only locations (no `src/`, `tests/`, or other product code), **expand scope** to: (a) every file and location referenced by **OPEN** issues in the **Issue Tracker** from the **most recent** `.cortex/reviews/code-review-report-*.md` (use the report with the greatest lexicographic `code-review-report-*` suffix if unsure), and (b) all files that appear in the last five commits: `git log --oneline -5 --name-only` (union of paths). Review that expanded set—not only the telemetry diff.

**Step 3**: Run `run_quality_gate()` — zero-arg tool that runs all Phase A checks (type, format, lint, tests, markdown). Record the full result.

After Step 3, run **Step 4**, then continue to the remaining analysis steps.

---

## Step 4: Regression Check

Load the **most recent prior** `.cortex/reviews/code-review-report-*.md` (the newest file strictly before the report you are about to write).

- **Issue regressions**: If an issue was **RESOLVED** (or **WONTFIX**) in that report but the same defect clearly appears again in the current scope, flag it as a **regression** and cite the prior **Issue Tracker** ID. **Regressions are at least High severity.**
- **Score regressions**: If any of the 9 metric scores **decreased** versus that report, explain the drop with concrete evidence; an unexplained decrease is a **High** severity process gap.

---

## Step 5: Static Analysis — @review-static-analysis subagent

Use @review-static-analysis to handle Steps 5–12. If the subagent is unavailable, run inline:

Parse `run_quality_gate()` results from Step 3 for type_check and quality output.

Record: compiler warnings, deprecated API usage, unused imports/variables, type errors.

## Step 6: Bug Detection

Review code in scope for language-specific bugs:

- **Python**: Unguarded `None`, mutable default args, bare `except:`, async/await misuse, unclosed resources. **Narrow exception handling**: avoid `except Exception` or bare `except` unless intentional (e.g. top-level fallback with logging); catch specific exceptions (e.g. `json.JSONDecodeError`, `OSError`, `ValidationError`) so bugs and validation failures are not hidden.
- **All**: Race conditions, logic errors, memory leaks, incorrect error handling, off-by-one

Use `Read` and `Grep` to inspect suspicious patterns (e.g. `except Exception`, `except:`).

## Step 7: Consistency Check

Review code for:

- Naming conventions, coding styles, error handling patterns
- DI bypasses, API design inconsistencies
- File organization and code style across related files
- **Data modeling**: Prefer Pydantic for internal structures per project rules; flag uses of plain `dict` or `dataclass` where Pydantic would improve consistency, validation, or alignment with project standards

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
- **Path and filename safety**: Any string from user input, tool names, or external data that is used in file paths or filenames must be sanitized—no path components (e.g. `../`), no unsafe characters. When code builds paths from variables (e.g. `f"{base}/{tool_name}.md"`), recommend sanitization (e.g. replace non-alphanumeric with a safe delimiter, strip path components) so files cannot be written outside the intended directory

## Step 12: Performance Review

Check for:

- O(n^2) algorithms, unnecessary allocations
- Blocking I/O in async contexts
- Memory leaks, resource cleanup

## Step 12.5: File Review Artifact (Threshold-Gated)

After writing the review report, decide whether to file it into the memory bank:

1. Resolve filing threshold from `.cortex/config/lint-config.json` key `review_filing_threshold`.
2. If config is missing, malformed, or key is absent, use default threshold `7`.
3. Compare the computed **Overall** review score (0-10) against the threshold.
4. If `overall_score >= threshold`, call:
   - `manage_file(operation="file_artifact", artifact_type="review_report", title="<review title>", content="<full review markdown>")`
5. If below threshold, skip filing and note the skip reason in `## Next`.

For successful filing, include the returned filed artifact path in `## Next`.

---

## Report Assembly

1. Generate timestamp: run `date +%Y-%m-%dT%H-%M`.
2. Write report to `.cortex/reviews/code-review-report-{timestamp}.md`.

### Report Format

**Before scoring**: Load the most recent `.cortex/reviews/code-review-report-*.md` (same “latest lexicographic suffix” rule as Step 2). From its **Issue Tracker**, **carry forward every OPEN row** into the new report (update Location/Description if the code moved or changed). Mark items **RESOLVED** only when verified fixed in this review, or **WONTFIX** with a one-line rationale. Assign new issues IDs `REV-{YYYY-MM-DD}-{N}` (e.g. `REV-2026-03-21-1`); **N** starts at 1 for each report date and increments per new issue. Allowed statuses: **OPEN**, **RESOLVED**, **WONTFIX**.

Score all 9 metrics (0-10): Architecture, Test Coverage, Documentation, Code Style, Error Handling, Performance, Security, Maintainability, Rules Compliance. Overall = average.

**Score deltas**: After each metric name, show the prior score (from the previous report) and the delta, e.g. `Architecture: 8 (was 8, +0)` or `Error Handling: 7 (was 6, +1)`. If the previous report lacks a metric, write the literal *(no prior)* (not a score). If any metric’s **numeric score is unchanged for 3 or more consecutive reports** (including this one—use prior reports on disk), append **`STALE — requires targeted action plan`** and one sentence naming the stuck area.

Each metric score **MUST** cite specific tool output or concrete code evidence. Scores without evidence are invalid. Example: `Test Coverage: 7 — pytest shows 85% coverage, edge cases in test_parser_edge_cases.py`.

#### Issue Tracker (required in every report)

Include a section titled exactly `## Issue Tracker` with a table:

| ID | First Found | Status | Location | Description |

- **First Found**: report date `YYYY-MM-DD` when the issue was first logged (carry forward unchanged for existing IDs).
- Rows must cover all carried-forward OPEN issues plus any new findings.

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
| 3-4 | Some error handling, many gaps | Examples of unhandled failure paths, generic or overly broad exception handling (e.g. `except Exception` hiding `ValidationError`) |
| 5-6 | Reasonable handling with a few weak spots | Specific locations with structured errors but some missing propagation, context, or overly broad catches |
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
| 7-8 | Strong security posture following best practices | Evidence of thorough validation, path/filename sanitization when building paths from variables, secret management, and safe logging |
| 9-10 | Exceptional security with defense-in-depth | Concrete examples of threat modeling, path safety, layered defenses, and audits |

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
| 7-8 | Strong compliance with minor edge cases | Evidence from checks (e.g., `run_quality_gate`) plus a few minor issues |
| 9-10 | Full compliance with documented standards | Clean check outputs and code examples showing consistent rule adherence |

For each issue found, include:

- Severity (Critical / High / Medium / Low)
- Location (file:line)
- Description and suggestion

#### Improvement Suggestions

For non-blocking improvements, add a dedicated **Improvement suggestions** section. **Each suggestion is INVALID unless it includes all of:**

1. **Exact `file:line`** for the change (or the anchor location if multi-line).
2. **Concrete before code** and **concrete after code** (minimal excerpt, enough to apply).
3. **Single-commit scope**: name at most **3 files** touched for that suggestion; if more are needed, split into separate suggestions.

Also include **Effort** (Low / Medium / High), **Impact** (Low / Medium / High), and list suggestions in **priority order** (by impact and effort).

**Anti-patterns**:

- **BAD**: “Narrow exception handlers across the codebase” (no location, no before/after).
- **GOOD**: “In `src/cortex/validation/validation_config.py:92`, replace `except Exception` with `except (OSError, json.JSONDecodeError, ValidationError)` — before: `except Exception:` / after: `except (OSError, json.JSONDecodeError, ValidationError):`”

## MCP Tool Usage

- `session()` — verify health, get orientation
- `run_quality_gate()` — Phase A quality checks (type, lint, tests, markdown)
- `manage_file()` — read memory bank files (zero-arg reads activeContext.md)
- `plan(operation="archive_completed")` — archive completed plans

## Failure Handling

- Critical bugs found → create todo items to fix immediately
- Rules violations found → fix immediately
- Consecutive MCP failures → follow circuit-breaker pattern per `shared-conventions.md`

## Step 13: Post-Prompt Hook (Self-Improvement)

After writing the final report for this review run, invoke the post-prompt self-improvement hook:

- Read `.cortex/synapse/prompts/post-prompt-hook.md` and execute it to analyze the session and emit any applicable Skills, Plans, or Rules.
- Treat this hook as **non-blocking**: if it fails or is unavailable (for example, MCP connection issues), record a brief note in the final report `## Next` section and consider the review workflow complete.

## Final report (required format)

**MANDATORY**: Use the **Artifact (review)** report type from `docs/guides/synapse-final-report-templates.md`.

```markdown
## Result

✅/⚠️ Review complete — <n> issues found

## Scores

| Metric | Score | Delta |
|--------|-------|-------|
| Architecture | <n> | <+/-n> |
| Test Coverage | <n> | <+/-n> |
| Documentation | <n> | <+/-n> |
| Code Style | <n> | <+/-n> |
| Error Handling | <n> | <+/-n> ⚠️ |
| Performance | <n> | <+/-n> |
| Security | <n> | <+/-n> |
| Maintainability | <n> | <+/-n> |
| Rules Compliance | <n> | <+/-n> |
| **Overall** | **<n>** | **<+/-n>** |

## Issues

| ID | Severity | Location |
|----|----------|----------|
| REV-<date>-<n> | Critical/High/Medium/Low | <file:line> — <description> |

## Next

<Fix High/Critical issues OR None>
```

**Rules**:

- Flag negative deltas with ⚠️
- Issues table: carried forward from prior reports + new findings
- ⚠️ in Result if any High/Critical issues

## Success Criteria

- Steps 4–12 completed (regression check, then static analysis through performance)
- Previous report loaded for issue carry-forward, score deltas, and regression detection
- All 9 metrics scored with reasoning and deltas (or `no prior` where applicable)
- **Issue Tracker** section present and complete
- **Improvement suggestions** meet file:line + before/after + ≤3 files each
- Report saved to reviews directory
