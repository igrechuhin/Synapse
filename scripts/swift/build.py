#!/usr/bin/env python3
"""Build the Swift package.

Runs `swift build` (or a sub-command) against the TradeWing SwiftPM project.

Configuration:
    SWIFT_COMMAND: Sub-command to pass to swift (default: build)
    BUILD_TIMEOUT: Timeout in seconds (default: 300)
    SWIFT_FLAGS: Extra flags forwarded to swift build (default: empty)
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

try:
    from _utils import get_config_int, get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
    from _utils import get_config_int, get_project_root


BUILD_TIMEOUT = get_config_int("BUILD_TIMEOUT", 300)
SWIFT_COMMAND = os.getenv("SWIFT_COMMAND", "build")
SWIFT_FLAGS = os.getenv("SWIFT_FLAGS", "")


def find_swift() -> str:
    """Return path to swift executable.

    Returns:
        Path to swift binary or 'swift' as fallback.
    """
    for candidate in ["/usr/bin/swift", "/usr/local/bin/swift"]:
        if Path(candidate).exists():
            return candidate
    return "swift"


def build_cmd(swift: str) -> list[str]:
    """Construct the swift invocation.

    Args:
        swift: Path to the swift binary.

    Returns:
        List of command parts.
    """
    cmd = [swift, SWIFT_COMMAND]
    if SWIFT_FLAGS:
        cmd.extend(SWIFT_FLAGS.split())
    return cmd


def main() -> None:
    """Run swift build."""
    project_root = get_project_root(Path(__file__))
    swift = find_swift()
    cmd = build_cmd(swift)

    print(f"Running: {' '.join(cmd)}")
    print(f"Working directory: {project_root}")

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=BUILD_TIMEOUT,
        )

        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        if result.returncode != 0:
            print("❌ Swift build failed.", file=sys.stderr)
            sys.exit(1)

        print("✅ Swift build succeeded")
        sys.exit(0)

    except subprocess.TimeoutExpired:
        print(f"❌ Build timed out after {BUILD_TIMEOUT}s.", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"❌ swift not found: {swift}", file=sys.stderr)
        print(
            "Install Xcode command-line tools: xcode-select --install", file=sys.stderr
        )
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running build: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
