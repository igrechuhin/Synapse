#!/usr/bin/env python3
"""Pre-commit hook to enforce Swift function length limits.

Parses .swift files with a brace-balanced heuristic to find functions, inits,
and subscripts that exceed the configured logical-line limit.

Configuration:
    MAX_FUNCTION_LINES: Hard limit — exit 1 if exceeded (default: 30)
    SOURCES_DIR:        Directory to scan (default: Sources/)
"""

from __future__ import annotations

import re
import sys
import os
from pathlib import Path

try:
    from _utils import get_config_int, get_config_path, get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
    from _utils import get_config_int, get_config_path, get_project_root


MAX_FUNCTION_LINES = get_config_int("MAX_FUNCTION_LINES", 30)

_GENERATED_SUFFIXES = (".pb.swift", ".generated.swift")

_FUNC_START_RE = re.compile(
    "".join(
        [
            r"^\s*(?:(?:public|internal|private|fileprivate|open|override|",
            r"mutating|static|class|final|async|throws)\s+)*",
            r"(?:func|init|subscript)\b",
        ]
    )
)


def count_logical_lines_in_body(lines: list[str], body_start: int) -> int:
    """Count logical lines inside a brace-delimited body.

    Args:
        lines: All lines of the file (0-indexed).
        body_start: Index of the line containing the opening brace.

    Returns:
        Number of non-blank, non-comment lines inside the body.
    """
    depth = 0
    logical = 0
    found_open = False
    i = body_start

    while i < len(lines):
        for ch in lines[i]:
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
                logical += 1
        i += 1

    return logical


def _get_files_from_env() -> list[Path] | None:
    """Return explicit file list from FILES env var, or None if not set."""
    files_env = os.environ.get("FILES")
    if not files_env:
        return None
    return [Path(p) for p in files_env.strip().splitlines() if p]


def check_file(path: Path, project_root: Path) -> list[str]:
    """Check a single Swift file for function length violations.

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

    violations: list[str] = []

    try:
        rel = path.relative_to(project_root)
    except ValueError:
        rel = path

    i = 0
    while i < len(lines):
        if _FUNC_START_RE.match(lines[i]):
            func_line = i + 1  # 1-based
            name_match = re.search(r"(?:func|init|subscript)\s+(\w*)", lines[i])
            func_name = name_match.group(1) if name_match else "(anonymous)"

            # Find body start (opening brace may be on same or next line).
            # A bodyless declaration — a protocol requirement such as
            # `func allows(_:at:) async -> Bool` — has no body at all. Detect it
            # by its terminator: the scan stops at a closing brace or at the next
            # declaration, so it cannot latch onto an unrelated body further down
            # the file and report that body's length against this declaration.
            # Do NOT bound the scan by a fixed line window — a wide parameter list
            # can push the opening brace arbitrarily far below the `func` line, and
            # bounding it would silently exclude those functions from the check.
            body_start = i
            bodyless = False
            while body_start < len(lines) and "{" not in lines[body_start]:
                if body_start > i and (
                    "}" in lines[body_start] or _FUNC_START_RE.match(lines[body_start])
                ):
                    bodyless = True
                    break
                body_start += 1

            if bodyless or body_start >= len(lines):
                i += 1
                continue

            logical = count_logical_lines_in_body(lines, body_start)

            if logical > MAX_FUNCTION_LINES:
                excess = logical - MAX_FUNCTION_LINES
                violations.append(
                    f"  {rel}:{func_line}: {func_name}() — {logical} lines (max: {MAX_FUNCTION_LINES}, excess: {excess})"
                )
            i = body_start + 1
        else:
            i += 1

    return violations


def main() -> None:
    """Check all Swift files for function length violations."""
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

    all_violations: list[str] = []

    files_from_env = _get_files_from_env()
    if files_from_env is not None:
        # Dispatcher mode: check exactly these files
        swift_files = [
            f
            for f in files_from_env
            if f.suffix == ".swift"
            and not any(f.name.endswith(s) for s in _GENERATED_SUFFIXES)
        ]
    else:
        # Standalone fallback: scan Sources/ and Tests/
        if not sources_dir.exists():
            print(f"❌ Sources directory not found: {sources_dir}", file=sys.stderr)
            sys.exit(1)

        swift_files = [
            f
            for f in sorted(sources_dir.rglob("*.swift"))
            if not any(f.name.endswith(s) for s in _GENERATED_SUFFIXES)
        ]

        tests_dir = sources_dir.parent / "Tests"
        if tests_dir.exists():
            swift_files += [
                f
                for f in sorted(tests_dir.rglob("*.swift"))
                if not any(f.name.endswith(s) for s in _GENERATED_SUFFIXES)
            ]

    for swift_file in swift_files:
        all_violations.extend(check_file(swift_file, project_root))

    if all_violations:
        print("❌ Function length violations detected:", file=sys.stderr)
        print(file=sys.stderr)
        for v in all_violations:
            print(v, file=sys.stderr)
        print(file=sys.stderr)
        print(
            f"Total violations: {len(all_violations)} function(s) exceed {MAX_FUNCTION_LINES} lines",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"✅ All Swift functions within length limits ({MAX_FUNCTION_LINES} lines)")
    sys.exit(0)


if __name__ == "__main__":
    main()
