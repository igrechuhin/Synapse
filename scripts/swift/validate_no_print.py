#!/usr/bin/env python3
"""Enforce SharedLogger usage — ban bare print() in Swift production sources.

All production logging must use SharedLogger. print() is only allowed in:
  - Test files
  - CLI entry points (cli.swift, main.swift)
  - Generated files (.pb.swift, .generated.swift)

Zero-tolerance: any violation exits with code 1.

Configuration:
    SOURCES_DIR: Directory to scan (default: Sources/)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    from _utils import get_config_path, get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
    from _utils import get_config_path, get_project_root


_GENERATED_SUFFIXES = (".pb.swift", ".generated.swift")
_ALLOWED_FILENAMES = {"cli.swift", "main.swift"}

_PRINT_RE = re.compile(r"\bprint\s*\(")


def check_file(path: Path, project_root: Path) -> list[str]:
    """Check a single Swift file for bare print() calls.

    Args:
        path: Path to the .swift file.
        project_root: Project root for relative paths in messages.

    Returns:
        List of human-readable violation strings.
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
        return []

    try:
        rel = path.relative_to(project_root)
    except ValueError:
        rel = path

    violations: list[str] = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("//"):
            continue
        if _PRINT_RE.search(line):
            violations.append(f"  {rel}:{i}: {line.rstrip()}")
    return violations


def main() -> None:
    """Scan Swift production sources for bare print() calls."""
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

    all_violations: list[str] = []

    for swift_file in sorted(sources_dir.rglob("*.swift")):
        if any(swift_file.name.endswith(s) for s in _GENERATED_SUFFIXES):
            continue
        if "Tests" in swift_file.parts:
            continue
        if swift_file.name in _ALLOWED_FILENAMES:
            continue
        all_violations.extend(check_file(swift_file, project_root))

    if all_violations:
        print(
            "❌ print() usage in production code (use SharedLogger instead):",
            file=sys.stderr,
        )
        print(file=sys.stderr)
        for v in all_violations:
            print(v, file=sys.stderr)
        print(file=sys.stderr)
        print(
            f"Found {len(all_violations)} print() violation(s).",
            file=sys.stderr,
        )
        sys.exit(1)

    print("✅ No bare print() calls in production Swift code")
    sys.exit(0)


if __name__ == "__main__":
    main()
