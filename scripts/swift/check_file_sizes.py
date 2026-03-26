#!/usr/bin/env python3
"""Pre-commit hook to enforce Swift file size limits.

Checks all .swift files under Sources/ (excluding generated files and Tests/)
against the configured line limit. Files between the warn threshold and the
max are reported as warnings; files over the max cause exit 1.

Configuration:
    MAX_FILE_LINES:  Hard limit — exit 1 if exceeded (default: 400)
    WARN_FILE_LINES: Soft warning threshold (default: 350)
    SOURCES_DIR:     Directory to scan (default: Sources/)
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from _utils import get_config_int, get_config_path, get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from _utils import get_config_int, get_config_path, get_project_root


MAX_FILE_LINES = get_config_int("MAX_FILE_LINES", 400)
WARN_FILE_LINES = get_config_int("WARN_FILE_LINES", 350)

_GENERATED_SUFFIXES = (".pb.swift", ".generated.swift")


def count_logical_lines(path: Path) -> int:
    """Count non-blank, non-comment lines in a Swift file.

    Args:
        path: Path to the .swift file.

    Returns:
        Number of logical lines of code.
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
        return 0

    count = 0
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("//"):
            count += 1
    return count


def is_excluded(path: Path) -> bool:
    """Return True if this file should be skipped.

    Args:
        path: Path to the .swift file.

    Returns:
        True if the file should be excluded from checks.
    """
    if any(path.name.endswith(s) for s in _GENERATED_SUFFIXES):
        return True
    if "Tests" in path.parts:
        return True
    return False


def main() -> None:
    """Check all Swift files for size violations."""
    project_root = get_project_root(Path(__file__))

    sources_dir_override = get_config_path("SOURCES_DIR")
    if sources_dir_override is not None:
        sources_dir = (
            sources_dir_override
            if sources_dir_override.is_absolute()
            else project_root / sources_dir_override
        )
    else:
        sources_dir = project_root / "Sources"

    if not sources_dir.exists():
        print(f"❌ Sources directory not found: {sources_dir}", file=sys.stderr)
        sys.exit(1)

    violations: list[tuple[Path, int]] = []
    warnings_list: list[tuple[Path, int]] = []

    for swift_file in sorted(sources_dir.rglob("*.swift")):
        if is_excluded(swift_file):
            continue
        lines = count_logical_lines(swift_file)
        if lines > MAX_FILE_LINES:
            violations.append((swift_file, lines))
        elif lines > WARN_FILE_LINES:
            warnings_list.append((swift_file, lines))

    def rel(p: Path) -> Path:
        try:
            return p.relative_to(project_root)
        except ValueError:
            return p

    if warnings_list:
        print("⚠️  File size warnings (approaching limit):", file=sys.stderr)
        for path, lines in sorted(warnings_list, key=lambda x: -x[1]):
            print(
                f"  {rel(path)}: {lines} lines "
                f"(warn >{WARN_FILE_LINES}, max {MAX_FILE_LINES})",
                file=sys.stderr,
            )
        print(file=sys.stderr)

    if violations:
        print("❌ File size violations detected:", file=sys.stderr)
        print(file=sys.stderr)
        for path, lines in sorted(violations, key=lambda x: -x[1]):
            excess = lines - MAX_FILE_LINES
            print(
                f"  {rel(path)}: {lines} lines (max: {MAX_FILE_LINES}, excess: {excess})",
                file=sys.stderr,
            )
        print(file=sys.stderr)
        print(
            f"Total violations: {len(violations)} file(s) exceed {MAX_FILE_LINES} lines",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"✅ All Swift files within size limits ({MAX_FILE_LINES} lines)")
    sys.exit(0)


if __name__ == "__main__":
    main()
