#!/usr/bin/env python3
"""Regression tests for subprocess output decoding in comprehensive_test."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from comprehensive_test import decode_process_output, run_script


class ComprehensiveTestOutputDecodingTests(unittest.TestCase):
    """Validate robust decoding for subprocess outputs."""

    def test_decode_process_output_handles_png_header_byte(self) -> None:
        raw = bytes([0x89]) + b"PNG\r\n"

        decoded = decode_process_output(raw)

        self.assertEqual(decoded, "\ufffdPNG\r\n")

    def test_run_script_handles_non_utf8_child_output(self) -> None:
        log_lines: list[str] = []
        script = Path(__file__)

        with patch("comprehensive_test.subprocess.run") as run_mock:
            run_mock.return_value.stdout = bytes([0x89]) + b"binary-output"
            run_mock.return_value.stderr = b""
            run_mock.return_value.returncode = 0

            result = run_script("Binary-safe check", script, log_lines)

        self.assertTrue(result)
        self.assertTrue(any("\ufffdbinary-output" in line for line in log_lines))


if __name__ == "__main__":
    unittest.main()
