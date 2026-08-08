#!/usr/bin/env python3
"""Pre-commit hook to enforce file size limits for PHP.

Configuration:
    MAX_FILE_LINES:       Hard limit (default: 400)
    FILE_SIZE_WARN_LINES: Warning threshold (default: 350)
"""

from __future__ import annotations

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


MAX_LINES = get_config_int("MAX_FILE_LINES", 400)
WARN_LINES = get_config_int("FILE_SIZE_WARN_LINES", 350)


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

    violations: list[tuple[Path, int]] = []
    warnings_list: list[tuple[Path, int]] = []

    for php_file in php_files:
        if not php_file.exists():
            continue
        lines = count_logical_lines(php_file.read_text(encoding="utf-8"))
        if lines > MAX_LINES:
            violations.append((php_file, lines))
        elif lines > WARN_LINES:
            warnings_list.append((php_file, lines))

    if warnings_list:
        print("⚠️  File size warnings (approaching limit):", file=sys.stderr)
        for path, lines in sorted(warnings_list, key=lambda x: -x[1]):
            msg = f"  {_relative(path, project_root)}: {lines} lines (warn above {WARN_LINES}, max {MAX_LINES})"
            print(msg, file=sys.stderr)
        print(file=sys.stderr)

    if violations:
        print("❌ File size violations detected:", file=sys.stderr)
        print(file=sys.stderr)
        for path, lines in sorted(violations, key=lambda x: -x[1]):
            excess = lines - MAX_LINES
            msg = f"  {_relative(path, project_root)}: {lines} lines (max: {MAX_LINES}, excess: {excess})"
            print(msg, file=sys.stderr)
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
