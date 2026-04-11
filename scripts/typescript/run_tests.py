#!/usr/bin/env python3
"""Run the TypeScript project test suite.

Runs `npm test` (or the configured test script) for the project.

Configuration:
    TEST_SCRIPT: npm script name to run (default: test)
    TEST_TIMEOUT: Timeout in seconds (default: 300)
    PACKAGE_MANAGER: Package manager to use: npm, yarn, or pnpm (default: auto-detected)
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

try:
    from _utils import get_config_int, get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
    from _utils import get_config_int, get_project_root


TEST_SCRIPT = os.getenv("TEST_SCRIPT", "test")
TEST_TIMEOUT = get_config_int("TEST_TIMEOUT", 300)
PACKAGE_MANAGER = os.getenv("PACKAGE_MANAGER", "")


def detect_package_manager(project_root: Path) -> str:
    """Detect the package manager from lockfile presence.

    Args:
        project_root: Path to the project root.

    Returns:
        Package manager name: 'npm', 'yarn', or 'pnpm'.
    """
    if PACKAGE_MANAGER:
        return PACKAGE_MANAGER
    if (project_root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (project_root / "yarn.lock").exists():
        return "yarn"
    return "npm"


def _has_typescript_project(project_root: Path) -> bool:
    """Return True when the project root contains TypeScript config or package.json."""
    return (project_root / "package.json").exists() or (
        project_root / "tsconfig.json"
    ).exists()


def main() -> None:
    """Run the project test suite."""
    project_root = get_project_root(Path(__file__))
    if not _has_typescript_project(project_root):
        print("✅ No TypeScript project detected (skipped)")
        sys.exit(0)

    pm = detect_package_manager(project_root)
    cmd = [pm, "run", TEST_SCRIPT]

    print(f"Running: {' '.join(cmd)}")
    print(f"Timeout: {TEST_TIMEOUT}s")

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=TEST_TIMEOUT,
        )

        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        if result.returncode != 0:
            print(f"❌ Tests failed (exit {result.returncode}).", file=sys.stderr)
            sys.exit(1)

        print("✅ All tests passed")
        sys.exit(0)

    except subprocess.TimeoutExpired:
        print(f"❌ Tests timed out after {TEST_TIMEOUT}s.", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"❌ {pm} not found.", file=sys.stderr)
        print("Install Node.js: https://nodejs.org", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running tests: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
