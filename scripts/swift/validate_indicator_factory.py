#!/usr/bin/env python3
"""Validate IndicatorComputerFactory.swift single-file constraint.

Rules enforced:
  1. Exactly one *Factory*.swift file exists in Sources/IndicatorsService/
     (direct children only, not in subdirectories).
  2. That file contains a switch statement over indicatorType.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    from _utils import get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from _utils import get_project_root


_SWITCH_RE = re.compile(r"switch\s+\w*[Ii]ndicator\w*[Tt]ype\w*")


def main() -> None:
    """Validate the IndicatorComputerFactory constraint."""
    project_root = get_project_root(Path(__file__))
    indicators_dir = project_root / "Sources" / "IndicatorsService"

    if not indicators_dir.exists():
        print("IndicatorsService directory not found, skipping.")
        sys.exit(0)

    factory_files = [
        f
        for f in indicators_dir.iterdir()
        if f.is_file() and "Factory" in f.name and f.suffix == ".swift"
    ]

    if len(factory_files) == 0:
        print(
            f"❌ No *Factory*.swift file found in {indicators_dir}",
            file=sys.stderr,
        )
        sys.exit(1)

    if len(factory_files) > 1:
        print(
            f"❌ Multiple *Factory*.swift files in {indicators_dir} "
            f"(must be exactly one):",
            file=sys.stderr,
        )
        for f in factory_files:
            print(f"  {f.name}", file=sys.stderr)
        sys.exit(1)

    factory_file = factory_files[0]
    print(f"Factory file: {factory_file.name}")

    try:
        content = factory_file.read_text(encoding="utf-8")
    except Exception as e:
        print(f"❌ Error reading {factory_file}: {e}", file=sys.stderr)
        sys.exit(1)

    if not _SWITCH_RE.search(content):
        print(
            f"❌ {factory_file.name} missing switch statement over indicatorType",
            file=sys.stderr,
        )
        sys.exit(1)

    print("✅ IndicatorComputerFactory validation passed")
    sys.exit(0)


if __name__ == "__main__":
    main()
