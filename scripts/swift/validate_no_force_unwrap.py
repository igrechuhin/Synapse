#!/usr/bin/env python3
"""Detect force-unwrap (!) usage in Swift production sources.

Force-unwrapping is prohibited in production code. Use guard/if let instead.
Excludes test files, generated files, comment lines, and IBOutlet/IBAction.

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
    sys.path.insert(0, str(Path(__file__).parent))
    from _utils import get_config_path, get_project_root


_GENERATED_SUFFIXES = (".pb.swift", ".generated.swift")

# Matches a ! that is used as force-unwrap:
#   - preceded by a word character, ), or ]
#   - not followed by = (!=) or another ! (!!)
_FORCE_UNWRAP_RE = re.compile(r"[\w\)\]]!(?![=!])")
_IBOUTLET_RE = re.compile(r"@IB(?:Outlet|Action)")


def check_file(path: Path, project_root: Path) -> list[str]:
    """Check a single Swift file for force-unwrap violations.

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
        # Skip comments
        if stripped.startswith("//"):
            continue
        # Skip IBOutlet/IBAction (UIKit pattern)
        if _IBOUTLET_RE.search(line):
            continue
        # Skip fatalError lines (allowed in stubs)
        if "fatalError(" in line:
            continue
        if _FORCE_UNWRAP_RE.search(line):
            violations.append(f"  {rel}:{i}: {line.rstrip()}")
    return violations


def main() -> None:
    """Scan Swift production sources for force-unwrap violations."""
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
            "❌ Force-unwrap (!) detected in production code (use guard/if let instead):",
            file=sys.stderr,
        )
        print(file=sys.stderr)
        for v in all_violations:
            print(v, file=sys.stderr)
        print(file=sys.stderr)
        print(
            f"Found {len(all_violations)} force-unwrap violation(s).",
            file=sys.stderr,
        )
        sys.exit(1)

    print("✅ No force-unwrap violations in production Swift code")
    sys.exit(0)


if __name__ == "__main__":
    main()
