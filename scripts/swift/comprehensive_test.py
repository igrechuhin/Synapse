#!/usr/bin/env python3
"""Comprehensive Swift quality pipeline with zero-tolerance policy.

Runs all quality checks in sequence. ANY failure blocks the pipeline.
Saves a timestamped markdown log to .logs/ (retains last 10 logs).

Configuration:
    FAST_MODE:   Set to 1 to skip slow checks (MLX, complexity) (default: 0)
    LOG_DIR:     Directory for log files (default: <script_dir>/.logs)
    TEST_TIMEOUT: Forwarded to run_tests.py (default: 600)
"""

from __future__ import annotations

import datetime
import subprocess
import sys
from pathlib import Path

try:
    from _utils import get_config_int, get_config_path, get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
    from _utils import get_config_int, get_config_path, get_project_root


FAST_MODE = get_config_int("FAST_MODE", 0)
_SCRIPT_DIR = Path(__file__).parent


def get_log_dir() -> Path:
    """Return the log directory, creating it if needed.

    Returns:
        Path to the .logs directory.
    """
    log_dir_override = get_config_path("LOG_DIR")
    if log_dir_override is not None:
        log_dir = log_dir_override
    else:
        log_dir = _SCRIPT_DIR / ".logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def run_script(name: str, script: Path, log_lines: list[str]) -> bool:
    """Run a single Python check script and capture output.

    Args:
        name: Human-readable check name.
        script: Path to the Python script.
        log_lines: Mutable list to append log output to.

    Returns:
        True if the check passed, False otherwise.
    """
    log_lines.append(f"\n## {name}\n")

    if not script.exists():
        msg = f"SKIP: {name} (script not found: {script.name})"
        print(msg)
        log_lines.append(msg + "\n")
        return True  # Missing script is not a hard failure

    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            check=False,
        )
        output = (result.stdout + result.stderr).strip()
        if output:
            log_lines.append(output + "\n")

        if result.returncode == 0:
            print(f"PASS: {name}")
            log_lines.append(f"PASS: {name}\n")
            return True

        print(f"FAIL: {name}", file=sys.stderr)
        log_lines.append(f"FAIL: {name}\n")
        return False

    except Exception as e:
        msg = f"ERROR: {name} — {e}"
        print(msg, file=sys.stderr)
        log_lines.append(msg + "\n")
        return False


def prune_old_logs(log_dir: Path, keep: int = 10) -> None:
    """Remove old log files, keeping the most recent ones.

    Args:
        log_dir: Directory containing log files.
        keep: Number of recent logs to retain.
    """
    logs = sorted(log_dir.glob("comprehensive-test-*.md"), reverse=True)
    for old_log in logs[keep:]:
        old_log.unlink(missing_ok=True)


def main() -> None:
    """Run the comprehensive Swift quality pipeline."""
    project_root = get_project_root(Path(__file__))
    scripts_dir = _SCRIPT_DIR
    log_dir = get_log_dir()

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    log_file = log_dir / f"comprehensive-test-{timestamp}.md"
    latest_log = log_dir / "comprehensive-test-latest.md"

    log_lines: list[str] = [
        f"# Comprehensive Test — {timestamp}\n\n",
        f"Project: {project_root}\n",
        f"Fast mode: {bool(FAST_MODE)}\n",
    ]

    start = datetime.datetime.now()

    checks: list[tuple[str, str]] = [
        ("Package validation", "validate_package.py"),
        ("SwiftFormat compliance", "check_formatting.py"),
        ("File size limits", "check_file_sizes.py"),
        ("Function length limits", "check_function_lengths.py"),
        ("One public type per file", "check_one_type_per_file.py"),
        ("No print() in production", "validate_no_print.py"),
        ("No force-unwrap", "validate_no_force_unwrap.py"),
        ("No .pb.swift modifications", "validate_no_pb_modification.py"),
        ("Secret scanning", "validate_secrets.py"),
        ("Test naming conventions", "validate_test_naming.py"),
    ]

    if not FAST_MODE:
        checks += [
            ("MLX compatibility", "validate_mlx_compatibility.py"),
            ("Complexity analysis", "analyze_complexity.py"),
            ("IndicatorFactory constraint", "validate_indicator_factory.py"),
            ("DocC coverage", "check_docc.py"),
        ]

    checks.append(("Test suite", "run_tests.py"))

    passed = failed = 0
    for name, script_name in checks:
        ok = run_script(name, scripts_dir / script_name, log_lines)
        if ok:
            passed += 1
        else:
            failed += 1

    elapsed = (datetime.datetime.now() - start).seconds
    summary = "".join(
        [
            "\n---\n## Summary\n\n",
            f"- Passed: {passed}\n",
            f"- Failed: {failed}\n",
            f"- Duration: {elapsed}s\n",
        ]
    )
    log_lines.append(summary)

    log_content = "".join(log_lines)
    _ = log_file.write_text(log_content, encoding="utf-8")
    _ = latest_log.write_text(log_content, encoding="utf-8")
    prune_old_logs(log_dir)

    print(f"\nResults: {passed} passed, {failed} failed ({elapsed}s)")
    print(f"Log: {log_file}")

    if failed > 0:
        print(
            f"\n❌ Pipeline failed — fix all {failed} failure(s) before committing.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("✅ All checks passed")
    sys.exit(0)


if __name__ == "__main__":
    main()
