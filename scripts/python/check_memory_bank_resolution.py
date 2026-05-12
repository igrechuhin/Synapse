#!/usr/bin/env python3
"""Diagnose memory-bank root/file resolution consistency."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _utils import get_project_root, resolve_memory_bank_file_path, resolve_memory_bank_root


def build_resolution_report(
    project_root: Path, structure_memory_bank_path: str | None
) -> dict[str, object]:
    """Build structured diagnostics for memory-bank root and roadmap lookup."""
    resolved_root = resolve_memory_bank_root(
        project_root=project_root,
        structure_memory_bank_path=structure_memory_bank_path,
    )
    roadmap_path = resolve_memory_bank_file_path(
        project_root=project_root,
        file_name="roadmap.md",
        structure_memory_bank_path=structure_memory_bank_path,
    )
    return {
        "project_root": str(project_root.resolve()),
        "structure_memory_bank_path": structure_memory_bank_path,
        "resolved_memory_bank_root": str(resolved_root),
        "roadmap_lookup_path": str(roadmap_path),
        "roadmap_exists": roadmap_path.exists(),
        "root_exists": resolved_root.exists(),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Diagnose memory-bank root resolution for docs/manage_file alignment."
        )
    )
    parser.add_argument(
        "--structure-memory-bank-path",
        default=None,
        help="Optional memory-bank path from cortex://structure for alignment checks.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_resolution_report(
        project_root=get_project_root(),
        structure_memory_bank_path=args.structure_memory_bank_path,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["roadmap_exists"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
