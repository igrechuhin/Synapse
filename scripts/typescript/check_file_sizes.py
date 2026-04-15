#!/usr/bin/env python3
"""Pre-commit hook to enforce file size limits for TypeScript."""

from __future__ import annotations

import os
import sys
from pathlib import Path

try:
    from _utils import get_config_int, get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
    from _utils import get_config_int, get_project_root  # type: ignore[no-redef]


MAX_LINES = get_config_int("MAX_FILE_LINES", 400)
WARN_LINES = get_config_int("FILE_SIZE_WARN_LINES", 350)


def _get_files_from_env() -> list[Path] | None:
    files_env = os.environ.get("FILES")
    if files_env is None:
        return None
    stripped = files_env.strip()
    if not stripped:
        return None
    return [Path(p) for p in stripped.splitlines() if p]


def _allow_full_scan() -> bool:
    """Return True when fallback full-repo scan is explicitly enabled."""
    return os.environ.get("ALLOW_FULL_SCAN") == "1"


def _count_logical_lines(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"Error reading {path}: {exc}", file=sys.stderr)
        return 0

    count = 0
    in_block_comment = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        if in_block_comment:
            if "*/" in line:
                in_block_comment = False
            continue

        if line.startswith("//"):
            continue

        if line.startswith("/*"):
            in_block_comment = "*/" not in line
            continue

        count += 1
    return count


def main() -> None:
    files_from_env = _get_files_from_env()
    project_root = get_project_root(Path(__file__))
    violations: list[tuple[Path, int]] = []
    warnings_list: list[tuple[Path, int]] = []

    ts_files: list[Path]
    if files_from_env is not None:
        ts_files = [f for f in files_from_env if f.suffix in {".ts", ".tsx"}]
    else:
        if not _allow_full_scan():
            print("✅ No FILES provided and ALLOW_FULL_SCAN!=1 (skipped)")
            sys.exit(0)

        src_dir = project_root / "src"
        ts_files = []
        if src_dir.exists():
            ts_files.extend(sorted(src_dir.rglob("*.ts")))
            ts_files.extend(sorted(src_dir.rglob("*.tsx")))

        tests_dir = project_root / "tests"
        if tests_dir.exists():
            ts_files.extend(sorted(tests_dir.rglob("*.ts")))
            ts_files.extend(sorted(tests_dir.rglob("*.tsx")))

        if not ts_files:
            print("✅ No TypeScript sources detected for full scan (skipped)")
            sys.exit(0)

    for ts_file in ts_files:
        lines = _count_logical_lines(ts_file)
        if lines > MAX_LINES:
            violations.append((ts_file, lines))
        elif lines > WARN_LINES:
            warnings_list.append((ts_file, lines))

    def _rel(path: Path, root: Path) -> Path:
        try:
            return path.resolve().relative_to(root)
        except Exception:
            return path

    if warnings_list:
        print("⚠️  File size warnings (approach limit):", file=sys.stderr)
        for path, lines in sorted(warnings_list, key=lambda x: -x[1]):
            print(
                f"  {_rel(path, project_root)}: {lines} lines (warn above {WARN_LINES}, max {MAX_LINES})",
                file=sys.stderr,
            )
        print(file=sys.stderr)

    if violations:
        print("❌ File size violations detected:", file=sys.stderr)
        print(file=sys.stderr)
        for path, lines in sorted(violations, key=lambda x: x[1], reverse=True):
            rel = _rel(path, project_root)
            excess = lines - MAX_LINES
            print(
                f"  {rel}: {lines} lines (max: {MAX_LINES}, excess: {excess})",
                file=sys.stderr,
            )
        print(file=sys.stderr)
        print(
            f"Total violations: {len(violations)} file(s) exceed {MAX_LINES} lines",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"✅ All files within size limits ({MAX_LINES} lines)")
    sys.exit(0)


if __name__ == "__main__":
    main()
