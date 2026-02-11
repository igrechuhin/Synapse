#!/usr/bin/env python3
"""Pre-commit check: detect unawaited coroutines in test files.

Scans src/ for async function and method names, then scans test files for
calls to those names that are not awaited. Reports file and line number.
Exit 0 = no issues, 1 = unawaited coroutines found.

Configuration:
    TESTS_DIR: Tests directory path (default: auto-detected)
"""

import ast
import sys
from pathlib import Path

try:
    from _utils import get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from _utils import get_project_root


def _collect_async_names_from_tree(tree: ast.AST) -> set[str]:
    """Collect async function/method names from a module AST."""
    names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            names.add(node.name)
    return names


# Names that are too generic (often sync in tests: dict.get, mock.get, etc.).
# Excluded to avoid massive false positives; focus on distinct async APIs.
_ASYNC_NAME_BLOCKLIST: frozenset[str] = frozenset(
    {"get", "set", "run", "write", "read", "load", "validate", "invalidate", "reset"}
)


def collect_async_names_from_src(project_root: Path, src_dir: Path) -> set[str]:
    """Collect async function and method names from src/, excluding generic names."""
    all_names: set[str] = set()
    if not src_dir.exists():
        return all_names
    for py_path in src_dir.rglob("*.py"):
        if "__pycache__" in str(py_path):
            continue
        try:
            source = py_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            names = _collect_async_names_from_tree(tree)
            all_names |= {n for n in names if n not in _ASYNC_NAME_BLOCKLIST}
        except (SyntaxError, OSError):
            continue
    return all_names


class _UnawaitedCallVisitor(ast.NodeVisitor):
    """Visitor that finds calls to async names that are not awaited."""

    def __init__(self, async_names: set[str], source_lines: list[str]) -> None:
        self.async_names = async_names
        self.source_lines = source_lines
        self._stack: list[ast.AST] = []
        self.violations: list[tuple[int, int, str]] = []  # (line, col, name)

    def _call_target_name(self, node: ast.Call) -> str | None:
        """Return the name of the called function if it's a known async name."""
        func = node.func
        if isinstance(func, ast.Name):
            return func.id if func.id in self.async_names else None
        if isinstance(func, ast.Attribute):
            return func.attr if func.attr in self.async_names else None
        return None

    def _is_awaited(self) -> bool:
        """True if current call is inside an Await node."""
        for n in self._stack:
            if isinstance(n, ast.Await):
                return True
        return False

    def generic_visit(self, node: ast.AST) -> None:
        self._stack.append(node)
        try:
            _ = super().generic_visit(node)
        finally:
            _ = self._stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        name = self._call_target_name(node)
        if name is not None and not self._is_awaited():
            line = node.lineno
            col = node.col_offset
            self.violations.append((line, col, name))
        self.generic_visit(node)


def check_file(path: Path, async_names: set[str]) -> list[tuple[int, int, str]]:
    """Check a single test file for unawaited coroutine calls.

    Returns list of (line, col, name) for each violation.
    """
    if not async_names:
        return []
    try:
        source = path.read_text(encoding="utf-8")
        lines = source.splitlines()
    except OSError:
        return []
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []
    visitor = _UnawaitedCallVisitor(async_names, lines)
    _ = visitor.visit(tree)
    return visitor.violations


def find_test_directories(project_root: Path) -> list[Path]:
    """Find test directories (tests/ or test/)."""
    for name in ("tests", "test"):
        candidate = project_root / name
        if candidate.exists() and candidate.is_dir():
            return [candidate]
    return []


def find_test_files(test_dirs: list[Path]) -> list[Path]:
    """Collect test_*.py and *_test.py under test directories."""
    files: list[Path] = []
    for d in test_dirs:
        for p in d.rglob("test_*.py"):
            if "__pycache__" not in str(p):
                files.append(p)
        for p in d.rglob("*_test.py"):
            if "__pycache__" not in str(p):
                files.append(p)
    return sorted(set(files))


def main() -> int:
    """Run check. Exit 0 if no issues, 1 if unawaited coroutines found."""
    script_path = Path(__file__).resolve()
    project_root = get_project_root(script_path)
    src_dir = project_root / "src"
    async_names = collect_async_names_from_src(project_root, src_dir)
    test_dirs = find_test_directories(project_root)
    if not test_dirs:
        print("No test directories found; skipping async test check.", file=sys.stderr)
        return 0
    test_files = find_test_files(test_dirs)
    all_violations: list[tuple[Path, int, int, str]] = []
    for path in test_files:
        for line, col, name in check_file(path, async_names):
            all_violations.append((path, line, col, name))
    if not all_violations:
        print("All async calls in tests are awaited.")
        return 0
    print("Unawaited coroutines detected (add await):", file=sys.stderr)
    for path, line, col, name in sorted(all_violations, key=lambda x: (x[0], x[1])):
        try:
            rel = path.relative_to(project_root)
        except ValueError:
            rel = path
        print(f"  {rel}:{line}:{col}: {name}()", file=sys.stderr)
    print(
        "Fix: ensure every call to an async function is awaited (e.g. await x()).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
