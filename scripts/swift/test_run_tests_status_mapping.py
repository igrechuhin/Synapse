#!/usr/bin/env python3
"""Tests for Swift test status normalization."""

from __future__ import annotations

import unittest

from swift_test_runner import (
    decode_process_output,
    did_tests_pass,
    parse_swift_test_summary,
)


class SwiftRunTestsStatusMappingTests(unittest.TestCase):
    """Validate parser and normalized pass/fail mapping."""

    def test_parse_summary_extracts_total_and_failed_counts(self) -> None:
        output = "Executed 123 tests, with 0 failures (0 unexpected) in 5.432 seconds"

        total, failed = parse_swift_test_summary(output)

        self.assertEqual(total, 123)
        self.assertEqual(failed, 0)

    def test_parse_summary_returns_none_for_missing_summary(self) -> None:
        total, failed = parse_swift_test_summary(
            "Build complete! No test summary line."
        )

        self.assertIsNone(total)
        self.assertIsNone(failed)

    def test_decode_process_output_handles_png_header_byte(self) -> None:
        raw = bytes([0x89]) + b"PNG\r\n"

        decoded = decode_process_output(raw)

        self.assertEqual(decoded, "\ufffdPNG\r\n")

    def test_decode_process_output_handles_none(self) -> None:
        decoded = decode_process_output(None)

        self.assertEqual(decoded, "")

    def test_did_tests_pass_true_when_returncode_zero_and_zero_failures(self) -> None:
        self.assertTrue(did_tests_pass(returncode=0, failed_tests=0))

    def test_did_tests_pass_false_when_returncode_zero_and_failures(self) -> None:
        self.assertFalse(did_tests_pass(returncode=0, failed_tests=2))

    def test_did_tests_pass_false_when_nonzero_returncode_but_zero_failed(self) -> None:
        self.assertFalse(did_tests_pass(returncode=1, failed_tests=0))

    def test_did_tests_pass_false_when_nonzero_returncode_and_failures(self) -> None:
        self.assertFalse(did_tests_pass(returncode=1, failed_tests=3))

    def test_did_tests_pass_false_when_nonzero_returncode_and_no_parsed_count(
        self,
    ) -> None:
        self.assertFalse(did_tests_pass(returncode=1, failed_tests=None))


if __name__ == "__main__":
    _ = unittest.main()
