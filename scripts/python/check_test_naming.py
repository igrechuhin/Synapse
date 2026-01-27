#!/usr/bin/env python3
"""Pre-commit hook to enforce test function naming conventions.

This script checks that all test functions in test files follow the naming
convention: test_<name> (with underscore after "test").

Test functions must start with "test_" followed by an underscore, not "test"
directly followed by a letter (e.g., "testread" is invalid, "test_read" is valid).

Configuration:
    TESTS_DIR: Tests directory path (default: auto-detected)
"""

import ast
import sys
from pathlib import Path

# Import shared utilities
try:
    from _utils import get_config_path, get_project_root
except ImportError:
    # Fallback if running from different location
    sys.path.insert(0, str(Path(__file__).parent))
    from _utils import get_config_path, get_project_root


class TestNamingVisitor(ast.NodeVisitor):
    """AST visitor to find test functions with invalid naming."""

    def __init__(self, source_lines: list[str]):
        """Initialize visitor.

        Args:
            source_lines: List of source code lines
        """
        self.source_lines = source_lines
        self.violations: list[tuple[str, int]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Visit a function definition.

        Args:
            node: AST node for function definition
        """
        self._check_test_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Visit an async function definition.

        Args:
            node: AST node for async function definition
        """
        self._check_test_function(node)
        self.generic_visit(node)

    def _check_test_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        """Check if test function follows naming convention.

        Args:
            node: Function node to check
        """
        func_name = node.name

        # Check if function name starts with "test" but not "test_"
        # Pattern: "test" followed by a lowercase letter (invalid)
        # Valid: "test_", "test_something", "test_read"
        # Invalid: "testread", "testgenerate", "testcreate"
        if func_name.startswith("test") and len(func_name) > 4:
            # Check if it's "test" followed directly by a letter (no underscore)
            if func_name[4].isalpha() and func_name[4].islower():
                self.violations.append((func_name, node.lineno))


def check_test_naming(path: Path) -> list[tuple[str, int]]:
    """Check all test functions in file for naming violations.

    Args:
        path: Path to Python test file to check

    Returns:
        List of violations as (function_name, line_number)
    """
    try:
        with open(path, encoding="utf-8") as f:
            source = f.read()
            source_lines = source.split("\n")
    except Exception as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
        return []

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as e:
        print(f"Syntax error in {path}: {e}", file=sys.stderr)
        return []

    visitor = TestNamingVisitor(source_lines)
    visitor.visit(tree)

    return visitor.violations


def find_test_directories(project_root: Path) -> list[Path]:
    """Find test directories to check.

    Args:
        project_root: Path to project root

    Returns:
        List of test directory paths
    """
    test_dirs: list[Path] = []

    # Check for explicit TESTS_DIR configuration
    tests_dir = get_config_path("TESTS_DIR")
    if tests_dir is not None:
        if not tests_dir.is_absolute():
            tests_dir = project_root / tests_dir
        else:
            tests_dir = Path(tests_dir)
        if tests_dir.exists():
            test_dirs.append(tests_dir)
            return test_dirs

    # Try common test directory patterns
    for pattern in ["tests", "test"]:
        candidate = project_root / pattern
        if candidate.exists() and candidate.is_dir():
            test_dirs.append(candidate)
            break

    return test_dirs


def main():
    """Check all test files for naming violations."""
    # Get project root
    script_path = Path(__file__)
    project_root = get_project_root(script_path)

    # Find test directories
    test_dirs = find_test_directories(project_root)

    if not test_dirs:
        print(
            "Warning: No test directories found",
            file=sys.stderr,
        )
        print(f"Project root: {project_root}", file=sys.stderr)
        sys.exit(0)  # Not an error, just nothing to check

    all_violations: list[tuple[Path, str, int]] = []

    for test_dir in test_dirs:
        for test_file in test_dir.rglob("test_*.py"):
            # Skip __pycache__
            if "__pycache__" in str(test_file):
                continue

            violations = check_test_naming(test_file)
            for func_name, line_num in violations:
                all_violations.append((test_file, func_name, line_num))

        # Also check files ending with _test.py
        for test_file in test_dir.rglob("*_test.py"):
            if "__pycache__" in str(test_file):
                continue

            violations = check_test_naming(test_file)
            for func_name, line_num in violations:
                all_violations.append((test_file, func_name, line_num))

    if all_violations:
        print("❌ Test function naming violations detected:", file=sys.stderr)
        print(file=sys.stderr)
        print(
            "Test functions must follow the pattern: test_<name>",
            file=sys.stderr,
        )
        print(
            "Invalid: testread, testgenerate, testcreate, etc.",
            file=sys.stderr,
        )
        print(
            "Valid: test_read, test_generate, test_create, etc.",
            file=sys.stderr,
        )
        print(file=sys.stderr)

        # Group by file
        by_file: dict[Path, list[tuple[str, int]]] = {}
        for path, func_name, line_num in all_violations:
            if path not in by_file:
                by_file[path] = []
            by_file[path].append((func_name, line_num))

        for path in sorted(by_file.keys()):
            try:
                relative_path = path.relative_to(project_root)
            except ValueError:
                relative_path = path
            print(f"  {relative_path}:", file=sys.stderr)
            for func_name, line_num in sorted(by_file[path], key=lambda x: x[1]):
                # Suggest correct name
                # Extract the part after "test" and add underscore
                if func_name.startswith("test") and len(func_name) > 4:
                    rest = func_name[4:]
                    suggested = f"test_{rest}"
                    print(
                        (
                            f"    Line {line_num}: {func_name}() -> "
                            + f"should be {suggested}()"
                        ),
                        file=sys.stderr,
                    )
            print(file=sys.stderr)

        total_violations = len(all_violations)
        print(
            (
                f"Total violations: {total_violations} test function(s) "
                + "with invalid naming"
            ),
            file=sys.stderr,
        )
        sys.exit(1)

    print("✅ All test functions follow naming convention (test_<name>)")
    sys.exit(0)


if __name__ == "__main__":
    main()
