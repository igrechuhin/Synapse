#!/usr/bin/env python3
"""Build the JavaScript/Node.js project.

Runs `npm run build` (or the configured build script) for the project.

Configuration:
    BUILD_SCRIPT: npm script name to run (default: build)
    BUILD_TIMEOUT: Timeout in seconds (default: 300)
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


BUILD_SCRIPT = os.getenv("BUILD_SCRIPT", "build")
BUILD_TIMEOUT = get_config_int("BUILD_TIMEOUT", 300)
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


def main() -> None:
    """Run the project build script."""
    project_root = get_project_root(Path(__file__))
    pm = detect_package_manager(project_root)
    cmd = [pm, "run", BUILD_SCRIPT]

    print(f"Running: {' '.join(cmd)}")
    print(f"Working directory: {project_root}")

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=BUILD_TIMEOUT,
        )

        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        if result.returncode != 0:
            print(f"❌ Build failed (exit {result.returncode}).", file=sys.stderr)
            sys.exit(1)

        print("✅ Build succeeded")
        sys.exit(0)

    except subprocess.TimeoutExpired:
        print(f"❌ Build timed out after {BUILD_TIMEOUT}s.", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"❌ {pm} not found.", file=sys.stderr)
        print("Install Node.js: https://nodejs.org", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running build: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
