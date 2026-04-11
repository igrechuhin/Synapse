#!/usr/bin/env python3
"""Build the TypeScript project.

Runs `npm run build` (or the configured build script) for the project.
Falls back to `tsc --noEmit` for type-checking when no build script is defined.

Configuration:
    BUILD_SCRIPT: npm script name to run (default: build)
    BUILD_TIMEOUT: Timeout in seconds (default: 300)
    PACKAGE_MANAGER: Package manager to use: npm, yarn, or pnpm (default: auto-detected)
    TSC_ONLY: Set to 1 to run tsc --noEmit instead of npm run build (default: 0)
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
TSC_ONLY = get_config_int("TSC_ONLY", 0)


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


def has_typescript_project(project_root: Path) -> bool:
    """Return True when the project root contains TypeScript config or package.json."""
    return (project_root / "package.json").exists() or (
        project_root / "tsconfig.json"
    ).exists()


def has_build_script(project_root: Path, pm: str) -> bool:
    """Check whether a build script is defined in package.json.

    Args:
        project_root: Path to the project root.
        pm: Package manager name (unused; reserved for future use).

    Returns:
        True when package.json defines a 'build' (or BUILD_SCRIPT) entry.
    """
    pkg = project_root / "package.json"
    if not pkg.exists():
        return False
    try:
        import json

        data = json.loads(pkg.read_text())
        return BUILD_SCRIPT in data.get("scripts", {})
    except Exception:
        return False


def main() -> None:
    """Run the TypeScript build."""
    project_root = get_project_root(Path(__file__))
    if not has_typescript_project(project_root):
        print("✅ No TypeScript project detected (skipped)")
        sys.exit(0)

    pm = detect_package_manager(project_root)

    if TSC_ONLY or not has_build_script(project_root, pm):
        cmd = ["tsc", "--noEmit"]
    else:
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
        print(f"❌ {cmd[0]} not found.", file=sys.stderr)
        print("Install Node.js/TypeScript: https://nodejs.org", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running build: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
