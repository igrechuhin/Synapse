#!/usr/bin/env python3
"""Regression tests for check_public_docs script behavior."""

from __future__ import annotations

import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


class CheckPublicDocsTests(unittest.TestCase):
    """Validate undocumented-public detection scenarios."""

    def test_reports_undocumented_public_declaration(self) -> None:
        # Arrange
        swift_source = """
        public struct MissingDocsType {
            public init() {}
        }
        """

        # Act
        completed = _run_checker(swift_source)

        # Assert
        self.assertEqual(completed.returncode, 1)
        self.assertIn(
            "undocumented_public_declarations=2 threshold=0", completed.stdout
        )

    def test_accepts_docc_comment_when_attribute_is_between_comment_and_declaration(
        self,
    ) -> None:
        # Arrange
        swift_source = """
        /// Declared with availability metadata.
        @available(macOS 15.5, *)
        public struct DoccedWithAttribute {
            /// Creates value.
            @available(macOS 15.5, *)
            public init() {}
        }
        """

        # Act
        completed = _run_checker(swift_source)

        # Assert
        self.assertEqual(completed.returncode, 0)
        self.assertIn(
            "undocumented_public_declarations=0 threshold=0", completed.stdout
        )

    def test_counts_public_extension_members_and_ignores_private_members(self) -> None:
        # Arrange
        swift_source = """
        public struct ExtensionCarrier {}

        public extension ExtensionCarrier {
            func undocumentedMethod() {}
            private func hiddenMethod() {}
        }
        """

        # Act
        completed = _run_checker(swift_source)

        # Assert
        self.assertEqual(completed.returncode, 1)
        self.assertIn(
            "undocumented_public_declarations=2 threshold=0", completed.stdout
        )
        self.assertNotIn("hiddenMethod", completed.stdout)


def _run_checker(swift_source: str) -> subprocess.CompletedProcess[str]:
    script_path = Path(__file__).resolve().with_name("check_public_docs.py")
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_file = Path(tmp_dir) / "Sample.swift"
        _ = test_file.write_text(
            textwrap.dedent(swift_source).strip() + "\n", encoding="utf-8"
        )
        return subprocess.run(
            ["python3", str(script_path), str(test_file)],
            check=False,
            capture_output=True,
            text=True,
        )


if __name__ == "__main__":
    _ = unittest.main()
