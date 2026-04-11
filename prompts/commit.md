# Commit Changes

**CRITICAL**: Execute ALL phases below AUTOMATICALLY. Do NOT pause, summarize, or ask for confirmation between phases. Start with Preflight immediately.

Phase B (Documentation) is the **compound** step of the engineering loop — it updates the memory bank so the next session can build on this work.

## Clean Semantics

For `/cortex/commit`, **clean** means **git-clean** for the commit scope:

- Superproject and required submodules have no unresolved working-tree drift for files included in the commit path.
- Submodule pointer (gitlink) is in sync with the intended submodule commit.
- Local edits are not considered clean until they are either committed (where required) or intentionally discarded/staged per workflow.

## Session Discipline

Use a single-goal session pattern to improve completion reliability (aligned with the superproject `CLAUDE.md` **Session Discipline** section):

- Confirm **one primary goal** early in the session and keep work scoped to that goal.
- If unrelated issues appear, note them and defer them to a separate follow-up session.
- If multiple unrelated fixes are already in progress, split execution into separate scoped passes instead of one mixed bundle.

**Step 13** below applies the **session scope split-commit hint** before commit creation: when staged changes mix unrelated goals, suggest splitting into separate commits when practical.

## Sequential Execution Order

Each phase must complete before the next begins:

1. **Preflight** → 2. **Phase A** → 3. **Phase B** → 4. **Phase C** → 5. **Step 12** → 6. **Step 13** → 7. **Step 14** → 8. **Step 15** → 9. **Step 16**

---

## Cursor Arg-Stripping Protocol

Cursor's MCP bridge strips all tool arguments to `{}`. Use these patterns:

**For `pipeline_handoff` write calls** — embed `operation`, `phase`, and `pipeline` directly in
the data JSON. The tool strips these routing keys before storing the payload:

```json
// Write to: .cortex/.session/current-task.json — routing + payload in one write
{"operation": "write", "phase": "<phase>", "pipeline": "commit", ...payload...}
```

Then call `pipeline_handoff()`. **The write response includes `pipeline_state`** —
check `pipeline_state.phases.<phase>.status` for gate verification instead of a separate read.

**For `init` and `clear`** — write just the routing keys:

```json
{"operation": "init", "pipeline": "commit"}
```

```json
{"operation": "clear", "pipeline": "commit"}
```

**Other Cursor fallbacks:**

- **For `manage_file`**: zero-arg always returns `activeContext.md`. To read other files (e.g. `roadmap.md`, `progress.md`), read `.cortex/memory-bank/{file}.md` directly with `Read`.
- **For `validate`**: read the `cortex://validation` resource instead (it runs both timestamp and roadmap_sync checks).
- **Zero-arg tools work normally**: `run_quality_gate()`, `run_docs_gate()`, `autofix()`, `session()`, `plan(operation="archive_completed")`.

## Pipeline Initialization

Before invoking Preflight, write the session config then call init:

```json
// Write to: .cortex/.session/current-task.json
{"operation": "init", "pipeline": "commit"}
```

```text
pipeline_handoff(operation="init", pipeline="commit")
```

This creates `.cortex/.session/{session_id}/commit/` where all phase inputs and outputs are stored.

---

## Preflight — @commit-preflight subagent

Use @commit-preflight to handle this phase. If the subagent is unavailable, run these steps inline:

1. Call `session()` to verify MCP health. If unhealthy, STOP.
2. Read `cortex://rules` resource for coding standards. Non-blocking if unavailable.
3. Run `git status` to confirm changes exist. If no changes, STOP.
4. Run `git stash create`. If a hash is returned, run `git stash store -m "cortex-commit-pipeline-snapshot" <hash>` and record it as `snapshot_ref`. If empty (clean tree), record `snapshot_ref = "HEAD"`. **Symlink fallback**: if `git stash create` fails with "beyond a symbolic link" (common when `.cortex/memory-bank` or `.cortex/plans` are symlinked in local workflows), record `snapshot_ref = "HEAD"` and continue — this is non-blocking.
5. **Synapse pre-stage (required before Phase A)**: Run `git -C .cortex/synapse status --short` (or `git submodule status`). If the synapse submodule shows `+` (OUT_OF_SYNC / pointer mismatch) or any dirty state:
   a. Run `git -C .cortex/synapse status --porcelain -- :/ :(exclude).cache` to check for real uncommitted changes.
   b. If dirty (excluding `.cache`): commit inside — `git -C .cortex/synapse add -A -- :/ :(exclude).cache && git -C .cortex/synapse commit -m "chore: update usage analytics"`.
   c. Stage the updated gitlink in the superproject: `git add .cortex/synapse`.
   This ensures Phase A's submodule hygiene check sees a clean, in-sync submodule.
6. Write result:

```json
// Write to: .cortex/.session/current-task.json
{"operation":"write","phase":"preflight","pipeline":"commit","status":"complete","snapshot_ref":"<value>","changes_detected":true}
```

Then call `pipeline_handoff()`. **GATE**: check `pipeline_state.phases.preflight.status == "complete"` from the response.

---

## Phase A: Pre-Commit Checks — @commit-phase-a subagent

Use @commit-phase-a to handle this phase. If the subagent is unavailable, run these steps inline:

1. Call `run_quality_gate()` — zero-arg MCP tool that runs Phase A end-to-end and returns full results. Do NOT use `start_quality_job` + `get_quality_job_status`; in Cursor's MCP bridge those calls receive empty `{}` args.
2. Parse the result: check `preflight_passed` (bool) and `coverage` (float).
3. If `preflight_passed: false`: call `autofix()`, then call `run_quality_gate()` again. Repeat up to 3 times.
4. **CI parity checks (mandatory before passing Phase A)**: even when `preflight_passed: true`, run parity scripts across all language subfolders, passing the changed file list via `FILES` so each script only checks files matching its own extension:

   ```bash
   CHANGED_FILES=$(git diff --name-only HEAD && git diff --name-only)
   for script in check_file_sizes.py check_function_lengths.py build.py; do
     find .cortex/synapse/scripts -mindepth 2 -maxdepth 2 -name "$script" | sort | \
       while read -r s; do FILES="$CHANGED_FILES" python3 "$s"; done
   done
   ```

   Each script's `_get_files_from_env()` filters by its own extension (`.py`, `.swift`, `.ts`, …). When `FILES` contains no files matching the script's language it exits 0 immediately — no directory-scan fallback is triggered.

   If any script exits non-zero, treat Phase A as failed, fix inline, and re-run `run_quality_gate()` (max 3 total iterations). Skip a script name only when no matching file exists.
5. Write result to pipeline state:

```json
// Write to: .cortex/.session/current-task.json
{"operation":"write","phase":"checks","pipeline":"commit","status":"passed or failed","coverage":0.0,"fix_iterations":0,"preflight_passed":true,"dirty_checks":{},"last_clean_results":{}}
```

Then call `pipeline_handoff()`. **GATE**: check `pipeline_state.phases.checks.status == "passed"` from the response.

**Validation rules for Phase A**:

- Treat the structured status in `phases.checks` as the **single source of truth** for Phase A.
- **Never** infer that Phase A passed from log snippets, banners (including any `"✅ All quality checks passed!"` messages), or previous runs.
- If the quality result reports any **failed** or **skipped** critical checks, Phase A is considered **failed** and the commit pipeline must **stop without creating a commit**.
- **Markdown lint failure**: Check `markdown_result.output` in the quality gate response for the exact violations (file:line and rule code). Call `autofix()` (which includes markdown auto-fix for fixable rules); if markdown errors remain (e.g. MD036 is not auto-fixable), apply manual fixes per **fix.md** and the violation details. Zero markdown errors required before Phase A can pass. **SwiftPM note**: if violations are in `.build/checkouts/**` (external Swift package dependency docs), these are suppressed by the Cortex quality gate's `.build` exclude — if they still appear, the Cortex server is outdated; update it.
- **Submodule hygiene failure**: If Phase A fails with `submodule_hygiene`, Preflight step 5 (synapse pre-stage) was not executed or did not complete. Go back and run Preflight step 5 now: commit any changes inside `.cortex/synapse` (excluding `.cache`), then `git add .cortex/synapse` in the superproject. Then retry `run_quality_gate()`.

---

## Phase B: Documentation and State — @commit-phase-b subagent

Use @commit-phase-b to handle this phase. If the subagent is unavailable, run these steps inline:

1. Read memory bank files: `manage_file(file_name="activeContext.md", operation="read")`, `manage_file(file_name="progress.md", operation="read")`, `manage_file(file_name="roadmap.md", operation="read")`. If Cursor strips args (zero-arg returns only activeContext), read `.cortex/memory-bank/progress.md` and `.cortex/memory-bank/roadmap.md` directly.
2. Update structured memory bank files using targeted mutations — **not** `manage_file(write)`:
   - activeContext: `update_memory_bank(operation="active_context_append", date_str="YYYY-MM-DD", title="...", summary="...")`
   - progress: `update_memory_bank(operation="progress_append", date_str="YYYY-MM-DD", title="...", summary="...")`
   - roadmap: `update_memory_bank(operation="roadmap_add/remove/remove_section", ...)`
   - `manage_file(write)` is for arbitrary wiki pages only (techContext.md, systemPatterns.md, etc.) — never use it for roadmap/progress/activeContext.
3. Archive completed plans: `plan(operation="archive_completed")` — scans `.cortex/plans/` for `status: COMPLETE`, moves to archive, removes roadmap entries.
4. Call `autofix()` to auto-fix markdown lint and memory-bank housekeeping issues in files modified by steps 2-3. This prevents Phase B writes from introducing CI-blocking markdown violations and auto-resolves deterministic memory-bank lint findings.
5. Call `run_docs_gate()` — zero-arg MCP tool for Phase B docs/memory-bank validation (includes memory-bank lint checks in regular commit flow).
6. Parse the response. If `docs_phase_passed: false`:
   - Check `timestamps_result.valid`. If `false`: timestamps have format errors — fix them via `manage_file()` and retry `run_docs_gate()`.
   - Check `roadmap_sync_result.valid`. If `false`: inspect `roadmap_sync_result` for specific issues. Fix any simple structural issues (stale plan refs, missing entries) via `manage_file()` and retry once. If roadmap_sync still fails after one retry **and timestamps are valid**, treat it as a **non-blocking warning** — record it and proceed to Phase C without blocking the commit.
7. Write result:

```json
// Write to: .cortex/.session/current-task.json
{"operation":"write","phase":"docs","pipeline":"commit","status":"complete","memory_bank_updated":true,"docs_phase_passed":true,"plans_archived":0,"roadmap_sync_warning":false}
```

Then call `pipeline_handoff()`. **GATE**: check `pipeline_state.phases.docs.status == "complete"` from the response. `docs_phase_passed: false` caused by roadmap_sync only (with timestamps passing) is **non-blocking** — note it and continue.

---

## Phase C: Validation & Synapse Submodule — @commit-phase-c subagent

Use @commit-phase-c to handle this phase. If the subagent is unavailable, run these steps inline:

1. Call `validate(check_type="timestamps")` and `validate(check_type="roadmap_sync")` to verify consistency. If Cursor strips args, read the `cortex://validation` resource instead (runs both checks).
2. **Synapse submodule handling** — run `cd .cortex/synapse && git status --short`:
   - **Clean**: `submodule_status = "clean"`. No action needed.
   - **Dirty** (any changes — analytics, prompts, agents, rules, scripts, etc.):
     a. Review the diff: `cd .cortex/synapse && git diff --stat` — verify changes are intentional (match current session work or are routine analytics updates).
     b. Stage all changes: `cd .cortex/synapse && git add -A`.
     c. Commit inside the submodule: `cd .cortex/synapse && git commit -m "<message>"`. Use conventional commit format describing the Synapse changes (e.g. `chore: update prompts for zero-arg tools, remove inlined cursor-agents`). For analytics-only changes, use `chore: update usage analytics`.
     d. **Push the submodule**: `cd .cortex/synapse && git push`. Push failures are non-blocking (auth/network/SSL) — record `push_succeeded: false` and the error, provide the manual push command, and continue. The superproject MUST NOT reference a submodule commit that doesn't exist on the remote, so always push before staging the updated gitlink.
     e. Record `submodule_status = "committed"`, `synapse_commit_sha`, and `synapse_push_succeeded` in pipeline state.
     f. After the submodule commit, the superproject sees a new gitlink — this will be staged in Step 13.
3. Write result:

```json
// Write to: .cortex/.session/current-task.json
{"operation":"write","phase":"validate","pipeline":"commit","status":"passed","timestamps_valid":true,"roadmap_sync_valid":true,"submodule_status":"clean or committed","synapse_commit_sha":null,"synapse_push_succeeded":true}
```

Then call `pipeline_handoff()`.

**GATE**: check `pipeline_state.phases.validate.status == "passed"` from the response.

---

## Step 12: Final Gate — @commit-final-gate subagent

Use @commit-final-gate to handle this phase. If the subagent is unavailable, run these steps inline:

1. Classify what changed since Phase A — **use your knowledge of what Phase B and C actually wrote**, not `git diff HEAD` or `git status` (those show the full working tree including pre-existing uncommitted files unrelated to this commit, which is expected and not a problem):
   - `source_changed`: any file under `src/` or `tests/` was **written by Phase B or C steps** in this pipeline run.
   - `markdown_changed`: any `.md`/`.mdc` file was **written by Phase B or C steps** (`.cortex/memory-bank/`, `.cortex/plans/`, `AGENTS.md`, `CLAUDE.md`, `.cortex/synapse/prompts/`). Phase B always modifies memory-bank files, so this is usually `true`.
   - **Do not flag pre-existing working-tree changes** (files modified before the pipeline started) as unexpected. Those are the user's in-progress work and are unrelated to `autofix()` behavior.
   - **`autofix()` `files_modified` field** lists only rumdl-fixed markdown files — seeing it non-empty (e.g. `.cortex/memory-bank/*.md`) is normal and expected, not a sign of unexpected scope expansion.
2. **If `source_changed`**: write fresh config then run the gate:

   ```json
   // Write to: .cortex/.session/current-task.json
   {"operation":"write","phase":"checks","pipeline":"commit","force_fresh":true,"test_timeout":600}
   ```

   Then call `pipeline_handoff()` and `run_quality_gate()`.

   Full re-run including tests, types, lint, format, markdown. If any check fails: call `autofix()` and retry (max 3 iterations).
   After a green result, re-run CI parity checks (same discovery as Phase A step 4). If any fails, Step 12 is failed (do not commit).
3. **If only `markdown_changed`** (no source changes): run `autofix()` to auto-fix any remaining markdown lint. Then verify:

   ```json
   // Write to: .cortex/.session/current-task.json
   {"operation":"write","phase":"checks","pipeline":"commit","force_fresh":true,"test_timeout":600}
   ```

   Then call `pipeline_handoff()` and `run_quality_gate()`.

   Since no source code changed, test/type/lint/format results from Phase A are still valid — only markdown lint needs verification. If tests timeout but all non-test checks pass, Step 12 passes (Phase A already proved tests are green and no source changed).
4. **If nothing changed**: skip re-run, write success with `skipped_checks` list.
5. Write result:

```json
// Write to: .cortex/.session/current-task.json
{"operation":"write","phase":"final-gate","pipeline":"commit","status":"passed or failed","coverage":0.0,"fix_loops_executed":0,"skipped_checks":[]}
```

Then call `pipeline_handoff()`. **GATE**: check `pipeline_state.phases.final-gate.status == "passed"` from the response before proceeding to Step 13.

**Validation rules for Step 12**:

- Rely on `phases.final-gate` structured status, **not** on log snippets or success banners.
- If any critical check fails or is skipped in this final run, Step 12 is **failed** and you must **block commit creation**.
- Skipped-clean checks are NOT failures — they are optimizations where a check is trusted from Phase A.
- **Timeout-only test failures** (when only `.cortex/` markdown changed, not `src/`/`tests/`): if Step 12 fails exclusively due to pytest timeouts and all non-test checks (format, lint, types, markdown) pass, Step 12 **passes**. Rationale: Phase A already proved tests are green; timeouts in the detached subprocess are caused by resource contention with the MCP server, not code bugs.
- **Structural-check mismatch rule**: if `run_quality_gate()` reports pass but `check_file_sizes.py`, `check_function_lengths.py`, or the language-specific build script (Phase A step 5) fails, treat the gate as stale/partial and block commit creation until all parity checks pass.

---

## Step 13: Commit Creation

**Preconditions** (verify ALL by reading pipeline state):

1. `phases.final-gate.status == "passed"`
2. All phases present in state

**Session scope split-commit hint**: Enforce the single-goal session pattern at commit time. If staged changes contain multiple unrelated goals (for example, "CI/tooling recovery" plus "feature implementation"), suggest splitting into separate commits aligned to one goal each before creating the commit.

- Recommend one commit per goal with explicit scope boundaries.
- If the user explicitly requests one combined commit, proceed without blocking, but record "Session Scope Risk: multi-goal combined commit" in the summary.

**Staging**: `git add <path>` for each related file. Never `git add -A`. Never stage `.env*`, credentials, keys, sensitive files.

If `phases.validate.submodule_status == "committed"`: stage the submodule pointer — `git add .cortex/synapse`. This records the new Synapse commit in the superproject.

**Commit message**: Content-descriptive, not process-descriptive. Use conventional commits (`feat:`, `fix:`, `docs:`, `chore:`). Describe WHAT changed. Anti-pattern: "Run full Cortex commit pipeline." Good: "feat: add structured quality config, update activeContext."

**Post-commit**: `git show --stat` to verify.

---

## Step 14: Push Branch

**Safety-net Synapse check** — run `cd .cortex/synapse && git log --oneline origin/main..HEAD` to detect any unpushed Synapse commits (Phase C should have pushed already, but push may have failed non-blockingly or args may have been stripped). If there are unpushed Synapse commits, push the submodule first — `cd .cortex/synapse && git push`. Always push the submodule before the superproject so the superproject's gitlink points to a commit that exists on the remote.

Then push the superproject branch (including `main`) without extra confirmation. Push failures are non-blocking. SSL errors: retry up to 2 times.

---

## Step 15: Cleanup — MANDATORY

Clean up the pipeline state:

```json
// Write to: .cortex/.session/current-task.json
{"operation": "clear", "pipeline": "commit"}
```

Then call `pipeline_handoff()`.

---

## Git Safety

- Only commit/push when user explicitly invoked `/cortex/commit`
- Selective staging only (no `git add -A`)
- Verify no sensitive files staged before `git add`

## Failure Handling

- **Preflight fails (MCP unhealthy)**: STOP — MCP required for all phases
- **Preflight fails (no changes)**: STOP — nothing to commit
- **Preflight `git stash create` fails with "beyond a symbolic link"**: Non-blocking — use `snapshot_ref = "HEAD"` and continue. This is expected in TradeWing because `.cortex/memory-bank` and `.cortex/plans` may be symlinked in local workflows.
- **Phase A fails after 3 fix iterations**: STOP, report unresolvable issues
- **Phase A fails due to project build failure** (step 5 exits non-zero): fix compilation/build errors, re-run both `run_quality_gate()` and the language-specific build script. Do NOT create the commit until the build succeeds.
- **Phase A fails due to markdown lint**: Read `markdown_result.output` for exact violations (file:line, rule code). Call `autofix()` (includes markdown auto-fix for fixable rules). If errors remain (e.g. MD036 is not auto-fixable), apply manual fixes using the violation details. Zero markdown errors required before Phase A can pass.
- **Phase B timestamps fail**: Fix timestamp format errors via `manage_file()`, retry `run_docs_gate()`. Timestamps failure IS blocking.
- **Phase B roadmap_sync fails only**: Non-blocking warning — record it, proceed to Phase C.
- **Phase B memory-bank lint fails**: Run `autofix()` first (required) to apply deterministic housekeeping fixes, then retry `run_docs_gate()`. If unresolved after 3 attempts, stop and report remaining blockers.
- **Phase C Synapse commit fails** (e.g. merge conflict inside submodule): STOP, block commit, report the submodule error
- **Phase C Synapse push fails** (auth/network/SSL): Non-blocking — record the error and `synapse_push_succeeded: false` in pipeline state. Step 14 will retry the push as a safety net. Provide the manual push command to the user.
- **Step 12 fails after 3 iterations**: Block commit — unless failures are exclusively pytest timeouts and no source code (`src/`/`tests/`) changed since Phase A (see timeout-only rule above)
- **MCP disconnects**: All phase checks use blocking zero-arg tools (`run_quality_gate`, `run_docs_gate`) that run end-to-end in a single call. On disconnect, simply retry the tool call.
- **3 consecutive MCP failures**: Circuit-breaker per `shared-conventions.md`. Call `pipeline_handoff(operation="read", pipeline="commit")` to restore context after reconnect.
- **On any pipeline failure**: Report phase and error. Offer rollback using `snapshot_ref` from `phases.preflight`. Do NOT auto-rollback.

## Resuming After Context Compression

If context is lost mid-pipeline, call:

```text
pipeline_handoff(operation="read", pipeline="commit")
```

This restores the full record of completed phases, coverage values, snapshot_ref, and submodule status — continue from the first phase not yet in `phases`.

## Step 16: Post-Prompt Hook (Self-Improvement)

After writing the final report for this commit pipeline run, invoke the post-prompt self-improvement hook:

- Read `.cortex/synapse/prompts/post-prompt-hook.md` and execute it to analyze the session and emit any applicable Skills, Plans, or Rules.
- Treat this hook as **non-blocking**: if it fails or is unavailable (for example, MCP connection issues), record a brief note in the final report `## Next` section and consider the commit pipeline itself complete.

## Final report (required format)

**MANDATORY**: Use the **Pipeline** report type from `docs/guides/synapse-final-report-templates.md`.

```markdown
## Result

✅ Committed <sha> to <branch> (<n> files)

## Phases

| Phase | Status | Notes |
|-------|--------|-------|
| Preflight | ✅/❌ | snapshot: <ref> |
| Quality (A) | ✅/❌ | <coverage>% coverage |
| Docs (B) | ✅/❌ | <roadmap updated OR —> |
| Validate (C) | ✅/❌ | — |
| Final gate | ✅/❌ | <n> fix iterations |

## Artifacts

- Commit: `<sha>` on `<branch>`
- Files: <list>
- Coverage: <n>%
- Pushed: ✅/❌ <remote>

## Next

<action items OR None>
```

**Rules**:

- Memory bank updates go in Docs (B) Notes column only when changed
- Failed phases: put ❌ in Status column, details in Notes
- `## Next`: explicit "None" or action items

## Success Criteria

- All phases (Preflight, A, B, C) and Step 12 passed
- Commit created with content-descriptive message
- Push completed (or non-blocking failure documented)
- Pipeline state cleared
- Post-prompt hook executed (or non-blocking failure documented)
