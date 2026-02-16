#!/usr/bin/env python3
"""Pre-commit hook to enforce file size limits.

This script checks that all Python files in the source directory are under
the configured line limit (default: 400 lines, excluding blank lines,
comments, and docstrings).

Configuration:
    MAX_FILE_LINES: Maximum lines per file (default: 400)
    SRC_DIR: Source directory path (default: auto-detected)
"""

import sys
from pathlib import Path

# Import shared utilities
try:
    from _utils import (
        find_src_directory,
        get_config_int,
        get_config_path,
        get_project_root,
    )
except ImportError:
    # Fallback if running from different location
    sys.path.insert(0, str(Path(__file__).parent))
    from _utils import (
        find_src_directory,
        get_config_int,
        get_config_path,
        get_project_root,
    )

# Reuse cortex.core.constants when run from Cortex repo; else config or 400
_default_max_file_lines = 400
_default_excluded: tuple[str, ...] = ("models.py",)
try:
    _script_path = Path(__file__).resolve()
    _proj_root = get_project_root(_script_path)
    _src = _proj_root / "src"
    if _src.exists() and str(_src) not in sys.path:
        sys.path.insert(0, str(_src))
    from cortex.core.constants import (
        FILE_SIZE_EXCLUDED_FILENAMES as _default_excluded,
        MAX_FILE_LINES as _default_max_file_lines,
    )
except (ImportError, RuntimeError):
    pass
MAX_LINES = get_config_int("MAX_FILE_LINES", _default_max_file_lines)
EXCLUDED_FILENAMES = _default_excluded


def count_lines(path: Path) -> int:
    """Count non-blank, non-comment, non-docstring lines.

    Args:
        path: Path to Python file to count

    Returns:
        Number of logical lines of code
    """
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
        return 0

    count = 0
    in_docstring = False

    for line in lines:
        stripped = line.strip()

        # Track docstrings
        if '"""' in stripped or "'''" in stripped:
            in_docstring = not in_docstring
            continue

        if in_docstring:
            continue

        # Skip blank lines and comments
        if not stripped or stripped.startswith("#"):
            continue

        count += 1

    return count


def main():
    """Check all Python files for size violations."""
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
        print(f"Project root: {project_root}", file=sys.stderr)
        sys.exit(1)

    violations: list[tuple[Path, int]] = []

    # Must match cortex.core.constants.FILE_SIZE_EXCLUDED_FILENAMES and pre_commit_helpers
    for py_file in src_dir.glob("**/*.py"):
        # Skip __pycache__ and test files
        if "__pycache__" in str(py_file) or py_file.name.startswith("test_"):
            continue
        # Skip excluded filenames (e.g. Pydantic model definitions)
        if py_file.name in EXCLUDED_FILENAMES:
            continue

        lines = count_lines(py_file)
        if lines > MAX_LINES:
            violations.append((py_file, lines))

    if violations:
        print("❌ File size violations detected:", file=sys.stderr)
        print(file=sys.stderr)

        def sort_key(x: tuple[Path, int]) -> int:
            return x[1]

        for path, lines in sorted(violations, key=sort_key, reverse=True):
            try:
                relative_path: Path = path.relative_to(project_root)
            except ValueError:
                relative_path = path
            excess: int = lines - MAX_LINES
            print(
                (
                    f"  {relative_path}: {lines} lines "
                    + f"(max: {MAX_LINES}, excess: {excess})"
                ),
                file=sys.stderr,
            )
        print(file=sys.stderr)
        print(
            f"Total violations: {len(violations)} file(s) exceed {MAX_LINES} lines",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"✅ All files within size limits ({MAX_LINES} lines)")
    sys.exit(0)


if __name__ == "__main__":
    main()
