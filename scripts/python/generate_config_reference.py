#!/usr/bin/env python3
"""Generate configuration reference defaults from Pydantic models and default dicts.

Writes docs/api/config-defaults.json with current default values for
validation, optimization, and structure config. Run from project root:

    uv run python .cortex/synapse/scripts/python/generate_config_reference.py

Used to keep docs/api/configuration-reference.md in sync with source.
"""

from __future__ import annotations

import json
import sys
from enum import Enum
from pathlib import Path
from typing import Any, cast

try:
    from _utils import get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _utils import get_project_root

_PROJECT_ROOT = get_project_root(Path(__file__))
if str(_PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "src"))


def _serialize(obj: object) -> Any:
    """Convert Pydantic models and enums to JSON-serializable form."""
    if hasattr(obj, "model_dump"):
        raw = cast("Any", obj).model_dump(mode="python")
        d = cast("dict[str, Any]", raw)
        return {str(k): _serialize(v) for k, v in d.items()}
    if isinstance(obj, dict):
        d: dict[str, Any] = cast("dict[str, Any]", obj)
        return {str(k): _serialize(v) for k, v in d.items()}
    if isinstance(obj, list):
        lst: list[Any] = cast("list[Any]", obj)
        return [_serialize(v) for v in lst]
    if isinstance(obj, Enum):
        return obj.value
    return obj


def main() -> int:
    """Dump default configs to docs/api/config-defaults.json."""
    from cortex.optimization.optimization_config import DEFAULT_OPTIMIZATION_CONFIG
    from cortex.structure.structure_config import DEFAULT_STRUCTURE
    from cortex.tools.tool_categories import build_category_config
    from cortex.validation.models import ValidationConfigModel

    out_path = _PROJECT_ROOT / "docs" / "api" / "config-defaults.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    validation_defaults = ValidationConfigModel().model_dump(mode="python")
    # optimization: use DEFAULT_OPTIMIZATION_CONFIG (source of truth for loader)
    # inject tool_search like OptimizationConfig._load_config() does
    opt = dict(DEFAULT_OPTIMIZATION_CONFIG)
    opt["tool_search"] = build_category_config().model_dump()
    optimization_defaults = _serialize(opt)
    structure_defaults = _serialize(DEFAULT_STRUCTURE)

    payload = {
        "validation": validation_defaults,
        "optimization": optimization_defaults,
        "structure": structure_defaults,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
