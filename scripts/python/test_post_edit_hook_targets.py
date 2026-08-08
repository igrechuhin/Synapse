#!/usr/bin/env python3
"""Self-check for post_edit_hook target selection."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from post_edit_hook import _pytest_targets  # type: ignore[import-not-found,private-usage] # noqa: E402


def demo(tmp: Path) -> None:
    (tmp / "src/cortex/services").mkdir(parents=True)
    (tmp / "tests/services").mkdir(parents=True)
    (tmp / "src/cortex/services/thing.py").touch()
    (tmp / "tests/services/test_thing.py").touch()
    (tmp / "src/cortex/services/lonely.py").touch()
    (tmp / "tests/services/test_thing.py").touch()

    assert _pytest_targets(tmp, None) == []
    assert _pytest_targets(tmp, tmp / "notes.md") is None
    assert _pytest_targets(tmp, Path("/elsewhere/x.py")) is None
    assert _pytest_targets(tmp, tmp / ".cortex/scripts/php/run.py") is None
    assert _pytest_targets(tmp, tmp / "tests/services/test_thing.py") == [
        "tests/services/test_thing.py"
    ]
    assert _pytest_targets(tmp, tmp / "src/cortex/services/thing.py") == [
        "tests/services/test_thing.py"
    ]
    assert _pytest_targets(tmp, tmp / "src/cortex/services/lonely.py") == []
    print("ok")


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        demo(Path(d))
