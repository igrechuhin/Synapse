#!/usr/bin/env python3
"""Kill stuck SwiftPM processes and remove the build lock.

SwiftPM serialises its `.build` directory with a lock file and a PID check.
When a previous `swift build` / `swift test` run is interrupted (signal,
timeout, crash) the child process can stay alive, preventing the next
invocation from acquiring the lock.  This script detects and kills those
processes before they block the next build.

Configuration (all optional, via environment variables):
    KILL_SIGNAL:      POSIX signal name to send first (default: TERM).
    KILL_GRACE_S:     Seconds to wait after TERM before KILL (default: 5).
    BUILD_DIR:        Path to the .build directory to unlock (default: auto).
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

try:
    from _utils import get_config_int, get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
    from _utils import get_config_int, get_project_root

KILL_GRACE_S = get_config_int("KILL_GRACE_S", 5)
_SIGNAL_MAP = {"TERM": signal.SIGTERM, "KILL": signal.SIGKILL, "INT": signal.SIGINT}
KILL_SIGNAL = _SIGNAL_MAP.get(os.getenv("KILL_SIGNAL", "TERM").upper(), signal.SIGTERM)


def _swiftpm_pids() -> list[int]:
    """Return PIDs of running swift / swiftc / swift-build processes."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", r"swift(c|-build|-test|-package)?(\s|$)"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return [int(p) for p in result.stdout.split() if p.isdigit()]
    except Exception:
        return []


def _kill(pid: int, sig: signal.Signals) -> bool:
    try:
        os.kill(pid, sig)
        return True
    except ProcessLookupError:
        return False  # already gone
    except PermissionError:
        print(f"  ⚠️  No permission to signal PID {pid}", file=sys.stderr)
        return False


def kill_stuck_processes() -> int:
    """Terminate stuck SwiftPM processes.

    Returns:
        Number of processes killed.
    """
    pids = _swiftpm_pids()
    if not pids:
        print("✅ No stuck SwiftPM processes found")
        return 0

    print(f"⚠️  Found {len(pids)} stuck SwiftPM process(es): {pids}")

    # Send TERM first; give processes a chance to clean up.
    for pid in pids:
        if _kill(pid, KILL_SIGNAL):
            print(f"  → sent {KILL_SIGNAL.name} to PID {pid}")

    if KILL_GRACE_S > 0:
        time.sleep(KILL_GRACE_S)

    # Force-kill anything that survived.
    survivors = [p for p in pids if _swiftpm_pids_contain(p)]
    for pid in survivors:
        print(f"  → PID {pid} still alive, sending KILL")
        _ = _kill(pid, signal.SIGKILL)

    print(f"✅ Killed {len(pids)} SwiftPM process(es)")
    return len(pids)


def _swiftpm_pids_contain(pid: int) -> bool:
    return pid in _swiftpm_pids()


def remove_build_lock(project_root: Path) -> None:
    """Remove the SwiftPM build lock file if present."""
    build_dir = Path(os.getenv("BUILD_DIR", str(project_root / ".build")))
    lock = build_dir / "manifest.db-wal"  # presence signals an incomplete write
    lockfile = build_dir / ".build.lock"

    for candidate in [lockfile, lock]:
        if candidate.exists():
            try:
                candidate.unlink()
                print(f"✅ Removed lock: {candidate.relative_to(project_root)}")
            except OSError as exc:
                print(f"⚠️  Could not remove {candidate}: {exc}", file=sys.stderr)


def main() -> None:
    project_root = get_project_root(Path(__file__))

    killed = kill_stuck_processes()
    remove_build_lock(project_root)

    if killed:
        print(f"Cleanup complete — killed {killed} process(es).")
    else:
        print("Cleanup complete — nothing to do.")


if __name__ == "__main__":
    main()
