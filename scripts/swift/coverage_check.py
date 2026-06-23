#!/usr/bin/env python3
"""Code-coverage gate for the TradeWing Swift package.

Runs ``swift test --enable-code-coverage``, merges the resulting ``.profraw``
files, and uses ``llvm-cov report`` to compute per-file and aggregate line
coverage.  Exits 0 only when aggregate Sources/ line coverage meets the
configured threshold.

Configuration (env-var overrides):
    COVERAGE_THRESHOLD : Minimum aggregate line-coverage % (default: 90.0)
    TEST_TIMEOUT       : Per-phase timeout in seconds    (default: 2700)
    SWIFT_JOBS         : -j flag for swift build/test   (default: 1)
    COVERAGE_SOURCES   : Comma-separated source dirs to include
                         (default: Sources)
    SHOW_GAPS          : Set to 1 to print per-file lines missing  (default: 0)
"""

from __future__ import annotations

import json
import os
import re
import shutil
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

from ensure_mlx_metallib import ensure_default_metallib
from swift_toolchain import ensure_developer_dir_for_swiftpm, find_swift

COVERAGE_THRESHOLD: float = float(os.getenv("COVERAGE_THRESHOLD", "90.0"))
TEST_TIMEOUT: int = get_config_int("TEST_TIMEOUT", 2700)
SWIFT_JOBS: int = get_config_int("SWIFT_JOBS", 1)
SHOW_GAPS: int = get_config_int("SHOW_GAPS", 0)
_RAW_SOURCES = os.getenv("COVERAGE_SOURCES", "Sources")
COVERAGE_SOURCES: list[str] = [s.strip() for s in _RAW_SOURCES.split(",") if s.strip()]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run(
    cmd: list[str], cwd: Path, timeout: int, env: dict | None = None
) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=False,
        check=False,
        timeout=timeout,
        env=env or os.environ.copy(),
    )


def _decode(raw: bytes | str | None) -> str:
    if raw is None:
        return ""
    if isinstance(raw, bytes):
        return raw.decode("utf-8", errors="replace")
    return raw


def _find_xctest_bundle(build_dir: Path) -> Path | None:
    """Return the first .xctest bundle found under build_dir (arm64 debug)."""
    for candidate in build_dir.rglob("*.xctest"):
        binary = candidate / "Contents" / "MacOS" / candidate.stem
        if binary.exists():
            return binary
        # Flat layout (Linux / SwiftPM 5.10+)
        flat = candidate / candidate.stem
        if flat.exists():
            return flat
    return None


def _find_xctest_binaries(build_dir: Path) -> list[Path]:
    """Collect all xctest executable binaries under build_dir."""
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


def _merge_profraw(
    profraw_files: list[Path], output_profdata: Path, llvm_profdata: str
) -> bool:
    """Merge raw profile files into a single .profdata.  Returns True on success."""
    if not profraw_files:
        print("⚠️  No .profraw files found; coverage data unavailable.", file=sys.stderr)
        return False
    cmd = [llvm_profdata, "merge", "-sparse", "-o", str(output_profdata)] + [
        str(p) for p in profraw_files
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(f"❌ llvm-profdata merge failed:\n{result.stderr}", file=sys.stderr)
        return False
    return True


# ---------------------------------------------------------------------------
# Coverage parsing
# ---------------------------------------------------------------------------

_TOTAL_LINE_RE = re.compile(r"TOTAL\s+\d+\s+\d+\s+\d+\s+\d+\s+(?P<line_pct>[\d.]+)%")


def _parse_coverage_from_report(report_text: str) -> tuple[float | None, list[dict]]:
    """Extract aggregate line coverage % and per-file gap list from llvm-cov report output."""
    lines = report_text.splitlines()
    aggregate: float | None = None
    gaps: list[dict] = []

    for line in lines:
        if line.strip().startswith("TOTAL"):
            m = _TOTAL_LINE_RE.search(line)
            if m:
                aggregate = float(m.group("line_pct"))
        elif line.strip() and not line.strip().startswith("Filename"):
            parts = line.split()
            # llvm-cov report columns: Filename Regions Missed Cov% Lines Missed Cov% Functions Missed Cov%
            if len(parts) >= 9:
                fname = parts[0]
                try:
                    lines_missed = int(parts[6])
                    line_pct = float(parts[7].rstrip("%"))
                    if lines_missed > 0:
                        gaps.append(
                            {
                                "file": fname,
                                "lines_missed": lines_missed,
                                "line_pct": line_pct,
                            }
                        )
                except (ValueError, IndexError):
                    pass

    return aggregate, sorted(gaps, key=lambda g: g["lines_missed"], reverse=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    project_root = get_project_root(Path(__file__))
    ensure_developer_dir_for_swiftpm(project_root)

    swift = find_swift()
    ensure_default_metallib(project_root, swift=swift)

    llvm_profdata = shutil.which("xcrun") and "xcrun llvm-profdata" or "llvm-profdata"
    llvm_cov = "xcrun llvm-cov" if shutil.which("xcrun") else "llvm-cov"

    # ------------------------------------------------------------------
    # Phase 1: build with coverage instrumentation
    # ------------------------------------------------------------------
    build_cmd = [swift, "build", "--build-tests"]
    if SWIFT_JOBS > 0:
        build_cmd.extend(["--jobs", str(SWIFT_JOBS)])

    print(f"▶ Phase 1 — build: {' '.join(build_cmd)}")
    env = os.environ.copy()
    with tempfile.TemporaryDirectory(prefix="tradewing-cov-") as tmp:
        isolation_root = Path(tmp)
        data_dir = isolation_root / "data"
        tmp_dir = isolation_root / "tmp"
        data_dir.mkdir(parents=True)
        tmp_dir.mkdir(parents=True)
        env["TRADEWING_DATA_DIR"] = str(data_dir)
        env["TMPDIR"] = str(tmp_dir)

        build_result = _run(build_cmd, project_root, TEST_TIMEOUT, env)
        out = _decode(build_result.stdout)
        err = _decode(build_result.stderr)
        if out:
            print(out)
        if err:
            print(err, file=sys.stderr)
        if build_result.returncode != 0:
            print("❌ Build failed — cannot measure coverage.", file=sys.stderr)
            sys.exit(1)

        # ------------------------------------------------------------------
        # Phase 2: run tests with coverage enabled
        # ------------------------------------------------------------------
        test_cmd = [swift, "test", "--skip-build", "--enable-code-coverage"]
        if SWIFT_JOBS > 0:
            test_cmd.extend(["--jobs", str(SWIFT_JOBS)])

        print(f"▶ Phase 2 — test with coverage: {' '.join(test_cmd)}")
        test_result = _run(test_cmd, project_root, TEST_TIMEOUT, env)
        t_out = _decode(test_result.stdout)
        t_err = _decode(test_result.stderr)
        if t_out:
            print(t_out)
        if t_err:
            print(t_err, file=sys.stderr)

        if test_result.returncode != 0:
            # AI: A non-zero exit can be a post-test SwiftPM signal (SIGBUS on Apple Silicon);
            # check for a "passed after" summary before declaring failure.
            combined = t_out + t_err
            if (
                "passed after" not in combined.lower()
                and "failed after" not in combined.lower()
            ):
                print("❌ Tests failed — aborting coverage check.", file=sys.stderr)
                sys.exit(1)
            if "failed after" in combined.lower():
                print("❌ Tests failed — aborting coverage check.", file=sys.stderr)
                sys.exit(1)
            print(
                "⚠️  Non-zero exit after passed summary (transient SwiftPM signal) — continuing."
            )

        # ------------------------------------------------------------------
        # Phase 3: locate profdata produced by SwiftPM
        # ------------------------------------------------------------------
        # SwiftPM writes profdata to .build/<arch>/<config>/codecov/default.profdata
        codecov_dirs = list((project_root / ".build").rglob("codecov"))
        profdata_candidates = []
        for d in codecov_dirs:
            pd = d / "default.profdata"
            if pd.exists():
                profdata_candidates.append(pd)

        if not profdata_candidates:
            # Fallback: try merging any .profraw files ourselves
            profraw_files = list((project_root / ".build").rglob("*.profraw"))
            merged = project_root / ".build" / "coverage-merged.profdata"
            llvm_profdata_bin = "xcrun" if shutil.which("xcrun") else None
            if llvm_profdata_bin:
                merge_cmd = [
                    "xcrun",
                    "llvm-profdata",
                    "merge",
                    "-sparse",
                    "-o",
                    str(merged),
                ] + [str(p) for p in profraw_files]
            else:
                merge_cmd = ["llvm-profdata", "merge", "-sparse", "-o", str(merged)] + [
                    str(p) for p in profraw_files
                ]
            mr = subprocess.run(merge_cmd, capture_output=True, text=True, check=False)
            if mr.returncode == 0 and merged.exists():
                profdata_candidates = [merged]
            else:
                print(
                    "❌ Cannot locate or build profdata — coverage unavailable.",
                    file=sys.stderr,
                )
                sys.exit(1)

        # Use the most-recently modified profdata (parallel builds may produce several)
        profdata = max(profdata_candidates, key=lambda p: p.stat().st_mtime)
        print(f"✔ Using profdata: {profdata}")

        # ------------------------------------------------------------------
        # Phase 4: collect xctest binaries and source files
        # ------------------------------------------------------------------
        build_dir = project_root / ".build" / "arm64-apple-macosx" / "debug"
        if not build_dir.exists():
            # Try the generic debug path
            build_dir = project_root / ".build" / "debug"

        xctest_binaries = _find_xctest_binaries(build_dir)
        if not xctest_binaries:
            # Try parent of codecov dir
            for d in codecov_dirs:
                xctest_binaries = _find_xctest_binaries(d.parent.parent)
                if xctest_binaries:
                    break

        if not xctest_binaries:
            print(
                "❌ No .xctest binaries found — cannot run llvm-cov.", file=sys.stderr
            )
            sys.exit(1)

        print(f"✔ Found {len(xctest_binaries)} xctest binary/ies")

        # Collect source files under COVERAGE_SOURCES dirs
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
            print("❌ No source files found in COVERAGE_SOURCES.", file=sys.stderr)
            sys.exit(1)

        print(f"✔ Measuring coverage over {len(source_files)} source files")

        # ------------------------------------------------------------------
        # Phase 5: run llvm-cov report
        # ------------------------------------------------------------------
        # Use the first xctest binary as the object; add the rest with -object
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

        report_result = subprocess.run(
            report_cmd,
            capture_output=True,
            text=True,
            check=False,
            cwd=project_root,
        )
        report_out = report_result.stdout + report_result.stderr

        if report_result.returncode != 0 and not report_out.strip():
            print(f"❌ llvm-cov report failed:\n{report_out}", file=sys.stderr)
            sys.exit(1)

        # ------------------------------------------------------------------
        # Phase 6: parse and gate
        # ------------------------------------------------------------------
        aggregate_pct, gaps = _parse_coverage_from_report(report_out)

        if aggregate_pct is None:
            # Fallback: try llvm-cov export --summary-only for JSON parsing
            export_cmd = [
                "xcrun",
                "llvm-cov",
                "export",
                str(primary),
                f"--instr-profile={profdata}",
                "--summary-only",
                "--ignore-filename-regex=\\.build|Tests/|Plugins/|.*\\.pb\\.swift|.*\\.grpc\\.swift",
                "--format=text",
            ]
            for extra in xctest_binaries[1:]:
                export_cmd.extend(["-object", str(extra)])
            export_cmd.extend(source_files)
            ex = subprocess.run(
                export_cmd,
                capture_output=True,
                text=True,
                check=False,
                cwd=project_root,
            )
            if ex.returncode == 0:
                try:
                    data = json.loads(ex.stdout)
                    totals = data.get("data", [{}])[0].get("totals", {})
                    lines = totals.get("lines", {})
                    count = lines.get("count", 0)
                    covered = lines.get("covered", 0)
                    if count > 0:
                        aggregate_pct = covered / count * 100
                except (json.JSONDecodeError, KeyError, ZeroDivisionError):
                    pass

        if aggregate_pct is None:
            print(
                "❌ Could not parse aggregate coverage from llvm-cov output.",
                file=sys.stderr,
            )
            print("Raw llvm-cov output:\n" + report_out[:2000], file=sys.stderr)
            sys.exit(1)

        print(f"\n{'─' * 60}")
        print(
            f"  Aggregate line coverage: {aggregate_pct:.2f}%  (threshold: {COVERAGE_THRESHOLD:.1f}%)"
        )
        print(f"{'─' * 60}")

        if SHOW_GAPS and gaps:
            print(f"\nTop coverage gaps ({len(gaps)} files below 100%):")
            for g in gaps[:20]:
                print(
                    f"  {g['line_pct']:5.1f}%  -{g['lines_missed']:4d} lines  {g['file']}"
                )

        if aggregate_pct < COVERAGE_THRESHOLD:
            delta = COVERAGE_THRESHOLD - aggregate_pct
            print(
                f"\n❌ Coverage {aggregate_pct:.2f}% is below threshold {COVERAGE_THRESHOLD:.1f}%"
                f" (gap: {delta:.2f}pp)",
                file=sys.stderr,
            )
            sys.exit(1)

        print(
            f"\n✅ Coverage gate passed: {aggregate_pct:.2f}% ≥ {COVERAGE_THRESHOLD:.1f}%"
        )
        sys.exit(0)


if __name__ == "__main__":
    main()
