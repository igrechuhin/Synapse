#!/usr/bin/env python3
"""Run the PHP test suite.

Probes for Pest first, then PHPUnit. When neither is installed the gate skips
with exit 0.

Coverage is opt-in. Passing a coverage flag without Xdebug or PCOV installed
makes both runners exit non-zero, which would turn a passing suite into a red
gate. Set PHP_COVERAGE=1 to enable it.

Configuration:
    PHP_TEST_RUNNER:  Test runner binary (default: probe pest, phpunit)
    PHP_COVERAGE:     Set to 1 to enable coverage reporting (default: off)
    PHP_TEST_TIMEOUT: Timeout in seconds (default: 600)
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

try:
    from _utils import get_config_int
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
    from _utils import get_config_int

from _php_toolchain import find_php_tool, php_project_root, skip


RUNNER_CANDIDATES = ["pest", "phpunit"]
PHP_TEST_TIMEOUT = get_config_int("PHP_TEST_TIMEOUT", 600)


def build_test_cmd(tool: str, coverage: bool) -> list[str]:
    """Construct the test runner invocation.

    Args:
        tool: Path to the test runner binary.
        coverage: True to request a coverage report.

    Returns:
        List of command parts.
    """
    cmd = [tool]
    if not coverage:
        return cmd

    name = Path(tool).name
    cmd.append("--coverage" if name == "pest" else "--coverage-text")
    return cmd


def main() -> None:
    project_root = php_project_root(Path(__file__))

    tool = find_php_tool(
        RUNNER_CANDIDATES, project_root, env_override="PHP_TEST_RUNNER"
    )
    if tool is None or not Path(tool).exists():
        skip(
            "No PHP test runner installed, skipping "
            "(composer require --dev pestphp/pest)"
        )

    coverage = os.environ.get("PHP_COVERAGE") == "1"
    cmd = build_test_cmd(tool, coverage)

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=PHP_TEST_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        print(f"❌ Test suite timed out after {PHP_TEST_TIMEOUT}s", file=sys.stderr)
        sys.exit(1)
    except OSError as exc:
        print(f"❌ Error running tests: {exc}", file=sys.stderr)
        sys.exit(1)

    if result.stdout:
        print(result.stdout)

    if result.returncode != 0:
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        print("\n❌ Test suite failed.", file=sys.stderr)
        sys.exit(1)

    print("✅ All tests passed")
    sys.exit(0)


if __name__ == "__main__":
    main()
