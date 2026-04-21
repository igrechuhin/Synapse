---
name: commit-phase-b
description: Use when the /cortex/commit orchestrator reaches Phase B (documentation) after Phase A passes. Updates activeContext.md, progress.md, roadmap.md; archives completed plans; runs run_docs_gate(). This is the Compound step of the engineering loop.
---

You are the documentation and state management specialist. Update the memory bank, archive completed plans, and validate docs. Complete all steps below and report results via `pipeline_handoff`.

## Step 0: Read handoff context

Call `pipeline_handoff(operation="read", pipeline="commit", phase="checks")`. Confirm `phases.checks.status == "passed"` before proceeding.

## Resume Check (required)

Before Step 1, call `pipeline_handoff(operation="status", pipeline="commit")`.

- If `phases.docs == "completed"`: skip execution, return prior result.
- If `phases.docs == "failed"` or `phases.docs == "running"`: continue and re-run this phase.
- If `phases.docs == "pending"` or missing: continue normally.

Immediately before Step 1, call `pipeline_handoff(operation="mark_running", pipeline="commit", phase="docs")`.

## Step 1: Load memory bank

Read current state:

- `manage_file(file_name="activeContext.md", operation="read")`
- `manage_file(file_name="progress.md", operation="read")`
- `manage_file(file_name="roadmap.md", operation="read")`

If Cursor strips args (zero-arg returns only activeContext), read `.cortex/memory-bank/progress.md` and `.cortex/memory-bank/roadmap.md` directly via `Read`.

## Step 2: Update memory bank

Update files to reflect current changes:

- `activeContext.md`: record what was accomplished this session (completed work, findings).
- `progress.md`: update recent activity and metrics.
- `roadmap.md`: move completed items out; update status of in-progress items.

Write via `manage_file(file_name="...", operation="write", content="...", change_description="...")`. If args are stripped, write `.cortex/memory-bank/` files directly — but **never truncate**: new content must be at least as long as the content as read.

**Recovery**: if a previous write accidentally used truncated content, restore the full original by reading from version control (`git show HEAD:.cortex/memory-bank/roadmap.md`), append the intended new entry, then write the complete result.

**Roadmap discipline**: completed items go to `activeContext.md`; remove them from `roadmap.md`.

## Step 3: Archive completed plans

Call `plan(operation="archive_completed")`. This scans `.cortex/plans/` for `status: COMPLETE`, moves them to archive, and removes their roadmap entries. Record plans archived count (even if 0).

## Step 4: Auto-fix markdown

Call `autofix()` to fix any markdown lint issues introduced by Steps 2–3 (trailing spaces, blank lines, duplicate headings).

## Step 5: Run docs gate

Call `run_docs_gate()` — zero-arg MCP tool for Phase B docs/memory-bank validation.

Parse the response:

- `docs_phase_passed: true` → proceed to Step 6.
- `docs_phase_passed: false`:
  - If `timestamps_result.valid == false`: fix timestamp format errors via `manage_file()`, retry `run_docs_gate()`. **Blocking.**
  - If only `roadmap_sync_result.valid == false` (timestamps pass): non-blocking warning — record it and continue.

## Step 6: Write result

```json
{"operation":"write","phase":"docs","pipeline":"commit","status":"complete","memory_bank_updated":true,"docs_phase_passed":true,"plans_archived":0,"roadmap_sync_warning":false}
```

Write to `.cortex/.session/current-task.json`, then call `pipeline_handoff()`. Check `pipeline_state.phases.docs.status == "complete"`.

## Report

Respond with:

- Memory bank: ✅ updated / ❌ error
- Plans archived: `<n>`
- Docs gate: ✅ passed / ⚠️ roadmap_sync warning / ❌ failed
