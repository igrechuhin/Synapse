#!/usr/bin/env python3
"""Regression tests for one-type checker source-read failures."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from check_one_type_per_file import check_file


class CheckOneTypePerFileTests(unittest.TestCase):
    """Unreadable sources fail without changing valid-source admission."""

    def test_cli_rejects_invalid_utf8_and_accepts_valid_control(self) -> None:
        script_path = Path(__file__).resolve().with_name("check_one_type_per_file.py")
        with tempfile.TemporaryDirectory() as root_name:
            root = Path(root_name)
            source = root / "Sample.swift"
            for content, status in ((b"\xff", 1), (b"public struct Sample {}\n", 0)):
                with self.subTest(content=content):
                    _ = source.write_bytes(content)
                    completed = subprocess.run(
                        [sys.executable, str(script_path)],
                        env={**os.environ, "SOURCES_DIR": str(root)},
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(completed.returncode, status)
                    if status:
                        self.assertIn(f"Error reading {source}:", completed.stderr)
                        self.assertNotIn("All Swift files comply", completed.stdout)
                    else:
                        self.assertIn("All Swift files comply", completed.stdout)
                        self.assertEqual(completed.stderr, "")

    def test_missing_source_returns_failure_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as root_name:
            root = Path(root_name)
            source = root / "Missing.swift"
            violations = check_file(source, root)
            self.assertEqual(len(violations), 1)
            self.assertIn(f"Error reading {source}:", violations[0])

    def test_unexpected_read_exception_propagates(self) -> None:
        with patch.object(Path, "read_text", side_effect=RuntimeError("unexpected")):
            with self.assertRaisesRegex(RuntimeError, "unexpected"):
                _ = check_file(Path("Sample.swift"), Path.cwd())


if __name__ == "__main__":
    _ = unittest.main()
