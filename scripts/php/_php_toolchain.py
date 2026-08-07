#!/usr/bin/env python3
"""Shared PHP toolchain discovery for Synapse PHP quality gates.

Probes vendor/bin/ (Composer) before system PATH, so a project's pinned tool
version always wins over a global install.

Configuration:
    PHP_FORMATTER:    Formatter binary (default: probe pint, php-cs-fixer)
    PHP_ANALYZER:     Static analyzer (default: probe phpstan, psalm)
    PHP_TEST_RUNNER:  Test runner (default: probe pest, phpunit)
    PHP_BINARY:       php interpreter (default: probe PATH)
    PROJECT_ROOT:     Project root override (default: filesystem walk)
    PHP_SRC_DIR:      Source directory (default: probe app/, src/, lib/)
    PHP_TESTS_DIR:    Tests directory (default: probe tests/, test/)
    PHP_TOOL_TIMEOUT: Subprocess timeout in seconds (default: 120)
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import NoReturn

try:
    from _utils import get_config_int, get_config_path, get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
    from _utils import get_config_int, get_config_path, get_project_root


PHP_TOOL_TIMEOUT = get_config_int("PHP_TOOL_TIMEOUT", 120)

_SRC_CANDIDATES = ("app", "src", "lib")
_TESTS_CANDIDATES = ("tests", "test")


def find_php_tool(
    candidates: list[str],
    project_root: Path,
    env_override: str | None = None,
) -> str | None:
    """Locate the first available tool from an ordered candidate list.

    Args:
        candidates: Tool names in preference order, e.g. ["pint", "php-cs-fixer"].
        project_root: Path to project root.
        env_override: Environment variable that, when set, short-circuits probing.

    Returns:
        Path to the tool, or None when every candidate is exhausted.
    """
    if env_override:
        override = os.getenv(env_override)
        if override:
            return override

    for name in candidates:
        vendor_tool = project_root / "vendor" / "bin" / name
        if vendor_tool.exists():
            return str(vendor_tool)
        system_tool = shutil.which(name)
        if system_tool:
            return system_tool

    return None


def find_php_binary() -> str | None:
    """Locate the php interpreter itself.

    Returns:
        Path to php, or None when not installed.
    """
    override = os.getenv("PHP_BINARY")
    if override:
        return override
    return shutil.which("php")


def php_project_root(script_path: Path) -> Path:
    """Resolve the PHP project root.

    get_project_root() walks the filesystem for .git / README.md markers and has
    no environment override. When a gate is invoked by absolute path from
    outside a consumer repo, that walk lands on Synapse itself rather than the
    PHP project, so tool discovery would probe the wrong vendor/bin.

    PROJECT_ROOT takes precedence; otherwise the walk applies unchanged.

    Args:
        script_path: Path to the calling script, normally __file__.

    Returns:
        Path to the PHP project root.
    """
    override = get_config_path("PROJECT_ROOT")
    if override is not None and override.is_dir():
        return override
    return get_project_root(script_path)


def _resolve_configured_dir(key: str, project_root: Path) -> Path | None:
    """Resolve a directory from an environment variable, if set and present."""
    configured = get_config_path(key)
    if configured is None:
        return None
    resolved = configured if configured.is_absolute() else project_root / configured
    return resolved if resolved.is_dir() else None


def php_source_dirs(project_root: Path) -> list[Path]:
    """Detect PHP source and test directories.

    Laravel uses app/; PSR-4 packages use src/. Only the first source match is
    returned, so a project with both does not get double-scanned.

    Args:
        project_root: Path to project root.

    Returns:
        List of existing directories to scan. May be empty.
    """
    dirs: list[Path] = []

    configured_src = _resolve_configured_dir("PHP_SRC_DIR", project_root)
    if configured_src is not None:
        dirs.append(configured_src)
    else:
        for name in _SRC_CANDIDATES:
            candidate = project_root / name
            if candidate.is_dir() and any(candidate.rglob("*.php")):
                dirs.append(candidate)
                break

    configured_tests = _resolve_configured_dir("PHP_TESTS_DIR", project_root)
    if configured_tests is not None:
        dirs.append(configured_tests)
    else:
        for name in _TESTS_CANDIDATES:
            candidate = project_root / name
            if candidate.is_dir():
                dirs.append(candidate)
                break

    return dirs


def php_files_from_env() -> list[Path] | None:
    """Parse the FILES environment variable, filtered to *.php.

    Returns:
        List of paths, or None when FILES is unset or blank.
    """
    files_env = os.environ.get("FILES")
    if files_env is None:
        return None
    stripped = files_env.strip()
    if not stripped:
        return None
    return [
        Path(line) for line in stripped.splitlines() if line.strip().endswith(".php")
    ]


def allow_full_scan() -> bool:
    """Return True when the fallback full-repo scan is explicitly enabled."""
    return os.environ.get("ALLOW_FULL_SCAN") == "1"


def count_logical_lines(text: str) -> int:
    """Count non-blank, non-comment PHP lines.

    PHP 8 attributes (#[Foo]) are code, not hash comments, and are counted.

    Args:
        text: Full file contents.

    Returns:
        Number of logical lines.
    """
    count = 0
    in_block_comment = False

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        if in_block_comment:
            if "*/" in line:
                in_block_comment = False
            continue

        if line.startswith("//"):
            continue
        if line.startswith("#") and not line.startswith("#["):
            continue
        if line.startswith("/*"):
            in_block_comment = "*/" not in line
            continue

        count += 1

    return count


def skip(message: str) -> NoReturn:
    """Print a skip notice and exit 0.

    A missing tool is a project configuration gap, not a code defect, so it
    must not block the commit pipeline.
    """
    print(f"⚠️  {message}")
    sys.exit(0)
