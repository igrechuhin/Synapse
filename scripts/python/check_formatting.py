#!/usr/bin/env python3
"""Pre-commit hook to check code formatting.

This script runs the formatter (black) in check-only mode to verify that all
code is properly formatted. This catches formatting issues before commit.

Configuration:
    FORMATTER_CMD: Formatter command to run (default: black)
    SRC_DIR: Source directory path (default: auto-detected)
    TESTS_DIR: Tests directory path (default: auto-detected)
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


def get_formatter_command(project_root: Path) -> list[str]:
    """Get formatter command to run.

    Args:
        project_root: Path to project root

    Returns:
        List of command parts to run
    """
    # Try .venv/bin/black first
    venv_black = project_root / ".venv" / "bin" / "black"
    if venv_black.exists():
        return [str(venv_black), "--check"]

    # Try uv run black
    try:
        subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            check=True,
            cwd=project_root,
        )
        return ["uv", "run", "black", "--check"]
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Fallback to system black
    return ["black", "--check"]


def get_directories_to_check(project_root: Path) -> list[str]:
    """Get directories to check with formatter.

    Args:
        project_root: Path to project root

    Returns:
        List of directory paths to check
    """
    dirs: list[str] = []

    # Add source directory
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

    # Add tests directory
    tests_dir = get_config_path("TESTS_DIR")
    if tests_dir is None:
        # Try common test directory patterns
        for pattern in ["tests", "test"]:
            candidate = project_root / pattern
            if candidate.exists() and candidate.is_dir():
                dirs.append(str(candidate))
                break
    else:
        if not tests_dir.is_absolute():
            tests_dir = project_root / tests_dir
        else:
            tests_dir = Path(tests_dir)
        if tests_dir.exists():
            dirs.append(str(tests_dir))

    # Add scripts directory if it exists
    scripts_dir = project_root / ".cortex" / "synapse" / "scripts"
    if scripts_dir.exists():
        dirs.append(str(scripts_dir))

    return dirs


def main():
    """Check code formatting without auto-fixing."""
    # Get project root
    script_path = Path(__file__)
    project_root = get_project_root(script_path)

    # Get formatter command
    formatter_cmd = get_formatter_command(project_root)

    # Get directories to check
    dirs_to_check = get_directories_to_check(project_root)

    if not dirs_to_check:
        print(
            "Warning: No directories found to check",
            file=sys.stderr,
        )
        print(f"Project root: {project_root}", file=sys.stderr)
        sys.exit(0)  # Not an error, just nothing to check

    # Run formatter in check-only mode
    cmd = formatter_cmd + dirs_to_check

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            # Print formatter output
            if result.stdout:
                print(result.stdout, file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)

            print(
                "\n❌ Formatting errors detected. Run formatter to fix.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Success
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            # Black outputs to stderr even on success
            print(result.stderr)
        print("✅ All formatting checks passed")
        sys.exit(0)

    except FileNotFoundError:
        print(
            f"Error: Formatter command not found: {formatter_cmd[0]}",
            file=sys.stderr,
        )
        print(
            "Install the formatter or ensure it's in your PATH or .venv/bin/",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as e:
        print(f"Error running formatter: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
