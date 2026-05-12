#!/usr/bin/env python3
"""Tests for canonical memory-bank root resolution helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from check_memory_bank_resolution import build_resolution_report
from _utils import resolve_memory_bank_file_path, resolve_memory_bank_root


class MemoryBankResolutionTests(unittest.TestCase):
    """Validate structure-aware memory-bank root/file resolution."""

    def test_resolve_root_prefers_existing_structure_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            structure_root = project_root / ".cortex" / "memory-bank-override"
            structure_root.mkdir(parents=True)

            result = resolve_memory_bank_root(
                project_root=project_root,
                structure_memory_bank_path=structure_root,
            )

            self.assertEqual(result, structure_root.resolve())

    def test_resolve_root_falls_back_when_structure_path_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            expected_fallback = project_root / ".cortex" / "memory-bank"
            expected_fallback.mkdir(parents=True)

            result = resolve_memory_bank_root(
                project_root=project_root,
                structure_memory_bank_path=project_root / "missing-memory-bank",
            )

            self.assertEqual(result, expected_fallback.resolve())

    def test_resolve_file_path_uses_structure_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            structure_root = project_root / ".cortex" / "memory-bank"
            structure_root.mkdir(parents=True)

            roadmap_path = resolve_memory_bank_file_path(
                project_root=project_root,
                file_name="roadmap.md",
                structure_memory_bank_path=str(structure_root),
            )

            self.assertEqual(roadmap_path, structure_root.resolve() / "roadmap.md")

    def test_build_resolution_report_flags_missing_roadmap(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            structure_root = project_root / ".cortex" / "memory-bank"
            structure_root.mkdir(parents=True)

            report = build_resolution_report(
                project_root=project_root,
                structure_memory_bank_path=str(structure_root),
            )

            self.assertEqual(
                report["roadmap_lookup_path"],
                str(structure_root.resolve() / "roadmap.md"),
            )
            self.assertFalse(report["roadmap_exists"])

    def test_build_resolution_report_flags_existing_roadmap(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            structure_root = project_root / ".cortex" / "memory-bank"
            structure_root.mkdir(parents=True)
            roadmap_file = structure_root / "roadmap.md"
            roadmap_file.write_text("# Roadmap\n", encoding="utf-8")

            report = build_resolution_report(
                project_root=project_root,
                structure_memory_bank_path=str(structure_root),
            )

            self.assertTrue(report["roadmap_exists"])


if __name__ == "__main__":
    _ = unittest.main()
