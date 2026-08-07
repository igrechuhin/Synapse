#!/usr/bin/env python3
"""Pre-commit hook to run PHP syntax linting (php -l).

php -l ships with the PHP interpreter, so this gate never skips for a missing
tool. A missing php binary is a broken environment and fails hard.

Configuration:
    PHP_BINARY:       php interpreter (default: probe PATH)
    PHP_TOOL_TIMEOUT: Timeout in seconds (default: 120)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from _php_toolchain import (
    PHP_TOOL_TIMEOUT,
    allow_full_scan,
    find_php_binary,
    php_files_from_env,
    php_project_root,
    php_source_dirs,
)


def lint_file(php_binary: str, path: Path) -> tuple[bool, str]:
    """Run php -l against a single file.

    php -l accepts exactly one file per invocation.

    Args:
        php_binary: Path to the php interpreter.
        path: PHP file to check.

    Returns:
        Tuple of (passed, message). message is empty when passed.
    """
    try:
        result = subprocess.run(
            [php_binary, "-l", str(path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=PHP_TOOL_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return False, f"timed out after {PHP_TOOL_TIMEOUT}s"
    except (FileNotFoundError, OSError) as exc:
        return False, f"could not run php: {exc}"

    if result.returncode == 0:
        return True, ""
    return False, (result.stdout or result.stderr).strip()


def _collect_files(project_root: Path) -> list[Path] | None:
    from_env = php_files_from_env()
    if from_env is not None:
        return from_env

    if not allow_full_scan():
        return None

    files: list[Path] = []
    for directory in php_source_dirs(project_root):
        files.extend(sorted(directory.rglob("*.php")))
    return files


def main() -> None:
    project_root = php_project_root(Path(__file__))

    php_binary = find_php_binary()
    if php_binary is None or not Path(php_binary).exists():
        print("❌ php interpreter not found", file=sys.stderr)
        print(
            "Install PHP or set PHP_BINARY to the interpreter path.",
            file=sys.stderr,
        )
        sys.exit(1)

    php_files = _collect_files(project_root)

    if php_files is None:
        print("✅ No FILES provided and ALLOW_FULL_SCAN!=1 (skipped)")
        sys.exit(0)

    if not php_files:
        print("✅ No PHP sources detected (skipped)")
        sys.exit(0)

    failures: list[tuple[Path, str]] = []
    for php_file in php_files:
        if not php_file.exists():
            continue
        passed, message = lint_file(php_binary, php_file)
        if not passed:
            failures.append((php_file, message))

    if failures:
        print("❌ PHP syntax errors detected:", file=sys.stderr)
        print(file=sys.stderr)
        for path, message in failures:
            print(f"  {path}: {message}", file=sys.stderr)
        print(file=sys.stderr)
        print(f"Total: {len(failures)} file(s) with syntax errors", file=sys.stderr)
        sys.exit(1)

    print(f"✅ PHP syntax valid ({len(php_files)} file(s) checked)")
    sys.exit(0)


if __name__ == "__main__":
    main()
