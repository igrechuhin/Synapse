#!/usr/bin/env python3
"""Auto-fix PHP formatting issues.

Delegates to check_formatting.run_formatter in write mode so the probe order and
command construction stay in one place.

Configuration:
    PHP_FORMATTER:    Formatter binary (default: probe pint, php-cs-fixer)
    PHP_TOOL_TIMEOUT: Timeout in seconds (default: 120)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_formatting import run_formatter  # noqa: E402 # type: ignore[attr-defined]


def main() -> None:
    run_formatter(write=True)


if __name__ == "__main__":
    main()
