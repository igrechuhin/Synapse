#!/usr/bin/env python3
"""Scan Swift sources for hardcoded secrets.

Searches for common secret patterns in .swift files. Generated files
(.pb.swift, .generated.swift) and test files are excluded.
Zero-tolerance: any match exits with code 1.

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
    sys.path.insert(0, str(Path(__file__).parent))
    from _utils import get_config_path, get_project_root


_GENERATED_SUFFIXES = (".pb.swift", ".generated.swift")

_SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("api_key / apiKey literal", re.compile(r'(?:api_?key|apiKey)\s*=\s*"[A-Za-z0-9_\-]{8,}"', re.I)),
    ("password literal", re.compile(r'password\s*=\s*"[^"]+"', re.I)),
    ("secret literal", re.compile(r'\bsecret\s*=\s*"[^"]+"', re.I)),
    ("access_token literal", re.compile(r'access_?token\s*=\s*"[^"]+"', re.I)),
    ("private_key literal", re.compile(r'private_?key\s*=\s*"[^"]+"', re.I)),
    ("PEM private key block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("bearer token literal", re.compile(r'"bearer\s+[A-Za-z0-9_\-\.]{20,}"', re.I)),
]


def scan_file(path: Path) -> list[tuple[int, str, str]]:
    """Scan a single file for secret patterns.

    Args:
        path: Path to the .swift file.

    Returns:
        List of (line_number, pattern_name, line_content) for each match.
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
        return []

    matches: list[tuple[int, str, str]] = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("//"):
            continue
        for name, pattern in _SECRET_PATTERNS:
            if pattern.search(line):
                matches.append((i, name, line.rstrip()))
    return matches


def main() -> None:
    """Scan all Swift files for hardcoded secrets."""
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

    total_violations = 0

    for swift_file in sorted(sources_dir.rglob("*.swift")):
        if any(swift_file.name.endswith(s) for s in _GENERATED_SUFFIXES):
            continue
        if "Tests" in swift_file.parts:
            continue

        findings = scan_file(swift_file)
        if findings:
            try:
                rel = swift_file.relative_to(project_root)
            except ValueError:
                rel = swift_file
            for lineno, pattern_name, content in findings:
                print(
                    f"❌ {rel}:{lineno}: potential secret ({pattern_name}): {content}",
                    file=sys.stderr,
                )
                total_violations += 1

    if total_violations > 0:
        print(file=sys.stderr)
        print(
            f"Secret scan found {total_violations} violation(s). "
            "Use environment variables instead of hardcoded values.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("✅ No hardcoded secrets detected")
    sys.exit(0)


if __name__ == "__main__":
    main()
