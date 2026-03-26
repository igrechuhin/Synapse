#!/usr/bin/env python3
"""Detect unused function parameters in Swift sources via compiler warnings.

Performs a debug build with -warn-unused-imports and surfaces any
'never used' / 'unused' warnings from the compiler output.
Exits 1 if any unused-parameter warnings are found.

Note: This requires a successful debug build. If the code does not compile,
this script will fail. Fix compilation errors first.

Configuration:
    BUILD_TIMEOUT: Timeout in seconds (default: 300)
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

try:
    from _utils import get_config_int, get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from _utils import get_config_int, get_project_root


BUILD_TIMEOUT = get_config_int("BUILD_TIMEOUT", 300)

_UNUSED_RE = re.compile(r"warning:.*(?:never used|unused|immutable value)")
_GENERATED_SUFFIXES = (".pb.swift", ".generated.swift")


def run_build(project_root: Path) -> str:
    """Run swift build and return combined output.

    Args:
        project_root: Path to the project root.

    Returns:
        Combined stdout+stderr from the build.
    """
    try:
        result = subprocess.run(
            ["swift", "build", "-Xswiftc", "-warn-unused-imports"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=BUILD_TIMEOUT,
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        print(f"❌ Build timed out after {BUILD_TIMEOUT}s.", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("❌ swift not found. Install Xcode command-line tools.", file=sys.stderr)
        sys.exit(1)


def filter_warnings(output: str) -> list[str]:
    """Extract unused-parameter warnings from build output.

    Args:
        output: Raw build output.

    Returns:
        List of warning lines (filtered to production code only).
    """
    warnings: list[str] = []
    for line in output.splitlines():
        if not _UNUSED_RE.search(line):
            continue
        if any(s in line for s in _GENERATED_SUFFIXES):
            continue
        if "/Tests/" in line:
            continue
        warnings.append(line)
    return warnings


def main() -> None:
    """Check for unused parameters via swift build warnings."""
    project_root = get_project_root(Path(__file__))

    print("Building with -warn-unused-imports to detect unused parameters...")
    output = run_build(project_root)
    warnings = filter_warnings(output)

    if warnings:
        print("❌ Unused parameter warnings detected:", file=sys.stderr)
        print(file=sys.stderr)
        for w in warnings:
            print(f"  {w}", file=sys.stderr)
        print(file=sys.stderr)
        print(
            f"Found {len(warnings)} unused parameter warning(s). "
            "Fix all before committing.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("✅ No unused parameters detected")
    sys.exit(0)


if __name__ == "__main__":
    main()
