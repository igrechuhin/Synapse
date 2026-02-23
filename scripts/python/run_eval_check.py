#!/usr/bin/env python3
"""Run evaluation suite (fast or full) and exit with 0/1 based on pass rate threshold.

Used by CI to run eval-full and block merge if score drops below threshold (e.g. 85%).

Usage:
    uv run python .cortex/synapse/scripts/python/run_eval_check.py --mode full --threshold 0.85
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import cast

_IntConvertible = int | float | str

try:
    from _utils import get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _utils import get_project_root

# Ensure project src is on path for cortex imports
_PROJECT_ROOT = get_project_root(Path(__file__))
if str(_PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "src"))


async def _run_eval(mode: str, project_root: Path) -> str:
    """Run tool evaluation and return JSON payload string."""
    from cortex.tools.phase5_evaluation import run_tool_evaluation

    return await run_tool_evaluation(
        task_ids=None,
        mode=mode,
        category=None,
        ctx=None,
    )


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
    args = parser.parse_args()

    payload_str = asyncio.run(_run_eval(args.mode, _PROJECT_ROOT))
    payload = cast(dict[str, object], json.loads(payload_str))
    exec_summary = cast(dict[str, object], payload.get("execution_summary") or {})
    passed = int(cast(_IntConvertible, exec_summary.get("execution_passed", 0)))
    total = int(cast(_IntConvertible, exec_summary.get("execution_total_run", 0)))
    rate = (passed / total) if total else 1.0
    success = rate >= args.threshold
    pct = round(rate * 100, 1)
    threshold_pct = round(args.threshold * 100)
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
