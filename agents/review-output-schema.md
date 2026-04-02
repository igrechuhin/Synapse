---
name: review-output-schema
description: Reference document defining the output format and templates for code review reports. Used by the review.md orchestrator and its sub-agents to produce structured, plan-ready review reports.
---

# Review Output Schema

This document defines the output format for code review reports. The `review.md` orchestrator references this schema to produce structured reports that can be directly consumed by `plan.md`.

## Report File

- **Location**: `{reviews_path}/code-review-report-YYYY-MM-DDTHH-mm.md`
- **Path resolution**: `get_structure_info()` -> `structure_info.paths.reviews`
- **Timestamp**: Real time only (`date +%Y-%m-%dT%H-%M`). Never use fallback or invented time.

## Report Structure

Each metric must include both a numeric **score** and an **evidence** string explaining the concrete basis for that score (tool outputs, code references, or docs). Scores without evidence are invalid.

```markdown
# Code Review Report

## Code Quality Assessment

- **Overall Score**: X/10 (average of 9 metrics below)
- **Detailed Reasoning**: Explanation with specific examples
- **Strengths**: What the codebase does well
- **Weaknesses**: Areas needing improvement

## Detailed Metrics (MANDATORY — all 9 scored)

- **Architecture**
  - **Score**: X/10 — Separation of concerns, design patterns, DI, SOLID
  - **Evidence**: Concrete code locations, module boundaries, and patterns used
- **Test Coverage**
  - **Score**: X/10 — Coverage %, quality, edge cases, AAA compliance
  - **Evidence**: `pytest --cov` or other coverage output plus key test names
- **Documentation**
  - **Score**: X/10 — Completeness, quality, clarity, examples
  - **Evidence**: Links/paths to docs, docstrings, and examples
- **Code Style**
  - **Score**: X/10 — Consistency, naming, formatting, best practices
  - **Evidence**: Linter/formatter output and representative code samples
- **Error Handling**
  - **Score**: X/10 — Propagation, typed errors, proper messages
  - **Evidence**: Specific error handling code paths and message examples
- **Performance**
  - **Score**: X/10 — Algorithm complexity, memory efficiency, bottlenecks
  - **Evidence**: Profiling traces, benchmarks, or code examples of hot paths
- **Security**
  - **Score**: X/10 — Input validation, no secrets, secure logging
  - **Evidence**: Validation code, secret management configuration, logging samples
- **Maintainability**
  - **Score**: X/10 — Organization, file structure, function length, readability
  - **Evidence**: File structure examples, function sizes, and dependency layout
- **Rules Compliance**
  - **Score**: X/10 — File size, function length, one-type-per-file adherence
  - **Evidence**: Outputs from `execute_pre_commit_checks` and specific compliant/violating files

## Critical Issues (Must-Fix)

[Use Issue Template below for each issue]

## Consistency Issues

- **Naming Inconsistencies**: Examples with fixes
- **Style Violations**: Examples
- **Pattern Violations**: Architectural inconsistencies
- **API Design Issues**: Inconsistent patterns

## Rules Violations

[Use Violation Template below for each violation]

## Completeness Issues

[Use Completeness Template below for each issue]

## Improvement Suggestions

[Use Improvement Template below for each suggestion]
```

## Issue Template

Each critical issue MUST include all fields to enable plan creation:

| Field | Required | Description |
|---|---|---|
| Title | Yes | Clear, descriptive issue name |
| Severity | Yes | Critical / High / Medium / Low |
| Priority | Yes | ASAP / High / Medium / Low |
| Impact | Yes | Impact on system, users, or development |
| Location | Yes | File paths and line numbers |
| Current State | Yes | What code currently does (with examples) |
| Expected State | Yes | What code should do (with examples) |
| Root Cause | Yes | Why this issue exists |
| Dependencies | Yes | Other issues or work required first |
| Implementation Steps | Yes | Numbered, actionable steps to fix |
| Testing Strategy | Yes | How to verify the fix |
| Success Criteria | Yes | Measurable outcomes |
| Estimated Effort | Yes | Low (1-4h) / Medium (4-16h) / High (16-40h) / Very High (40h+) |
| Risks | Yes | Risks and mitigation |

**Issue Categories**: Bugs, Security Vulnerabilities, Data Loss Risks, System Crashes, Rules Violations

## Violation Template

| Field | Required | Description |
|---|---|---|
| Rule | Yes | Specific rule violated (with reference) |
| Severity | Yes | Critical / High / Medium / Low |
| Location | Yes | File paths and line numbers |
| Current State | Yes | What violates the rule (with code) |
| Required State | Yes | What complies (with code) |
| Impact | Yes | Maintainability, performance, security |
| Implementation Steps | Yes | Numbered steps to fix |
| Dependencies | Yes | Other work required first |
| Estimated Effort | Yes | Low / Medium / High / Very High |
| Success Criteria | Yes | Measurable compliance |

**Violation Categories**: Coding Standards, File Organization, Performance Rules, Security Rules, Testing Standards, Error Handling

## Completeness Template

| Field | Required | Description |
|---|---|---|
| Type | Yes | TODO/FIXME/Placeholder/Missing Error Handling/Missing Tests/Missing Documentation |
| Severity | Yes | Critical / High / Medium / Low |
| Location | Yes | File paths and line numbers |
| Current State | Yes | What's missing (with code) |
| Required State | Yes | What needs implementing (with specs) |
| Impact | Yes | Impact of incomplete implementation |
| Implementation Steps | Yes | Numbered steps to complete |
| Testing Strategy | Yes | How to verify completion |
| Success Criteria | Yes | Measurable completion criteria |
| Estimated Effort | Yes | Low / Medium / High / Very High |

## Improvement Template

| Field | Required | Description |
|---|---|---|
| Title | Yes | Clear, descriptive improvement name |
| Category | Yes | Architecture/Security/Performance/Documentation/Maintainability |
| Priority | Yes | High / Medium / Low |
| Current State | Yes | What exists now (with examples) |
| Proposed State | Yes | What should be improved (with examples) |
| Benefits | Yes | Expected benefits |
| Implementation Steps | Yes | Numbered, actionable steps |
| Dependencies | Yes | Other work required first |
| Testing Strategy | Yes | How to verify improvement |
| Success Criteria | Yes | Measurable outcomes |
| Estimated Effort | Yes | Low / Medium / High / Very High |
| Impact Assessment | Yes | Low / Medium / High with reasoning |

**Grouping**: Group related improvements. Suggest implementation order. Identify quick wins (low effort, high impact).

## Plan-Ready Structure

The review report is structured for `plan.md` to extract:

- **Requirements and goals** from issue descriptions
- **Implementation tasks** from detailed step breakdowns
- **Dependencies** from prerequisite fields
- **Timeline estimates** from effort estimates
- **Success criteria** from measurable outcomes
- **Risk assessment** from risk fields
- **Technical design** from implementation approaches

## Structured Metric Schema

Each of the 9 metrics in the report MUST be represented as a structured object with both a numeric score and an evidence string. Downstream tools should assume the following shape:

```text
metrics:
  architecture:
    score: int        # 0-10
    evidence: str     # concrete evidence cited for the score
  test_coverage:
    score: int
    evidence: str
  documentation:
    score: int
    evidence: str
  code_style:
    score: int
    evidence: str
  error_handling:
    score: int
    evidence: str
  performance:
    score: int
    evidence: str
  security:
    score: int
    evidence: str
  maintainability:
    score: int
    evidence: str
  rules_compliance:
    score: int
    evidence: str
```
