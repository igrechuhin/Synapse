#!/usr/bin/env python3
"""Shared Swift/MLX toolchain helpers for TradeWing build and test runners."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def ensure_developer_dir_for_swiftpm(project_root: Path) -> None:
    """Set ``DEVELOPER_DIR`` to full Xcode when missing or pointing at Command Line Tools only."""
    if sys.platform != "darwin":
        return
    existing = os.environ.get("DEVELOPER_DIR", "")
    if existing and Path(existing).is_dir():
        if "CommandLineTools" in existing:
            msg = "DEVELOPER_DIR points at Command Line Tools; MLX needs full Xcode. Run: sudo xcode-select -s /Applications/Xcode.app/Contents/Developer"  # noqa: E501
            print(msg, file=sys.stderr)
            sys.exit(1)
        return
    script = project_root / ".cursor" / "scripts" / "resolve_developer_dir.sh"
    if not script.is_file():
        return
    proc = subprocess.run(
        ["/bin/bash", str(script)],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    if proc.returncode != 0:
        print(proc.stderr.strip() or proc.stdout.strip(), file=sys.stderr)
        sys.exit(1)
    resolved = proc.stdout.strip()
    if not resolved:
        print("resolve_developer_dir.sh returned empty path.", file=sys.stderr)
        sys.exit(1)
    os.environ["DEVELOPER_DIR"] = resolved


def find_swift() -> str:
    """Return path to swift executable using the active Xcode toolchain."""
    if sys.platform == "darwin":
        try:
            proc = subprocess.run(
                ["xcrun", "--find", "swift"],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
                env=os.environ,
            )
            if proc.returncode == 0:
                path = proc.stdout.strip()
                if path and Path(path).exists():
                    return path
        except (OSError, subprocess.SubprocessError):
            pass
    which = shutil.which("swift")
    if which:
        return which
    for candidate in ("/usr/bin/swift", "/usr/local/bin/swift"):
        if Path(candidate).exists():
            return candidate
    return "swift"
