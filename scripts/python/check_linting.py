#!/usr/bin/env python3
"""Pre-commit hook to check linting without auto-fixing.

This script runs the linter (ruff) in check-only mode to verify that all
linting issues are resolved. Unlike `ruff check --fix`, this catches
non-fixable errors like undefined names that must be manually resolved.

Configuration:
    LINTER_CMD: Linter command to run (default: ruff)
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
        get_synapse_scripts_dir,
    )
except ImportError:
    # Fallback if running from different location
    sys.path.insert(0, str(Path(__file__).parent))
    from _utils import (
        find_src_directory,
        get_config_path,
        get_project_root,
        get_synapse_scripts_dir,
    )


def get_linter_command(project_root: Path) -> list[str]:
    """Get linter command to run.

    Uses pyproject.toml rule set (E, F, I, B, UP) - matches CI workflow.

    Args:
        project_root: Path to project root

    Returns:
        List of command parts to run
    """
    # Try .venv/bin/ruff first
    venv_ruff = project_root / ".venv" / "bin" / "ruff"
    if venv_ruff.exists():
        return [str(venv_ruff), "check"]

    # Try uv run ruff
    try:
        _ = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            check=True,
            cwd=project_root,
        )
        return ["uv", "run", "ruff", "check"]
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Fallback to system ruff
    return ["ruff", "check"]


def get_directories_to_check(project_root: Path) -> list[str]:
    """Get directories to check with linter.

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
        for pattern in ["tests", "test", "tests/unit", "tests/integration"]:
            candidate = project_root / pattern
            if candidate.exists() and candidate.is_dir():
                tests_dir = candidate
                break
    else:
        if not tests_dir.is_absolute():
            tests_dir = project_root / tests_dir
        else:
            tests_dir = Path(tests_dir)

    if tests_dir is not None and tests_dir.exists():
        dirs.append(str(tests_dir))

    # Add scripts directory if it exists (for synapse scripts self-check)
    scripts_dir = get_synapse_scripts_dir(project_root)
    if scripts_dir.exists():
        dirs.append(str(scripts_dir))

    # Note: When used in commit pipeline, this checks src/ and tests/
    # (matching CI main step). When used in CI synapse step, this also
    # checks synapse scripts themselves
    return dirs


def main():
    """Check linting without auto-fixing.

    ZERO TOLERANCE POLICY: This script enforces zero tolerance for linting errors
    in ALL checked directories, including .cortex/synapse/. ANY error will cause
    the script to exit with code 1, blocking commits and CI.
    """
    # Get project root
    script_path = Path(__file__)
    project_root = get_project_root(script_path)

    # Get linter command
    linter_cmd = get_linter_command(project_root)

    # Get directories to check
    dirs_to_check = get_directories_to_check(project_root)

    # Explicitly verify synapse directory is checked
    synapse_scripts_dir = get_synapse_scripts_dir(project_root)
    if synapse_scripts_dir.exists():
        synapse_checked = any(
            Path(dir_path).resolve() == synapse_scripts_dir.resolve()
            or str(synapse_scripts_dir.resolve()) in str(Path(dir_path).resolve())
            for dir_path in dirs_to_check
        )

        if not synapse_checked:
            print(
                (
                    f"ERROR: Synapse scripts directory exists but is not "
                    f"being checked: {synapse_scripts_dir}"
                ),
                file=sys.stderr,
            )
            print(
                f"Directories being checked: {dirs_to_check}",
                file=sys.stderr,
            )
            sys.exit(1)

    if not dirs_to_check:
        print(
            "Warning: No directories found to check",
            file=sys.stderr,
        )
        print(f"Project root: {project_root}", file=sys.stderr)
        sys.exit(0)  # Not an error, just nothing to check

    # Run linter in check-only mode (no --fix flag)
    cmd = linter_cmd + dirs_to_check

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            # Print linter output
            if result.stdout:
                print(result.stdout, file=sys.stderr)
            if result.stderr:
                print(result.stderr, file=sys.stderr)

            # Check if errors are in synapse directory
            output_text = (result.stdout or "") + (result.stderr or "")
            synapse_errors = (
                ".cortex/synapse" in output_text or "synapse/scripts" in output_text
            )

            print(
                "\n❌ Linting errors detected. Fix these issues before committing.",
                file=sys.stderr,
            )
            if synapse_errors:
                print(
                    (
                        "\n⚠️  ZERO TOLERANCE: Linting errors found in "
                        + ".cortex/synapse/ directory."
                    ),
                    file=sys.stderr,
                )
                print(
                    (
                        "ALL errors in synapse directory must be fixed - "
                        + "no exceptions for pre-existing errors."
                    ),
                    file=sys.stderr,
                )
            print(
                "Note: Some errors cannot be auto-fixed and must be manually resolved.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Success
        if result.stdout:
            print(result.stdout)
        else:
            print("✅ All linting checks passed")
        sys.exit(0)

    except FileNotFoundError:
        print(
            f"Error: Linter command not found: {linter_cmd[0]}",
            file=sys.stderr,
        )
        print(
            "Install the linter or ensure it's in your PATH or .venv/bin/",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as e:
        print(f"Error running linter: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
