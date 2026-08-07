#!/usr/bin/env python3
"""Pre-commit hook to run PHP static analysis.

Probes for PHPStan first, then Psalm. When neither is installed the gate skips
with exit 0.

The analysis level is NOT forced. phpstan.neon (or phpstan.neon.dist) is the
project's own contract; overriding it would surface a backlog the project has
deliberately not opted into. Set PHPSTAN_LEVEL to override explicitly.

Configuration:
    PHP_ANALYZER:     Analyzer binary (default: probe phpstan, psalm)
    PHPSTAN_LEVEL:    Explicit level, overriding phpstan.neon (default: unset)
    PHP_TOOL_TIMEOUT: Timeout in seconds (default: 120)
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from _php_toolchain import (
    PHP_TOOL_TIMEOUT,
    find_php_tool,
    php_files_from_env,
    php_project_root,
    skip,
)


ANALYZER_CANDIDATES = ["phpstan", "psalm"]


def build_analyze_cmd(tool: str, paths: list[str], level: str | None) -> list[str]:
    """Construct the analyzer invocation.

    Args:
        tool: Path to the analyzer binary.
        paths: Files to analyze. Empty means "use the project config".
        level: Explicit analysis level, or None to defer to project config.

    Returns:
        List of command parts.
    """
    name = Path(tool).name

    if name == "psalm":
        cmd = [tool, "--no-progress"]
        cmd.extend(paths)
        return cmd

    cmd = [tool, "analyse", "--no-progress"]
    if level is not None:
        cmd.append(f"--level={level}")
    cmd.extend(paths)
    return cmd


def main() -> None:
    project_root = php_project_root(Path(__file__))

    tool = find_php_tool(ANALYZER_CANDIDATES, project_root, env_override="PHP_ANALYZER")
    if tool is None or not Path(tool).exists():
        skip(
            "No PHP static analyzer installed, skipping "
            "(composer require --dev phpstan/phpstan)"
        )

    from_env = php_files_from_env()
    paths = [str(p) for p in from_env] if from_env is not None else []

    level = os.getenv("PHPSTAN_LEVEL")
    cmd = build_analyze_cmd(tool, paths, level)

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=PHP_TOOL_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        print(f"❌ Analyzer timed out after {PHP_TOOL_TIMEOUT}s", file=sys.stderr)
        sys.exit(1)
    except OSError as exc:
        print(f"❌ Error running analyzer: {exc}", file=sys.stderr)
        sys.exit(1)

    if result.returncode != 0:
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        print("\n❌ Static analysis errors detected.", file=sys.stderr)
        sys.exit(1)

    if result.stdout:
        print(result.stdout)
    print("✅ Static analysis passed")
    sys.exit(0)


if __name__ == "__main__":
    main()
