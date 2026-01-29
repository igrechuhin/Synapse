#!/usr/bin/env python3
"""Analyze code for performance issues without running it.

This script analyzes the codebase for common performance anti-patterns:
- O(n²) or worse algorithms
- Inefficient string operations
- Repeated expensive operations
- Missing caching opportunities

Configuration:
    SRC_DIR: Source directory path (default: auto-detected)
    FOCUS_MODULES: Comma-separated list of module paths to focus on (optional)
"""

import ast
import os
import sys
from collections import defaultdict
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

# Import shared utilities
try:
    from _utils import find_src_directory, get_config_path, get_project_root
except ImportError:
    # Fallback if running from different location
    sys.path.insert(0, str(Path(__file__).parent))
    from _utils import find_src_directory, get_config_path, get_project_root


class PerformanceIssue(BaseModel):
    """Performance issue structure."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    type: str = Field(description="Issue type")
    severity: str = Field(description="Issue severity (high/medium/low)")
    line: int = Field(ge=1, description="Line number")
    function: str | None = Field(
        default=None, description="Function name if applicable"
    )
    message: str = Field(description="Issue description")


class PerformanceAnalyzer(ast.NodeVisitor):
    """AST visitor to detect performance anti-patterns."""

    def __init__(self, filename: str):
        self.filename = filename
        self.issues: list[PerformanceIssue] = []
        self.function_name: str | None = None
        self.nested_loops = 0
        self.loop_depth = 0

    def visit_FunctionDef(self, node: ast.FunctionDef):
        old_function = self.function_name
        self.function_name = node.name
        self.generic_visit(node)
        self.function_name = old_function

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        old_function = self.function_name
        self.function_name = node.name
        self.generic_visit(node)
        self.function_name = old_function

    def visit_For(self, node: ast.For):
        self.loop_depth += 1

        if self.loop_depth >= 2:
            self.issues.append(
                PerformanceIssue(
                    type="nested_loops",
                    severity="high",
                    line=node.lineno,
                    function=self.function_name,
                    message=(
                        f"Nested loop detected (depth {self.loop_depth}) - "
                        "potential O(n²) or worse"
                    ),
                )
            )

        self.generic_visit(node)
        self.loop_depth -= 1

    def visit_While(self, node: ast.While):
        self.loop_depth += 1

        if self.loop_depth >= 2:
            self.issues.append(
                PerformanceIssue(
                    type="nested_loops",
                    severity="high",
                    line=node.lineno,
                    function=self.function_name,
                    message=(
                        f"Nested while loop (depth {self.loop_depth}) - "
                        "potential O(n²) or worse"
                    ),
                )
            )

        self.generic_visit(node)
        self.loop_depth -= 1

    def visit_Attribute(self, node: ast.Attribute):
        # Check for repeated list appends in loops
        if self.loop_depth > 0 and node.attr == "append":
            if isinstance(node.value, ast.Name):
                self.issues.append(
                    PerformanceIssue(
                        type="list_append_in_loop",
                        severity="medium",
                        line=node.lineno,
                        function=self.function_name,
                        message="List append in loop - consider list comprehension",
                    )
                )

        # Check for .split() in loops
        if self.loop_depth > 0 and node.attr == "split":
            self.issues.append(
                PerformanceIssue(
                    type="string_split_in_loop",
                    severity="medium",
                    line=node.lineno,
                    function=self.function_name,
                    message="String split in loop - consider moving outside",
                )
            )

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Check for repeated file operations
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in ["read_file", "write_file", "exists"]:
                if self.loop_depth > 0:
                    self.issues.append(
                        PerformanceIssue(
                            type="file_io_in_loop",
                            severity="high",
                            line=node.lineno,
                            function=self.function_name,
                            message=(
                                f"File I/O ({node.func.attr}) in loop - "
                                "major performance impact"
                            ),
                        )
                    )

            # Check for len() in loop condition (common in while loops)
            if node.func.attr == "len" and self.loop_depth > 0:
                self.issues.append(
                    PerformanceIssue(
                        type="len_in_loop",
                        severity="low",
                        line=node.lineno,
                        function=self.function_name,
                        message="len() in loop - consider caching",
                    )
                )

        self.generic_visit(node)


def analyze_file(filepath: Path) -> list[PerformanceIssue]:
    """Analyze a Python file for performance issues."""
    try:
        with open(filepath) as f:
            content = f.read()

        tree = ast.parse(content, filename=str(filepath))
        analyzer = PerformanceAnalyzer(str(filepath))
        analyzer.visit(tree)
        return analyzer.issues
    except SyntaxError as e:
        print(f"Syntax error in {filepath}: {e}")
        return []
    except Exception as e:
        print(f"Error analyzing {filepath}: {e}")
        return []


def main():
    """Analyze all Python files in the project."""
    # Get project root and source directory
    script_path = Path(__file__)
    project_root = get_project_root(script_path)

    # Allow override via environment variable
    src_dir = get_config_path("SRC_DIR")
    if src_dir is None:
        src_dir = find_src_directory(project_root)
    else:
        # Make path relative to project root if not absolute
        if not src_dir.is_absolute():
            src_dir = project_root / src_dir
        else:
            src_dir = Path(src_dir)

    if not src_dir.exists():
        print(f"Error: Source directory {src_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    # Get focus modules from environment or analyze all
    focus_modules_str = os.getenv("FOCUS_MODULES")
    if focus_modules_str:
        focus_modules = [m.strip() for m in focus_modules_str.split(",")]
    else:
        # Analyze all Python files
        focus_modules = None

    all_issues: defaultdict[str, list[PerformanceIssue]] = defaultdict(list)
    total_issues = 0

    print("=" * 70)
    print("Performance Analysis")
    print("=" * 70)
    print()

    if focus_modules:
        # Analyze specific modules
        for module_path in focus_modules:
            filepath = src_dir / module_path
            if not filepath.exists():
                print(f"⚠️  File not found: {module_path}")
                continue

            issues = analyze_file(filepath)
            if issues:
                all_issues[module_path] = issues
                total_issues += len(issues)

                print(f"\n📁 {module_path}")
                print("-" * 70)

                # Group by severity
                by_severity_focus: defaultdict[str, list[PerformanceIssue]] = (
                    defaultdict(list)
                )
                for issue in issues:
                    by_severity_focus[issue.severity].append(issue)

                for severity in ["high", "medium", "low"]:
                    if severity in by_severity_focus:
                        for issue in by_severity_focus[severity]:
                            severity_icon = {
                                "high": "🔴",
                                "medium": "🟡",
                                "low": "🟢",
                            }[severity]
                            print(
                                f"  {severity_icon} Line {issue.line:4d} "
                                + f"[{issue.function or 'module'}]: {issue.message}"
                            )
    else:
        # Analyze all Python files
        for py_file in sorted(src_dir.rglob("*.py")):
            if "__pycache__" in str(py_file) or py_file.name.startswith("test_"):
                continue

            try:
                relative_path = py_file.relative_to(src_dir)
            except ValueError:
                relative_path = py_file

            issues = analyze_file(py_file)
            if issues:
                all_issues[str(relative_path)] = issues
                total_issues += len(issues)

                print(f"\n📁 {relative_path}")
                print("-" * 70)

                # Group by severity
                by_severity_all: defaultdict[str, list[PerformanceIssue]] = defaultdict(
                    list
                )
                for issue in issues:
                    by_severity_all[issue.severity].append(issue)

                for severity in ["high", "medium", "low"]:
                    if severity in by_severity_all:
                        for issue in by_severity_all[severity]:
                            severity_icon = {
                                "high": "🔴",
                                "medium": "🟡",
                                "low": "🟢",
                            }[severity]
                            print(
                                f"  {severity_icon} Line {issue.line:4d} "
                                + f"[{issue.function or 'module'}]: {issue.message}"
                            )

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total files analyzed: {len(all_issues)}")
    print(f"Total issues found: {total_issues}")

    if total_issues > 0:
        print("\nIssues by severity:")
        severity_counts: defaultdict[str, int] = defaultdict(int)
        for issues in all_issues.values():
            for issue in issues:
                severity_counts[issue.severity] += 1

        for severity in ["high", "medium", "low"]:
            if severity in severity_counts:
                print(f"  {severity.capitalize():8s}: {severity_counts[severity]}")

        print("\nTop priority fixes:")
        high_priority: list[tuple[str, PerformanceIssue]] = []
        for module, issues in all_issues.items():
            for issue in issues:
                if issue.severity == "high":
                    high_priority.append((module, issue))

        for i, (module, issue) in enumerate(high_priority[:5], 1):
            print(f"  {i}. {module}:{issue.line} - {issue.message}")

    print("=" * 70)


if __name__ == "__main__":
    main()
