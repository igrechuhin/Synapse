#!/usr/bin/env python3
"""Tests for PHP test naming conventions."""

from __future__ import annotations

import unittest

from check_test_naming import find_naming_violations


class PestNamingTests(unittest.TestCase):
    """Pest-style test declarations are accepted."""

    def test_accepts_it_helper(self) -> None:
        text = "<?php\nit('adds numbers', function () {\n    expect(1)->toBe(1);\n});\n"

        self.assertEqual(find_naming_violations(text), [])

    def test_accepts_test_helper(self) -> None:
        text = (
            "<?php\ntest('adds numbers', function () {\n    expect(1)->toBe(1);\n});\n"
        )

        self.assertEqual(find_naming_violations(text), [])


class PhpUnitNamingTests(unittest.TestCase):
    """PHPUnit-style test declarations are accepted."""

    def test_accepts_test_prefixed_method(self) -> None:
        text = (
            "<?php\nclass UserTest extends TestCase {\n"
            "    public function testItWorks(): void {}\n}\n"
        )

        self.assertEqual(find_naming_violations(text), [])

    def test_accepts_attribute_annotated_method(self) -> None:
        text = (
            "<?php\nclass UserTest extends TestCase {\n"
            "    #[Test]\n    public function itWorks(): void {}\n}\n"
        )

        self.assertEqual(find_naming_violations(text), [])

    def test_accepts_docblock_annotated_method(self) -> None:
        text = (
            "<?php\nclass UserTest extends TestCase {\n"
            "    /** @test */\n    public function itWorks(): void {}\n}\n"
        )

        self.assertEqual(find_naming_violations(text), [])


class NamingViolationTests(unittest.TestCase):
    """Untagged public methods are rejected."""

    def test_rejects_untagged_public_method(self) -> None:
        text = (
            "<?php\nclass UserTest extends TestCase {\n"
            "    public function itWorks(): void {}\n}\n"
        )

        violations = find_naming_violations(text)

        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0][1], "itWorks")

    def test_ignores_non_public_helper(self) -> None:
        text = (
            "<?php\nclass UserTest extends TestCase {\n"
            "    private function makeUser(): void {}\n}\n"
        )

        self.assertEqual(find_naming_violations(text), [])

    def test_ignores_setup_and_teardown(self) -> None:
        text = (
            "<?php\nclass UserTest extends TestCase {\n"
            "    public function setUp(): void {}\n"
            "    public function tearDown(): void {}\n}\n"
        )

        self.assertEqual(find_naming_violations(text), [])


if __name__ == "__main__":
    unittest.main()
