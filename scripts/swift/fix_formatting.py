#!/usr/bin/env python3
"""Apply SwiftFormat to all Swift source files.

Runs swiftformat and modifies files in-place. This is the auto-fix companion
to check_formatting.py.

Configuration:
    SWIFTFORMAT_TARGET: Directory or file to format (default: project root)
    SWIFTFORMAT_CONFIG: Path to .swiftformat config file (default: auto-detect)
    FORMAT_TIMEOUT:     Timeout in seconds (default: 120)
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

try:
    from _utils import get_config_int, get_config_path, get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
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


def build_format_cmd(swiftformat: str, target: str, project_root: Path) -> list[str]:
    """Construct the swiftformat invocation.

    Args:
        swiftformat: Path to the swiftformat binary.
        target: Directory or file to format.
        project_root: Path to project root.

    Returns:
        List of command parts.
    """
    cmd = [swiftformat, target]
    config_path = get_config_path("SWIFTFORMAT_CONFIG")
    if config_path is not None:
        resolved = config_path if config_path.is_absolute() else project_root / config_path
        if resolved.exists():
            cmd.extend(["--config", str(resolved)])
    return cmd


def main() -> None:
    """Run swiftformat to fix all files."""
    project_root = get_project_root(Path(__file__))

    swiftformat = find_swiftformat()
    if swiftformat is None:
        print("❌ swiftformat not found.", file=sys.stderr)
        print("Install via: brew install swiftformat", file=sys.stderr)
        sys.exit(1)

    target_env = os.getenv("SWIFTFORMAT_TARGET", "")
    target = target_env if target_env else "."
    cmd = build_format_cmd(swiftformat, target, project_root)

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
            print("❌ swiftformat encountered errors.", file=sys.stderr)
            sys.exit(1)

        print("✅ SwiftFormat complete")
        sys.exit(0)

    except subprocess.TimeoutExpired:
        print(f"❌ swiftformat timed out after {FORMAT_TIMEOUT}s.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running swiftformat: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
