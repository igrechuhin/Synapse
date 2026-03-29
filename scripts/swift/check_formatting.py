#!/usr/bin/env python3
"""Pre-commit hook to verify SwiftFormat compliance (lint mode, no changes).

Runs swiftformat in --lint mode. Exits with code 1 if any file would be
reformatted, blocking commits and CI.

Configuration:
    SWIFTFORMAT_CONFIG: Path to .swiftformat config file (default: auto-detect)
    FORMAT_TIMEOUT:     Timeout in seconds (default: 120)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

try:
    from _utils import get_config_int, get_config_path, get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
    from _utils import get_config_int, get_config_path, get_project_root


FORMAT_TIMEOUT = get_config_int("FORMAT_TIMEOUT", 120)


def find_swiftformat() -> str | None:
    """Find swiftformat binary.

    Returns:
        Path to swiftformat, or None if not found.
    """
    for candidate in [
        "/usr/local/bin/swiftformat",
        "/opt/homebrew/bin/swiftformat",
    ]:
        if Path(candidate).exists():
            return candidate
    try:
        result = subprocess.run(
            ["which", "swiftformat"],
            capture_output=True,
            text=True,
            check=True,
        )
        path = result.stdout.strip()
        if path:
            return path
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return None


def build_lint_cmd(swiftformat: str, project_root: Path) -> list[str]:
    """Construct the swiftformat lint invocation.

    Args:
        swiftformat: Path to the swiftformat binary.
        project_root: Path to project root.

    Returns:
        List of command parts.
    """
    cmd = [swiftformat, ".", "--lint"]
    config_path = get_config_path("SWIFTFORMAT_CONFIG")
    if config_path is not None:
        resolved = (
            config_path if config_path.is_absolute() else project_root / config_path
        )
        if resolved.exists():
            cmd.extend(["--config", str(resolved)])
    return cmd


def main() -> None:
    """Lint Swift files with swiftformat."""
    project_root = get_project_root(Path(__file__))

    swiftformat = find_swiftformat()
    if swiftformat is None:
        print("❌ swiftformat not found.", file=sys.stderr)
        print("Install via: brew install swiftformat", file=sys.stderr)
        sys.exit(1)

    cmd = build_lint_cmd(swiftformat, project_root)

    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=FORMAT_TIMEOUT,
        )

        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        if result.returncode != 0:
            print("\n❌ Formatting violations detected.", file=sys.stderr)
            print("Run 'swiftformat .' to fix.", file=sys.stderr)
            sys.exit(1)

        print("✅ All Swift files correctly formatted")
        sys.exit(0)

    except subprocess.TimeoutExpired:
        print(f"❌ swiftformat timed out after {FORMAT_TIMEOUT}s.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running swiftformat: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
