#!/usr/bin/env python3
"""Pre-commit hook to check type annotations.

This script runs the type checker (pyright) to verify type safety.

Configuration:
    TYPE_CHECKER_CMD: Type checker command to run (default: pyright)
    SRC_DIR: Source directory path (default: auto-detected)
"""

import json
import re
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


def get_type_checker_command(project_root: Path) -> list[str]:
    """Get type checker command to run.

    Args:
        project_root: Path to project root

    Returns:
        List of command parts to run
    """
    # Try .venv/bin/pyright first
    venv_pyright = project_root / ".venv" / "bin" / "pyright"
    if venv_pyright.exists():
        return [str(venv_pyright)]

    # Try uv run pyright
    try:
        _ = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            check=True,
            cwd=project_root,
        )
        return ["uv", "run", "pyright"]
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Fallback to system pyright
    return ["pyright"]


def get_directories_to_check(project_root: Path) -> list[str]:
    """Get directories to check with type checker.

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
        for pattern in ["tests", "test"]:
            candidate = project_root / pattern
            if candidate.exists() and candidate.is_dir():
                dirs.append(str(candidate))
                break
    else:
        if not tests_dir.is_absolute():
            tests_dir = project_root / tests_dir
        else:
            tests_dir = Path(tests_dir)
        if tests_dir.exists():
            dirs.append(str(tests_dir))

    # Add scripts directory if it exists
    scripts_dir = project_root / ".cortex" / "synapse" / "scripts"
    if scripts_dir.exists():
        dirs.append(str(scripts_dir))

    return dirs


def main():
    """Check type annotations."""
    # Get project root
    script_path = Path(__file__)
    project_root = get_project_root(script_path)

    # Get type checker command
    type_checker_cmd = get_type_checker_command(project_root)

    # Get directories to check
    dirs_to_check = get_directories_to_check(project_root)

    if not dirs_to_check:
        print(
            "Warning: No directories found to check",
            file=sys.stderr,
        )
        print(f"Project root: {project_root}", file=sys.stderr)
        sys.exit(0)  # Not an error, just nothing to check

    # Run type checker on each directory separately to avoid config exclusion issues
    # This ensures tests and scripts are checked even if pyrightconfig.json excludes them
    all_errors = False
    all_output = ""

    for dir_to_check in dirs_to_check:
        # Run type checker on this directory
        # Pyright automatically finds pyrightconfig.json in project root
        # Even when checking excluded directories, the config settings (like strict type checks) still apply
        # We explicitly check the directory to bypass the exclude list, but strict settings are still enforced
        # Try JSON output first, fall back to text if not supported
        has_errors = False
        error_count = 0
        warning_count = 0
        output = ""
        result = None

        # First, try with JSON output
        cmd_json = type_checker_cmd + ["--outputjson", dir_to_check]
        json_success = False
        try:
            result_json = subprocess.run(
                cmd_json,
                cwd=project_root,
                capture_output=True,
                text=True,
                check=False,
                timeout=300,  # 5 minute timeout
            )

            # Try to parse JSON output
            try:
                json_data = json.loads(result_json.stdout)
                all_output += f"\n=== Type checking {dir_to_check} (JSON) ===\n"

                if "generalDiagnostics" in json_data:
                    diagnostics = json_data["generalDiagnostics"]
                    for diag in diagnostics:
                        severity = diag.get("severity", "").lower()
                        rule = diag.get("rule", "")
                        # Count errors (severity "error") and warnings (severity "warning")
                        if severity == "error":
                            error_count += 1
                            has_errors = True
                        elif severity == "warning":
                            warning_count += 1
                            has_errors = True

                        # Also check for specific error rule types
                        error_rules = [
                            "reportArgumentType",
                            "reportUnknownVariableType",
                            "reportUnknownMemberType",
                            "reportAttributeAccessIssue",
                            "reportAssignmentType",
                            "reportIndexIssue",
                            "reportOperatorIssue",
                            "reportGeneralTypeIssues",
                            "reportUnknownArgumentType",
                        ]
                        if rule in error_rules:
                            has_errors = True

                # Also check summary if available
                if "summary" in json_data:
                    summary = json_data["summary"]
                    error_count = max(error_count, summary.get("errorCount", 0))
                    warning_count = max(warning_count, summary.get("warningCount", 0))
                    if error_count > 0 or warning_count > 0:
                        has_errors = True

                # Format output for display
                if has_errors or error_count > 0 or warning_count > 0:
                    all_output += (
                        f"Found {error_count} error(s), {warning_count} warning(s)\n"
                    )
                    # Add diagnostic details
                    if "generalDiagnostics" in json_data:
                        for diag in json_data["generalDiagnostics"]:
                            file = diag.get("file", "")
                            line = (
                                diag.get("range", {}).get("start", {}).get("line", "")
                            )
                            message = diag.get("message", "")
                            rule = diag.get("rule", "")
                            severity = diag.get("severity", "")
                            all_output += (
                                f"  {severity}: {file}:{line}: {message} ({rule})\n"
                            )
                else:
                    all_output += "No errors or warnings found\n"

                # Use JSON result
                result = result_json
                output = result_json.stdout + result_json.stderr
                json_success = True

            except (json.JSONDecodeError, KeyError, ValueError):
                # JSON parsing failed, fall through to text parsing
                json_success = False

        except (FileNotFoundError, subprocess.TimeoutExpired):
            # JSON output not supported or timed out, fall through to text
            json_success = False

        # If JSON parsing failed or not supported, use text output
        if not json_success:
            cmd = type_checker_cmd + [dir_to_check]
            try:
                result = subprocess.run(
                    cmd,
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=300,  # 5 minute timeout
                )

                output = result.stdout + result.stderr
                all_output += f"\n=== Type checking {dir_to_check} ===\n"
                all_output += output

                # Check for errors in output
                # More robust error detection - check for actual error/warning counts
                # Pyright/basedpyright output format: "X error(s), Y warning(s)"
                error_match = re.search(r"(\d+)\s+error", output, re.IGNORECASE)
                warning_match = re.search(r"(\d+)\s+warning", output, re.IGNORECASE)

                error_count = int(error_match.group(1)) if error_match else 0
                warning_count = int(warning_match.group(1)) if warning_match else 0

                # Check for specific error patterns (basedpyright/pyright format)
                # These patterns catch various error types that might not be counted in summary
                error_patterns = [
                    r"error:\s",  # Standard error format
                    r"reportArgumentType",  # Argument type errors
                    r"reportUnknownVariableType",  # Unknown variable type
                    r"reportUnknownMemberType",  # Unknown member type
                    r"reportAttributeAccessIssue",  # Attribute access issues
                    r"reportAssignmentType",  # Assignment type errors
                    r"reportIndexIssue",  # Index access issues
                    r"reportOperatorIssue",  # Operator issues
                    r"reportGeneralTypeIssues",  # General type issues
                    r"reportUnknownArgumentType",  # Unknown argument type
                ]

                has_error_pattern = any(
                    bool(re.search(pattern, output, re.IGNORECASE))
                    for pattern in error_patterns
                )

                # Check for warning patterns
                warning_patterns = [
                    r"warning:\s",
                ]
                has_warning_pattern = any(
                    bool(re.search(pattern, output, re.IGNORECASE))
                    for pattern in warning_patterns
                )

                if (
                    error_count > 0
                    or warning_count > 0
                    or has_error_pattern
                    or has_warning_pattern
                ):
                    has_errors = True

            except FileNotFoundError:
                print(
                    f"Error: Type checker command not found: {type_checker_cmd[0]}",
                    file=sys.stderr,
                )
                print(
                    "Install the type checker or ensure it's in your PATH or .venv/bin/",
                    file=sys.stderr,
                )
                sys.exit(1)
            except subprocess.TimeoutExpired:
                print(
                    f"Error: Type checker timed out for {dir_to_check}",
                    file=sys.stderr,
                )
                sys.exit(1)
            except Exception as e:
                print(f"Error running type checker: {e}", file=sys.stderr)
                sys.exit(1)

        # Fail if any errors or warnings found
        # Also check return code - non-zero typically indicates errors
        if result is not None and (
            result.returncode != 0 or has_errors or error_count > 0 or warning_count > 0
        ):
            all_errors = True

    # Print all output
    if all_output:
        print(all_output)
        if all_errors:
            print(all_output, file=sys.stderr)

    if all_errors:
        print(
            "\n❌ Type errors or warnings detected. Fix before committing.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("✅ All type checks passed")
    sys.exit(0)


if __name__ == "__main__":
    main()
