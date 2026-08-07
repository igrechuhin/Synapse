#!/usr/bin/env python3
"""Tests for PHP gate exit-code behavior."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent


def run_gate(script: str, project_root: Path, env: dict[str, str] | None = None):
    """Run a gate script against a temp project and capture the result."""
    full_env = dict(os.environ)
    full_env.pop("FILES", None)
    full_env.pop("ALLOW_FULL_SCAN", None)
    full_env["PROJECT_ROOT"] = str(project_root)
    if env:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / script)],
        cwd=project_root,
        capture_output=True,
        text=True,
        env=full_env,
    )


class FileSizeGateTests(unittest.TestCase):
    """check_file_sizes.py exit codes."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        (self.root / "app").mkdir()

    def test_exits_zero_without_files_env(self) -> None:
        result = run_gate("check_file_sizes.py", self.root)

        self.assertEqual(result.returncode, 0)
        self.assertIn("skipped", result.stdout)

    def test_exits_zero_for_small_file(self) -> None:
        target = self.root / "app" / "Small.php"
        target.write_text("<?php\n$a = 1;\n")

        result = run_gate("check_file_sizes.py", self.root, {"FILES": str(target)})

        self.assertEqual(result.returncode, 0)
        self.assertIn("✅", result.stdout)

    def test_exits_one_for_oversized_file(self) -> None:
        target = self.root / "app" / "Big.php"
        body = "\n".join(f"$x{i} = {i};" for i in range(500))
        target.write_text(f"<?php\n{body}\n")

        result = run_gate("check_file_sizes.py", self.root, {"FILES": str(target)})

        self.assertEqual(result.returncode, 1)
        self.assertIn("❌", result.stderr)


class FunctionLengthGateTests(unittest.TestCase):
    """check_function_lengths.py exit codes."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        (self.root / "app").mkdir()

    def test_exits_zero_for_short_function(self) -> None:
        target = self.root / "app" / "Ok.php"
        target.write_text(
            "<?php\nclass Ok {\n    public function go(): void\n    {\n"
            "        $a = 1;\n    }\n}\n"
        )

        result = run_gate(
            "check_function_lengths.py", self.root, {"FILES": str(target)}
        )

        self.assertEqual(result.returncode, 0)

    def test_exits_one_for_long_function(self) -> None:
        target = self.root / "app" / "Long.php"
        body = "\n".join(f"        $x{i} = {i};" for i in range(60))
        target.write_text(
            f"<?php\nclass Long {{\n    public function go(): void\n    {{\n"
            f"{body}\n    }}\n}}\n"
        )

        result = run_gate(
            "check_function_lengths.py", self.root, {"FILES": str(target)}
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("❌", result.stderr)


class LintGateTests(unittest.TestCase):
    """check_linting.py exit codes."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        (self.root / "app").mkdir()

    def test_exits_zero_for_valid_syntax(self) -> None:
        target = self.root / "app" / "Valid.php"
        target.write_text("<?php\n$a = 1;\n")

        result = run_gate("check_linting.py", self.root, {"FILES": str(target)})

        self.assertEqual(result.returncode, 0)
        self.assertIn("✅", result.stdout)

    def test_exits_one_for_syntax_error(self) -> None:
        target = self.root / "app" / "Broken.php"
        target.write_text("<?php\n$a = ;\n")

        result = run_gate("check_linting.py", self.root, {"FILES": str(target)})

        self.assertEqual(result.returncode, 1)
        self.assertIn("❌", result.stderr)

    def test_exits_one_when_php_binary_missing(self) -> None:
        target = self.root / "app" / "Valid.php"
        target.write_text("<?php\n$a = 1;\n")

        result = run_gate(
            "check_linting.py",
            self.root,
            {"FILES": str(target), "PHP_BINARY": "/nonexistent/php"},
        )

        self.assertEqual(result.returncode, 1)
        self.assertIn("❌", result.stderr)


class FormattingGateTests(unittest.TestCase):
    """check_formatting.py skip behavior and command construction."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        (self.root / "app").mkdir()

    def test_skips_with_exit_zero_when_no_formatter(self) -> None:
        target = self.root / "app" / "A.php"
        target.write_text("<?php\n$a = 1;\n")

        result = run_gate(
            "check_formatting.py",
            self.root,
            {"FILES": str(target), "PHP_FORMATTER": "/nonexistent/pint"},
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("⚠️", result.stdout)
        self.assertIn("composer require", result.stdout)


class BuildFormatCmdTests(unittest.TestCase):
    """Formatter command construction."""

    def setUp(self) -> None:
        sys.path.insert(0, str(SCRIPTS_DIR))

    def test_pint_check_mode_uses_test_flag(self) -> None:
        from check_formatting import build_format_cmd

        cmd = build_format_cmd("/v/bin/pint", ["app"], write=False)

        self.assertEqual(cmd, ["/v/bin/pint", "app", "--test"])

    def test_pint_write_mode_omits_test_flag(self) -> None:
        from check_formatting import build_format_cmd

        cmd = build_format_cmd("/v/bin/pint", ["app"], write=True)

        self.assertEqual(cmd, ["/v/bin/pint", "app"])

    def test_php_cs_fixer_check_mode_uses_dry_run(self) -> None:
        from check_formatting import build_format_cmd

        cmd = build_format_cmd("/v/bin/php-cs-fixer", ["app"], write=False)

        self.assertEqual(
            cmd, ["/v/bin/php-cs-fixer", "fix", "app", "--dry-run", "--diff"]
        )


class TypesGateTests(unittest.TestCase):
    """check_types.py skip behavior."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        (self.root / "app").mkdir()

    def test_skips_with_exit_zero_when_no_analyzer(self) -> None:
        target = self.root / "app" / "A.php"
        target.write_text("<?php\n$a = 1;\n")

        result = run_gate(
            "check_types.py",
            self.root,
            {"FILES": str(target), "PHP_ANALYZER": "/nonexistent/phpstan"},
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("⚠️", result.stdout)
        self.assertIn("composer require", result.stdout)


class BuildAnalyzeCmdTests(unittest.TestCase):
    """Analyzer command construction."""

    def setUp(self) -> None:
        sys.path.insert(0, str(SCRIPTS_DIR))

    def test_phpstan_omits_level_when_unset(self) -> None:
        from check_types import build_analyze_cmd

        cmd = build_analyze_cmd("/v/bin/phpstan", [], None)

        self.assertEqual(cmd, ["/v/bin/phpstan", "analyse", "--no-progress"])

    def test_phpstan_includes_level_when_set(self) -> None:
        from check_types import build_analyze_cmd

        cmd = build_analyze_cmd("/v/bin/phpstan", [], "6")

        self.assertEqual(
            cmd, ["/v/bin/phpstan", "analyse", "--no-progress", "--level=6"]
        )

    def test_phpstan_appends_paths_when_given(self) -> None:
        from check_types import build_analyze_cmd

        cmd = build_analyze_cmd("/v/bin/phpstan", ["app/User.php"], None)

        self.assertEqual(
            cmd,
            ["/v/bin/phpstan", "analyse", "--no-progress", "app/User.php"],
        )

    def test_psalm_uses_its_own_flags(self) -> None:
        from check_types import build_analyze_cmd

        cmd = build_analyze_cmd("/v/bin/psalm", [], None)

        self.assertEqual(cmd, ["/v/bin/psalm", "--no-progress"])


if __name__ == "__main__":
    unittest.main()
