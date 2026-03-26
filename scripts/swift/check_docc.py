#!/usr/bin/env python3
"""Verify DocC documentation coverage for public Swift APIs.

Checks that all public structs, classes, enums, actors, and protocols in
production sources have at least a one-line /// documentation comment.
Reports gaps; exits 1 only when gap count exceeds DOC_GAP_THRESHOLD.

Configuration:
    SOURCES_DIR:       Directory to scan (default: Sources/)
    DOC_GAP_THRESHOLD: Max allowed gaps before exit 1 (default: 10)
    STRICT:            Set to 1 to also check public func docs (default: 0)
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


DOC_GAP_THRESHOLD = get_config_int("DOC_GAP_THRESHOLD", 10)
STRICT = get_config_int("STRICT", 0)

_GENERATED_SUFFIXES = (".pb.swift", ".generated.swift")

_PUBLIC_TYPE_RE = re.compile(
    "".join(
        [
            r"^\s*(?:public|open)\s+(?:final\s+)?",
            r"(?:struct|class|enum|actor|protocol)\s+(\w+)",
        ]
    )
)
_PUBLIC_FUNC_RE = re.compile(
    "".join(
        [
            r"^\s*(?:public|open)\s+(?:override\s+)?(?:static\s+)?(?:final\s+)?",
            r"(?:mutating\s+)?(?:async\s+)?func\s+(\w+)",
        ]
    )
)
_DOC_COMMENT_RE = re.compile(r"^\s*///")


def has_doc_above(lines: list[str], index: int) -> bool:
    """Return True if any of the 5 lines before index is a doc comment.

    Args:
        lines: All lines of the file (0-indexed).
        index: Index of the declaration line.

    Returns:
        True if a /// doc comment is found in the preceding lines.
    """
    for prev in range(max(0, index - 5), index):
        if _DOC_COMMENT_RE.match(lines[prev]):
            return True
    return False


def check_file(path: Path, project_root: Path) -> list[str]:
    """Check a single Swift file for missing documentation.

    Args:
        path: Path to the .swift file.
        project_root: Project root for relative path messages.

    Returns:
        List of human-readable gap descriptions.
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

    gaps: list[str] = []
    for i, line in enumerate(lines):
        m = _PUBLIC_TYPE_RE.match(line)
        if m is None and STRICT:
            m = _PUBLIC_FUNC_RE.match(line)
        if m and not has_doc_above(lines, i):
            gaps.append(f"  {rel}:{i + 1}: '{m.group(1)}' missing /// documentation")
    return gaps


def main() -> None:
    """Check all Swift files for documentation gaps."""
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

    all_gaps: list[str] = []

    for swift_file in sorted(sources_dir.rglob("*.swift")):
        if any(swift_file.name.endswith(s) for s in _GENERATED_SUFFIXES):
            continue
        if "Tests" in swift_file.parts:
            continue
        all_gaps.extend(check_file(swift_file, project_root))

    if not all_gaps:
        print("✅ All public Swift APIs have documentation")
        sys.exit(0)

    print(f"Documentation gaps found: {len(all_gaps)}", file=sys.stderr)
    for gap in all_gaps[:50]:
        print(gap, file=sys.stderr)
    if len(all_gaps) > 50:
        print(f"  ... and {len(all_gaps) - 50} more", file=sys.stderr)

    if len(all_gaps) > DOC_GAP_THRESHOLD:
        print(
            f"\n❌ {len(all_gaps)} doc gap(s) exceed threshold of {DOC_GAP_THRESHOLD}. Record as finding and fix before commit.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(
        f"\nNote: {len(all_gaps)} doc gap(s) found (below threshold {DOC_GAP_THRESHOLD}). Consider recording as a finding."
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
