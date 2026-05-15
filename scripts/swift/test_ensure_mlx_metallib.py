#!/usr/bin/env python3
"""Tests for MLX metallib install helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ensure_mlx_metallib import _colocated_metallib_dirs, _copy_is_fresh


class EnsureMlxMetallibTests(unittest.TestCase):
    """Validate colocated metallib directory discovery."""

    def test_colocated_metallib_dirs_finds_xctest_macos_directories(self) -> None:
        with tempfile.TemporaryDirectory() as root_name:
            root = Path(root_name)
            macos_dir = (
                root
                / ".build"
                / "arm64-apple-macosx"
                / "debug"
                / "TradeWingPackageTests.xctest"
                / "Contents"
                / "MacOS"
            )
            macos_dir.mkdir(parents=True)

            found = _colocated_metallib_dirs(root)

            self.assertEqual(found, [macos_dir])

    def test_copy_is_fresh_requires_existing_target(self) -> None:
        with tempfile.TemporaryDirectory() as root_name:
            root = Path(root_name)
            built = root / "built.metallib"
            built.write_bytes(b"metal")

            self.assertFalse(_copy_is_fresh(root / "missing.metallib", built))


if __name__ == "__main__":
    unittest.main()
