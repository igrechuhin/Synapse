#!/usr/bin/env python3
"""
Pre-commit/quality gate helper to enforce C# function length limits.

This repo is primarily Swift, but the quality gate expects C# scripts to
exist for multi-language parity. When no C# sources are present, this script
exits successfully.

Configuration (env vars):
  MAX_FUNCTION_LINES - hard limit (default: 30)
  SOURCES_DIR         - directory to scan (default: Sources/)
  FILES               - optional newline-separated explicit file list to scan
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

try:
    from _utils import get_config_int, get_config_path, get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
    from _utils import get_config_int, get_config_path, get_project_root


MAX_FUNCTION_LINES = get_config_int("MAX_FUNCTION_LINES", 30)

_EXCLUDED_SUFFIXES: tuple[str, ...] = (
    ".g.cs",
    ".Designer.cs",
)

# Heuristic: a line starting a method-like construct.
# This is intentionally conservative to avoid false positives.
_FUNC_START_RE = re.compile(
    r"^\s*(?:public|private|protected|internal)\b"
    r"(?:[\s\w<>,\[\]]+)?"
    r"\s*\w+\s*\([^;{}]*\)\s*$"
)


def is_excluded(path: Path) -> bool:
    name = path.name
    if any(name.endswith(s) for s in _EXCLUDED_SUFFIXES):
        return True
    parts = set(path.parts)
    if {"bin", "obj", ".build"} & parts:
        return True
    return False


def count_logical_lines_in_body(lines: list[str], body_start: int) -> int:
    """Count non-blank, non-comment lines inside a brace-delimited body."""

    depth = 0
    logical = 0
    found_open = False
    i = body_start

    while i < len(lines):
        line = lines[i]
        for ch in line:
            if ch == "{":
                depth += 1
                found_open = True
            elif ch == "}":
                depth -= 1

        if found_open and depth == 0:
            break

        if found_open and depth > 0:
            stripped = lines[i].strip()
            if stripped and not stripped.startswith("//"):
                # Skip some common block-comment lines. This stays heuristic.
                if not stripped.startswith("/*") and not stripped.startswith("*"):
                    logical += 1

        i += 1

    return logical


def _get_files_from_env() -> list[Path] | None:
    files_env = os.environ.get("FILES")
    if files_env is None:
        return None
    stripped = files_env.strip()
    if not stripped:
        return None
    return [Path(p) for p in stripped.splitlines() if p]


def check_file(path: Path, project_root: Path) -> list[str]:
    """Check a single C# file for function length violations."""

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
    i = 0
    while i < len(lines):
        if _FUNC_START_RE.match(lines[i]):
            # Look for the opening brace within a small window.
            body_start = i
            while body_start < min(i + 6, len(lines)):
                if "{" in lines[body_start]:
                    break
                body_start += 1

            if body_start >= len(lines) or "{" not in lines[body_start]:
                i += 1
                continue

            logical = count_logical_lines_in_body(lines, body_start)
            if logical > MAX_FUNCTION_LINES:
                violations.append(
                    f"  {rel}:{i + 1}: function body {logical} lines (max {MAX_FUNCTION_LINES})"
                )

            i = body_start + 1
        else:
            i += 1

    return violations


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

    all_violations: list[str] = []
    for cs_file in cs_files:
        if is_excluded(cs_file):
            continue
        all_violations.extend(check_file(cs_file, project_root))

    if all_violations:
        print("❌ C# function length violations detected:", file=sys.stderr)
        print(file=sys.stderr)
        for v in all_violations:
            print(v, file=sys.stderr)
        print(file=sys.stderr)
        print(
            f"Total violations: {len(all_violations)} function(s) exceed {MAX_FUNCTION_LINES} lines",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"✅ All C# functions within length limits ({MAX_FUNCTION_LINES} lines)")
    sys.exit(0)


if __name__ == "__main__":
    main()
