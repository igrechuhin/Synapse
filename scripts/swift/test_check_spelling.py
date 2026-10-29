#!/usr/bin/env python3
"""Behavioral tests for the Swift spelling checker.

Covers the false-green regression (checker failures must stay failures),
command unavailability, version preflight, timeout handling, exit-code
preservation, empty-scope distinction, and Sources/Tests-only collection.
"""

from __future__ import annotations

import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().with_name("check_spelling.py")

CSPELL_STUB = """#!{python}
import sys
from pathlib import Path

args = sys.argv[1:]
if args == ["--version"]:
    print(Path(__file__).with_name("version.txt").read_text(), end="")
    sys.exit(0)
log = Path(__file__).with_name("argv.log")
calls = log.read_text().count("\\n") if log.exists() else 0
with log.open("a") as handle:
    handle.write("\\0".join(args) + "\\n")
second_batch_fail = Path(__file__).with_name("second_batch_fail")
if second_batch_fail.exists() and "lint" in args and calls >= 1:
    sys.stdout.write("Sources/App.swift:1:8 - Unknown word (batchtwo)\\n")
    sys.exit(1)
diagnostic = Path(__file__).with_name("diagnostic.txt")
if diagnostic.exists():
    sys.stdout.write(diagnostic.read_text())
if Path(__file__).with_name("hang").exists() and "lint" in args:
    import time
    time.sleep(30)
sys.exit(int(Path(__file__).with_name("exit_code.txt").read_text()))
"""


class SwiftSpellingCheckerTests(unittest.TestCase):
    """Real behavior branches of check_spelling.py for Swift."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        (self.root / "Sources").mkdir()
        (self.root / "Tests").mkdir()
        (self.root / "Sources" / "App.swift").write_text("public struct App {}\n")
        self.stub = self.root / "cspell-stub"
        self.stub.write_text(CSPELL_STUB.format(python=sys.executable))
        self.stub.chmod(self.stub.stat().st_mode | stat.S_IXUSR)
        self._set_stub_state(version="8.6.1\n", exit_code="0")

    def _set_stub_state(
        self,
        *,
        version: str = "8.6.1\n",
        exit_code: str = "0",
        diagnostic: str | None = None,
        hang: bool = False,
    ) -> None:
        (self.root / "version.txt").write_text(version)
        (self.root / "exit_code.txt").write_text(exit_code)
        log = self.root / "argv.log"
        if log.exists():
            log.unlink()
        diag = self.root / "diagnostic.txt"
        if diagnostic is None:
            diag.unlink(missing_ok=True)
        else:
            diag.write_text(diagnostic)
        (self.root / "hang").unlink(missing_ok=True)
        if hang:
            (self.root / "hang").write_text("")

    def _run(self, **env_overrides: str) -> subprocess.CompletedProcess[str]:
        env = {
            k: v for k, v in os.environ.items() if not k.startswith("SPELL_CHECKER_")
        }
        env.update(
            {
                "SRC_DIR": str(self.root / "Sources"),
                "TESTS_DIR": str(self.root / "Tests"),
                "SPELL_CHECKER_CMD": str(self.stub),
            }
        )
        env.update(env_overrides)
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            env=env,
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )

    def test_checker_failure_is_failure_not_false_green(self) -> None:
        """Original false-green case: nonzero checker exit stays a failure."""
        self._set_stub_state(
            exit_code="1",
            diagnostic=(
                "Sources/App.swift:1:8 - Unknown word (appp)\n" "1/1 files checked.\n"
            ),
        )
        completed = self._run()
        self.assertEqual(completed.returncode, 1)
        self.assertIn("Unknown word", completed.stderr)
        self.assertIn("Spelling check failed (checker exit code 1)", completed.stderr)
        self.assertNotIn("passed", completed.stdout)

    def test_config_error_status_and_diagnostic_survive(self) -> None:
        """cspell configuration errors (exit 2) keep their exact status."""
        self._set_stub_state(
            exit_code="2",
            diagnostic=(
                "Failed to read config file '.cspell.json': "
                "Unexpected token in JSON\n"
            ),
        )
        completed = self._run()
        self.assertEqual(completed.returncode, 2)
        self.assertIn("Failed to read config file", completed.stderr)
        self.assertIn("Spelling check failed (checker exit code 2)", completed.stderr)
        self.assertNotIn("passed", completed.stdout)

    def test_clean_scope_passes(self) -> None:
        completed = self._run()
        self.assertEqual(completed.returncode, 0)
        self.assertIn("All Swift spelling checks passed", completed.stdout)

    def test_unavailable_command_fails_loudly(self) -> None:
        completed = self._run(SPELL_CHECKER_CMD="/nonexistent/cspell")
        self.assertEqual(completed.returncode, 1)
        self.assertIn("Error starting spell checker", completed.stderr)
        self.assertNotIn("passed", completed.stdout)

    def test_unsupported_version_fails_preflight(self) -> None:
        self._set_stub_state(version="7.0.0\n")
        completed = self._run()
        self.assertEqual(completed.returncode, 1)
        self.assertIn("Unsupported cspell version; require 8.6.1", completed.stderr)

    def test_timeout_is_failure_exit_124(self) -> None:
        self._set_stub_state(hang=True)
        completed = self._run(SPELL_CHECKER_TIMEOUT="1")
        self.assertEqual(completed.returncode, 124)
        self.assertIn("timed out after 1 second", completed.stderr)
        self.assertNotIn("passed", completed.stdout)

    def test_empty_scope_distinct_from_clean_pass(self) -> None:
        (self.root / "Sources" / "App.swift").unlink()
        completed = self._run()
        self.assertEqual(completed.returncode, 0)
        self.assertIn(
            "No Swift files found to check in Sources/Tests scope", completed.stderr
        )
        self.assertNotIn("All Swift spelling checks passed", completed.stdout)

    def test_only_swift_files_in_documented_scope(self) -> None:
        (self.root / "Sources" / "helper.py").write_text("pyt = 1\n")
        (self.root / "Elsewhere").mkdir()
        (self.root / "Elsewhere" / "Outside.swift").write_text("x\n")
        (self.root / "Sources" / "Sub").mkdir()
        (self.root / "Sources" / "Sub" / "Inner.swift").write_text("y\n")
        (self.root / "Tests" / "AppTests.swift").write_text("struct AppTests {}\n")
        completed = self._run()
        self.assertEqual(completed.returncode, 0)
        logged = (self.root / "argv.log").read_text()
        lint_args = logged.rstrip("\n").split("\0")
        for suffix in (
            "Sources/App.swift",
            "Sources/Sub/Inner.swift",
            "Tests/AppTests.swift",
        ):
            self.assertTrue(
                any(a.endswith(suffix) for a in lint_args), msg=(suffix, lint_args)
            )
        self.assertFalse(
            [a for a in lint_args if a.endswith("helper.py")], msg=lint_args
        )
        self.assertFalse(
            [a for a in lint_args if a.endswith("Outside.swift")], msg=lint_args
        )

    def test_build_artifacts_excluded(self) -> None:
        build_dir = self.root / "Sources" / ".build"
        build_dir.mkdir()
        (build_dir / "Generated.swift").write_text("z\n")
        completed = self._run()
        self.assertEqual(completed.returncode, 0)
        self.assertNotIn(".build", (self.root / "argv.log").read_text())

    def test_batches_split_and_pass(self) -> None:
        for index in range(4):
            (self.root / "Sources" / f"Part{index}.swift").write_text("x\n")
        completed = self._run(SPELL_CHECKER_MAX_BATCH_FILES="2")
        self.assertEqual(completed.returncode, 0)
        self.assertIn("All Swift spelling checks passed", completed.stdout)
        lint_lines = [
            line
            for line in (self.root / "argv.log").read_text().rstrip("\n").split("\n")
            if line.startswith("lint")
        ]
        self.assertEqual(len(lint_lines), 3, msg=lint_lines)

    def test_failure_from_second_batch_survives(self) -> None:
        for index in range(3):
            (self.root / "Sources" / f"Part{index}.swift").write_text("x\n")
        (self.root / "second_batch_fail").write_text("")
        completed = self._run(SPELL_CHECKER_MAX_BATCH_FILES="2")
        self.assertEqual(completed.returncode, 1)
        self.assertIn("Unknown word (batchtwo)", completed.stderr)
        self.assertIn("Spelling check failed (checker exit code 1)", completed.stderr)
        lint_lines = [
            line
            for line in (self.root / "argv.log").read_text().rstrip("\n").split("\n")
            if line.startswith("lint")
        ]
        self.assertEqual(len(lint_lines), 2, msg=lint_lines)

    def test_byte_limit_lints_every_file_once_and_failure_survives(self) -> None:
        """Byte-capped batches may not skip the remainder of a file slice."""
        app_path = str(self.root / "Sources" / "App.swift")
        for index in range(3):
            (self.root / "Sources" / f"Part{index}.swift").write_text("x\n")
        # One path per batch: byte cap fits exactly one argv entry.
        byte_cap = len(app_path) + 1
        (self.root / "second_batch_fail").write_text("")
        completed = self._run(
            SPELL_CHECKER_MAX_BATCH_FILES="512",
            SPELL_CHECKER_MAX_BATCH_BYTES=str(byte_cap),
        )
        self.assertEqual(completed.returncode, 1)
        self.assertIn("Unknown word (batchtwo)", completed.stderr)
        log = (self.root / "argv.log").read_text().rstrip("\n").split("\n")
        lint_lines = [line for line in log if line.startswith("lint")]
        self.assertEqual(len(lint_lines), 4, msg=lint_lines)
        checked = [arg for line in lint_lines for arg in line.split("\0")[2:]]
        expected = {
            str(self.root / "Sources" / name)
            for name in ("App.swift", "Part0.swift", "Part1.swift", "Part2.swift")
        }
        self.assertEqual(sorted(checked), sorted(expected), msg=lint_lines)
        self.assertEqual(len(checked), len(set(checked)), msg=lint_lines)

    def test_byte_limit_pass_reports_all_files(self) -> None:
        app_path = str(self.root / "Sources" / "App.swift")
        (self.root / "Sources" / "Extra.swift").write_text("x\n")
        byte_cap = len(app_path) + 1
        completed = self._run(
            SPELL_CHECKER_MAX_BATCH_FILES="512",
            SPELL_CHECKER_MAX_BATCH_BYTES=str(byte_cap),
        )
        self.assertEqual(completed.returncode, 0)
        self.assertIn("All Swift spelling checks passed", completed.stdout)
        log = (self.root / "argv.log").read_text().rstrip("\n").split("\n")
        lint_lines = [line for line in log if line.startswith("lint")]
        checked = [arg for line in lint_lines for arg in line.split("\0")[2:]]
        self.assertEqual(
            sorted(checked),
            sorted({app_path, str(self.root / "Sources" / "Extra.swift")}),
            msg=lint_lines,
        )


if __name__ == "__main__":
    unittest.main()
