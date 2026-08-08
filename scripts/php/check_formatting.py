#!/usr/bin/env python3
"""Pre-commit hook to verify PHP formatting without writing changes.

Probes for Laravel Pint first, then PHP-CS-Fixer. When neither is installed the
gate skips with exit 0, since a missing formatter is a configuration gap rather
than a code defect.

Configuration:
    PHP_FORMATTER:    Formatter binary (default: probe pint, php-cs-fixer)
    PHP_TOOL_TIMEOUT: Timeout in seconds (default: 120)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from _php_toolchain import (
    PHP_TOOL_TIMEOUT,
    find_php_tool,
    php_files_from_env,
    php_project_root,
    php_source_dirs,
    skip,
)


FORMATTER_CANDIDATES = ["pint", "php-cs-fixer"]


def build_format_cmd(tool: str, paths: list[str], write: bool) -> list[str]:
    """Construct the formatter invocation.

    Args:
        tool: Path to the formatter binary.
        paths: Files or directories to format.
        write: True to apply changes, False for check-only.

    Returns:
        List of command parts.
    """
    name = Path(tool).name

    if name == "pint":
        cmd = [tool, *paths]
        if not write:
            cmd.append("--test")
        return cmd

    cmd = [tool, "fix", *paths]
    if not write:
        cmd.extend(["--dry-run", "--diff"])
    return cmd


def resolve_paths(project_root: Path) -> list[str]:
    """Resolve the paths to hand the formatter."""
    from_env = php_files_from_env()
    if from_env is not None:
        return [str(p) for p in from_env]
    return [str(d) for d in php_source_dirs(project_root)]


def run_formatter(write: bool) -> None:
    """Run the formatter in check or write mode and exit accordingly."""
    project_root = php_project_root(Path(__file__))

    tool = find_php_tool(
        FORMATTER_CANDIDATES, project_root, env_override="PHP_FORMATTER"
    )
    if tool is None or not Path(tool).exists():
        msg = (
            "No PHP formatter installed, skipping "
            "(composer require --dev laravel/pint)"
        )
        skip(msg)

    paths = resolve_paths(project_root)
    if not paths:
        print("✅ No PHP sources detected (skipped)")
        sys.exit(0)

    cmd = build_format_cmd(tool, paths, write=write)

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=PHP_TOOL_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        print(f"❌ Formatter timed out after {PHP_TOOL_TIMEOUT}s", file=sys.stderr)
        sys.exit(1)
    except OSError as exc:
        print(f"❌ Error running formatter: {exc}", file=sys.stderr)
        sys.exit(1)

    if result.returncode != 0:
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        hint = (
            "Formatter could not apply all changes."
            if write
            else "Run fix_formatting.py to fix."
        )
        print(f"\n❌ Formatting issues detected. {hint}", file=sys.stderr)
        sys.exit(1)

    if result.stdout:
        print(result.stdout)
    print("✅ All formatting checks passed")
    sys.exit(0)


def main() -> None:
    run_formatter(write=False)


if __name__ == "__main__":
    main()
