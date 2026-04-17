#!/usr/bin/env python3
"""CI/local entrypoint: validate internal markdown links in docs and policy files.

Delegates to ``cortex.tools.files.markdown_link_validation`` (single implementation
shared with the Phase A markdown check). Run from repository root:

    .venv/bin/python .cortex/synapse/scripts/python/check_markdown_links.py
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from cortex.tools.files.markdown_link_validation import run_cli
except ImportError:
    _repo_root = Path(__file__).resolve().parents[4]
    sys.path.insert(0, str(_repo_root / "src"))
    from cortex.tools.files.markdown_link_validation import run_cli


if __name__ == "__main__":
    raise SystemExit(run_cli())
