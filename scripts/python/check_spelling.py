#!/usr/bin/env python3
"""Pre-commit hook to check spelling in code files.

This script checks for spelling errors in Python files using cSpell-compatible
word lists. It identifies unknown words that should be added to a dictionary
or fixed.

Configuration:
    SPELL_CHECKER_CMD: Spell checker command (default: cspell)
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


def get_spell_checker_command() -> list[str]:
    """Get spell checker command to run.

    Returns:
        List of command parts to run
    """
    # Try cspell (cSpell CLI)
    try:
        _ = subprocess.run(
            ["cspell", "--version"],
            capture_output=True,
            check=True,
        )
        return ["cspell"]
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Try npx cspell
    try:
        _ = subprocess.run(
            ["npx", "--version"],
            capture_output=True,
            check=True,
        )
        return ["npx", "-y", "cspell"]
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Fallback: return command anyway, will fail with clear error
    return ["cspell"]


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
    scripts_dir = project_root / ".cortex" / "synapse" / "scripts"
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
    """Check spelling using cspell.

    Args:
        files: List of files to check
        project_root: Path to project root

    Returns:
        Tuple of (error_count, output_text)
    """
    if not files:
        return (0, "")

    spell_checker_cmd = get_spell_checker_command()

    # Create file list for cspell
    file_paths = [str(f.relative_to(project_root)) for f in files]

    # Run cspell
    try:
        result = subprocess.run(
            spell_checker_cmd + ["--files-only", "--no-progress"] + file_paths,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )

        output = result.stdout + result.stderr
        error_count = result.returncode

        # Count errors from output (cspell returns non-zero on errors)
        if error_count != 0:
            # Count unique files with errors
            error_files: set[str] = set()
            for line in output.split("\n"):
                if line.strip() and not line.startswith("cspell"):
                    # Extract file path from error line
                    parts = line.split(":")
                    if len(parts) >= 1:
                        file_path = parts[0].strip()
                        if file_path and file_path.endswith(".py"):
                            error_files.add(file_path)

            error_count = len(error_files)

        return (error_count, output)

    except FileNotFoundError:
        return (
            -1,
            (
                f"Error: Spell checker command not found: {spell_checker_cmd[0]}\n"
                "Install cspell: npm install -g cspell\n"
                "Or use: npx -y cspell"
            ),
        )
    except Exception as e:
        return (-1, f"Error running spell checker: {e}")


def main():
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
    error_count, output = check_spelling_with_cspell(files_to_check, project_root)

    if error_count < 0:
        # Error running spell checker
        print(output, file=sys.stderr)
        sys.exit(1)

    if error_count > 0:
        # Print output
        if output:
            print(output, file=sys.stderr)

        print(
            f"\n❌ Spelling errors detected in {error_count} file(s).",
            file=sys.stderr,
        )
        print(
            "Fix spelling errors or add words to .cspell.json dictionary.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("✅ All spelling checks passed")
    sys.exit(0)


if __name__ == "__main__":
    main()
