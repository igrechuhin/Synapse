#!/usr/bin/env python3
"""Run performance benchmarks for MCP Memory Bank.

This script runs comprehensive performance benchmarks and generates reports
for tracking performance over time.
"""

import asyncio
import sys
from pathlib import Path

from _utils import get_project_root

# Add src to path (project root via shared _utils)
sys.path.insert(0, str(get_project_root(Path(__file__)) / "src"))

from cortex.benchmarks.framework import BenchmarkRunner
from cortex.benchmarks.lightweight_benchmarks import (
    create_lightweight_benchmark_suite,
)
from cortex.benchmarks.memory_benchmarks import create_memory_benchmark_suite


async def main():
    """Run all benchmark suites."""
    print("=" * 80)
    print("MCP Memory Bank Performance Benchmarks")
    print("=" * 80)

    # Create benchmark runner
    output_dir = get_project_root(Path(__file__)) / "benchmark_results"
    runner = BenchmarkRunner(output_dir=output_dir)

    # Add benchmark suites
    runner.add_suite(create_lightweight_benchmark_suite())
    runner.add_suite(create_memory_benchmark_suite())

    # Run all benchmarks
    results = await runner.run_all()

    # Save results
    runner.save_results(results, filename="benchmark_results.json")
    runner.generate_markdown_report(results, filename="benchmark_report.md")

    print("\n" + "=" * 80)
    print("Benchmark run complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
