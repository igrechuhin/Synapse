#!/usr/bin/env python3
"""Pre-commit hook to enforce Swift file size limits.

Checks Swift files against the configured line limit. Files between the warn
threshold and the max are reported as warnings; files over the max cause exit
1.

Configuration:
    MAX_FILE_LINES:  Hard limit — exit 1 if exceeded (default: 400)
    WARN_FILE_LINES: Soft warning threshold (default: 350)
    SOURCES_DIR:     Directory to scan (default: Sources/)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    from _utils import get_config_int, get_config_path, get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
    from _utils import get_config_int, get_config_path, get_project_root


MAX_FILE_LINES = get_config_int("MAX_FILE_LINES", 400)
WARN_FILE_LINES = get_config_int("WARN_FILE_LINES", 350)

_GENERATED_SUFFIXES = (".pb.swift", ".generated.swift", ".grpc.swift")

# Intentionally large files excluded from the size check (match CI quality.yml).
# IndicatorComputerFactory.swift — single-file registry, planned refactor tracked separately.
# ContainerFactory.swift         — DI container registry, planned refactor tracked separately.
_EXCLUDED_FILENAMES: frozenset[str] = frozenset(
    {"IndicatorComputerFactory.swift", "ContainerFactory.swift"}
)


def count_logical_lines(path: Path) -> int:
    """Count non-blank, non-comment lines in a Swift file.

    Args:
        path: Path to the .swift file.

    Returns:
        Number of logical lines of code.
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
        return 0

    count = 0
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("//"):
            count += 1
    return count


def is_excluded(path: Path) -> bool:
    """Return True if this file should be skipped.

    Args:
        path: Path to the .swift file.

    Returns:
        True if the file should be excluded from checks.
    """
    if any(path.name.endswith(s) for s in _GENERATED_SUFFIXES):
        return True
    if path.name in _EXCLUDED_FILENAMES:
        return True
    return False


def _get_files_from_env() -> list[Path] | None:
    """Return explicit file list from `FILES` env var, or None if unset/empty."""
    files_env = os.environ.get("FILES")
    if files_env is None:
        return None
    stripped = files_env.strip()
    if not stripped:
        return None
    return [Path(p) for p in stripped.splitlines() if p]


def main() -> None:
    """Check Swift files for size violations."""
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
    swift_files: list[Path]

    if files_from_env is not None:
        # Dispatcher mode: check only explicitly provided files.
        swift_files = [
            f for f in files_from_env if f.suffix == ".swift" and not is_excluded(f)
        ]
    else:
        # Standalone/CI fallback: scan Sources/ and include Tests/ if present.
        if not sources_dir.exists():
            print(f"✅ No Swift sources directory detected (skipped): {sources_dir}")
            sys.exit(0)

        swift_files = [
            f for f in sorted(sources_dir.rglob("*.swift")) if not is_excluded(f)
        ]

        tests_dir = sources_dir.parent / "Tests"
        if tests_dir.exists():
            swift_files += [
                f for f in sorted(tests_dir.rglob("*.swift")) if not is_excluded(f)
            ]

    violations: list[tuple[Path, int]] = []
    warnings_list: list[tuple[Path, int]] = []

    for swift_file in swift_files:
        if is_excluded(swift_file):
            continue
        # Root Package.swift is the SPM manifest; it cannot be split across files.
        # CI file-size job only scans Sources/ and Tests/ (see .github/workflows/quality.yml).
        resolved = swift_file.resolve()
        if (
            swift_file.name == "Package.swift"
            and resolved.parent == project_root.resolve()
        ):
            continue
        lines = count_logical_lines(swift_file)
        if lines > MAX_FILE_LINES:
            violations.append((swift_file, lines))
        elif lines > WARN_FILE_LINES:
            warnings_list.append((swift_file, lines))

    def rel(p: Path) -> Path:
        try:
            return p.relative_to(project_root)
        except ValueError:
            return p

    if warnings_list:
        print("⚠️  File size warnings (approaching limit):", file=sys.stderr)
        for path, lines in sorted(warnings_list, key=lambda x: -x[1]):
            print(
                f"  {rel(path)}: {lines} lines (warn >{WARN_FILE_LINES}, max {MAX_FILE_LINES})",
                file=sys.stderr,
            )
        print(file=sys.stderr)

    if violations:
        print("❌ File size violations detected:", file=sys.stderr)
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

    print(f"✅ All Swift files within size limits ({MAX_FILE_LINES} lines)")
    sys.exit(0)


if __name__ == "__main__":
    main()
