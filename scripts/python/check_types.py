#!/usr/bin/env python3
"""Pre-commit hook to check type annotations.

This script runs the type checker (pyright) to verify type safety.

Configuration:
    TYPE_CHECKER_CMD: Type checker command to run (default: pyright)
    SRC_DIR: Source directory path (default: auto-detected)
"""

import subprocess
import sys
from pathlib import Path

# Import shared utilities
try:
    from _utils import (
        find_src_directory,
        get_config_path,
        get_project_root,
    )
except ImportError:
    # Fallback if running from different location
    sys.path.insert(0, str(Path(__file__).parent))
    from _utils import (
        find_src_directory,
        get_config_path,
        get_project_root,
    )


def get_type_checker_command(project_root: Path) -> list[str]:
    """Get type checker command to run.

    Args:
        project_root: Path to project root

    Returns:
        List of command parts to run
    """
    # Try .venv/bin/pyright first
    venv_pyright = project_root / ".venv" / "bin" / "pyright"
    if venv_pyright.exists():
        return [str(venv_pyright)]

    # Try uv run pyright
    try:
        subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            check=True,
            cwd=project_root,
        )
        return ["uv", "run", "pyright"]
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Fallback to system pyright
    return ["pyright"]


def get_directories_to_check(project_root: Path) -> list[str]:
    """Get directories to check with type checker.

    Args:
        project_root: Path to project root

    Returns:
        List of directory paths to check
    """
    dirs: list[str] = []

    # Add source directory (type checking usually only on src/)
    src_dir = get_config_path("SRC_DIR")
    if src_dir is None:
        src_dir = find_src_directory(project_root)
    else:
        if not src_dir.is_absolute():
            src_dir = project_root / src_dir
        else:
            src_dir = Path(src_dir)

    if src_dir.exists():
        dirs.append(str(src_dir))

    return dirs


def main():
    """Check type annotations."""
    # Get project root
    script_path = Path(__file__)
    project_root = get_project_root(script_path)

    # Get type checker command
    type_checker_cmd = get_type_checker_command(project_root)

    # Get directories to check
    dirs_to_check = get_directories_to_check(project_root)

    if not dirs_to_check:
        print(
            "Warning: No directories found to check",
            file=sys.stderr,
        )
        print(f"Project root: {project_root}", file=sys.stderr)
        sys.exit(0)  # Not an error, just nothing to check

    # Run type checker
    cmd = type_checker_cmd + dirs_to_check

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )

        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        # Check for errors in output
        output = result.stdout + result.stderr
        has_errors = "error" in output.lower() and "0 errors" not in output.lower()
        has_warnings = (
            "warning" in output.lower() and "0 warnings" not in output.lower()
        )

        if result.returncode != 0 or has_errors or has_warnings:
            print(
                "\n❌ Type errors or warnings detected. Fix before committing.",
                file=sys.stderr,
            )
            sys.exit(1)

        print("✅ All type checks passed")
        sys.exit(0)

    except FileNotFoundError:
        print(
            f"Error: Type checker command not found: {type_checker_cmd[0]}",
            file=sys.stderr,
        )
        print(
            "Install the type checker or ensure it's in your PATH or .venv/bin/",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as e:
        print(f"Error running type checker: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
