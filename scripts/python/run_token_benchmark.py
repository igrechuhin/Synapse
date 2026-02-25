#!/usr/bin/env python3
"""Run token efficiency benchmark and optionally compare with baseline.

Captures token usage from recent tool invocations (via query_usage token_efficiency)
and saves a report for before/after comparison when optimizing tools.

Usage:
    uv run python .cortex/synapse/scripts/python/run_token_benchmark.py [--days 7]
    uv run python .cortex/synapse/scripts/python/run_token_benchmark.py --baseline
    uv run python .cortex/synapse/scripts/python/run_token_benchmark.py --compare
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

try:
    from _utils import get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _utils import get_project_root

_PROJECT_ROOT = get_project_root(Path(__file__))
if str(_PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "src"))


def _snapshot_from_payload(payload: object) -> dict[str, object]:
    """Extract comparable snapshot from TokenEfficiencyPayload."""
    if not isinstance(payload, dict):
        return {}
    p = cast(dict[str, object], payload)
    raw_top = cast(list[object], p.get("top_by_total") or [])
    raw_avg = cast(list[object], p.get("top_by_avg") or [])
    top_total: list[dict[str, object]] = [
        cast(dict[str, object], x) for x in raw_top if isinstance(x, dict)
    ]
    top_avg: list[dict[str, object]] = [
        cast(dict[str, object], x) for x in raw_avg if isinstance(x, dict)
    ]
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "event_count_with_tokens": p.get("event_count_with_tokens", 0),
        "days": p.get("days", 0),
        "top_by_total": [
            {
                "tool_name": e.get("tool_name"),
                "total_response_tokens": e.get("total_response_tokens"),
                "call_count": e.get("call_count"),
                "avg_tokens_per_call": e.get("avg_tokens_per_call"),
            }
            for e in top_total
        ],
        "top_by_avg": [
            {
                "tool_name": e.get("tool_name"),
                "avg_tokens_per_call": e.get("avg_tokens_per_call"),
                "total_response_tokens": e.get("total_response_tokens"),
            }
            for e in top_avg
        ],
        "optimization_recommendations": p.get("optimization_recommendations", []),
    }


async def _run_token_efficiency(project_root: Path, days: int) -> str:
    """Run token efficiency analysis and return JSON payload string."""
    from cortex.tools import usage_analytics
    from cortex.tools.phase5_token_efficiency_helpers import (
        get_token_efficiency_payload,
    )

    tracker = await usage_analytics._get_tracker(project_root)  # type: ignore[attr-defined]

    payload = await get_token_efficiency_payload(
        project_root, tracker, days=days, top_n=10
    )
    return payload.model_dump_json(indent=2)


def _ensure_benchmark_dir(project_root: Path) -> Path:
    """Ensure .cortex/.cache/token_benchmark exists."""
    from cortex.core.path_resolver import get_cache_path

    benchmark_dir = get_cache_path(project_root, "token_benchmark")
    benchmark_dir.mkdir(parents=True, exist_ok=True)
    return benchmark_dir


def _to_int(val: object | None) -> int:
    """Convert JSON number to int; return 0 for non-numeric."""
    return int(val) if isinstance(val, (int, float)) else 0


def _print_comparison(baseline: dict[str, object], current: dict[str, object]) -> None:
    """Print before/after comparison."""
    base_events = _to_int(baseline.get("event_count_with_tokens"))
    curr_events = _to_int(current.get("event_count_with_tokens"))
    base_total_raw = cast(list[object], baseline.get("top_by_total") or [])
    curr_total_raw = cast(list[object], current.get("top_by_total") or [])
    base_total: list[dict[str, object]] = [
        cast(dict[str, object], x) for x in base_total_raw if isinstance(x, dict)
    ]
    curr_total: list[dict[str, object]] = [
        cast(dict[str, object], x) for x in curr_total_raw if isinstance(x, dict)
    ]

    print("\n=== Token Efficiency Benchmark Comparison ===\n")
    print(f"Baseline: {base_events} events with tokens")
    print(f"Current:  {curr_events} events with tokens")
    print()

    by_tool: dict[str, dict[str, object]] = {}
    for e in base_total:
        name = str(e.get("tool_name", ""))
        by_tool[name] = {"baseline": e}
    for e in curr_total:
        name = str(e.get("tool_name", ""))
        if name not in by_tool:
            by_tool[name] = {}
        by_tool[name]["current"] = e

    print("Per-tool (total response tokens):")
    for tool_name, data in sorted(by_tool.items()):
        base_val = 0
        curr_val = 0
        bl = data.get("baseline")
        cu = data.get("current")
        if isinstance(bl, dict):
            bl_dict = cast(dict[str, object], bl)
            base_val = _to_int(bl_dict.get("total_response_tokens"))
        if isinstance(cu, dict):
            cu_dict = cast(dict[str, object], cu)
            curr_val = _to_int(cu_dict.get("total_response_tokens"))
        delta = curr_val - base_val
        pct = (100 * delta / base_val) if base_val else 0
        sign = "+" if delta >= 0 else ""
        print(
            f"  {tool_name}: {base_val} -> {curr_val} ({sign}{delta}, {sign}{pct:.1f}%)"
        )

    recs_raw = cast(list[object], current.get("optimization_recommendations") or [])
    recs: list[str] = [r for r in recs_raw if isinstance(r, str)]
    if recs:
        print("\nOptimization recommendations:")
        for r in recs:
            print(f"  - {r}")


def main() -> int:
    """Run benchmark, optionally save baseline or compare."""
    parser = argparse.ArgumentParser(
        description="Run token efficiency benchmark for before/after comparison."
    )
    _ = parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Analysis window in days (default: 7)",
    )
    _ = parser.add_argument(
        "--baseline",
        action="store_true",
        help="Save current run as baseline for future comparison",
    )
    _ = parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare current run with saved baseline",
    )
    args = parser.parse_args()

    payload_str = asyncio.run(
        _run_token_efficiency(_PROJECT_ROOT, days=max(1, min(365, args.days)))
    )
    payload = cast(dict[str, object], json.loads(payload_str))

    if payload.get("status") == "unavailable":
        print("Usage tracker not available. Run tools via MCP to collect data.")
        return 1

    benchmark_dir = _ensure_benchmark_dir(_PROJECT_ROOT)
    last_path = benchmark_dir / "last.json"
    baseline_path = benchmark_dir / "baseline.json"

    snapshot = _snapshot_from_payload(payload)

    with open(last_path, "w") as f:
        json.dump(snapshot, f, indent=2)

    if args.baseline:
        with open(baseline_path, "w") as f:
            json.dump(snapshot, f, indent=2)
        print(f"Baseline saved to {baseline_path}")
        return 0

    if args.compare:
        if not baseline_path.exists():
            print("No baseline found. Run with --baseline first.")
            return 1
        with open(baseline_path) as f:
            baseline = cast(dict[str, object], json.load(f))
        _print_comparison(baseline, snapshot)
        return 0

    print(f"Token benchmark saved to {last_path}")
    print(f"Events with tokens: {snapshot.get('event_count_with_tokens', 0)}")
    recs_raw = cast(list[object], snapshot.get("optimization_recommendations") or [])
    recs_list = [r for r in recs_raw if isinstance(r, str)]
    if recs_list:
        print("\nTop optimization recommendations:")
        for r in recs_list[:5]:
            print(f"  - {r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
