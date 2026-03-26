#!/usr/bin/env python3
"""Run the Swift test suite with timeout protection and zero-tolerance policy.

Executes `swift test` for the TradeWing project. Any test failure exits
with code 1, blocking commits and CI.

Configuration:
    TEST_TIMEOUT:  Timeout in seconds (default: 600)
    TEST_FILTER:   Filter pattern forwarded to --filter (default: empty)
    TEST_TARGET:   Specific target name forwarded to --target (default: empty)
    PARALLEL:      Set to 0 to disable parallel test execution (default: 1)
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

try:
    from _utils import get_config_int, get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from _utils import get_config_int, get_project_root


TEST_TIMEOUT = get_config_int("TEST_TIMEOUT", 600)
TEST_FILTER = os.getenv("TEST_FILTER", "")
TEST_TARGET = os.getenv("TEST_TARGET", "")
PARALLEL = get_config_int("PARALLEL", 1)


def find_swift() -> str:
    """Return path to swift executable.

    Returns:
        Path to swift binary or 'swift' as fallback.
    """
    for candidate in ["/usr/bin/swift", "/usr/local/bin/swift"]:
        if Path(candidate).exists():
            return candidate
    return "swift"


def build_test_cmd(swift: str) -> list[str]:
    """Construct the swift test invocation.

    Args:
        swift: Path to the swift binary.

    Returns:
        List of command parts.
    """
    cmd = [swift, "test"]
    if PARALLEL:
        cmd.append("--parallel")
    if TEST_TARGET:
        cmd.extend(["--target", TEST_TARGET])
    if TEST_FILTER:
        cmd.extend(["--filter", TEST_FILTER])
    return cmd


def main() -> None:
    """Run swift test."""
    project_root = get_project_root(Path(__file__))
    swift = find_swift()
    cmd = build_test_cmd(swift)

    print(f"Running: {' '.join(cmd)}")
    print(f"Timeout: {TEST_TIMEOUT}s")

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=TEST_TIMEOUT,
        )

        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        if result.returncode != 0:
            print("❌ Tests failed.", file=sys.stderr)
            sys.exit(1)

        print("✅ All tests passed")
        sys.exit(0)

    except subprocess.TimeoutExpired:
        print(f"❌ Tests timed out after {TEST_TIMEOUT}s.", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"❌ swift not found: {swift}", file=sys.stderr)
        print(
            "Install Xcode command-line tools: xcode-select --install", file=sys.stderr
        )
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running tests: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
