#!/usr/bin/env python3
"""Run evaluation suite (fast or full) and exit with 0/1 based on pass rate threshold.

Used by CI to run eval-full and block merge if score drops below threshold (e.g. 85%).

A/B baseline comparison (Layered Evaluation Step 4): When tool descriptions change,
run with --compare-baseline to detect regressions against a stored baseline.
Use --save-baseline after a known-good run to update the baseline.

Usage:
    uv run python .cortex/synapse/scripts/python/run_eval_check.py --mode full --threshold 0.85
    uv run python .cortex/synapse/scripts/python/run_eval_check.py --save-baseline
    uv run python .cortex/synapse/scripts/python/run_eval_check.py --compare-baseline
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import cast

_IntConvertible = int | float | str

# Regression tolerance when comparing to baseline (5% allowed drop)
_BASELINE_REGRESSION_TOLERANCE = 0.05

try:
    from _utils import get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _utils import get_project_root

# Ensure project src is on path for cortex imports
_PROJECT_ROOT = get_project_root(Path(__file__))
if str(_PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "src"))


def _get_baseline_path(project_root: Path) -> Path:
    """Path to baseline execution summary for A/B comparison (committable)."""
    from cortex.core.path_resolver import CortexResourceType, get_cortex_path

    evals_dir = get_cortex_path(project_root, CortexResourceType.CORTEX_DIR) / "evals"
    return evals_dir / "baseline_execution.json"


async def _run_eval(mode: str, project_root: Path) -> str:
    """Run tool evaluation and return JSON payload string."""
    from cortex.tools.phase5_evaluation import run_tool_evaluation

    return await run_tool_evaluation(
        task_ids=None,
        mode=mode,
        category=None,
        ctx=None,
    )


def _extract_pass_rate(exec_summary: dict[str, object]) -> tuple[int, int, float]:
    """Extract passed, total, rate from execution_summary."""
    passed = int(cast(_IntConvertible, exec_summary.get("execution_passed", 0)))
    total = int(cast(_IntConvertible, exec_summary.get("execution_total_run", 0)))
    rate = (passed / total) if total else 1.0
    return passed, total, rate


def _save_baseline(project_root: Path, exec_summary: dict[str, object]) -> None:
    """Save execution summary as baseline for A/B comparison."""
    path = _get_baseline_path(project_root)
    _ = path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(json.dumps(exec_summary, indent=2), encoding="utf-8")
    print(f"Baseline saved to {path}")


def _load_baseline(project_root: Path) -> dict[str, object] | None:
    """Load baseline execution summary; return None if missing."""
    path = _get_baseline_path(project_root)
    if not path.is_file():
        return None
    return cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))


def main() -> int:
    """Run eval, parse execution_summary, exit 0 if pass rate >= threshold else 1."""
    parser = argparse.ArgumentParser(
        description="Run evaluation suite and exit 0 if pass rate >= threshold."
    )
    _ = parser.add_argument(
        "--mode",
        choices=("fast", "full"),
        default="full",
        help="fast: 10 tasks (~30s); full: all tasks (default: full)",
    )
    _ = parser.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="Minimum pass rate 0.0-1.0 to succeed (default: 0.85)",
    )
    _ = parser.add_argument(
        "--save-baseline",
        action="store_true",
        help="Save current execution summary as baseline for A/B comparison",
    )
    _ = parser.add_argument(
        "--compare-baseline",
        action="store_true",
        help="Compare current run to baseline; fail if regression > 5%%",
    )
    _ = parser.add_argument(
        "--current-results",
        type=str,
        default=None,
        metavar="PATH",
        help="With --compare-baseline: path to JSON file with execution_summary from prior run",
    )
    _ = parser.add_argument(
        "--output-summary",
        type=str,
        default=None,
        metavar="PATH",
        help="Write payload (with execution_summary) to file for use with --compare-baseline --current-results",
    )
    args = parser.parse_args()

    if args.compare_baseline and args.current_results:
        results_path = Path(args.current_results)
        if not results_path.is_file():
            print(f"Current results file not found: {results_path}", file=sys.stderr)
            return 1
        payload = cast(dict[str, object], json.loads(results_path.read_text()))
        exec_summary = cast(dict[str, object], payload.get("execution_summary") or {})
    else:
        payload_str = asyncio.run(_run_eval(args.mode, _PROJECT_ROOT))
        payload = cast(dict[str, object], json.loads(payload_str))
        exec_summary = cast(dict[str, object], payload.get("execution_summary") or {})
        if args.output_summary:
            summary_path = Path(args.output_summary)
            _ = summary_path.parent.mkdir(parents=True, exist_ok=True)
            _ = summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            print(f"Summary written to {summary_path}")
    passed, total, rate = _extract_pass_rate(exec_summary)
    pct = round(rate * 100, 1)
    threshold_pct = round(args.threshold * 100)

    if args.save_baseline:
        _save_baseline(_PROJECT_ROOT, exec_summary)
        print(f"Eval ({args.mode}): {passed}/{total} passed ({pct}%).")
        return 0

    if args.compare_baseline:
        baseline = _load_baseline(_PROJECT_ROOT)
        if baseline is None:
            print(
                "No baseline found; skipping A/B comparison. "
                + "Run with --save-baseline after a known-good eval to enable."
            )
            return 0
        _, _, base_rate = _extract_pass_rate(baseline)
        base_pct = round(base_rate * 100, 1)
        min_acceptable = base_rate - _BASELINE_REGRESSION_TOLERANCE
        success = rate >= min_acceptable
        print(
            f"Eval ({args.mode}): {passed}/{total} passed ({pct}%). "
            + f"Baseline: {base_pct}%. Tolerance: 5%."
        )
        if not success:
            msg = f"::error::Eval regressed: {pct}% < baseline {base_pct}% - 5%."
            print(msg, file=sys.stderr)
            return 1
        print("A/B comparison passed (no significant regression).")
        return 0

    success = rate >= args.threshold
    print(
        f"Eval ({args.mode}): {passed}/{total} passed ({pct}%). Threshold: {threshold_pct}%."
    )
    if not success:
        print(
            f"::error::Eval pass rate {pct}% is below threshold {threshold_pct}%.",
            file=sys.stderr,
        )
        return 1
    print("Eval check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
