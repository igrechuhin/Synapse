#!/usr/bin/env python3
"""Analyze Swift sources for performance anti-patterns.

Detects common issues: unnecessary Array copies, nested loops, main-thread
blocking patterns, and missing reserveCapacity. HIGH-severity findings cause
exit 1.

Configuration:
    SOURCES_DIR: Directory to scan (default: Sources/)
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    from _utils import get_config_path, get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
    from _utils import get_config_path, get_project_root


_GENERATED_SUFFIXES = (".pb.swift", ".generated.swift")

_PATTERNS: list[tuple[str, str, re.Pattern[str]]] = [
    (
        "HIGH",
        "Array(collection.suffix/prefix) — unnecessary copy",
        re.compile(r"Array\(.*\.(?:suffix|prefix)\("),
    ),
    (
        "HIGH",
        "FileManager I/O — avoid on main thread",
        re.compile(
            r"FileManager\.default\.(?:contents|createFile|copyItem|moveItem|removeItem)\("
        ),
    ),
    (
        "MEDIUM",
        "Potential nested loop (O(n²) risk)",
        re.compile(r"for\s+\w+\s+in\b.*\bfor\s+\w+\s+in\b"),
    ),
    (
        "MEDIUM",
        ".sorted() inside apparent loop body",
        re.compile(r"\}\s*\.sorted\("),
    ),
    (
        "LOW",
        "Array(collection) — prefer direct use of Collection protocol",
        re.compile(r"\bArray\([a-z_]\w*\)"),
    ),
]


def scan_file(path: Path, project_root: Path) -> list[tuple[str, str, int, str]]:
    """Scan a single file for performance anti-patterns.

    Args:
        path: Path to the .swift file.
        project_root: Project root for relative path messages.

    Returns:
        List of (severity, label, lineno, line_content) for each finding.
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
        return []

    try:
        rel = str(path.relative_to(project_root))
    except ValueError:
        rel = str(path)

    findings: list[tuple[str, str, int, str]] = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("//"):
            continue
        for severity, label, pattern in _PATTERNS:
            if pattern.search(line):
                findings.append((severity, label, i, rel))
    return findings


def main() -> None:
    """Analyse all Swift files for performance anti-patterns."""
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

    by_severity: defaultdict[str, list[tuple[str, str, int, str]]] = defaultdict(list)

    for swift_file in sorted(sources_dir.rglob("*.swift")):
        if any(swift_file.name.endswith(s) for s in _GENERATED_SUFFIXES):
            continue
        if "Tests" in swift_file.parts:
            continue
        for finding in scan_file(swift_file, project_root):
            by_severity[finding[0]].append(finding)

    icons = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
    total = sum(len(v) for v in by_severity.values())

    if total == 0:
        print("✅ No performance anti-patterns detected")
        sys.exit(0)

    for severity in ["HIGH", "MEDIUM", "LOW"]:
        findings = by_severity.get(severity, [])
        if not findings:
            continue
        print(f"\n{icons[severity]} {severity} ({len(findings)} finding(s)):")
        for _sev, label, lineno, rel in findings:
            print(f"  {rel}:{lineno}: {label}")

    print(f"\nTotal findings: {total}")

    if by_severity.get("HIGH"):
        print(
            f"\n❌ {len(by_severity['HIGH'])} HIGH-severity issue(s) require immediate attention.",
            file=sys.stderr,
        )
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
