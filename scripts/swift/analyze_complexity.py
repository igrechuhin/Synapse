#!/usr/bin/env python3
"""Analyze cyclomatic complexity of Swift functions.

Uses a keyword-based heuristic (if, guard, for, while, switch case, catch,
&&, ||) to estimate complexity. Reports functions exceeding MAX_COMPLEXITY.

Configuration:
    MAX_COMPLEXITY: Maximum allowed complexity per function (default: 10)
    SOURCES_DIR:    Directory to scan (default: Sources/)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    from _utils import get_config_int, get_config_path, get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from _utils import get_config_int, get_config_path, get_project_root


MAX_COMPLEXITY = get_config_int("MAX_COMPLEXITY", 10)

_GENERATED_SUFFIXES = (".pb.swift", ".generated.swift")

_FUNC_START_RE = re.compile(
    "".join(
        [
            r"^\s*(?:(?:public|internal|private|fileprivate|open|override|",
            r"mutating|static|class|final|async|throws)\s+)*",
            r"(?:func|init)\b",
        ]
    )
)

_COMPLEXITY_RE = re.compile(
    "".join(
        [
            r"\b(?:if|guard|for|while|switch|catch)\b",
            r"|(?:case\s+\w)",
            r"|&&|\|\||\?\?|\bwhere\b",
        ]
    )
)


def collect_body(lines: list[str], start: int) -> list[str]:
    """Collect lines belonging to a function body starting at 'start'.

    Args:
        lines: All lines of the file.
        start: Index of the function declaration line.

    Returns:
        Lines that form the function body.
    """
    depth = 0
    found_open = False
    body: list[str] = []
    i = start

    while i < len(lines):
        for ch in lines[i]:
            if ch == "{":
                depth += 1
                found_open = True
            elif ch == "}":
                depth -= 1
        if found_open:
            body.append(lines[i])
        if found_open and depth == 0:
            break
        i += 1

    return body


def check_file(path: Path, project_root: Path) -> list[str]:
    """Analyse a single Swift file for complexity violations.

    Args:
        path: Path to the .swift file.
        project_root: Project root for relative path messages.

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
    i = 0
    while i < len(lines):
        if _FUNC_START_RE.match(lines[i]):
            func_line = i + 1
            nm = re.search(r"(?:func|init)\s+(\w*)", lines[i])
            func_name = nm.group(1) if nm else "(anonymous)"
            body = collect_body(lines, i)
            complexity = 1 + sum(len(_COMPLEXITY_RE.findall(ln)) for ln in body)
            if complexity > MAX_COMPLEXITY:
                violations.append(
                    f"  {rel}:{func_line}: {func_name}() — complexity {complexity} (max: {MAX_COMPLEXITY})"
                )
            i += len(body)
        else:
            i += 1

    return violations


def main() -> None:
    """Analyse all Swift files for cyclomatic complexity violations."""
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
        all_violations.extend(check_file(swift_file, project_root))

    if all_violations:
        print(
            f"❌ Complexity violations (exceed {MAX_COMPLEXITY}):",
            file=sys.stderr,
        )
        print(file=sys.stderr)
        for v in all_violations:
            print(v, file=sys.stderr)
        sys.exit(1)

    print(f"✅ All Swift functions within complexity limit ({MAX_COMPLEXITY})")
    sys.exit(0)


if __name__ == "__main__":
    main()
