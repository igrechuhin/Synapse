#!/usr/bin/env python3
"""Pre-commit hook to check spelling in Swift sources.

Checks ``*.swift`` files under the documented Swift scope (``Sources/`` and
``Tests/``) using cSpell. Exit codes and diagnostics of the checker are
preserved: a nonzero checker status is a failure, never converted into a file
count or suppressed.

Requires cspell 8.6.1: bounded ``--version`` then ``lint --no-progress <files>``.
The checker discovers .cspell.json from the project working directory.

Configuration:
    SPELL_CHECKER_CMD: Installed cspell 8.6.1 command (shell-style argv, no shell)
    SPELL_CHECKER_PREFLIGHT_TIMEOUT: Positive finite seconds (default: 10)
    SPELL_CHECKER_TIMEOUT: Positive finite seconds per lint run (default: 120)
    SPELL_CHECKER_MAX_BATCH_FILES: Max files per lint invocation (default: 512)
    SPELL_CHECKER_MAX_BATCH_BYTES: Max summed argv bytes per invocation (default: 65536)
    Lint batches keep exec argv bounded; every batch runs, the first nonzero
    checker status wins, and all batch diagnostics are reported.
    Commands never install/download tools. Timeouts terminate the owned process
    group on POSIX: one second to exit, then one second to reap after SIGKILL.
    SRC_DIR: Swift source directory (default: Sources/)
    TESTS_DIR: Swift tests directory (default: Tests/)
"""

import math
import os
import shlex
import shutil
import signal
import subprocess
import sys
from pathlib import Path

try:
    from _utils import get_config_path, get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
    from _utils import get_config_path, get_project_root

SUPPORTED_CSPELL_VERSION = "8.6.1"

# Directories never spelling-checked (build artifacts and VCS metadata).
_EXCLUDED_DIR_NAMES = frozenset({".build", ".git"})


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


def _resolve_dir(project_root: Path, config_key: str, default: str) -> Path | None:
    """Resolve a configured directory against the project root."""
    value = get_config_path(config_key)
    path = Path(value) if value is not None else project_root / default
    if not path.is_absolute():
        path = project_root / path
    return path if path.exists() else None


def get_swift_files(project_root: Path) -> list[Path]:
    """Collect ``*.swift`` files from the documented Sources/Tests scope only."""
    files: list[Path] = []
    for key, default in (("SRC_DIR", "Sources"), ("TESTS_DIR", "Tests")):
        directory = _resolve_dir(project_root, key, default)
        if directory is not None:
            files.extend(
                path
                for path in directory.rglob("*.swift")
                if not _EXCLUDED_DIR_NAMES.intersection(path.parts)
            )
    return sorted(set(files))


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
        file_paths = [
            (
                str(path.relative_to(project_root))
                if path.is_relative_to(project_root)
                else str(path)
            )
            for path in files
        ]
        return _lint_batches(command, file_paths, project_root, timeout)
    except (OSError, ValueError) as error:
        return 1, f"Error configuring spell checker: {error}"


def _lint_batches(
    command: list[str], file_paths: list[str], project_root: Path, timeout: float
) -> tuple[int, str]:
    """Lint every bounded batch; first nonzero status wins, all output kept."""
    max_files = int(os.environ.get("SPELL_CHECKER_MAX_BATCH_FILES", 512))
    max_bytes = int(os.environ.get("SPELL_CHECKER_MAX_BATCH_BYTES", 65536))
    if max_files <= 0 or max_bytes <= 1:
        raise ValueError("Batch limits must be positive")
    first_nonzero, outputs = 0, []
    index = 0
    while index < len(file_paths):
        batch, size = [], 0
        while index < len(file_paths) and len(batch) < max_files:
            path = file_paths[index]
            path_bytes = len(os.fsencode(path)) + 1
            if path_bytes > max_bytes:
                raise ValueError(
                    f"File path exceeds SPELL_CHECKER_MAX_BATCH_BYTES "
                    f"({max_bytes}): {path}"
                )
            if batch and size + path_bytes > max_bytes:
                break
            batch.append(path)
            size += path_bytes
            index += 1
        if not batch:
            raise ValueError("Batch byte limit smaller than one file path")
        returncode, output = _run_checker(
            command + ["lint", "--no-progress"] + batch, project_root, timeout
        )
        if output:
            outputs.append(output)
        if returncode != 0 and first_nonzero == 0:
            first_nonzero = returncode
    return first_nonzero, "\n".join(outputs)


def main() -> None:
    """Check spelling in Swift sources."""
    project_root = get_project_root(Path(__file__))
    files_to_check = get_swift_files(project_root)

    if not files_to_check:
        print(
            "Warning: No Swift files found to check in Sources/Tests scope",
            file=sys.stderr,
        )
        print(f"Project root: {project_root}", file=sys.stderr)
        sys.exit(0)  # Not an error, just nothing to check

    returncode, output = check_spelling_with_cspell(files_to_check, project_root)
    if returncode != 0:
        if output:
            print(output, file=sys.stderr)
        print(
            f"\n❌ Spelling check failed (checker exit code {returncode}).",
            file=sys.stderr,
        )
        sys.exit(returncode if returncode > 0 else min(255, 128 - returncode))

    print("✅ All Swift spelling checks passed")
    sys.exit(0)


if __name__ == "__main__":
    main()
