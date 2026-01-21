#!/usr/bin/env python3
"""Pre-commit hook to run tests.

This script runs the test suite (pytest) with coverage and verifies
that all tests pass and coverage threshold is met.

Configuration:
    TEST_CMD: Test command to run (default: pytest)
    TESTS_DIR: Tests directory path (default: auto-detected)
    COVERAGE_THRESHOLD: Minimum coverage percentage (default: 90)
    TEST_TIMEOUT: Timeout in seconds (default: 300)
"""

import subprocess
import sys
from pathlib import Path

# Import shared utilities
try:
    from _utils import (
        get_config_int,
        get_config_path,
        get_project_root,
    )
except ImportError:
    # Fallback if running from different location
    sys.path.insert(0, str(Path(__file__).parent))
    from _utils import (
        get_config_int,
        get_config_path,
        get_project_root,
    )


COVERAGE_THRESHOLD = get_config_int("COVERAGE_THRESHOLD", 90)
TEST_TIMEOUT = get_config_int("TEST_TIMEOUT", 300)


def get_test_command(project_root: Path) -> list[str]:
    """Get test command to run.

    Args:
        project_root: Path to project root

    Returns:
        List of command parts to run
    """
    # Try .venv/bin/pytest first
    venv_pytest = project_root / ".venv" / "bin" / "pytest"
    if venv_pytest.exists():
        return [str(venv_pytest)]

    # Try uv run pytest
    try:
        subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            check=True,
            cwd=project_root,
        )
        return ["uv", "run", "pytest"]
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Fallback to system pytest
    return ["pytest"]


def get_tests_directory(project_root: Path) -> Path | None:
    """Get tests directory.

    Args:
        project_root: Path to project root

    Returns:
        Path to tests directory or None if not found
    """
    tests_dir = get_config_path("TESTS_DIR")
    if tests_dir is not None:
        if not tests_dir.is_absolute():
            tests_dir = project_root / tests_dir
        else:
            tests_dir = Path(tests_dir)
        if tests_dir.exists():
            return tests_dir

    # Try common test directory patterns
    for pattern in ["tests", "test"]:
        candidate = project_root / pattern
        if candidate.exists() and candidate.is_dir():
            return candidate

    return None


def main():
    """Run tests with coverage."""
    # Get project root
    script_path = Path(__file__)
    project_root = get_project_root(script_path)

    # Get test command
    test_cmd = get_test_command(project_root)

    # Get tests directory
    tests_dir = get_tests_directory(project_root)

    if tests_dir is None:
        print(
            "Warning: No tests directory found",
            file=sys.stderr,
        )
        print(f"Project root: {project_root}", file=sys.stderr)
        sys.exit(0)  # Not an error, just nothing to test

    # Build test command with coverage
    cmd = test_cmd + [
        str(tests_dir),
        "-v",
        "--cov=src",
        "--cov-report=term",
        f"--cov-fail-under={COVERAGE_THRESHOLD}",
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=TEST_TIMEOUT,
        )

        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        if result.returncode != 0:
            print(
                "\n❌ Tests failed or coverage below threshold.",
                file=sys.stderr,
            )
            sys.exit(1)

        print("✅ All tests passed with required coverage")
        sys.exit(0)

    except subprocess.TimeoutExpired:
        print(
            f"\n❌ Tests timed out after {TEST_TIMEOUT} seconds.",
            file=sys.stderr,
        )
        sys.exit(1)
    except FileNotFoundError:
        print(
            f"Error: Test command not found: {test_cmd[0]}",
            file=sys.stderr,
        )
        print(
            "Install pytest or ensure it's in your PATH or .venv/bin/",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as e:
        print(f"Error running tests: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
