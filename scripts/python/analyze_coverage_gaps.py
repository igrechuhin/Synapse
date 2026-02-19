#!/usr/bin/env python3
"""Identify files with the most uncovered lines from a coverage JSON report.

Parses a coverage.py JSON report (e.g. from `coverage json -o coverage.json` or
pytest --cov-report=json:coverage.json), sorts files by uncovered line count,
and prints the top N files with optional directory/module filtering.

Configuration:
    COVERAGE_JSON: Path to coverage JSON file (default: coverage.json in project root)
    TOP_N: Number of top files to show (default: 10)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import cast

# Import shared utilities
try:
    from _utils import get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from _utils import get_project_root


def load_coverage_json(path: Path) -> dict[str, object]:
    """Load and return coverage JSON data."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def collect_file_gaps(
    data: dict[str, object],
    directory_filter: str | None,
    module_filter: str | None,
) -> list[tuple[str, int, list[int]]]:
    """Collect (filepath, missing_count, missing_lines) for each file."""
    files_raw = data.get("files", {})
    files = cast(dict[str, object], files_raw if isinstance(files_raw, dict) else {})

    result: list[tuple[str, int, list[int]]] = []
    for filepath, file_data in files.items():
        if not isinstance(file_data, dict):
            continue
        fdata = cast(dict[str, object], file_data)
        summary = fdata.get("summary")
        missing_lines_raw = fdata.get("missing_lines", [])
        missing_lines = cast(
            list[int],
            missing_lines_raw if isinstance(missing_lines_raw, list) else [],
        )
        if summary is None:
            count = len(missing_lines)
        else:
            sum_dict = cast(dict[str, object], summary)
            count_raw = sum_dict.get("missing_lines", len(missing_lines))
            count = (
                int(count_raw)
                if isinstance(count_raw, (int, float, str))
                else len(missing_lines)
            )
        if count <= 0:
            continue
        if directory_filter and directory_filter not in filepath:
            continue
        if module_filter and module_filter not in filepath:
            continue
        result.append((filepath, count, missing_lines))
    return result


def main() -> int:
    """Run coverage gap analysis and print top N files."""
    parser = argparse.ArgumentParser(
        description="Identify files with most uncovered lines from coverage JSON.",
    )
    _ = parser.add_argument(
        "--json",
        "-j",
        type=Path,
        default=None,
        help="Path to coverage JSON (default: coverage.json in project root)",
    )
    _ = parser.add_argument(
        "--top",
        "-n",
        type=int,
        default=10,
        help="Number of top files to show (default: 10)",
    )
    _ = parser.add_argument(
        "--directory",
        "-d",
        type=str,
        default=None,
        help="Filter to file paths containing this substring (e.g. src/cortex/tools)",
    )
    _ = parser.add_argument(
        "--module",
        "-m",
        type=str,
        default=None,
        help="Filter to file paths containing this module name substring",
    )
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    project_root = get_project_root(script_path)
    json_path = args.json or project_root / "coverage.json"

    if not json_path.exists():
        print(
            f"Error: Coverage JSON not found at {json_path}",
            file=sys.stderr,
        )
        print(
            "Generate it with: uv run python -m pytest tests/ --cov=src/cortex "
            + "--cov-report=json:coverage.json",
            file=sys.stderr,
        )
        return 1

    try:
        data = load_coverage_json(json_path)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error reading {json_path}: {e}", file=sys.stderr)
        return 1

    gaps = collect_file_gaps(
        data,
        directory_filter=args.directory,
        module_filter=args.module,
    )
    gaps.sort(key=lambda x: -x[1])

    top = gaps[: args.top]
    if not top:
        print("No uncovered lines found (or no files match filters).")
        return 0

    print(f"Top {len(top)} files by uncovered line count:\n")
    for i, (filepath, count, lines) in enumerate(top, 1):
        line_preview = (
            f" (e.g. {lines[:5]}{'...' if len(lines) > 5 else ''})" if lines else ""
        )
        print(f"  {i}. {filepath}: {count} uncovered{line_preview}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
