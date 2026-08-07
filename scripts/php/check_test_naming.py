#!/usr/bin/env python3
"""Pre-commit hook to verify PHP test naming conventions.

Accepts Pest it()/test() helpers, PHPUnit test-prefixed methods, and methods
carrying the #[Test] attribute or the @test docblock annotation.

Only *Test.php files are checked.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from _php_toolchain import (
    allow_full_scan,
    php_files_from_env,
    php_project_root,
    php_source_dirs,
)


_PUBLIC_METHOD_RE = re.compile(r"^\s*public\s+function\s+(\w+)\s*\(")
_EXEMPT_METHODS = frozenset(
    {"setUp", "tearDown", "setUpBeforeClass", "tearDownAfterClass", "__construct"}
)


def find_naming_violations(text: str) -> list[tuple[int, str]]:
    """Find public methods in a test file that are not recognizable as tests.

    Args:
        text: Full file contents.

    Returns:
        List of (line_number, method_name) for each violation.
    """
    violations: list[tuple[int, str]] = []
    lines = text.splitlines()

    for index, line in enumerate(lines):
        match = _PUBLIC_METHOD_RE.match(line)
        if match is None:
            continue

        name = match.group(1)
        if name in _EXEMPT_METHODS or name.startswith("test"):
            continue

        preceding = "\n".join(lines[max(0, index - 5) : index])
        if "#[Test]" in preceding or "@test" in preceding:
            continue

        violations.append((index + 1, name))

    return violations


def _is_test_file(path: Path) -> bool:
    return path.name.endswith("Test.php")


def _collect_files(project_root: Path) -> list[Path] | None:
    from_env = php_files_from_env()
    if from_env is not None:
        return [p for p in from_env if _is_test_file(p)]

    if not allow_full_scan():
        return None

    files: list[Path] = []
    for directory in php_source_dirs(project_root):
        files.extend(sorted(directory.rglob("*Test.php")))
    return files


def main() -> None:
    project_root = php_project_root(Path(__file__))
    test_files = _collect_files(project_root)

    if test_files is None:
        print("✅ No FILES provided and ALLOW_FULL_SCAN!=1 (skipped)")
        sys.exit(0)

    if not test_files:
        print("✅ No PHP test files detected (skipped)")
        sys.exit(0)

    all_violations: list[tuple[Path, int, str]] = []
    for test_file in test_files:
        if not test_file.exists():
            continue
        text = test_file.read_text(encoding="utf-8")
        for line_no, name in find_naming_violations(text):
            all_violations.append((test_file, line_no, name))

    if all_violations:
        print("❌ Test naming violations detected:", file=sys.stderr)
        print(file=sys.stderr)
        for path, line_no, name in all_violations:
            print(f"  {path}:{line_no} {name}()", file=sys.stderr)
        print(file=sys.stderr)
        print(
            "Test methods must start with 'test', carry #[Test], or use "
            "the @test annotation.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"✅ Test naming valid ({len(test_files)} file(s) checked)")
    sys.exit(0)


if __name__ == "__main__":
    main()
