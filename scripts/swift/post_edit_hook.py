#!/usr/bin/env python3
"""Post-edit quality hook (Swift).

Designed to be run from a Claude Code PostToolUse hook after an Edit tool call.
Runs a fast `swift build` and prints a short tail of output.
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


def _tail_lines(text: str, max_lines: int) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text.rstrip()
    return "\n".join(lines[-max_lines:]).rstrip()


def main() -> int:
    project_root = get_project_root(Path(__file__))
    package_swift = project_root / "Package.swift"
    if not package_swift.exists():
        print("Post-edit hook: no Package.swift found; skipping.")
        return 0

    cmd = ["swift", "build"]
    result = subprocess.run(
        cmd,
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    combined = ""
    if result.stdout:
        combined += result.stdout
    if result.stderr:
        combined += ("\n" if combined else "") + result.stderr

    tail = _tail_lines(combined, 20)
    if tail:
        print(tail)

    return 0 if result.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
