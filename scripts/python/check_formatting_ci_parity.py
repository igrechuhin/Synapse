#!/usr/bin/env python3
"""CI-parity formatting check: run the same formatter command and paths as CI.

This script runs the exact formatting check the CI workflow runs for the main
source and test trees (e.g. black --check src/ tests/ for Python). Use it in
Step 12.1.3 of the commit workflow to avoid path/scope mismatch between local
scripts and CI.

Configuration:
    Paths and formatter are language-specific; this script is for Python.
"""

import subprocess
import sys
from pathlib import Path

try:
    from _utils import get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from _utils import get_project_root


def get_ci_formatter_command(project_root: Path) -> list[str]:
    """Build the formatter command CI uses (e.g. uv run black --check)."""
    venv_black = project_root / ".venv" / "bin" / "black"
    if venv_black.exists():
        return [str(venv_black), "--check"]
    try:
        _ = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            check=True,
            cwd=project_root,
        )
        return ["uv", "run", "black", "--check"]
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return ["black", "--check"]


def main() -> None:
    """Run CI-parity formatting check (same paths as CI: src/ tests/)."""
    script_path = Path(__file__)
    project_root = get_project_root(script_path)

    cmd = get_ci_formatter_command(project_root) + ["src/", "tests/"]
    result = subprocess.run(
        cmd,
        cwd=project_root,
        capture_output=False,
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
