---
name: shared-conventions
description: Shared conventions reference for all orchestration prompts and agents. Defines severity levels, pre-flight protocol, path resolution, tooling preferences, and session model. Referenced by prompts instead of inline duplication.
---

# Shared Conventions

This document defines conventions shared by all orchestration prompts and agents. Prompts reference this file instead of duplicating definitions inline.

## Severity Levels

All prompts and agents use three severity tiers:

- **GATE**: Blocks pipeline/workflow. Failure means stop. Do not proceed until resolved.
- **CHECK**: Requires explicit verification. Parse output and confirm before proceeding.
- **PREFER**: Best practice. Recommended but non-blocking.

Do NOT use: CRITICAL, MANDATORY, ABSOLUTE BLOCK, NO EXCEPTIONS, ZERO TOLERANCE, or other ad-hoc emphasis. Map all severity to GATE/CHECK/PREFER.

## Session Model

Each prompt (commit, review, implement, plan, analyze, fix) runs in an **independent agent session**. No agent state carries between sessions.

- The **memory bank** (roadmap.md, activeContext.md, progress.md, etc.) is the sole inter-session continuity mechanism.
- Prompts must NOT assume access to outputs from other prompts or prior sessions.
- Within a session, pipeline-state-tracker or commit-state-tracker may be used for intra-session checkpointing to survive context compression.
- The `analyze` compound step at the end of commit is the mechanism that feeds learning back for the next session cycle.

## Standard Pre-Flight Protocol

Every orchestration prompt begins with this protocol:

1. **Delegate to `common-checklist` agent** — loads project structure, memory bank files, rules, and detects primary language.
2. **Verify** the agent returns `status: "complete"`. If `status: "error"`, STOP and report.
3. **Delegate to `agent-health-checker` agent** — pass all agent filenames required by the prompt. Verify `status: "passed"`.
4. **GATE**: If health check returns `status: "failed"`, STOP and report missing agents. Do not proceed with partial agent set.

After pre-flight passes, continue directly to execution steps without pausing for user confirmation.

## Path Resolution

- **GATE**: All paths must be resolved dynamically via Cortex MCP tools.
- Use `get_structure_info()` for plans, memory bank, reviews, rules, and project root paths.
- Use `manage_file()` for reading/writing memory bank files.
- **Never hardcode** `.cortex/`, `structure_info.root`, or memory-bank paths.
- Use canonical absolute paths returned by MCP tools only.

## Tooling Preferences

- Use **Cortex MCP tools** for all memory bank, rules, validation, and structure operations.
- Use **standard IDE tools** (`Read`, `Write`, `Glob`, `Grep`, `Edit`) for code and file operations. See Agent Tool Mapping below for per-agent equivalents.
- **Do NOT** run language-specific formatters/linters/test runners directly (e.g., `black`, `ruff`, `pytest`). Use `execute_pre_commit_checks()` or `autofix()` instead.
- Shell commands are a last resort when MCP tools and IDE tools are both unavailable.

## Agent Tool Mapping

| Operation        | Generic Name       | Cursor              | Claude Code |
|------------------|--------------------|---------------------|------------|
| Read file        | Read               | Read                | Read       |
| Edit file        | Edit               | ApplyPatch/StrReplace | Edit     |
| Write file       | Write              | Write               | Write      |
| List/find files  | Glob               | LS/Glob             | Glob       |
| Search content   | Grep               | Grep                | Grep       |

Prompts use generic names. Agents should map to their available tools.

## Max-Retry Limits

All fix loops and retry mechanisms must have explicit bounds:

- **Fix loops** (fix -> re-run -> verify): Maximum **3 iterations**. After 3 failed attempts, STOP and report unresolvable issues. **Convergence check**: If iteration 2 violation count >= iteration 1 count, abort early — the loop is oscillating and will not converge.
- **MCP connection retries**: Maximum **2 retries** (automatic wrapper handles first retry; manual retry is the second). After exhaustion, use fallback or STOP.
- **Test retries**: No retries. Tests either pass or the pipeline stops.

## Circuit-Breaker Pattern

When **3 consecutive MCP tool calls fail** (across any steps in the current pipeline):

1. **Persist pipeline state** via `checkpoint_write` with `status: "circuit_breaker_tripped"` and `last_successful_step`.
2. **Report to user**: "MCP circuit-breaker tripped after 3 consecutive failures. Pipeline state saved. To resume: re-run the pipeline — it will pick up from step {last_successful_step + 1}."
3. **Do NOT** continue executing remaining steps.
4. **Do NOT** attempt to roll back completed steps (they are already checkpointed).

**Counter reset**: The failure counter resets to 0 after any successful MCP tool call.

**Staleness guard**: Pipeline state files include a `started_at` timestamp. Ignore state files older than 1 hour when resuming.

## Memory Bank Contract

See `memory-bank-contract.md` for the complete write discipline. Key rules:

- **Allowed write tools**: `manage_file(operation="write")`, `add_roadmap_entry`, `remove_roadmap_entry`, `update_memory_bank`
- **Forbidden write tools**: file-write/edit tools (`Write`, `Edit`, and agent-specific equivalents) used directly on memory bank paths
- Post-write verification is mandatory for roadmap.md edits
