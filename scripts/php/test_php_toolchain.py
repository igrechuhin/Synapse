#!/usr/bin/env python3
"""Tests for shared PHP toolchain discovery."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from _php_toolchain import (
    count_logical_lines,
    find_php_tool,
    php_files_from_env,
    php_project_root,
    php_source_dirs,
)


class FindPhpToolTests(unittest.TestCase):
    """Probe order and override behavior."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        os.environ.pop("PHP_FORMATTER", None)

    def _make_vendor_bin(self, name: str) -> Path:
        vendor = self.root / "vendor" / "bin"
        vendor.mkdir(parents=True, exist_ok=True)
        tool = vendor / name
        tool.write_text("#!/bin/sh\n")
        tool.chmod(0o755)
        return tool

    def test_vendor_bin_wins_over_path(self) -> None:
        expected = self._make_vendor_bin("pint")

        result = find_php_tool(["pint"], self.root)

        self.assertEqual(result, str(expected))

    def test_falls_through_to_second_candidate(self) -> None:
        expected = self._make_vendor_bin("php-cs-fixer")

        result = find_php_tool(["pint", "php-cs-fixer"], self.root)

        self.assertEqual(result, str(expected))

    def test_returns_none_when_candidates_exhausted(self) -> None:
        result = find_php_tool(["definitely-not-a-real-tool-xyz"], self.root)

        self.assertIsNone(result)

    def test_env_override_short_circuits_probe(self) -> None:
        self._make_vendor_bin("pint")
        os.environ["PHP_FORMATTER"] = "/custom/pint"
        self.addCleanup(os.environ.pop, "PHP_FORMATTER", None)

        result = find_php_tool(["pint"], self.root, env_override="PHP_FORMATTER")

        self.assertEqual(result, "/custom/pint")


class PhpSourceDirsTests(unittest.TestCase):
    """Laravel app/ versus PSR-4 src/ detection."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        for key in ("PHP_SRC_DIR", "PHP_TESTS_DIR"):
            os.environ.pop(key, None)

    def test_detects_laravel_app_directory(self) -> None:
        app = self.root / "app"
        app.mkdir()
        (app / "User.php").write_text("<?php\n")

        result = php_source_dirs(self.root)

        self.assertIn(app, result)

    def test_detects_psr4_src_directory(self) -> None:
        src = self.root / "src"
        src.mkdir()
        (src / "Thing.php").write_text("<?php\n")

        result = php_source_dirs(self.root)

        self.assertIn(src, result)

    def test_app_preferred_over_src_when_both_exist(self) -> None:
        for name in ("app", "src"):
            d = self.root / name
            d.mkdir()
            (d / "A.php").write_text("<?php\n")

        result = php_source_dirs(self.root)

        self.assertIn(self.root / "app", result)
        self.assertNotIn(self.root / "src", result)

    def test_includes_tests_directory(self) -> None:
        (self.root / "tests").mkdir()

        result = php_source_dirs(self.root)

        self.assertIn(self.root / "tests", result)


class PhpFilesFromEnvTests(unittest.TestCase):
    """FILES environment variable parsing."""

    def setUp(self) -> None:
        os.environ.pop("FILES", None)

    def test_returns_none_when_unset(self) -> None:
        self.assertIsNone(php_files_from_env())

    def test_returns_none_when_blank(self) -> None:
        os.environ["FILES"] = "   "
        self.addCleanup(os.environ.pop, "FILES", None)

        self.assertIsNone(php_files_from_env())

    def test_filters_to_php_files_only(self) -> None:
        os.environ["FILES"] = "app/User.php\nREADME.md\napp/Post.php"
        self.addCleanup(os.environ.pop, "FILES", None)

        result = php_files_from_env()

        self.assertEqual(result, [Path("app/User.php"), Path("app/Post.php")])


class PhpProjectRootTests(unittest.TestCase):
    """PROJECT_ROOT override takes precedence over filesystem walking."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        os.environ.pop("PROJECT_ROOT", None)

    def test_env_override_wins(self) -> None:
        os.environ["PROJECT_ROOT"] = str(self.root)
        self.addCleanup(os.environ.pop, "PROJECT_ROOT", None)

        result = php_project_root(Path(__file__))

        self.assertEqual(result, self.root)

    def test_falls_back_to_filesystem_walk(self) -> None:
        """Without the override, resolves to the Synapse repo root."""
        result = php_project_root(Path(__file__))

        self.assertTrue((result / "README.md").exists())


class CountLogicalLinesTests(unittest.TestCase):
    """PHP comment stripping."""

    def test_skips_blank_and_line_comments(self) -> None:
        text = "<?php\n\n// comment\n$a = 1;\n# hash comment\n$b = 2;\n"

        self.assertEqual(count_logical_lines(text), 3)

    def test_skips_block_comments(self) -> None:
        text = "<?php\n/*\n * docblock\n */\n$a = 1;\n"

        self.assertEqual(count_logical_lines(text), 2)

    def test_counts_php8_attribute_as_code(self) -> None:
        """#[Test] is an attribute, not a hash comment."""
        text = "<?php\n#[Test]\npublic function foo() {}\n"

        self.assertEqual(count_logical_lines(text), 3)


if __name__ == "__main__":
    unittest.main()
