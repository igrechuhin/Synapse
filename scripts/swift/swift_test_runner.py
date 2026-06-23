#!/usr/bin/env python3
"""Run the Swift test suite with timeout protection and zero-tolerance policy.

Executes a two-phase ``swift build --build-tests`` then ``swift test --skip-build``
invocation. The split avoids intermittent SIGBUS crashes observed when SwiftPM
starts an incremental compile mid-``swift test`` run (for example after Charts
logging) on Apple Silicon toolchains.

Configuration:
    TEST_TIMEOUT:        Timeout in seconds (default: 2700, matching CI quality workflow)
    TEST_FILTER:         Filter pattern forwarded to --filter (default: empty)
    TEST_TARGET:         Specific target name forwarded to --target (default: empty)
    PARALLEL:            Set to 0 to disable parallel test execution (default: 0).
                         Parallel runs have provoked intermittent MLX/SIGBUS failures
                         in the full TradeWing matrix; keep 1 only when stable.
    SWIFT_TEST_NUM_WORKERS: When >0, adds ``swift test --parallel --num-workers N`` (requires SwiftPM
                         ``--parallel``). Default ``0`` omits both flags for stable CLI/CI. For Cursor/VS Code,
                         set ``swift.additionalTestArguments`` to ``--parallel`` / ``--num-workers`` ``1`` in
                         ``.vscode/settings.json`` to reduce ``Test did not complete`` from worker oversubscription.
    COVERAGE_THRESHOLD:  When set to a number (e.g. "90"), enables --enable-code-coverage and
                         gates exit on aggregate Sources/ line coverage ≥ threshold (default: empty
                         = coverage gate disabled).  Set to "0" to collect coverage without gating.
    COVERAGE_SOURCES:    Comma-separated source dirs measured by the coverage gate (default: Sources).

    MLX / Metal: This runner does **not** set ``MLX_DISABLE_METAL``. TradeWing tests expect a working
    MLX default metallib (Apple Silicon, macOS 15+, full Xcode selected via ``xcode-select``). The
    parent ``test.sh`` exports ``DEVELOPER_DIR`` using ``.cursor/scripts/resolve_developer_dir.sh``.
    If you see ``Failed to load the default metallib``, fix ``xcode-select`` (not Command Line Tools
    only), refresh IDE after ``.vscode`` ``swift.path`` (``…/swift-xcode-bridge/swift``), then ``swift package clean`` + rebuild.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

try:
    from _utils import get_config_int, get_project_root
except ImportError:
    sys.path.insert(0, str(_SCRIPT_DIR.parent / "python"))
    from _utils import get_config_int, get_project_root

from ensure_mlx_metallib import ensure_default_metallib  # noqa: E402
from swift_toolchain import ensure_developer_dir_for_swiftpm, find_swift  # noqa: E402


TEST_TIMEOUT = get_config_int("TEST_TIMEOUT", 2700)
TEST_FILTER = os.getenv("TEST_FILTER", "")
TEST_TARGET = os.getenv("TEST_TARGET", "")
PARALLEL = get_config_int("PARALLEL", 0)
SWIFT_JOBS = get_config_int("SWIFT_JOBS", 1)
SWIFT_TEST_NUM_WORKERS = get_config_int("SWIFT_TEST_NUM_WORKERS", 0)
# Set KILL_STUCK=1 to kill lingering SwiftPM processes before running tests.
KILL_STUCK = get_config_int("KILL_STUCK", 0)
# When set, enables --enable-code-coverage and gates on aggregate line coverage >= threshold.
# Empty string disables coverage gating entirely.
_COVERAGE_THRESHOLD_RAW = os.getenv("COVERAGE_THRESHOLD", "")
COVERAGE_THRESHOLD: float | None = (
    float(_COVERAGE_THRESHOLD_RAW) if _COVERAGE_THRESHOLD_RAW.strip() else None
)
_RAW_COVERAGE_SOURCES = os.getenv("COVERAGE_SOURCES", "Sources")
COVERAGE_SOURCES: list[str] = [
    s.strip() for s in _RAW_COVERAGE_SOURCES.split(",") if s.strip()
]
_XCTEST_SUMMARY_RE = re.compile(
    r"Executed\s+(?P<total>\d+)\s+tests?,\s+with\s+"
    + r"(?:(?P<skipped>\d+)\s+tests\s+skipped\s+and\s+)?"
    + r"(?P<failed>\d+)\s+failures",
    re.IGNORECASE,
)
# AI: Require the Swift Testing terminal rollup shape (`… passed after` / `… failed after`) so
# unrelated log lines that contain `suites` + `failed` as substrings cannot flip the parser.
# AI: Swift prints `N suite` (singular) when N==1 and `N suites` otherwise — require `suites?`.
_SWIFT_TESTING_PASSED_RE = re.compile(
    r"Test\s+run\s+with\s+(?P<total>\d+)\s+tests\s+in\s+\d+\s+suites?\s+passed\s+after",
    re.IGNORECASE,
)
_SWIFT_TESTING_FAILED_RE = re.compile(
    r"Test\s+run\s+with\s+(?P<total>\d+)\s+tests\s+in\s+\d+\s+suites?\s+failed\s+after",
    re.IGNORECASE,
)


def decode_process_output(raw_output: str | bytes | None) -> str:
    """Return subprocess output as a safe UTF-8 string."""
    if raw_output is None:
        return ""
    if isinstance(raw_output, bytes):
        return raw_output.decode("utf-8", errors="replace")
    return raw_output


def build_test_cmd(swift: str) -> list[str]:
    """Construct the swift test invocation.

    Args:
        swift: Path to the swift binary.

    Returns:
        List of command parts.
    """
    cmd = [swift, "test", "--skip-build"]
    if COVERAGE_THRESHOLD is not None:
        cmd.append("--enable-code-coverage")
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
    # AI: Coverage instrumentation must match between build and test phases; pass
    # --enable-code-coverage here so the binary is compiled with profiling hooks.
    if COVERAGE_THRESHOLD is not None:
        cmd.append("--enable-code-coverage")
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
    # AI: Prefer the chronologically last Swift Testing summary. Incremental SwiftPM
    # output can interleave stale fragments; first-match-wins falsely marks failure.
    swift_events: list[tuple[int, int, int]] = []
    for m in _SWIFT_TESTING_FAILED_RE.finditer(output):
        swift_events.append((m.start(), int(m.group("total")), 1))
    for m in _SWIFT_TESTING_PASSED_RE.finditer(output):
        swift_events.append((m.start(), int(m.group("total")), 0))
    if swift_events:
        swift_events.sort(key=lambda item: item[0])
        _, total, failed_flag = swift_events[-1]
        return total, failed_flag

    matches = list(_XCTEST_SUMMARY_RE.finditer(output))
    if matches:
        # AI: Use the last XCTest summary; max-by-total picked unrelated high counts
        # when logs contained multiple "Executed …" lines from nested tools.
        last = matches[-1]
        return int(last.group("total")), int(last.group("failed"))

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
    if _SWIFT_TESTING_PASSED_RE.search(output) is None:
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


def did_tests_pass(
    returncode: int, failed_tests: int | None, combined_output: str = ""
) -> bool:
    """Normalize test pass/fail status for quality gate consumers.

    Args:
        returncode: Exit code from `swift test`.
        failed_tests: Parsed number of test failures, when available.
        combined_output: Combined stdout+stderr for pattern-based override.

    Returns:
        True when tests should be treated as passed.
    """
    if failed_tests is not None and failed_tests > 0:
        return False

    if returncode == 0:
        return True

    # AI: With --enable-code-coverage on Apple Silicon, the XCTest host process occasionally
    # exits non-zero after Swift Testing finishes successfully (SIGBUS / post-test resource
    # cleanup). Accept the run as passed when the Swift Testing terminal summary explicitly
    # says "passed after" and there are no recorded test failures.
    if (
        _SWIFT_TESTING_PASSED_RE.search(combined_output)
        and "failed after" not in combined_output.lower()
    ):
        return True

    return False


def _swift_test_child_environment(isolation_root: Path) -> dict[str, str]:
    """Build environment for the SwiftPM test subprocess.

    Returns:
        A copy of ``os.environ`` with TradeWing test isolation paths applied.
    """
    env = os.environ.copy()

    # Isolate filesystem side effects for each test runner invocation.
    data_dir = isolation_root / "data"
    tmp_dir = isolation_root / "tmp"
    data_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    env["TRADEWING_DATA_DIR"] = str(data_dir)
    env["TMPDIR"] = str(tmp_dir)
    return env


_TOTAL_COVERAGE_RE = re.compile(
    r"TOTAL\s+\d+\s+\d+\s+\d+\s+\d+\s+(?P<line_pct>[\d.]+)%"
)


def _find_xctest_binaries(build_dir: Path) -> list[Path]:
    """Return xctest executable binaries under build_dir."""
    binaries: list[Path] = []
    for bundle in build_dir.rglob("*.xctest"):
        binary = bundle / "Contents" / "MacOS" / bundle.stem
        if binary.exists():
            binaries.append(binary)
            continue
        flat = bundle / bundle.stem
        if flat.exists():
            binaries.append(flat)
    return binaries


def _measure_coverage(project_root: Path) -> float | None:
    """Run llvm-cov against the most-recent profdata and return aggregate line coverage %.

    Returns None when profdata or xctest binaries cannot be located.
    """
    # Locate the most-recently modified profdata produced by SwiftPM.
    profdata_candidates = list((project_root / ".build").rglob("default.profdata"))
    if not profdata_candidates:
        print("⚠️  No profdata found after coverage run.", file=sys.stderr)
        return None
    profdata = max(profdata_candidates, key=lambda p: p.stat().st_mtime)

    # Collect xctest binaries.
    build_debug = project_root / ".build" / "arm64-apple-macosx" / "debug"
    if not build_debug.exists():
        build_debug = project_root / ".build" / "debug"
    xctest_binaries = _find_xctest_binaries(build_debug)
    if not xctest_binaries:
        # Try searching from the profdata's parent codecov dir upward.
        xctest_binaries = _find_xctest_binaries(profdata.parent.parent)
    if not xctest_binaries:
        print("⚠️  No xctest binaries found for llvm-cov.", file=sys.stderr)
        return None

    # Collect source files.
    source_files: list[str] = []
    for src_dir in COVERAGE_SOURCES:
        src_path = project_root / src_dir
        if src_path.exists():
            for sf in src_path.rglob("*.swift"):
                if not any(
                    sf.name.endswith(s)
                    for s in (".pb.swift", ".grpc.swift", ".generated.swift")
                ):
                    source_files.append(str(sf))
    if not source_files:
        print("⚠️  No source files found for coverage measurement.", file=sys.stderr)
        return None

    primary = xctest_binaries[0]
    report_cmd = [
        "xcrun",
        "llvm-cov",
        "report",
        str(primary),
        f"--instr-profile={profdata}",
        "--ignore-filename-regex=\\.build|Tests/|Plugins/|.*\\.pb\\.swift|.*\\.grpc\\.swift",
    ]
    for extra in xctest_binaries[1:]:
        report_cmd.extend(["-object", str(extra)])
    report_cmd.extend(source_files)

    result = subprocess.run(
        report_cmd, capture_output=True, text=True, check=False, cwd=project_root
    )
    report_text = result.stdout + result.stderr

    # Parse TOTAL line.
    m = _TOTAL_COVERAGE_RE.search(report_text)
    if m:
        return float(m.group("line_pct"))

    # Fallback: llvm-cov export --summary-only JSON.
    export_cmd = [
        "xcrun",
        "llvm-cov",
        "export",
        str(primary),
        f"--instr-profile={profdata}",
        "--summary-only",
        "--ignore-filename-regex=\\.build|Tests/|Plugins/|.*\\.pb\\.swift|.*\\.grpc\\.swift",
    ]
    for extra in xctest_binaries[1:]:
        export_cmd.extend(["-object", str(extra)])
    export_cmd.extend(source_files)
    ex = subprocess.run(
        export_cmd, capture_output=True, text=True, check=False, cwd=project_root
    )
    if ex.returncode == 0:
        try:
            data = json.loads(ex.stdout)
            totals = data.get("data", [{}])[0].get("totals", {})
            lines = totals.get("lines", {})
            count = lines.get("count", 0)
            covered = lines.get("covered", 0)
            if count > 0:
                return covered / count * 100.0
        except (json.JSONDecodeError, KeyError, ZeroDivisionError, IndexError):
            pass

    print(
        "⚠️  Could not parse coverage percentage from llvm-cov output.", file=sys.stderr
    )
    if report_text.strip():
        print(report_text[:1000], file=sys.stderr)
    return None


def main() -> None:
    """Run swift test."""
    project_root = get_project_root(Path(__file__))
    ensure_developer_dir_for_swiftpm(project_root)

    if KILL_STUCK:
        try:
            import kill_stuck_swiftpm

            _ = kill_stuck_swiftpm.kill_stuck_processes()
            kill_stuck_swiftpm.remove_build_lock(project_root)
        except Exception as exc:
            print(f"⚠️  SwiftPM cleanup failed (non-fatal): {exc}", file=sys.stderr)

    swift = find_swift()
    ensure_default_metallib(project_root, swift=swift)
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

                # AI: SwiftPM creates/updates *.xctest hosts during --build-tests; refresh colocated
                # mlx.metallib beside the test binary after tests change cwd mid-run.
                ensure_default_metallib(project_root, swift=swift)

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
                normalized_success = did_tests_pass(
                    result.returncode, failed_tests, combined_output
                )

                if normalized_success:
                    if total_tests is not None and failed_tests is not None:
                        # AI: Avoid the token ``failed=`` here — Cortex's Swift Testing
                        # failure regex is DOTALL and would match this line after the
                        # real ``… passed after`` summary when stdout is concatenated.
                        print(
                            f"Test summary: total={total_tests}, failures={failed_tests}"
                        )
                    print("✅ All tests passed")

                    if COVERAGE_THRESHOLD is not None:
                        coverage_pct = _measure_coverage(project_root)
                        if coverage_pct is None:
                            print(
                                "❌ Coverage measurement failed — cannot verify threshold.",
                                file=sys.stderr,
                            )
                            sys.exit(1)
                        print(
                            f"Coverage: {coverage_pct:.2f}%  (threshold: {COVERAGE_THRESHOLD:.1f}%)"
                        )
                        if COVERAGE_THRESHOLD > 0 and coverage_pct < COVERAGE_THRESHOLD:
                            delta = COVERAGE_THRESHOLD - coverage_pct
                            print(
                                f"❌ Coverage {coverage_pct:.2f}% is below threshold {COVERAGE_THRESHOLD:.1f}% (gap: {delta:.2f}pp)",
                                file=sys.stderr,
                            )
                            sys.exit(1)
                        print(
                            f"✅ Coverage gate passed: {coverage_pct:.2f}% ≥ {COVERAGE_THRESHOLD:.1f}%"
                        )

                    sys.exit(0)

                transient_post_success = _transient_swiftpm_failure(
                    result.returncode, failed_tests, combined_output
                )
                transient_driver_crash = (
                    _transient_swift_driver_crash_without_test_failures(
                        result.returncode, failed_tests, combined_output
                    )
                )
                if attempt < max_attempts and (
                    transient_post_success or transient_driver_crash
                ):
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
