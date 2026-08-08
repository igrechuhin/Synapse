#!/usr/bin/env python3
"""Post-edit quality hook (Python).

Designed to be run from a Claude Code PostToolUse hook after an Edit tool call.
Runs a fast pytest invocation scoped to the edited file and prints a short
tail of output.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from _utils import get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from _utils import get_project_root


def _pytest_cmd(project_root: Path) -> list[str] | None:
    venv_pytest = project_root / ".venv" / "bin" / "pytest"
    if venv_pytest.exists():
        return [str(venv_pytest)]

    if shutil.which("uv") is not None:
        return ["uv", "run", "pytest"]

    if shutil.which("pytest") is not None:
        return ["pytest"]

    return None


def _tail_lines(text: str, max_lines: int) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text.rstrip()
    return "\n".join(lines[-max_lines:]).rstrip()


def _edited_path() -> Path | None:
    """Read the edited file path from the hook's stdin JSON payload."""
    if sys.stdin.isatty():
        return None
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return None
    raw = payload.get("tool_input", {}).get("file_path")
    return Path(raw) if raw else None


def _pytest_targets(project_root: Path, edited: Path | None) -> list[str] | None:
    """Test paths to run: None means skip, empty list means whole suite."""
    if edited is None:
        return []
    if edited.suffix != ".py":
        return None

    try:
        rel = edited.resolve().relative_to(project_root.resolve())
    except ValueError:
        return None

    parts = rel.parts
    if parts[0] == "tests":
        return [str(rel)]
    if parts[0] != "src":
        # Scripts and tooling outside src/ are not covered by tests/.
        return None

    matches = sorted(project_root.glob(f"tests/**/test_{edited.stem}.py"))
    return [str(m.relative_to(project_root)) for m in matches] if matches else []


def main() -> int:
    project_root = get_project_root(Path(__file__))
    tests_dir = project_root / "tests"
    if not tests_dir.exists():
        print("Post-edit hook: no tests/ directory found; skipping.")
        return 0

    targets = _pytest_targets(project_root, _edited_path())
    if targets is None:
        print("Post-edit hook: no tests cover this file; skipping.")
        return 0

    cmd_base = _pytest_cmd(project_root)
    if cmd_base is None:
        print(
            "Post-edit hook: pytest not found (tried .venv, uv, PATH).",
            file=sys.stderr,
        )
        return 0

    cmd = cmd_base + (targets or ["tests/"]) + ["--timeout=30", "-x", "-q"]
    result = subprocess.run(
        cmd,
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )

    combined = ""
    if result.stdout:
        combined += result.stdout
    if result.stderr:
        combined += ("\n" if combined else "") + result.stderr

    tail = _tail_lines(combined, 20)
    if tail:
        print(tail)

    return 0 if result.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
