# Fix Compiler Errors and Warnings

**AI EXECUTION COMMAND**: Fix all compiler errors and warnings across the entire codebase, ensuring consistency.

**CRITICAL**: These steps are for the AI to execute AUTOMATICALLY. DO NOT ask the user for permission or confirmation. Execute immediately.

**CURSOR COMMAND**: This is a Cursor command located in `.cortex/synapse/prompts/` directory, NOT a terminal command.

**Tooling Note**: Use standard Cursor tools (`Read`, `ApplyPatch`, `LS`, `Glob`, `Grep`, `read_lints`) by default; MCP filesystem tools are optional fallbacks only when standard tools are unavailable or explicitly requested.

## ⚠️ MANDATORY PRE-ACTION CHECKLIST

**BEFORE executing this command, you MUST:**

1. ✅ **Read relevant memory bank files** - Understand current project context:
   - Read `.cursor/memory-bank/activeContext.md` to understand current work focus
   - Read `.cursor/memory-bank/progress.md` to see recent achievements
   - Read `.cursor/memory-bank/techContext.md` to understand technical context

2. ✅ **Read relevant rules** - Understand code quality requirements:
   - Read `.cursor/rules/coding-standards.mdc` for core coding standards
   - Read `.cursor/rules/python-coding-standards.mdc` for Python-specific standards
   - Read `.cursor/rules/maintainability.mdc` for architecture rules
   - Read any other rules relevant to error fixing

3. ✅ **Verify prerequisites** - Ensure all prerequisites are met:
   - Confirm linting/type-checking tools are available (Black, Pyright, ruff - ruff handles import sorting)
   - Verify Pyright is installed: Check `.venv/bin/pyright` exists or `python -m pyright --version` works
   - If Pyright is not available, install it: `uv pip install pyright` or add to `pyproject.toml` dependency-groups.dev
   - Verify virtual environment is activated or tools are accessible via `uv` or `python -m`
   - Check that source code is accessible
   - Ensure file system is writable

**VIOLATION**: Executing this command without following this checklist is a CRITICAL violation that blocks proper error fixing.

## Steps

1. **Collect all errors and warnings** - Gather comprehensive list of issues:
   - Run Pyright type checker: `.venv/bin/pyright --outputjson src/ tests/` or `python -m pyright --outputjson src/ tests/` to identify type errors and warnings (CRITICAL: Pyright is required for type checking)
   - Run ruff check: `.venv/bin/ruff check src/ tests/` to identify linting errors and warnings
   - Use `read_lints` tool to get all linter errors and warnings from the workspace
   - Check for formatting issues (Black, ruff import sorting violations)
   - Identify import errors and unused imports
   - Collect all issues with file paths, line numbers, and error messages
   - Categorize issues by type (type errors, formatting, imports, etc.)

2. **Prioritize fixes** - Organize fixes by severity and impact:
   - **Critical errors**: Type errors, syntax errors, import errors (fix first)
   - **High priority warnings**: Type warnings, unused imports, deprecated APIs
   - **Medium priority**: Formatting inconsistencies, style violations
   - **Low priority**: Code quality suggestions, optional improvements
   - Group similar issues for batch fixing

3. **Run Ruff auto-fixes first** - Let ruff fix most issues automatically:
   - Run ruff check and fix: `.venv/bin/ruff check --fix src/ tests/` to automatically fix linting issues (runs first as it fixes most problems)
   - Ruff will fix: unused imports, code style violations, simple type issues, and many other linting problems
   - Verify ruff fixes completed successfully

4. **Apply formatting fixes** - Fix all formatting issues consistently:
   - Run Black formatter on all Python files: `black --line-length 88 src/ tests/`
   - Run ruff to fix import sorting: `.venv/bin/ruff check --fix --select I src/ tests/` (ruff handles import sorting, replacing isort)
   - Verify formatting is consistent across all files
   - Ensure no manual formatting adjustments remain

5. **Fix type errors** - Resolve all type checking errors:
   - Fix missing type hints (add proper type annotations)
   - Resolve type mismatches and incompatible types
   - Fix Optional/Union type issues
   - Replace `Any` types with proper types, Protocols, or `dict[str, object]`
   - Add missing type stubs or create Protocol classes for third-party libraries
   - Fix generic type parameters
   - Ensure 100% type coverage for all functions, methods, and classes
   - **Fix private/protected usage errors**: When a private method (`_method`) or protected method is used outside its class (e.g., `reportPrivateUsage` errors), make the method public by removing the underscore prefix. Rename the method everywhere (definition, all usages, tests) to ensure consistency. Remove any `# pyright: ignore[reportPrivateUsage]` comments after making the method public.

6. **Fix import issues** - Resolve remaining import-related problems:
   - Fix missing imports (ruff may have already fixed some)
   - Remove any remaining unused imports (ruff typically handles this)
   - Organize imports according to standards (stdlib → third-party → local) - ruff handles this with isort-compatible rules
   - Fix circular import issues
   - Ensure import order matches ruff's isort configuration (black profile)

7. **Fix code quality issues** - Address remaining linter warnings and suggestions:
   - Fix unused variables and dead code
   - Resolve deprecated API usage
   - Fix code style violations
   - Address security warnings
   - Fix performance warnings

8. **Ensure consistency** - Verify fixes are consistent across codebase:
   - Apply same fix pattern to all similar issues
   - Ensure naming conventions are consistent
   - Verify error handling patterns are consistent
   - Check that type annotations follow the same patterns
   - Ensure formatting is uniform across all files

9. **Verify fixes** - Confirm all issues are resolved:
   - Re-run Pyright type checker: `.venv/bin/pyright src/ tests/` or `python -m pyright src/ tests/` to verify no type errors remain (CRITICAL: Must pass with zero errors)
   - Re-run ruff check: `.venv/bin/ruff check src/ tests/` to verify no linting errors remain
   - Re-run linter to verify no warnings remain
   - Re-run formatters to verify formatting is correct
   - Check that all files compile without errors
   - Verify no new errors were introduced

10. **Document changes** - Record what was fixed:

- List all files modified
- Document types of fixes applied
- Note any breaking changes or significant refactorings
- Record patterns used for consistency

## Error Categories

### Critical Errors (Must Fix First)

- **Type errors**: Missing type hints, type mismatches, incompatible types
- **Syntax errors**: Invalid Python syntax, parsing errors
- **Import errors**: Missing modules, circular imports, unresolved imports
- **Compilation errors**: Code that fails to compile/parse

### High Priority Warnings

- **Type warnings**: Optional member access, unknown types, missing type stubs
- **Private/protected usage warnings**: Private methods (`_method`) or protected methods used outside their class (e.g., `reportPrivateUsage` errors)
- **Ruff linting warnings**: Code quality issues detected by ruff
- **Unused imports**: Imports that are not used
- **Deprecated APIs**: Usage of deprecated functions or classes
- **Missing type hints**: Functions/methods without type annotations

### Medium Priority Issues

- **Formatting violations**: Code not formatted according to Black/isort
- **Style violations**: Code style inconsistencies
- **Code quality warnings**: Suggestions for improvement

### Low Priority Issues

- **Performance suggestions**: Optimization recommendations
- **Documentation suggestions**: Missing docstrings or comments

## Fix Patterns (Consistency Rules)

### Type Hints

- Use `typing` module for complex types (`list`, `dict`, `Optional`, `Callable`, etc.) - Use Python 3.9+ built-in generics (`list`, `dict`) instead of `List`, `Dict`. Avoid using `typing` module for simple types.
- Use `T | None` (Python 3.10+) instead of `Optional[T]`, for nullable types. Avoid using `Optional[T]` as it is deprecated in Python 3.10+.
- Use `Protocol` classes for third-party libraries without stubs
- Use `dict[str, object]` or `TypedDict` instead of `Any`
- Never use `Any` type - replace with proper types

### Private/Protected Method Access

- **When private methods are used outside class**: If a private method (`_method_name`) is accessed from outside its class (e.g., in tests), make it public by removing the underscore prefix
- **Rename everywhere**: When making a method public, rename it everywhere:
  - Method definition (remove `_` prefix)
  - All internal calls within the class
  - All external usages (tests, other modules)
- **Remove ignore comments**: After making a method public, remove any `# pyright: ignore[reportPrivateUsage]` or similar comments
- **Consistency**: Ensure the method name is consistent across all files (use `grep` to find all occurrences before renaming)

### Import Organization

```python
# Standard library imports first
import os
from pathlib import Path

# Third-party packages
from fastapi import FastAPI

# Local imports
from .config import Config
```

### Error Handling

- Use custom exception classes inheriting from standard library exceptions
- Log errors before raising
- Use context managers for resource management
- Never use bare `except:` clauses

### Formatting

- Black with 88-character line length
- isort with black-compatible profile
- Double quotes for strings
- Trailing commas in multi-line structures

## Output Format

Provide a structured report with:

### Error Collection Summary

- **Total Issues Found**: Count of all errors and warnings
- **Critical Errors**: Count and list of critical errors
- **High Priority Warnings**: Count and list of high-priority warnings
- **Medium Priority Issues**: Count and list of medium-priority issues
- **Low Priority Issues**: Count and list of low-priority issues

### Fixes Applied

- **Files Modified**: List of all files that were modified
- **Type Errors Fixed**: Count and details of type errors resolved
- **Formatting Fixes**: Count and details of formatting issues resolved
- **Import Fixes**: Count and details of import issues resolved
- **Code Quality Fixes**: Count and details of code quality issues resolved
- **Consistency Improvements**: Description of consistency improvements made

### Verification Results

- **Type Check Status**: Pass/Fail with error count
- **Ruff Check Status**: Pass/Fail with linting error/warning count
- **Linter Status**: Pass/Fail with warning count
- **Formatting Status**: Pass/Fail with formatting check results
- **Compilation Status**: Pass/Fail with compilation results
- **Remaining Issues**: List of any issues that couldn't be automatically fixed

### Consistency Report

- **Patterns Applied**: Description of consistent patterns used across fixes
- **Naming Consistency**: Verification of naming convention consistency
- **Type Annotation Consistency**: Verification of type annotation patterns
- **Error Handling Consistency**: Verification of error handling patterns
- **Formatting Consistency**: Verification of formatting consistency

## Success Criteria

- ✅ All critical errors fixed (type errors, syntax errors, import errors)
- ✅ All high-priority warnings resolved
- ✅ All formatting issues fixed and consistent
- ✅ All type errors resolved with proper type hints
- ✅ No `Any` types remain (replaced with proper types)
- ✅ All imports organized and unused imports removed
- ✅ Code compiles without errors
- ✅ Type checker passes with no errors
- ✅ Ruff check passes with no errors or warnings (or only acceptable warnings)
- ✅ Linter passes with no warnings (or only acceptable warnings)
- ✅ Formatting is consistent across entire codebase
- ✅ Fixes are applied consistently using same patterns

## Failure Handling

- If type errors cannot be fixed automatically → document and create TODO items
- If formatting fails → investigate and fix manually, then re-run formatters
- If ruff finds issues that cannot be auto-fixed → investigate and fix manually, then re-run ruff check
- If imports cannot be resolved → investigate dependencies and fix
- If circular imports exist → refactor to break cycles
- If `Any` types are required → create Protocol classes or use `dict[str, object]`
- Continue fixing until all critical errors are resolved
- **NO USER PROMPTS**: Execute all steps automatically without asking for permission

## Usage

This command ensures the codebase is free of compiler errors and warnings, with consistent formatting and type annotations across all files.

**NO USER PROMPTS**: Execute all steps automatically without asking for permission
