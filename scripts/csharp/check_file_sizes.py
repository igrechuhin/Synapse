#!/usr/bin/env python3
"""
Pre-commit/quality gate helper to enforce C# file size limits.

This repo is primarily Swift, but the quality gate expects C# scripts to
exist for multi-language parity. When no C# sources are present, this script
exits successfully.

Configuration (env vars):
  MAX_FILE_LINES  - hard limit (default: 400)
  WARN_FILE_LINES - soft warning threshold (default: 350)
  SOURCES_DIR     - directory to scan (default: Sources/)
  FILES           - optional newline-separated explicit file list to scan
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    from _utils import get_config_int, get_config_path, get_project_root
except ImportError:
    # When run outside a properly configured environment, make sure we can
    # import Synapse shared script utilities.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
    from _utils import get_config_int, get_config_path, get_project_root


MAX_FILE_LINES = get_config_int("MAX_FILE_LINES", 400)
WARN_FILE_LINES = get_config_int("WARN_FILE_LINES", 350)

_EXCLUDED_SUFFIXES: tuple[str, ...] = (
    ".g.cs",
    ".Designer.cs",
)


def count_logical_lines(path: Path) -> int:
    """Count non-blank, non-comment lines in a C# file.

    This uses a lightweight heuristic: lines starting with `//` are treated as
    comments; lines starting with `/*` are ignored. It does not fully parse
    block comments, which is sufficient for size-limit enforcement.
    """

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
        return 0

    count = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("//"):
            continue
        if stripped.startswith("/*"):
            continue
        # Middle-of-block comment lines often start with '*'.
        if stripped.startswith("*"):
            continue
        count += 1

    return count


def is_excluded(path: Path) -> bool:
    name = path.name
    if any(name.endswith(s) for s in _EXCLUDED_SUFFIXES):
        return True
    # Common build/output directories.
    parts = set(path.parts)
    if {"bin", "obj", ".build"} & parts:
        return True
    return False


def _get_files_from_env() -> list[Path] | None:
    files_env = os.environ.get("FILES")
    if files_env is None:
        return None
    stripped = files_env.strip()
    if not stripped:
        return None
    return [Path(p) for p in stripped.splitlines() if p]


def main() -> None:
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

    files_from_env = _get_files_from_env()

    if files_from_env is not None:
        cs_files = [
            f for f in files_from_env if f.suffix == ".cs" and not is_excluded(f)
        ]
    else:
        if not sources_dir.exists():
            print(f"✅ No C# sources directory detected (skipped): {sources_dir}")
            sys.exit(0)

        cs_files = [f for f in sorted(sources_dir.rglob("*.cs")) if not is_excluded(f)]

        tests_dir = sources_dir.parent / "Tests"
        if tests_dir.exists():
            cs_files += [
                f for f in sorted(tests_dir.rglob("*.cs")) if not is_excluded(f)
            ]

    violations: list[tuple[Path, int]] = []
    warnings: list[tuple[Path, int]] = []

    def rel(p: Path) -> Path:
        try:
            return p.relative_to(project_root)
        except ValueError:
            return p

    for cs_file in cs_files:
        if is_excluded(cs_file):
            continue
        logical = count_logical_lines(cs_file)
        if logical > MAX_FILE_LINES:
            violations.append((cs_file, logical))
        elif logical > WARN_FILE_LINES:
            warnings.append((cs_file, logical))

    if warnings:
        print("⚠️  C# file size warnings (approaching limit):", file=sys.stderr)
        for path, lines in sorted(warnings, key=lambda x: -x[1]):
            print(
                f"  {rel(path)}: {lines} lines (warn >{WARN_FILE_LINES}, max {MAX_FILE_LINES})",
                file=sys.stderr,
            )
        print(file=sys.stderr)

    if violations:
        print("❌ C# file size violations detected:", file=sys.stderr)
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

    print(f"✅ All C# files within size limits ({MAX_FILE_LINES} lines)")
    sys.exit(0)


if __name__ == "__main__":
    main()
