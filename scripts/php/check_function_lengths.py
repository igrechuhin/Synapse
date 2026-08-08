#!/usr/bin/env python3
"""Pre-commit hook to enforce PHP function length limits.

Uses a brace-balanced heuristic to find function bodies, matching the approach
in scripts/swift/check_function_lengths.py.

Configuration:
    MAX_FUNCTION_LINES: Hard limit (default: 30)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    from _utils import get_config_int
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
    from _utils import get_config_int

from _php_toolchain import (
    allow_full_scan,
    count_logical_lines,
    php_files_from_env,
    php_project_root,
    php_source_dirs,
)


MAX_FUNCTION_LINES = get_config_int("MAX_FUNCTION_LINES", 30)

_FUNC_START_RE = re.compile(
    r"^\s*(?:(?:final|abstract|public|protected|private|static)\s+)*function\s+\w+"
)


def find_function_bodies(lines: list[str]) -> list[tuple[str, int, int]]:
    """Locate function bodies by brace balancing.

    Args:
        lines: All lines of the file (0-indexed).

    Returns:
        List of (function_name, start_line_number, logical_body_lines).
    """
    results: list[tuple[str, int, int]] = []
    index = 0

    while index < len(lines):
        if not _FUNC_START_RE.match(lines[index]):
            index += 1
            continue

        name_match = re.search(r"function\s+(\w+)", lines[index])
        name = name_match.group(1) if name_match else "<anonymous>"

        depth = 0
        found_open = False
        body: list[str] = []
        cursor = index

        while cursor < len(lines):
            for char in lines[cursor]:
                if char == "{":
                    depth += 1
                    found_open = True
                elif char == "}":
                    depth -= 1
            if found_open:
                body.append(lines[cursor])
                if depth == 0:
                    break
            if not found_open and ";" in lines[cursor]:
                break
            cursor += 1

        if found_open:
            logical = count_logical_lines("\n".join(body[1:-1]))
            results.append((name, index + 1, logical))
            index = cursor + 1
        else:
            index += 1

    return results


def _collect_files(project_root: Path) -> list[Path] | None:
    """Resolve the PHP files to check, or None when the scan is skipped."""
    from_env = php_files_from_env()
    if from_env is not None:
        return from_env

    if not allow_full_scan():
        return None

    files: list[Path] = []
    for directory in php_source_dirs(project_root):
        files.extend(sorted(directory.rglob("*.php")))
    return files


def _relative(path: Path, root: Path) -> Path:
    try:
        return path.resolve().relative_to(root.resolve())
    except ValueError:
        return path


def main() -> None:
    project_root = php_project_root(Path(__file__))
    php_files = _collect_files(project_root)

    if php_files is None:
        print("✅ No FILES provided and ALLOW_FULL_SCAN!=1 (skipped)")
        sys.exit(0)

    if not php_files:
        print("✅ No PHP sources detected (skipped)")
        sys.exit(0)

    violations: list[tuple[Path, str, int, int]] = []

    for php_file in php_files:
        if not php_file.exists():
            continue
        lines = php_file.read_text(encoding="utf-8").splitlines()
        for name, line_no, length in find_function_bodies(lines):
            if length > MAX_FUNCTION_LINES:
                violations.append((php_file, name, line_no, length))

    if violations:
        print("❌ Function length violations detected:", file=sys.stderr)
        print(file=sys.stderr)
        for path, name, line_no, length in sorted(violations, key=lambda x: -x[3]):
            msg = f"  {_relative(path, project_root)}:{line_no} {name}(): {length} lines (max: {MAX_FUNCTION_LINES})"
            print(msg, file=sys.stderr)
        print(file=sys.stderr)
        print(f"Total violations: {len(violations)} function(s)", file=sys.stderr)
        sys.exit(1)

    print(f"✅ All functions within {MAX_FUNCTION_LINES} lines")
    sys.exit(0)


if __name__ == "__main__":
    main()
