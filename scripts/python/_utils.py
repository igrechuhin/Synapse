#!/usr/bin/env python3
"""Shared utilities for Python quality check scripts.

This module provides common functionality for finding project root,
detecting source directories, and reading configuration from environment variables.
"""

import os
from pathlib import Path


def get_project_root(script_path: Path | None = None) -> Path:
    """Get the project root directory.

    Works whether script is in:
    - scripts/ (at project root)
    - .cortex/synapse/scripts/python/ (in Synapse submodule)

    Args:
        script_path: Path to the script file (defaults to __file__)

    Returns:
        Path to project root directory

    Raises:
        RuntimeError: If project root cannot be determined
    """
    if script_path is None:
        # Default to current file's location
        script_path = Path(__file__).resolve()

    current = script_path.resolve().parent

    # If we're in .cortex/synapse/scripts/python/, go up to project root
    # Path structure: project_root/.cortex/synapse/scripts/python/script.py
    # We need to go up 4 levels: python -> scripts -> synapse -> .cortex -> project_root
    parts = current.parts
    try:
        # Find .cortex in the path
        cortex_idx = None
        for i, part in enumerate(parts):
            if part == ".cortex":
                cortex_idx = i
                break

        if cortex_idx is not None:
            # We're in .cortex/, go up one level to project root
            return Path(*parts[:cortex_idx])
    except (ValueError, IndexError):
        pass

    # Walk up the directory tree looking for project root indicators
    for path in [current, *current.parents]:
        # Check for common project root indicators
        root_indicators = [
            "pyproject.toml",
            "setup.py",
            ".git",
            "README.md",
            "requirements.txt",
        ]

        # Skip if we're still inside .cortex/synapse
        if ".cortex" in str(path) and "synapse" in str(path):
            continue

        # Check if this looks like a project root
        has_indicator = any(
            (path / indicator).exists() for indicator in root_indicators
        )
        if has_indicator:
            return path

    # Last resort: go up from scripts/ directory
    if current.name == "scripts" or (
        current.parent.name == "python" and current.parent.parent.name == "scripts"
    ):
        return current.parent

    # If all else fails, use current working directory
    return Path.cwd()


def find_src_directory(project_root: Path) -> Path:
    """Find the source code directory.

    Tries common patterns:
    - src/ (most common)
    - src/<package>/ (if package name can be detected)
    - lib/
    - <project_name>/

    Args:
        project_root: Path to project root

    Returns:
        Path to source directory

    Raises:
        RuntimeError: If source directory cannot be found
    """
    # Try common patterns
    candidates = [
        project_root / "src",
        project_root / "lib",
    ]

    # Try to detect package name from project root
    project_name = project_root.name.lower().replace("-", "_")
    candidates.extend(
        [
            project_root / "src" / project_name,
            project_root / project_name,
        ]
    )

    # Check each candidate
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            # Verify it contains Python files
            if any(candidate.rglob("*.py")):
                return candidate

    # Default to src/ even if it doesn't exist yet (let caller handle error)
    return project_root / "src"


def get_config_int(key: str, default: int) -> int:
    """Get integer configuration from environment variable.

    Args:
        key: Environment variable name
        default: Default value if not set or invalid

    Returns:
        Integer value from environment or default
    """
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_config_path(key: str, default: Path | None = None) -> Path | None:
    """Get path configuration from environment variable.

    Args:
        key: Environment variable name
        default: Default value if not set

    Returns:
        Path from environment or default
    """
    value = os.getenv(key)
    if value is None:
        return default
    return Path(value)


def get_synapse_scripts_dir(project_root: Path) -> Path:
    """Get synapse scripts directory path.

    Uses SCRIPTS_DIR environment variable if set, otherwise falls back to
    the default .cortex/synapse/scripts location.

    Args:
        project_root: Path to project root

    Returns:
        Path to synapse scripts directory
    """
    scripts_dir = get_config_path("SCRIPTS_DIR")
    if scripts_dir is None:
        # Default to .cortex/synapse/scripts
        return project_root / ".cortex" / "synapse" / "scripts"

    # Make path relative to project root if not absolute
    if not scripts_dir.is_absolute():
        return project_root / scripts_dir

    return scripts_dir
