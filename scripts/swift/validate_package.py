#!/usr/bin/env python3
"""Validate Package.swift integrity.

Checks:
  - Package.swift parses without errors (via `swift package describe`)
  - All declared source targets have a Sources/<Target>/ directory
  - All declared test targets have a Tests/<Target>/ directory (or co-located)
  - No duplicate target names

Configuration:
    BUILD_TIMEOUT: Timeout for swift package describe (default: 120)
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import cast

try:
    from _utils import get_config_int, get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))
    from _utils import get_config_int, get_project_root


BUILD_TIMEOUT = get_config_int("BUILD_TIMEOUT", 120)


def describe_package(project_root: Path) -> dict[str, object] | None:
    """Run `swift package describe --type json` and return parsed output.

    Args:
        project_root: Path to the project root containing Package.swift.

    Returns:
        Parsed JSON dict, or None on failure.
    """
    try:
        result = subprocess.run(
            ["swift", "package", "describe", "--type", "json"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=BUILD_TIMEOUT,
        )
        if result.returncode != 0:
            print(result.stderr, file=sys.stderr)
            return None
        raw = json.loads(result.stdout)
        if not isinstance(raw, dict):
            print(
                "❌ swift package describe returned non-object JSON.", file=sys.stderr
            )
            return None
        return cast(dict[str, object], raw)
    except subprocess.TimeoutExpired:
        print(
            f"❌ swift package describe timed out after {BUILD_TIMEOUT}s.",
            file=sys.stderr,
        )
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse swift package describe output: {e}", file=sys.stderr)
        return None
    except FileNotFoundError:
        print("❌ swift not found. Install Xcode command-line tools.", file=sys.stderr)
        return None


def main() -> None:
    """Validate Package.swift integrity."""
    project_root = get_project_root(Path(__file__))

    if not (project_root / "Package.swift").exists():
        print(f"❌ Package.swift not found in {project_root}", file=sys.stderr)
        sys.exit(1)

    print("Parsing Package.swift...")
    pkg = describe_package(project_root)
    if pkg is None:
        print("❌ Package.swift failed to parse.", file=sys.stderr)
        sys.exit(1)
    print("Package.swift parsed successfully")

    targets_obj = pkg.get("targets")
    targets: list[dict[str, object]] = []
    if isinstance(targets_obj, list):
        for item in cast(list[object], targets_obj):
            if isinstance(item, dict):
                targets.append(cast(dict[str, object], item))
    violations: list[str] = []

    # Check for duplicate names
    names: list[str] = []
    for t in targets:
        name_obj = t.get("name")
        if isinstance(name_obj, str):
            names.append(name_obj)
    seen: set[str] = set()
    for name in names:
        if name in seen:
            violations.append(f"  Duplicate target name: '{name}'")
        seen.add(name)

    # Check directories exist
    for target in targets:
        name_obj = target.get("name")
        if not isinstance(name_obj, str):
            continue
        name = name_obj

        ttype_obj = target.get("type")
        ttype = ttype_obj if isinstance(ttype_obj, str) else "regular"

        if ttype == "test":
            std_dir = project_root / "Tests" / name
            if not std_dir.exists():
                # Some projects co-locate tests inside Sources/
                alt = project_root / "Sources" / name.replace("Tests", "") / "Tests"
                alt2 = project_root / "Sources" / name
                if not alt.exists() and not alt2.exists():
                    violations.append(
                        f"  Test target '{name}': no directory at Tests/{name}, Sources/*/Tests/, or Sources/{name}"
                    )
        else:
            src_dir = project_root / "Sources" / name
            if not src_dir.exists():
                violations.append(f"  Source target '{name}': missing Sources/{name}/")

    if violations:
        print("❌ Package.swift violations:", file=sys.stderr)
        for v in violations:
            print(v, file=sys.stderr)
        sys.exit(1)

    print("✅ Package.swift validation passed")
    sys.exit(0)


if __name__ == "__main__":
    main()
