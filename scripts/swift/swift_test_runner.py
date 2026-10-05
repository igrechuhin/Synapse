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
    PARALLEL:            Set to 0 to emit --no-parallel (default: 0), or 1 for --parallel.
                         Explicit --no-parallel disables independent Swift Testing test/case
                         parallelism; omitting --parallel does not. Internal test task groups
                         retain their concurrency. Parallel runs have provoked intermittent
                         MLX/SIGBUS failures in the full TradeWing matrix; use 1 only when stable.
    SWIFT_TEST_NUM_WORKERS: When >0, opts into --parallel --num-workers N even if PARALLEL=0.
                         This bounds XCTest subprocess workers, not Swift Testing tasks.
                         Swift Testing 6.2.4 has no global worker-count option. Default 0
                         leaves the selected PARALLEL policy unchanged.
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
# AI: 2026-10-02 fix (carried REV-2026-05-14-1): anchor every summary regex to a line
# start and use horizontal-only whitespace ([^\S\n]) so interleaved SwiftPM output cannot
# stitch fragments from separate lines into a phantom failed/passed summary match.
_H = r"[^\S\n]+"  # one-or-more horizontal whitespace; never crosses a newline
_XCTEST_SUMMARY_RE = re.compile(
    rf"^[^\S\n]*Executed{_H}(?P<total>\d+){_H}tests?,{_H}with{_H}"
    + rf"(?:(?P<skipped>\d+){_H}tests{_H}skipped{_H}and{_H})?"
    + rf"(?P<failed>\d+){_H}failures",
    re.IGNORECASE | re.MULTILINE,
)
# AI: Require the Swift Testing terminal rollup shape (`… passed after` / `… failed after`) so
# unrelated log lines that contain `suites` + `failed` as substrings cannot flip the parser.
# AI: Swift prints `N suite` (singular) when N==1 and `N suites` otherwise — require `suites?`.
# AI: The `✔`/`✘` rollup marker is optional so piped/non-TTY output without markers still matches.
# AI: 2026-10-02 (review P1): on macOS Swift Testing prefixes the rollup with a Supplementary
# Private Use Area glyph (observed U+10105B) followed by two spaces — the class also accepts
# the PUA ranges so real terminal rollups match; anything else still requires a line start.
_PUA_MARKER_CLASS = "[✔✘\U000F0000-\U0010FFFF]"
_SWIFT_TESTING_ROLLUP_PREFIX = (
    rf"^[^\S\n]*(?:{_PUA_MARKER_CLASS}[^\S\n]*)?Test{_H}run{_H}with{_H}"
    + rf"(?P<total>\d+){_H}tests{_H}in{_H}\d+{_H}suites?{_H}"
)
_SWIFT_TESTING_PASSED_RE = re.compile(
    _SWIFT_TESTING_ROLLUP_PREFIX + rf"passed{_H}after",
    re.IGNORECASE | re.MULTILINE,
)
_SWIFT_TESTING_FAILED_RE = re.compile(
    _SWIFT_TESTING_ROLLUP_PREFIX + rf"failed{_H}after",
    re.IGNORECASE | re.MULTILINE,
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
        # AI: Preserve the worker-count opt-in; SwiftPM requires --parallel for XCTest workers.
        # Swift Testing ignores --num-workers and remains parallel in this mode.
        cmd.extend(["--parallel", "--num-workers", str(SWIFT_TEST_NUM_WORKERS)])
    else:
        # AI: Swift Testing defaults to parallel execution when no policy flag is passed.
        cmd.append("--no-parallel")
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


def _coverage_binaries(project_root: Path, profdata: Path) -> list[Path]:
    """Locate coverage binaries, falling back to the profdata build directory."""
    build_debug = project_root / ".build" / "arm64-apple-macosx" / "debug"
    if not build_debug.exists():
        build_debug = project_root / ".build" / "debug"
    xctest_binaries = _find_xctest_binaries(build_debug)
    if not xctest_binaries:
        # Try searching from the profdata's parent codecov dir upward.
        xctest_binaries = _find_xctest_binaries(profdata.parent.parent)
    return xctest_binaries


def _coverage_source_files(project_root: Path) -> list[str]:
    """Collect configured Swift sources, excluding generated files."""
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
    return source_files


def _coverage_command(
    mode: str, binaries: list[Path], profdata: Path, source_files: list[str]
) -> list[str]:
    """Build report/export commands with the same objects and sources."""
    cmd = ["xcrun", "llvm-cov", mode, str(binaries[0]), f"--instr-profile={profdata}"]
    if mode == "export":
        cmd.append("--summary-only")
    cmd.append("--ignore-filename-regex=\\.build|Tests/|Plugins/|.*\\.pb\\.swift|.*\\.grpc\\.swift")
    for extra in binaries[1:]:
        cmd.extend(["-object", str(extra)])
    cmd.extend(source_files)
    return cmd


def _export_coverage(export_cmd: list[str], project_root: Path) -> float | None:
    """Read aggregate coverage from the llvm-cov JSON fallback."""
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
    return None


def _read_coverage_report(
    project_root: Path, binaries: list[Path], profdata: Path, source_files: list[str]
) -> float | None:
    """Parse the TOTAL report line, falling back to the summary-only JSON export."""
    report_cmd = _coverage_command("report", binaries, profdata, source_files)
    result = subprocess.run(
        report_cmd, capture_output=True, text=True, check=False, cwd=project_root
    )
    report_text = result.stdout + result.stderr
    m = _TOTAL_COVERAGE_RE.search(report_text)
    if m:
        return float(m.group("line_pct"))
    export_cmd = _coverage_command("export", binaries, profdata, source_files)
    coverage = _export_coverage(export_cmd, project_root)
    if coverage is not None:
        return coverage
    print(
        "⚠️  Could not parse coverage percentage from llvm-cov output.", file=sys.stderr
    )
    if report_text.strip():
        print(report_text[:1000], file=sys.stderr)
    return None


def _measure_coverage(project_root: Path) -> float | None:
    """Measure the most-recent profdata; return None when measurement is unavailable."""
    profdata_candidates = list((project_root / ".build").rglob("default.profdata"))
    if not profdata_candidates:
        print("⚠️  No profdata found after coverage run.", file=sys.stderr)
        return None
    profdata = max(profdata_candidates, key=lambda p: p.stat().st_mtime)
    xctest_binaries = _coverage_binaries(project_root, profdata)
    if not xctest_binaries:
        print("⚠️  No xctest binaries found for llvm-cov.", file=sys.stderr)
        return None
    source_files = _coverage_source_files(project_root)
    if not source_files:
        print("⚠️  No source files found for coverage measurement.", file=sys.stderr)
        return None
    return _read_coverage_report(project_root, xctest_binaries, profdata, source_files)


def _cleanup_stuck_swiftpm(project_root: Path) -> None:
    """Run optional SwiftPM cleanup without making cleanup errors fatal."""
    if KILL_STUCK:
        try:
            import kill_stuck_swiftpm

            _ = kill_stuck_swiftpm.kill_stuck_processes()
            kill_stuck_swiftpm.remove_build_lock(project_root)
        except Exception as exc:
            print(f"⚠️  SwiftPM cleanup failed (non-fatal): {exc}", file=sys.stderr)


def _run_swift_process(
    cmd: list[str], project_root: Path, env: dict[str, str]
) -> tuple[subprocess.CompletedProcess[bytes], str, str]:
    """Run one build/test phase and forward decoded output to its original streams."""
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
    return result, stdout, stderr


def _check_coverage(project_root: Path) -> None:
    """Require coverage measurement and the configured threshold when enabled."""
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


def _finish_success(
    project_root: Path, total_tests: int | None, failed_tests: int | None
) -> None:
    """Report successful tests, apply coverage gating, and exit successfully."""
    if total_tests is not None and failed_tests is not None:
        # AI: Avoid the token ``failed=`` here — Cortex's Swift Testing
        # failure regex is DOTALL and would match this line after the
        # real ``… passed after`` summary when stdout is concatenated.
        print(f"Test summary: total={total_tests}, failures={failed_tests}")
    print("✅ All tests passed")
    _check_coverage(project_root)
    sys.exit(0)


def _should_retry_tests(
    returncode: int, failed_tests: int | None, output: str, attempt: int, max_attempts: int
) -> bool:
    """Report retryable SwiftPM/driver signals while attempts remain."""
    transient_post_success = _transient_swiftpm_failure(returncode, failed_tests, output)
    transient_driver_crash = _transient_swift_driver_crash_without_test_failures(
        returncode, failed_tests, output
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
        return True
    return False


def _run_test_attempts(
    swift: str, project_root: Path, compile_cmd: list[str], cmd: list[str], env: dict[str, str]
) -> None:
    """Build and run tests, preserving the bounded transient-failure retry policy."""
    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        compile_result, _, _ = _run_swift_process(compile_cmd, project_root, env)
        if compile_result.returncode != 0:
            print("❌ swift build --build-tests failed.", file=sys.stderr)
            sys.exit(1)
        # AI: SwiftPM creates/updates *.xctest hosts during --build-tests; refresh colocated
        # mlx.metallib beside the test binary after tests change cwd mid-run.
        ensure_default_metallib(project_root, swift=swift)
        result, stdout, stderr = _run_swift_process(cmd, project_root, env)
        combined_output = "\n".join(part for part in [stdout, stderr] if part)
        total_tests, failed_tests = parse_swift_test_summary(combined_output)
        normalized_success = did_tests_pass(
            result.returncode, failed_tests, combined_output
        )
        if normalized_success:
            _finish_success(project_root, total_tests, failed_tests)
        if _should_retry_tests(
            result.returncode, failed_tests, combined_output, attempt, max_attempts
        ):
            continue
        print("❌ Tests failed.", file=sys.stderr)
        sys.exit(1)


def _run_isolated_tests(
    swift: str, project_root: Path, compile_cmd: list[str], cmd: list[str]
) -> None:
    """Keep isolation alive through attempts and preserve runner exception mapping."""
    try:
        with tempfile.TemporaryDirectory(prefix="tradewing-swift-test-") as root:
            test_isolation_root = Path(root)
            env = _swift_test_child_environment(test_isolation_root)
            _run_test_attempts(swift, project_root, compile_cmd, cmd, env)
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


def main() -> None:
    """Run swift test."""
    project_root = get_project_root(Path(__file__))
    ensure_developer_dir_for_swiftpm(project_root)
    _cleanup_stuck_swiftpm(project_root)
    swift = find_swift()
    ensure_default_metallib(project_root, swift=swift)
    compile_cmd = build_compile_tests_cmd(swift)
    cmd = build_test_cmd(swift)
    print(f"Running: {' '.join(compile_cmd)}")
    print(f"Then: {' '.join(cmd)}")
    print(f"Timeout: {TEST_TIMEOUT}s")
    _run_isolated_tests(swift, project_root, compile_cmd, cmd)


if __name__ == "__main__":
    main()
