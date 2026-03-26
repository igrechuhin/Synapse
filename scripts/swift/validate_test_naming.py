#!/usr/bin/env python3
"""Validate Swift XCTest function naming conventions.

All XCTest methods must follow: test_behaviorDescription_whenCondition()

Swift Testing @Test functions use free-form descriptive strings and are
excluded from the naming check.

Configuration:
    TESTS_DIR: Directory to scan (default: Tests/)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    from _utils import get_config_path, get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from _utils import get_config_path, get_project_root


# XCTest method: starts with `func test` (uppercase next char), no @Test above
_XCTEST_FUNC_RE = re.compile(r"^\s*func\s+(test[A-Z]\w*)\s*\(")
_SWIFT_TESTING_RE = re.compile(r"@Test\b")

# Valid pattern: test_<lowerCamelCase>_<lowerCamelCase>
_VALID_NAME_RE = re.compile(r"^test_[a-z][A-Za-z0-9]+_[a-z][A-Za-z0-9]+$")


def check_file(path: Path, project_root: Path) -> list[str]:
    """Check a single test file for naming violations.

    Args:
        path: Path to the .swift test file.
        project_root: Project root for relative paths in messages.

    Returns:
        List of human-readable violation strings.
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        print(f"Error reading {path}: {e}", file=sys.stderr)
        return []

    try:
        rel = path.relative_to(project_root)
    except ValueError:
        rel = path

    violations: list[str] = []
    for i, line in enumerate(lines, 1):
        # Skip @Test-annotated functions (Swift Testing framework)
        if i >= 2 and _SWIFT_TESTING_RE.search(lines[i - 2]):
            continue
        m = _XCTEST_FUNC_RE.match(line)
        if m:
            func_name = m.group(1)
            if not _VALID_NAME_RE.match(func_name):
                violations.append(
                    f"  {rel}:{i}: '{func_name}' — "
                    "expected test_behaviorDescription_whenCondition"
                )
    return violations


def main() -> None:
    """Check all XCTest files for naming convention violations."""
    project_root = get_project_root(Path(__file__))

    tests_dir_override = get_config_path("TESTS_DIR")
    if tests_dir_override is not None:
        tests_dir = (
            tests_dir_override
            if tests_dir_override.is_absolute()
            else project_root / tests_dir_override
        )
    else:
        tests_dir = project_root / "Tests"

    if not tests_dir.exists():
        print(f"No Tests/ directory found at {tests_dir}, skipping.")
        sys.exit(0)

    all_violations: list[str] = []

    for swift_file in sorted(tests_dir.rglob("*.swift")):
        all_violations.extend(check_file(swift_file, project_root))

    if all_violations:
        print("❌ Test naming violations detected:", file=sys.stderr)
        print(file=sys.stderr)
        for v in all_violations:
            print(v, file=sys.stderr)
        print(file=sys.stderr)
        print(
            f"Found {len(all_violations)} naming violation(s). "
            "Follow: test_behaviorDescription_whenCondition",
            file=sys.stderr,
        )
        sys.exit(1)

    print("✅ All XCTest functions follow naming conventions")
    sys.exit(0)


if __name__ == "__main__":
    main()
