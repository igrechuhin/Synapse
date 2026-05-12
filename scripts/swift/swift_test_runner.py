#!/usr/bin/env python3
"""Run the Swift test suite with timeout protection and zero-tolerance policy.

Executes a two-phase ``swift build --build-tests`` then ``swift test --skip-build``
invocation. The split avoids intermittent SIGBUS crashes observed when SwiftPM
starts an incremental compile mid-``swift test`` run (for example after Charts
logging) on Apple Silicon toolchains.

Configuration:
    TEST_TIMEOUT:  Timeout in seconds (default: 2700, matching CI quality workflow)
    TEST_FILTER:   Filter pattern forwarded to --filter (default: empty)
    TEST_TARGET:   Specific target name forwarded to --target (default: empty)
    PARALLEL:      Set to 0 to disable parallel test execution (default: 0).
                   Parallel runs have provoked intermittent MLX/SIGBUS failures
                   in the full TradeWing matrix; keep 1 only when stable.
    SWIFT_TEST_NUM_WORKERS: When >0, adds ``swift test --parallel --num-workers N`` (requires SwiftPM
                   ``--parallel``). Default ``0`` omits both flags for stable CLI/CI. For Cursor/VS Code,
                   set ``swift.additionalTestArguments`` to ``--parallel`` / ``--num-workers`` ``1`` in
                   ``.vscode/settings.json`` to reduce ``Test did not complete`` from worker oversubscription.
    SWIFT_TEST_ALLOW_METAL: Set to 1/true/yes to keep Metal-enabled MLX in the
                   child process. By default Metal is disabled (``MLX_DISABLE_METAL=1``)
                   so ``swift test`` is stable under subprocess output capture on
                   Apple Silicon (intermittent SIGBUS otherwise).
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from _utils import get_config_int, get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
    from _utils import get_config_int, get_project_root


TEST_TIMEOUT = get_config_int("TEST_TIMEOUT", 2700)
TEST_FILTER = os.getenv("TEST_FILTER", "")
TEST_TARGET = os.getenv("TEST_TARGET", "")
PARALLEL = get_config_int("PARALLEL", 0)
SWIFT_JOBS = get_config_int("SWIFT_JOBS", 1)
SWIFT_TEST_NUM_WORKERS = get_config_int("SWIFT_TEST_NUM_WORKERS", 0)
# Set KILL_STUCK=1 to kill lingering SwiftPM processes before running tests.
KILL_STUCK = get_config_int("KILL_STUCK", 0)
_XCTEST_SUMMARY_RE = re.compile(
    r"Executed\s+(?P<total>\d+)\s+tests?,\s+with\s+"
    + r"(?:(?P<skipped>\d+)\s+tests\s+skipped\s+and\s+)?"
    + r"(?P<failed>\d+)\s+failures",
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
    cmd = [swift, "test", "--skip-build"]
    if SWIFT_JOBS > 0:
        cmd.extend(["--jobs", str(SWIFT_JOBS)])
    if PARALLEL:
        cmd.append("--parallel")
        if SWIFT_TEST_NUM_WORKERS > 0:
            cmd.extend(["--num-workers", str(SWIFT_TEST_NUM_WORKERS)])
    elif SWIFT_TEST_NUM_WORKERS > 0:
        # AI: SwiftPM requires `--parallel` with `--num-workers`; one worker limits concurrent
        # Swift Testing tasks and avoids intermittent SIGBUS seen with Charts under load.
        cmd.extend(["--parallel", "--num-workers", str(SWIFT_TEST_NUM_WORKERS)])
    if TEST_TARGET:
        cmd.extend(["--target", TEST_TARGET])
    if TEST_FILTER:
        cmd.extend(["--filter", TEST_FILTER])
    return cmd


def build_compile_tests_cmd(swift: str) -> list[str]:
    """Construct ``swift build --build-tests`` with the same job parallelism as tests."""
    cmd = [swift, "build", "--build-tests"]
    if SWIFT_JOBS > 0:
        cmd.extend(["--jobs", str(SWIFT_JOBS)])
    return cmd


def parse_swift_test_summary(output: str) -> tuple[int | None, int | None]:
    """Parse total and failed test counts from `swift test` output.

    Args:
        output: Combined stdout/stderr from swift test execution.

    Returns:
        Tuple of (total_tests, failed_tests). If no summary is found, both values
        are None.
    """
    swift_testing = _SWIFT_TESTING_RUN_RE.search(output)
    swift_testing_total = (
        int(swift_testing.group("total")) if swift_testing is not None else None
    )
    # When Swift Testing emits its aggregate "… passed" line, treat it as canonical.
    # Full-matrix hybrid runs also stream XCTest per-suite summaries; taking the max
    # XCTest total can mis-attribute failures from unrelated log noise.
    if swift_testing is not None:
        return swift_testing_total, 0

    matches = list(_XCTEST_SUMMARY_RE.finditer(output))
    if matches:
        best = max(matches, key=lambda m: int(m.group("total")))
        xctest_total = int(best.group("total"))
        xctest_failed = int(best.group("failed"))

        return xctest_total, xctest_failed

    return None, None


def _transient_swiftpm_failure(
    returncode: int, failed_tests: int | None, output: str
) -> bool:
    """Detect SwiftPM post-test crashes after a successful Swift Testing summary.

    SwiftPM occasionally continues with an incremental build (for example,
    resource bundle work) after tests finish and the child exits with SIGBUS
    (negative return code on Unix) or ``unexpected signal`` in logs, even when
    the Swift Testing summary already reported success.
    """
    if failed_tests is not None and failed_tests > 0:
        return False
    if _SWIFT_TESTING_RUN_RE.search(output) is None:
        return False
    if returncode == 0:
        return False
    lowered = output.lower()
    if "unexpected signal" in lowered:
        return True
    # Negative exit status: child terminated by signal (e.g. SIGBUS == -10).
    return returncode < 0


def _transient_swift_driver_crash_without_test_failures(
    returncode: int, failed_tests: int | None, output: str
) -> bool:
    """Retry when the Swift driver dies mid-run without recording a Swift Testing failure."""
    if returncode == 0:
        return False
    if failed_tests is not None and failed_tests > 0:
        return False
    lowered = output.lower()
    if "unexpected signal" not in lowered:
        return False
    # If Swift Testing already recorded a failing test, do not treat as a hard crash retry.
    if "failed after" in lowered:
        return False
    return True


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


def _swift_test_child_environment(isolation_root: Path) -> dict[str, str]:
    """Build environment for the SwiftPM test subprocess.

    Returns:
        A copy of ``os.environ`` with MLX defaults adjusted for runner stability.
    """
    env = os.environ.copy()
    allow_metal = os.getenv("SWIFT_TEST_ALLOW_METAL", "1").strip().lower() in (
        "",
        "1",
        "true",
        "yes",
    )
    if not allow_metal:
        env["MLX_DISABLE_METAL"] = "1"

    # Isolate filesystem side effects for each test runner invocation.
    data_dir = isolation_root / "data"
    tmp_dir = isolation_root / "tmp"
    data_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    env["TRADEWING_DATA_DIR"] = str(data_dir)
    env["TMPDIR"] = str(tmp_dir)
    return env


def main() -> None:
    """Run swift test."""
    project_root = get_project_root(Path(__file__))

    if KILL_STUCK:
        try:
            import kill_stuck_swiftpm

            _ = kill_stuck_swiftpm.kill_stuck_processes()
            kill_stuck_swiftpm.remove_build_lock(project_root)
        except Exception as exc:
            print(f"⚠️  SwiftPM cleanup failed (non-fatal): {exc}", file=sys.stderr)

    swift = find_swift()
    compile_cmd = build_compile_tests_cmd(swift)
    cmd = build_test_cmd(swift)

    print(f"Running: {' '.join(compile_cmd)}")
    print(f"Then: {' '.join(cmd)}")
    print(f"Timeout: {TEST_TIMEOUT}s")

    max_attempts = 5

    try:
        with tempfile.TemporaryDirectory(prefix="tradewing-swift-test-") as root:
            test_isolation_root = Path(root)
            env = _swift_test_child_environment(test_isolation_root)

            for attempt in range(1, max_attempts + 1):
                compile_result = subprocess.run(
                    compile_cmd,
                    cwd=project_root,
                    capture_output=True,
                    text=False,
                    check=False,
                    timeout=TEST_TIMEOUT,
                    env=env,
                )
                compile_stdout = decode_process_output(compile_result.stdout)
                compile_stderr = decode_process_output(compile_result.stderr)
                if compile_stdout:
                    print(compile_stdout)
                if compile_stderr:
                    print(compile_stderr, file=sys.stderr)
                if compile_result.returncode != 0:
                    print("❌ swift build --build-tests failed.", file=sys.stderr)
                    sys.exit(1)

                result = subprocess.run(
                    cmd,
                    cwd=project_root,
                    capture_output=True,
                    text=False,
                    check=False,
                    timeout=TEST_TIMEOUT,
                    env=env,
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

                if normalized_success:
                    if total_tests is not None and failed_tests is not None:
                        print(
                            f"Test summary: total={total_tests}, failed={failed_tests}"
                        )
                    print("✅ All tests passed")
                    sys.exit(0)

                transient_post_success = _transient_swiftpm_failure(
                    result.returncode, failed_tests, combined_output
                )
                transient_driver_crash = _transient_swift_driver_crash_without_test_failures(
                    result.returncode, failed_tests, combined_output
                )
                if attempt < max_attempts and (transient_post_success or transient_driver_crash):
                    reason = (
                        "post-success SwiftPM signal"
                        if transient_post_success
                        else "Swift driver signal without recorded test failures"
                    )
                    print(
                        f"⚠️ Transient test runner failure ({reason}, attempt {attempt}/{max_attempts}); rebuilding and retrying...",
                        file=sys.stderr,
                    )
                    continue

                print("❌ Tests failed.", file=sys.stderr)
                sys.exit(1)

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
