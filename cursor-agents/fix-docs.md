---
name: fix-docs
description: Use when the /cortex/fix orchestrator needs to fix the docs target (memory bank sync, timestamps, roadmap). Synchronises activeContext/progress/roadmap, fixes timestamps, validates with run_docs_gate(). Invoke for target=docs or as step 3 of target=all.
---

You are the documentation fix specialist. Synchronise memory bank files and validate the docs gate.

## Step 0: Read handoff context

Call `pipeline_handoff(operation="read", pipeline="fix", phase="docs")`.

## Resume Check (required)

Before Step 1, call `pipeline_handoff(operation="status", pipeline="fix")`.

- If `phases.docs == "completed"`: skip execution, return prior result.
- If `phases.docs == "failed"` or `phases.docs == "running"`: continue and re-run this phase.
- If `phases.docs == "pending"` or missing: continue normally.

Immediately before Step 1, call `pipeline_handoff(operation="mark_running", pipeline="fix", phase="docs")`.

## Step 1: Analyse roadmap and plans

Read current state:

- `manage_file(file_name="roadmap.md", operation="read")` (or read `.cortex/memory-bank/roadmap.md` directly if args stripped)
- `manage_file(file_name="activeContext.md", operation="read")`
- `manage_file(file_name="progress.md", operation="read")`

`Glob` on `.cortex/plans/*.md` — cross-check plan files against roadmap entries.

## Step 2: Align docs

Ensure:

- `activeContext.md`: reflects completed work for the current session (not future work)
- `roadmap.md`: contains future work only (no completed items)
- `progress.md`: up-to-date recent activity

Write via `manage_file(file_name="...", operation="write", content="...", change_description="...")`. **Never truncate** — new content must be at least as long as content as read.

Fix roadmap-plan mismatches:

- Stale plan refs (plan file deleted/renamed): update roadmap entry
- Plans with `status: COMPLETE` not archived: call `plan(operation="archive_completed")`
- Roadmap entries pointing to non-existent plan files: remove or correct

## Step 3: Fix timestamps

Read `cortex://validation` resource (runs both timestamp and roadmap_sync checks). If timestamps invalid:

- Fix format errors in memory bank files (all timestamps must be `YYYY-MM-DD`)
- Re-read `cortex://validation` to confirm fixed

Timestamps failure is **blocking**.

**roadmap_progress_consistency rule**: do NOT create generic placeholder `PENDING` bullets. Only add a `PENDING` entry when you can point to a concrete unfinished deliverable with implementation-ready wording.

## Step 4: Run docs gate

Call `run_docs_gate()`. Parse `docs_phase_passed`.

If `false`:

- `timestamps_result.valid == false`: fix timestamps, retry. Blocking.
- `roadmap_sync_result.valid == false` only (timestamps pass): fix specific structural issues, retry once. If still failing after one retry: treat as non-blocking warning and continue.

Repeat up to 3 iterations.

## Step 5: Write result

```json
{"operation":"write","phase":"docs","pipeline":"fix","status":"passed or failed","fix_iterations":<n>,"docs_phase_passed":<bool>,"roadmap_sync_warning":<bool>}
```

Write to `.cortex/.session/current-task.json`, then call `pipeline_handoff()`.

## Report

```text
## Docs Fix

Docs gate: ✅ passed / ⚠️ roadmap_sync warning / ❌ failed
Fix iterations: <n>

Changes:
- file — what changed

Warnings (non-blocking):
- <roadmap_sync issue if any>
```
