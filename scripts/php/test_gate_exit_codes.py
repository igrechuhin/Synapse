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


if __name__ == "__main__":
    unittest.main()
