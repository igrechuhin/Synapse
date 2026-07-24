---
name: fix-docs
description: Use when the /cortex/fix orchestrator needs to fix the docs target (memory bank sync, timestamps, roadmap). Synchronises activeContext/progress/roadmap, fixes timestamps, validates with run_docs_gate(). Invoke for target=docs or as step 3 of target=all.
tools: mcp__cortex__*, Bash, Read, Edit, Grep
---

Sync memory bank, fix timestamps, run docs gate; write result.

## Resume Check (required)

Before Step 1, call `pipeline_handoff(operation="status", pipeline="fix")`.

- If `phases.docs == "completed"`: skip execution, return prior result.
- If `phases.docs == "failed"` or `phases.docs == "running"`: continue and re-run this phase.
- If `phases.docs == "pending"` or missing: continue normally.

Immediately before Step 1, call `pipeline_handoff(operation="mark_running", pipeline="fix", phase="docs")`.

1. **Read state**: read `.cortex/memory-bank/roadmap.md`, `activeContext.md`, `progress.md`. List `.cortex/plans/*.md` and cross-check against roadmap entries.
2. **Align**: ensure activeContext has completed work (not future); roadmap has future work only; progress is current. Write via `manage_file()` — never truncate. Fix mismatches: stale refs → update; `status:COMPLETE` plans not archived → call `plan(operation="archive_completed")`; missing plan files → correct entry.
3. **Timestamps**: read `cortex://validation` resource. If `timestamps_result.valid == false`, fix `YYYY-MM-DD` format errors in memory bank files and retry. Blocking.
4. **Docs gate**: call `run_docs_gate()` (max 3 iterations).
   - `docs_phase_passed: true` → write result.
   - `timestamps_result.valid == false` → fix and retry. Blocking.
   - `roadmap_sync_result.valid == false` only → fix, retry once. If still failing: non-blocking, set `roadmap_sync_warning:true`.
   - `DocsMemoryBankToolError "roadmap.md does not exist"` → check `manage_file(operation="metadata", file_name="roadmap.md")`. If `file_exists:true`, bridge false-negative, continue. If `false`, blocking.
5. **Write result** to `.cortex/.session/current-task.json` then call `pipeline_handoff()`:

```json
{"operation":"write","phase":"docs","pipeline":"fix","status":"passed or failed","fix_iterations":<n>,"docs_phase_passed":<bool>,"roadmap_sync_warning":<bool>}
```

Report: Docs gate ✅/⚠️/❌ · Fix iterations `<n>` · Changes: list
