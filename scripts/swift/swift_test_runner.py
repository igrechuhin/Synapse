#!/usr/bin/env python3
"""Run the Swift test suite with timeout protection and zero-tolerance policy.

Executes `swift test` for the TradeWing project. Any test failure exits
with code 1, blocking commits and CI.

Configuration:
    TEST_TIMEOUT:  Timeout in seconds (default: 600)
    TEST_FILTER:   Filter pattern forwarded to --filter (default: empty)
    TEST_TARGET:   Specific target name forwarded to --target (default: empty)
    PARALLEL:      Set to 0 to disable parallel test execution (default: 0).
                   Parallel runs have provoked intermittent MLX/SIGBUS failures
                   in the full TradeWing matrix; keep 1 only when stable.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

try:
    from _utils import get_config_int, get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
    from _utils import get_config_int, get_project_root


TEST_TIMEOUT = get_config_int("TEST_TIMEOUT", 600)
TEST_FILTER = os.getenv("TEST_FILTER", "")
TEST_TARGET = os.getenv("TEST_TARGET", "")
PARALLEL = get_config_int("PARALLEL", 0)
_XCTEST_SUMMARY_RE = re.compile(
    r"Executed\s+(?P<total>\d+)\s+tests?,\s+with\s+"
    r"(?:(?P<skipped>\d+)\s+tests\s+skipped\s+and\s+)?"
    r"(?P<failed>\d+)\s+failures",
    re.IGNORECASE,
)
_SWIFT_TESTING_RUN_RE = re.compile(
    r"Test\s+run\s+with\s+(?P<total>\d+)\s+tests\s+in\s+\d+\s+suites\s+passed",
    re.IGNORECASE,
)


def decode_process_output(raw_output: str | bytes | None) -> str:
    """Return subprocess output as a safe UTF-8 string."""
    if raw_output is None:
        return ""
    if isinstance(raw_output, bytes):
        return raw_output.decode("utf-8", errors="replace")
    return raw_output


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


def parse_swift_test_summary(output: str) -> tuple[int | None, int | None]:
    """Parse total and failed test counts from `swift test` output.

    Args:
        output: Combined stdout/stderr from swift test execution.

    Returns:
        Tuple of (total_tests, failed_tests). If no summary is found, both values
        are None.
    """
    matches = list(_XCTEST_SUMMARY_RE.finditer(output))
    if matches:
        best = max(matches, key=lambda m: int(m.group("total")))
        return int(best.group("total")), int(best.group("failed"))

    swift_testing = _SWIFT_TESTING_RUN_RE.search(output)
    if swift_testing is not None:
        return int(swift_testing.group("total")), 0

    return None, None


def did_tests_pass(returncode: int, failed_tests: int | None) -> bool:
    """Normalize test pass/fail status for quality gate consumers.

    Args:
        returncode: Exit code from `swift test`.
        failed_tests: Parsed number of test failures, when available.

    Returns:
        True when tests should be treated as passed.
    """
    # A non-zero exit code indicates a command/runtime-level error even if the
    # parsed test summary reports zero failures.
    if returncode != 0:
        return False

    if failed_tests is None:
        return True
    return failed_tests == 0


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
            text=False,
            check=False,
            timeout=TEST_TIMEOUT,
        )

        stdout = decode_process_output(result.stdout)
        stderr = decode_process_output(result.stderr)

        if stdout:
            print(stdout)
        if stderr:
            print(stderr, file=sys.stderr)

        combined_output = "\n".join(part for part in [stdout, stderr] if part)
        total_tests, failed_tests = parse_swift_test_summary(combined_output)
        normalized_success = did_tests_pass(result.returncode, failed_tests)

        if not normalized_success:
            print("❌ Tests failed.", file=sys.stderr)
            sys.exit(1)

        if total_tests is not None and failed_tests is not None:
            print(f"Test summary: total={total_tests}, failed={failed_tests}")
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
