---
name: error-pattern-detector
description: Error pattern detection reference for the commit pipeline. Catalogs known error patterns, their detection methods, required actions, and blocking rules. Agents and the final-gate-validator reference this document when parsing tool outputs.
---

# Error Pattern Detector — Reference Catalog

This document catalogs known error patterns that MUST be detected and fixed before commit. It is referenced by `error-fixer`, `quality-checker`, `type-checker`, `test-executor`, and `final-gate-validator` agents.

## Structured Pattern Table

Agents SHOULD parse this table programmatically when checking for errors.

```yaml
patterns:
  - id: type_errors
    gate: true
    detection: "results.type_check.errors non-empty or error count > 0"
    scope: "src/ and tests/"
    action: "Fix all, re-run, verify zero errors"

  - id: type_warnings
    gate: true
    detection: "type checker warning count > 0"
    scope: "src/ and tests/"
    action: "Fix all, re-run, verify zero warnings"
    condition: "Only if project uses a type system"

  - id: test_failures
    gate: true
    detection: "results.tests.success = false or tests_failed > 0"
    scope: "full test suite"
    action: "Fix failing tests, re-run, verify zero failures"
    validation: "success = true AND tests_failed = 0 AND pass_rate = 100.0"

  - id: coverage_below_threshold
    gate: true
    detection: "results.tests.coverage < threshold (default 0.90)"
    scope: "full test suite"
    action: "Add tests until coverage >= threshold, re-run in same run"
    validation: "results.tests.coverage >= threshold (float)"
    note: "Bootstrapping override via coverage_threshold in progress.md/techContext.md"

  - id: file_size_violations
    gate: true
    detection: "results.quality.file_size_violations non-empty"
    scope: "src/ and tests/"
    action: "Split large files, re-run, verify empty violations"
    threshold: "400 lines per file"

  - id: function_length_violations
    gate: true
    detection: "results.quality.function_length_violations non-empty"
    scope: "src/ and tests/"
    action: "Extract helpers, re-run, verify empty violations"
    threshold: "30 lines per function"

  - id: formatting_violations
    gate: true
    detection: "formatter output shows file count > 0 or error list non-empty"
    scope: "src/ and tests/"
    action: "Run formatter, re-run check, verify zero violations"
    note: "Python CI uses Black (not ruff format)"

  - id: linter_errors
    gate: true
    detection: "linter error count > 0"
    scope: "src/ and tests/"
    action: "Fix errors, re-run, verify zero errors"

  - id: spelling_errors
    gate: true
    detection: "results.spelling.success = false or errors list non-empty"
    scope: "src/ and tests/"
    action: "Fix spelling, re-run, verify zero errors"

  - id: markdown_lint_errors
    gate: true
    detection: "markdown lint error count > 0"
    scope: "ALL markdown files"
    action: "Fix errors, re-run, verify zero errors"

  - id: test_naming_violations
    gate: true
    detection: "test functions not matching test_<name> pattern"
    scope: "tests/"
    action: "Rename (testread -> test_read), re-run, verify zero"

  - id: integration_test_failures
    gate: true
    detection: "specific integration test category failures"
    scope: "integration tests"
    action: "Fix issues, re-run, verify all pass"

anti_patterns:
  - id: pre_existing_dismissed
    gate: true
    pattern: "Agent says 'pre-existing' and proceeds"
    reason: "CI fails on any violation regardless of origin"

  - id: fixing_without_rules
    gate: true
    pattern: "Fixes type/visibility without loaded rules"
    reason: "Fixes may violate project rules"

  - id: script_without_analysis
    gate: true
    pattern: "Script executed without manage_session_scripts"
    reason: "Violates script-generation-prevention rule"

  - id: step12_skipped_on_connection
    gate: true
    pattern: "Step 12.1/12.7 skipped after MCP error, using Phase A"
    reason: "New files from Steps 4-11 never validated by Phase A"

  - id: errors_after_checks
    gate: true
    pattern: "Code changes after Step 4 introduce new errors"
    reason: "Step 12 must re-verify all checks"

  - id: plan_status_md036
    gate: true
    pattern: "Plan uses **VALUE** instead of Status: VALUE"
    reason: "Triggers MD036 markdown lint error"

  - id: side_effect_imports
    gate: true
    pattern: "Imports for side effects flagged as unused"
    reason: "Use _ = module to satisfy type checker"

validation_protocol:
  - "Parse actual output — never assume success from exit codes"
  - "Extract explicit counts — verify count = 0"
  - "Read FULL output — never truncate"
  - "Re-run after fixes — never trust without re-checking"
```
