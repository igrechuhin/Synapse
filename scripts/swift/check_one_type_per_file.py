#!/usr/bin/env python3
"""Enforce the one-public-type-per-file rule for Swift sources.

Each .swift file may declare at most one public/open/internal type (struct,
class, enum, actor, protocol). The filename (minus .swift) must match the
primary type name.

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


_GENERATED_SUFFIXES = (".pb.swift", ".generated.swift", ".grpc.swift")

_PUBLIC_TYPE_RE = re.compile(
    "".join(
        [
            r"^\s*(?:public|open|internal)\s+(?:final\s+)?",
            r"(?:struct|class|enum|actor|protocol)\s+(\w+)",
        ]
    )
)


def check_file(path: Path, project_root: Path) -> list[str]:
    """Check a single Swift file for one-type violations.

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

    public_types: list[tuple[int, str]] = []
    for i, line in enumerate(lines, 1):
        m = _PUBLIC_TYPE_RE.match(line)
        if m:
            public_types.append((i, m.group(1)))

    violations: list[str] = []

    if len(public_types) > 1:
        names = ", ".join(f"{name} (line {ln})" for ln, name in public_types)
        violations.append(f"  {rel}: multiple public types declared: {names}")
        return violations

    if len(public_types) == 1:
        _, type_name = public_types[0]
        expected = path.stem
        if type_name != expected:
            violations.append(
                f"  {rel}: filename '{expected}' must match type name '{type_name}'"
            )

    return violations


def main() -> None:
    """Check all Swift files for one-public-type violations."""
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
        print("❌ One-public-type-per-file violations detected:", file=sys.stderr)
        print(file=sys.stderr)
        for v in all_violations:
            print(v, file=sys.stderr)
        sys.exit(1)

    print("✅ All Swift files comply with one-public-type-per-file rule")
    sys.exit(0)


if __name__ == "__main__":
    main()
