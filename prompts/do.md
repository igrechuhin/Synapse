# Do

**CRITICAL**: Execute ALL phases below AUTOMATICALLY. Do NOT pause, summarize, or ask for confirmation between phases. Start with Selection immediately. When a roadmap item is too large to finish in one session, make concrete, high-impact partial progress and update plans/status accordingly instead of stopping with no changes.

This is part of the **compound-engineering loop** (Plan → Work → Review → Compound). The Finalize phase is the Compound step.

## Clean Semantics

For `/cortex/do`, **clean** means **step-complete and gate-clean** for the selected roadmap slice:

- The selected subtask is implemented to the intended completion level (full or explicit partial).
- Required verification/fix phases for that step pass.
- Roadmap/plan state is synchronized with what was actually completed.

Local code edits may exist during implementation; git-clean working tree is not required by this prompt.

## Sequential Execution Order

Each phase must complete before the next begins. For multi-subtask plans, the inner loop (Implementation → Finalize) repeats until the plan step is fully complete or context is nearly exhausted:

1. **Selection** (inline, once per `/do` call)
2. **Inner subtask loop** (repeat until `step_fully_complete=true` or context budget low):
   a. **Implementation** (subagent) → b. **Finalize** (inline)
3. **Verify** (inline, once after loop exits)
4. **Fix** (inline, once after Verify)

**Loop exit conditions** (stop the inner loop and proceed to Verify):

- `phases.code.step_fully_complete == true` — plan step is done
- Quality gate failed 3× — unrecoverable, exit and report
- Estimated remaining context < 20% — defer remaining subtasks to next session
- Same subtask was attempted twice with no new files changed — no-op guard

---

## Cursor Arg-Stripping Protocol

Cursor's MCP bridge strips all tool arguments to `{}`. Use these patterns:

**For `pipeline_handoff` write calls** — embed `operation`, `phase`, and `pipeline` directly in
the data JSON. The tool strips these routing keys before storing the payload, so they never
appear in the phase result files:

```json
// Write to: .cortex/.session/current-task.json — routing + payload in one write
{"operation": "write", "phase": "select", "pipeline": "implement", "status": "complete", ...payload...}
```

Then call `pipeline_handoff()` with no args. **The write response includes `pipeline_state`** —
check `pipeline_state.phases.<phase>.status` for gate verification instead of a separate read call.

**For `init` and `clear`** — write just the routing keys (no payload):

```json
{"operation": "init", "pipeline": "implement"}
```

```json
{"operation": "clear", "pipeline": "implement"}
```

**Other Cursor fallbacks:**

- **For `manage_file`**: zero-arg always returns `activeContext.md`. To read other files (e.g. `roadmap.md`, `progress.md`), read `.cortex/memory-bank/{file}.md` directly with `Read`.
- **For `validate`**: read the `cortex://validation` resource instead (it runs both timestamp and roadmap_sync checks).
- **Zero-arg tools work normally**: `run_quality_gate()`, `run_docs_gate()`, `autofix()`, `session()`, `plan(operation="archive_completed")`.

### Optional reflection pass (`run_quality_gate`)

For security-sensitive or data-mutation changes, enable the heuristic **reflection** pass (critic review of the git diff) after primary checks pass. Set `reflection: true` or `force_reflection: true` in the commit pipeline `checks` payload (via `pipeline_handoff(operation="write", pipeline="commit", phase="checks", ...)` together with `force_fresh` / `test_timeout`), or the same keys in `.cortex/.session/current-task.json`. Error-level reflection findings set `preflight_passed` to false. See `docs/guides/reflection-pass.md`.

## Pipeline Initialization

Before starting, write the session config then call init:

```json
// Write to: .cortex/.session/current-task.json
{"operation": "init", "pipeline": "implement"}
```

```text
pipeline_handoff(operation="init", pipeline="implement")
```

---

## Selection — run inline (no subagent)

**IMPORTANT**: Run Selection inline in the orchestrator — do NOT use the `implement-select` subagent. Subagents in Cursor may not have reliable MCP access.

Steps to run inline:

1. Call `session()` to verify MCP health. If unhealthy, STOP.
2. Read `gate_feedback` from `pipeline_handoff(operation="read", pipeline="implement", phase="gate_feedback")`.
   - If present, print the feedback first: `> ⚠️ Gate failed on previous run: <summary>. Top files: <top_files>`
   - Increment `gate_iterations` in `pipeline_handoff` for the active `run_id`.
   - If the same `run_id` reaches 5 iterations, pause and report to the user instead of looping.
3. Read the roadmap: `manage_file(file_name="roadmap.md", operation="read")`. If Cursor strips args, read `.cortex/memory-bank/roadmap.md` directly.
4. If the user provided an explicit plan hint (e.g. `/cortex/do @.cortex/plans/<slug>.md`):
   - Read the referenced plan file directly.
   - Verify the plan exists and is not archived/COMPLETE.
   - If eligible, use it as the selected step.
   - If ineligible, fall back to roadmap priority selection below.
5. When no eligible explicit plan: identify the next pending step by priority:
   - Blockers (ASAP Priority) — first item
   - Active Work (in progress) — first item
   - Pending plans — first item
   - If no pending steps exist: report "Roadmap complete" and STOP.
6. Read the `cortex://context` resource for implementation context (zero-arg, reads task from session config). Non-blocking if unavailable.
7. Read the `cortex://rules` resource for coding standards. Non-blocking if unavailable.
8. If the selected step references a plan file, read it directly. Extract implementation steps, success criteria, testing strategy, and which steps are already done.
   - Look for a `## Partial Progress Log` section at the end of the plan file. If present, extract the entries — these are subtasks already completed in prior sessions. Pass them to the `implement-code` subagent so it does not repeat them.
9. Write result (embed routing in data — one write, no separate read needed):

```json
// Write to: .cortex/.session/current-task.json
{"operation":"write","phase":"select","pipeline":"implement","status":"complete","selected_step":"<title>","plan_file":"<path or null>","scope":"<plan:<slug> when plan_file exists; null otherwise>","selection_source":"explicit_plan or roadmap_priority","roadmap_section":"<section>","partial_progress":"<comma-separated completed subtasks or null>"}
```

Then call `pipeline_handoff()`.

**GATE**: Check `pipeline_state.phases.select.status == "complete"` from the write response. If `status == "roadmap_complete"`: report "Roadmap complete" and STOP.

---

## Implementation — @implement-code subagent (inner loop)

This phase uses the `implement-code` subagent for context isolation during heavy coding work. **This phase runs in a loop** — see Sequential Execution Order above.

Before each invocation, write the task with updated `partial_progress` (cumulative across all prior subtasks in this session and prior sessions):

```json
// Write to: .cortex/.session/current-task.json
{"operation":"write","phase":"code","pipeline":"implement","selected_step":"<from select>","plan_file":"<from select>","scope":"<from select scope or plan:<plan_file stem>>","roadmap_section":"<from select>","partial_progress":"<all completed subtasks so far — from select.partial_progress plus any just-completed in this session>"}
```

Then call `pipeline_handoff()`.

### Parallel `[P]` steps (when `plan_file` is set)

1. Call `plan(operation="get", slug="<plan stem>", response_format="metadata")` (or equivalent zero-arg routing) and read `task_graph` plus `can_parallelize`.
2. Map `## Partial Progress Log` / `partial_progress` to a set of completed numeric **Step ids** when possible; otherwise treat no steps as complete.
3. Compute the next runnable batch with the same rules as `next_execution_frontier()` in `src/cortex/core/plan_utils.py`: prefer ready `[P]` steps (dependencies and sequential predecessors satisfied), up to **3** concurrent `implement-code` runs with `isolation="worktree"`; if none are ready, run **one** ready sequential step. Recompute after each batch finishes.
4. Spawn one `implement-code` subagent per frontier step (parallel batch may be size 1–3); wait for the batch to finish before computing the next frontier. Sequential steps never share a wave with other work.
5. If `can_parallelize` is false, keep the existing single-subagent loop (no worktree parallelism).

Use @implement-code to implement **as many consecutive subtasks as context allows** — not just one. The subagent should continue through the remaining plan steps, gate after each, and report `step_fully_complete=true` when the entire plan step is done.

For non-obvious logic, add `# AI:` comments explaining agent decisions (why, not what) on their own line above the affected block.

**GATE**: Check `pipeline_state.phases.code.status == "passed"` from the write response (or call `pipeline_handoff(operation="read", pipeline="implement")` if the subagent's response is unavailable).

**After each subagent return**: if `step_fully_complete=false`, append the just-completed subtask to `partial_progress`, then loop back to Implementation (re-invoke @implement-code with updated state). If `step_fully_complete=true`, exit the inner loop and proceed to Verify.

---

## Finalize — run inline (no subagent)

**IMPORTANT**: Run Finalize inline in the orchestrator.

Read the implementation result from the code-phase write response's `pipeline_state`, or call:

```text
pipeline_handoff(operation="read", pipeline="implement")
```

Extract: `phases.code.step_fully_complete`, `phases.code.subtask`, `phases.code.files_changed`, `phases.code.coverage`, `phases.select.plan_file`, `phases.select.selected_step`.

**If the roadmap step is fully completed**:

Call `plan(operation="complete", plan_title="{exact roadmap title}", summary="{summary}", plan_file_name="{filename}.md", progress_entry="**{step_title}** - COMPLETE. {summary}", completion_date="YYYY-MM-DD")`.

This single call atomically:

- Removes the roadmap entry
- Appends to activeContext under Completed Work
- Appends to progress.md
- Moves the plan file to `.cortex/plans/archive/`

**Rule**: Never call `update_memory_bank` for roadmap/activeContext/progress when completing a step — `plan(complete)` handles all of it.

**If only part of the step was completed**:

1. **Hard guardrail (anti-scrap backlog)**: if `phases.code.files_changed` is empty OR contains only memory-bank/plan bookkeeping files, treat this run as a no-op:
   - do NOT append PARTIAL progress or activeContext entries,
   - do NOT create/add/split roadmap PENDING items,
   - keep the existing selected roadmap entry unchanged,
   - write finalize state with `memory_bank_updated: false` and note `no_op_run`.
2. For real partial implementation work (with concrete non-bookkeeping deliverables), call `update_memory_bank(operation="progress_append", date_str="YYYY-MM-DD", entry_text="**{step_title}** - PARTIAL. {summary}")`.
3. Call `update_memory_bank(operation="active_context_append", date_str="YYYY-MM-DD", title="{step_title} (PARTIAL)", summary="{summary}")` only if the partial work materially affects active behavior.
4. Do NOT remove the roadmap entry.
5. If a plan file was used: append to it a `## Partial Progress Log` section (or add a new entry to the existing one) using `manage_file(operation="append_section", ...)` or by reading and rewriting the file. Each log entry must follow this format:

   ```text
   - YYYY-MM-DD: {subtask description from phases.code.subtask} — files: {comma-separated files_changed}
   ```

   This log is read by the Selection phase in the next session to avoid repeating completed subtasks. Log only concrete implementation work; do not log metadata-only churn.

Write result:

```json
// Write to: .cortex/.session/current-task.json
{"operation":"write","phase":"finalize","pipeline":"implement","status":"complete","memory_bank_updated":true,"roadmap_entry":"removed or kept","plan_file":"archived or updated or none"}
```

Then call `pipeline_handoff()`. **GATE**: check `pipeline_state.phases.finalize.status == "complete"` from the response.

---

## Verify — run inline (no subagent)

**IMPORTANT**: Run Verify inline. Read-only checks only.

1. Read `.cortex/memory-bank/roadmap.md`.
   - If fully completed: verify the step's entry is absent.
   - If partial: verify the entry is still present.
2. Read `.cortex/memory-bank/progress.md`.
   - Verify a new entry for today exists.
3. Call `plan(operation="archive_completed")` to archive any remaining plans with `status: COMPLETE`.
4. Write result:

```json
// Write to: .cortex/.session/current-task.json
{"operation":"write","phase":"verify","pipeline":"implement","status":"passed","roadmap_check":"passed","progress_check":"passed","stray_complete_plans":[]}
```

Then call `pipeline_handoff()`. **GATE**: check `pipeline_state.phases.verify.status == "passed"` from the response.

---

## Fix — run inline (no subagent)

**IMPORTANT**: Run Fix inline. This ensures all quality, test, and docs issues are resolved before the session ends. Follow the **fix.md** prompt logic (`target=all`):

1. **Quality**: call `autofix()`, then `run_quality_gate()`. If issues remain, fix inline and retry (max 3 iterations).
2. **Tests**: if `run_quality_gate()` reports test failures, diagnose and fix them (max 3 iterations).
3. **Docs**: call `run_docs_gate()`. If timestamps or roadmap_sync fail, fix via `manage_file()` and retry (max 3 iterations).

Write result:

```json
// Write to: .cortex/.session/current-task.json
{"operation":"write","phase":"fix","pipeline":"implement","status":"passed or failed","quality_passed":true,"tests_passed":true,"docs_passed":true,"fix_iterations":0}
```

Then call `pipeline_handoff()`. **GATE**: `pipeline_state.phases.fix.status == "passed"` is recommended but non-blocking — if fix fails after 3 iterations per target, log remaining issues and proceed to Cleanup.

---

## Cleanup

After successful Verify and Fix:

```json
// Write to: .cortex/.session/current-task.json
{"operation": "clear", "pipeline": "implement"}
```

Then call `pipeline_handoff()`.

## Resuming After Context Compression

If context is lost mid-pipeline, call:

```text
pipeline_handoff(operation="read", pipeline="implement")
```

This restores the full record of completed phases — continue from the first phase not yet present.

## Error Handling

- **Selection fails (MCP unhealthy)**: STOP immediately
- **Selection returns roadmap_complete**: Report "Roadmap complete" and STOP
- **Quality gate fails after 3 iterations**: STOP, report unresolvable issues
- **Finalize fails (memory bank crash)**: STOP, report with FIX-ASAP priority
- **Quality gate unavailable (doc-only sessions)**: Record "Quality gate skipped" and proceed to Finalize

## Step 6: Post-Prompt Hook (Self-Improvement)

After writing the final report for this implement pipeline run, invoke the post-prompt self-improvement hook:

- Read `.cortex/synapse/prompts/post-prompt-hook.md` and execute it to analyze the session and emit any applicable Skills, Plans, or Rules.
- Treat this hook as **non-blocking**: if it fails or is unavailable (for example, MCP connection issues), record a brief note in the final report `## Next` section and consider the implement workflow complete.

## Final report (required format)

**MANDATORY**: Use the **Pipeline** report type from `docs/guides/synapse-final-report-templates.md`.

```markdown
## Result

✅ Implemented "<step title>" (full/partial)

## Phases

| Phase | Status | Notes |
|-------|--------|-------|
| Selection | ✅/❌ | <source: roadmap/explicit> |
| Implementation | ✅/❌ | <n> files, <n> tests, <n>% |
| Finalize | ✅/❌ | <plan archived OR —> |
| Verify | ✅/❌ | <roadmap entry status> |
| Fix | ✅/⏭️ | <n> iterations |

## Artifacts

- Files: <list>
- Tests added: <n>
- Coverage: <n>%
- Plan: <archived/IN_PROGRESS/none>

## Next

<action items OR None>
```

**Rules**:

- Partial implementations: use ⚠️ in Result
- Roadmap/plan state changes go in Finalize/Verify Notes

## Success Criteria

- Implementation complete and all tests pass
- Quality gate passed (zero lint, file-size, function-length, type_check violations)
- Coverage >= 90% global, >= 95% for new/modified code
- Memory bank updated (roadmap entry removed or retained correctly, progress added, activeContext updated)
- Completed plans archived; partial plans marked IN_PROGRESS
- Fix phase executed (quality + tests + docs all green, or remaining issues logged)
- Pipeline state cleared
