#!/usr/bin/env python3
"""Ensure no .pb.swift files were manually modified.

.pb.swift files are generated from .proto definitions and must not be edited
by hand. Changes should be made to .proto files, then regenerated.

Checks both staged changes and unstaged working-tree modifications against HEAD.
Zero-tolerance: any modification exits with code 1.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

try:
    from _utils import get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from _utils import get_project_root


def get_modified_pb_files(project_root: Path) -> list[str]:
    """Return .pb.swift files that differ from HEAD (staged or unstaged).

    Args:
        project_root: Path to the git repository root.

    Returns:
        Sorted list of modified .pb.swift paths relative to project root.
    """
    found: set[str] = set()
    for git_args in [
        ["git", "diff", "--name-only", "HEAD", "--", "*.pb.swift"],
        ["git", "diff", "--cached", "--name-only", "--", "*.pb.swift"],
    ]:
        try:
            result = subprocess.run(
                git_args,
                cwd=project_root,
                capture_output=True,
                text=True,
                check=False,
            )
            for line in result.stdout.splitlines():
                line = line.strip()
                if line:
                    found.add(line)
        except Exception:
            pass
    return sorted(found)


def main() -> None:
    """Check for manually modified .pb.swift files."""
    project_root = get_project_root(Path(__file__))

    modified = get_modified_pb_files(project_root)

    if modified:
        print(
            "❌ Manually modified .pb.swift files detected "
            "(edit .proto files and regenerate instead):",
            file=sys.stderr,
        )
        print(file=sys.stderr)
        for path in modified:
            print(f"  {path}", file=sys.stderr)
        sys.exit(1)

    print("✅ No .pb.swift files were manually modified")
    sys.exit(0)


if __name__ == "__main__":
    main()
