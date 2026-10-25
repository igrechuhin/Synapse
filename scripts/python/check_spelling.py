#!/usr/bin/env python3
"""Pre-commit hook to check spelling in code files.

This script checks for spelling errors in Python files using cSpell-compatible
word lists. It identifies unknown words that should be added to a dictionary
or fixed.

Requires cspell 8.6.1: bounded ``--version`` then ``lint --no-progress <files>``.
The checker discovers .cspell.json from the project working directory.

Configuration:
    SPELL_CHECKER_CMD: Installed cspell 8.6.1 command (shell-style argv, no shell)
    SPELL_CHECKER_PREFLIGHT_TIMEOUT: Positive finite seconds (default: 10)
    SPELL_CHECKER_TIMEOUT: Positive finite seconds per lint run (default: 120)
    Commands never install/download tools. Timeouts terminate the owned process
    group on POSIX: one second to exit, then one second to reap after SIGKILL.
    SRC_DIR: Source directory path (default: auto-detected)
    TESTS_DIR: Tests directory path (default: auto-detected)
"""

import math
import os
import shlex
import shutil
import signal
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


SUPPORTED_CSPELL_VERSION = "8.6.1"


def get_spell_checker_command(project_root: Path) -> list[str]:
    """Select one installed checker, without probing or downloading fallbacks."""
    override = os.environ.get("SPELL_CHECKER_CMD")
    if override is not None:
        command = shlex.split(override)
        if not command:
            raise ValueError("SPELL_CHECKER_CMD must name an installed cspell command")
        return command
    local = project_root / "node_modules" / ".bin" / "cspell"
    if local.exists() or local.is_symlink():
        return [str(local)]
    installed = shutil.which("cspell")
    if installed is None:
        raise FileNotFoundError(
            "cspell 8.6.1 not found; install it locally or on PATH, "
            + "or set SPELL_CHECKER_CMD to an installed checker"
        )
    return [installed]


def _timeout_seconds(name: str, default: float) -> float:
    """Require finite positive bounds, including when supplied by the caller."""
    value = float(os.environ.get(name, str(default)))
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a finite positive number of seconds")
    return value


def _signal_checker(process: subprocess.Popen[str], sig: signal.Signals) -> None:
    """Signal only the session created for this checker."""
    try:
        if os.name == "posix":
            os.killpg(process.pid, sig)
        elif process.poll() is None:
            process.kill()
    except ProcessLookupError:
        pass


def _stop_checker(process: subprocess.Popen[str]) -> str:
    """Reap the checker and terminate remaining members of its owned group."""
    _signal_checker(process, signal.SIGTERM)
    try:
        output, _ = process.communicate(timeout=1)
    except subprocess.TimeoutExpired:
        _signal_checker(process, signal.SIGKILL)
        output, _ = process.communicate(timeout=1)
    finally:
        _signal_checker(process, signal.SIGKILL)
    return output


def _run_checker(
    command: list[str], project_root: Path, timeout: float
) -> tuple[int, str]:
    """Return the real checker status and combined diagnostics, bounded in time."""
    try:
        # AI: Isolate checker descendants so timeout cleanup cannot signal sibling jobs.
        with subprocess.Popen(
            command,
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
            start_new_session=os.name == "posix",
        ) as process:
            try:
                output, _ = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                output = _stop_checker(process)
                return 124, output + f"\ncspell timed out after {timeout:g} seconds"
            return process.returncode, output
    except OSError as error:
        return 1, f"Error starting spell checker {command[0]}: {error}"


def _preflight_checker(command: list[str], project_root: Path) -> tuple[int, str]:
    """Require the pinned CI CLI contract before attempting lint."""
    timeout = _timeout_seconds("SPELL_CHECKER_PREFLIGHT_TIMEOUT", 10)
    returncode, output = _run_checker(command + ["--version"], project_root, timeout)
    if returncode != 0:
        return returncode, output
    if output.strip() != SUPPORTED_CSPELL_VERSION:
        return 1, (
            f"Unsupported cspell version; require {SUPPORTED_CSPELL_VERSION}.\n"
            + f"Checker --version output:\n{output}"
        )
    return 0, output


def get_files_to_check(project_root: Path) -> list[Path]:
    """Get files to check for spelling.

    Args:
        project_root: Path to project root

    Returns:
        List of file paths to check
    """
    files: list[Path] = []

    # Add source directory files
    src_dir = get_config_path("SRC_DIR")
    if src_dir is None:
        src_dir = find_src_directory(project_root)
    else:
        if not src_dir.is_absolute():
            src_dir = project_root / src_dir
        else:
            src_dir = Path(src_dir)

    if src_dir.exists():
        files.extend(src_dir.rglob("*.py"))

    # Add tests directory files
    tests_dir = get_config_path("TESTS_DIR")
    if tests_dir is None:
        # Try common test directory patterns
        for pattern in ["tests", "test"]:
            candidate = project_root / pattern
            if candidate.exists() and candidate.is_dir():
                files.extend(candidate.rglob("*.py"))
                break
    else:
        if not tests_dir.is_absolute():
            tests_dir = project_root / tests_dir
        else:
            tests_dir = Path(tests_dir)
        if tests_dir.exists():
            files.extend(tests_dir.rglob("*.py"))

    # Add scripts directory files
    scripts_dir = get_synapse_scripts_dir(project_root)
    if scripts_dir.exists():
        files.extend(scripts_dir.rglob("*.py"))

    # Filter out __pycache__ and other excluded directories
    filtered_files: list[Path] = []
    for file_path in files:
        if "__pycache__" not in str(file_path):
            if ".venv" not in str(file_path):
                if ".git" not in str(file_path):
                    filtered_files.append(file_path)

    return filtered_files


def check_spelling_with_cspell(
    files: list[Path], project_root: Path
) -> tuple[int, str]:
    """Return the checker exit code (not a finding count) and its diagnostics."""
    if not files:
        return (0, "")
    try:
        command = get_spell_checker_command(project_root)
        timeout = _timeout_seconds("SPELL_CHECKER_TIMEOUT", 120)
        returncode, output = _preflight_checker(command, project_root)
        if returncode != 0:
            return returncode, output
        file_paths = [str(path.relative_to(project_root)) for path in files]
        return _run_checker(
            command + ["lint", "--no-progress"] + file_paths, project_root, timeout
        )
    except (OSError, ValueError) as error:
        return 1, f"Error configuring spell checker: {error}"


def main() -> None:
    """Check spelling in code files."""
    # Get project root
    script_path = Path(__file__)
    project_root = get_project_root(script_path)

    # Get files to check
    files_to_check = get_files_to_check(project_root)

    if not files_to_check:
        print(
            "Warning: No files found to check",
            file=sys.stderr,
        )
        print(f"Project root: {project_root}", file=sys.stderr)
        sys.exit(0)  # Not an error, just nothing to check

    # Check spelling
    returncode, output = check_spelling_with_cspell(files_to_check, project_root)
    if returncode != 0:
        if output:
            print(output, file=sys.stderr)
        print(
            f"\n❌ Spelling check failed (checker exit code {returncode}).",
            file=sys.stderr,
        )
        sys.exit(returncode if returncode > 0 else min(255, 128 - returncode))

    print("✅ All spelling checks passed")
    sys.exit(0)


if __name__ == "__main__":
    main()
