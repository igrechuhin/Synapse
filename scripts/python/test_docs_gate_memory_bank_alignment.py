#!/usr/bin/env python3
"""Regression tests for docs-gate memory-bank alignment behavior."""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from cortex.core.context_logging import MCPContext
from cortex.core.models import ModelDict
from cortex.tools.execution.pre_commit_docs_memory_helpers import (
    run_docs_and_memory_bank_sync_impl,
)
from cortex.tools.validation.operations import ValidateCheckTypeName


class DocsGateMemoryBankAlignmentTests(unittest.IsolatedAsyncioTestCase):
    """Validate docs-gate behavior when roadmap lookup diagnostics disagree."""

    async def test_run_docs_gate_downgrades_false_missing_roadmap_error(self) -> None:
        timestamps_result: ModelDict = {"status": "success", "valid": True}
        roadmap_error: ModelDict = {
            "status": "error",
            "check_type": "roadmap_sync",
            "error": "roadmap.md does not exist in memory bank",
        }
        diagnostics: ModelDict = {
            "project_root": "/tmp/project",
            "memory_bank_root": "/tmp/project/.cortex/memory-bank",
            "roadmap_lookup_path": "/tmp/project/.cortex/memory-bank/roadmap.md",
            "roadmap_exists": True,
        }

        async def fake_run_single_validation(
            check_type_name: ValidateCheckTypeName, _ctx: MCPContext | None
        ) -> ModelDict:
            check_name = str(getattr(check_type_name, "value", check_type_name))
            if check_name == "timestamps":
                return timestamps_result
            return roadmap_error

        with (
            patch(
                "cortex.tools.execution.pre_commit_docs_memory_helpers.run_single_validation",
                side_effect=fake_run_single_validation,
            ),
            patch(
                "cortex.tools.execution.pre_commit_docs_memory_helpers._memory_bank_resolution_diagnostics",
                new=AsyncMock(return_value=diagnostics),
            ),
            patch(
                "cortex.tools.execution.pre_commit_docs_memory_helpers._roadmap_progress_consistency_violations",
                new=AsyncMock(return_value=[]),
            ),
        ):
            result = await run_docs_and_memory_bank_sync_impl(ctx=None)

        self.assertNotIn("error_type", result)
        roadmap_result_raw = result["roadmap_sync_result"]
        assert isinstance(roadmap_result_raw, dict)
        roadmap_result: ModelDict = roadmap_result_raw
        self.assertEqual(roadmap_result["status"], "success")
        self.assertFalse(roadmap_result["valid"])
        memory_bank_resolution_raw = roadmap_result["memory_bank_resolution"]
        assert isinstance(memory_bank_resolution_raw, dict)
        self.assertEqual(
            memory_bank_resolution_raw["roadmap_lookup_path"],
            diagnostics["roadmap_lookup_path"],
        )

    async def test_run_docs_gate_keeps_tool_error_when_roadmap_absent(self) -> None:
        timestamps_result: ModelDict = {"status": "success", "valid": True}
        roadmap_error: ModelDict = {
            "status": "error",
            "check_type": "roadmap_sync",
            "error": "roadmap.md does not exist in memory bank",
        }
        diagnostics: ModelDict = {
            "project_root": "/tmp/project",
            "memory_bank_root": "/tmp/project/.cortex/memory-bank",
            "roadmap_lookup_path": "/tmp/project/.cortex/memory-bank/roadmap.md",
            "roadmap_exists": False,
        }

        async def fake_run_single_validation(
            check_type_name: ValidateCheckTypeName, _ctx: MCPContext | None
        ) -> ModelDict:
            check_name = str(getattr(check_type_name, "value", check_type_name))
            if check_name == "timestamps":
                return timestamps_result
            return roadmap_error

        with (
            patch(
                "cortex.tools.execution.pre_commit_docs_memory_helpers.run_single_validation",
                side_effect=fake_run_single_validation,
            ),
            patch(
                "cortex.tools.execution.pre_commit_docs_memory_helpers._memory_bank_resolution_diagnostics",
                new=AsyncMock(return_value=diagnostics),
            ),
            patch(
                "cortex.tools.execution.pre_commit_docs_memory_helpers._roadmap_progress_consistency_violations",
                new=AsyncMock(return_value=[]),
            ),
        ):
            result = await run_docs_and_memory_bank_sync_impl(ctx=None)

        self.assertEqual(result["error_type"], "DocsMemoryBankToolError")
        roadmap_result_raw = result["roadmap_sync_result"]
        assert isinstance(roadmap_result_raw, dict)
        memory_bank_resolution_raw = roadmap_result_raw["memory_bank_resolution"]
        assert isinstance(memory_bank_resolution_raw, dict)
        self.assertEqual(
            memory_bank_resolution_raw["roadmap_exists"],
            diagnostics["roadmap_exists"],
        )


if __name__ == "__main__":
    _ = unittest.main()
