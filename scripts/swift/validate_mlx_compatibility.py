#!/usr/bin/env python3
"""Validate MLX framework compatibility for TradeWing.

Checks: macOS version, Metal GPU availability, Xcode version, Swift version,
and MLX package presence in Package.swift.

Configuration:
    REPORT: Set to 1 to print a markdown compatibility report (default: 0)
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

try:
    from _utils import get_config_int, get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
    from _utils import get_config_int, get_project_root


REPORT_MODE = get_config_int("REPORT", 0)

_MIN_MACOS = (13, 0)
_MIN_XCODE = 15
_MIN_SWIFT = (5, 9)


def run(cmd: list[str]) -> str:
    """Run a command and return stdout, or empty string on failure.

    Args:
        cmd: Command and arguments.

    Returns:
        stdout output stripped, or empty string.
    """
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False, timeout=15
        )
        return result.stdout.strip()
    except Exception:
        return ""


def check_macos() -> tuple[str, str, str]:
    """Check macOS version meets minimum requirement.

    Returns:
        Tuple of (label, status, detail).
    """
    version_str = run(["sw_vers", "-productVersion"])
    if not version_str:
        return "macOS version", "warn", "could not determine version"
    parts = version_str.split(".")
    major, minor = int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
    if (major, minor) >= _MIN_MACOS:
        return "macOS version", "pass", version_str
    return (
        "macOS version",
        "fail",
        f"{version_str} (MLX requires macOS {_MIN_MACOS[0]}.{_MIN_MACOS[1]}+)",
    )


def check_metal() -> tuple[str, str, str]:
    """Check Metal GPU availability.

    Returns:
        Tuple of (label, status, detail).
    """
    output = run(["system_profiler", "SPDisplaysDataType"])
    if "Metal: Supported" in output or "Metal:" in output:
        return "Metal GPU", "pass", "Supported"
    return "Metal GPU", "warn", "not detected (CPU fallback will apply)"


def check_xcode() -> tuple[str, str, str]:
    """Check Xcode version.

    Returns:
        Tuple of (label, status, detail).
    """
    output = run(["xcodebuild", "-version"])
    if not output:
        return "Xcode", "warn", "xcodebuild not found"
    m = re.search(r"Xcode\s+(\d+)", output)
    if not m:
        return "Xcode", "warn", f"could not parse: {output!r}"
    major = int(m.group(1))
    if major >= _MIN_XCODE:
        return "Xcode version", "pass", m.group(0)
    return "Xcode version", "warn", f"{m.group(0)} (Xcode {_MIN_XCODE}+ recommended)"


def check_swift() -> tuple[str, str, str]:
    """Check Swift version.

    Returns:
        Tuple of (label, status, detail).
    """
    output = run(["swift", "--version"])
    if not output:
        return "Swift version", "fail", "swift not found"
    m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", output)
    if not m:
        return "Swift version", "warn", f"could not parse: {output!r}"
    major, minor = int(m.group(1)), int(m.group(2))
    version_str = m.group(0)
    if (major, minor) >= (6, 0):
        return "Swift version", "pass", version_str
    if (major, minor) >= _MIN_SWIFT:
        return "Swift version", "warn", f"{version_str} (Swift 6+ preferred)"
    return (
        "Swift version",
        "fail",
        f"{version_str} (Swift {_MIN_SWIFT[0]}.{_MIN_SWIFT[1]}+ required)",
    )


def check_mlx_dependency(project_root: Path) -> tuple[str, str, str]:
    """Check MLX package presence in Package.swift.

    Args:
        project_root: Project root directory.

    Returns:
        Tuple of (label, status, detail).
    """
    pkg = project_root / "Package.swift"
    if not pkg.exists():
        return "MLX dependency", "warn", "Package.swift not found"
    content = pkg.read_text(encoding="utf-8")
    if "mlx-swift" in content or "MLX" in content:
        return "MLX dependency", "pass", "found in Package.swift"
    return "MLX dependency", "warn", "MLX not referenced in Package.swift"


def main() -> None:
    """Run MLX compatibility checks."""
    project_root = get_project_root(Path(__file__))

    checks = [
        check_macos(),
        check_metal(),
        check_xcode(),
        check_swift(),
        check_mlx_dependency(project_root),
    ]

    passed = sum(1 for _, s, _ in checks if s == "pass")
    warned = sum(1 for _, s, _ in checks if s == "warn")
    failed = sum(1 for _, s, _ in checks if s == "fail")

    icons = {"pass": "✅", "warn": "⚠️ ", "fail": "❌"}
    for label, status, detail in checks:
        print(f"{icons[status]} {label}: {detail}")

    print(f"\nResults: {passed} passed, {warned} warnings, {failed} failed")

    if REPORT_MODE:
        print("\n## MLX Compatibility Report\n")
        print("| Check | Status | Detail |")
        print("|-------|--------|--------|")
        for label, status, detail in checks:
            print(f"| {label} | {icons[status]} | {detail} |")

    if failed > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
