# Commit Changes

**CRITICAL**: Execute ALL steps below AUTOMATICALLY. Do NOT pause, summarize, or ask for confirmation. Start with Step 1 immediately.

## START HERE — Execute These Tool Calls Now

**Step 1**: Call `check_mcp_connection_health()`. If unhealthy, STOP.

**Step 2**: Call `load_context(task_description="Commit pipeline: pre-commit checks, memory bank, git", token_budget=4000)`.

**Step 3**: Call `rules(operation="get_relevant", task_description="Commit pipeline, test coverage, type fixes, and visibility rules")`. If this fails or returns `disabled`, continue — quality checks enforce rules independently.

**Step 4**: Run `git status --porcelain`. If empty, STOP — nothing to commit.

**Step 5**: Run `git stash create`. If a hash is returned, run `git stash store -m "cortex-commit-pipeline-snapshot" <hash>`.

After Step 5 passes, continue to Phase A below.

---

## Phase A: Pre-Commit Checks

Call `execute_pre_commit_checks(phase="A", test_timeout=300, coverage_threshold=0.90, strict_mode=False)` **exactly once per Phase A run**.

**Detached execution model (CRITICAL)**:

- This tool may run checks in a detached worker process and **block for 1–3+ minutes** while polling for the result. This is normal and **not** a hang.
- **Do not call `execute_pre_commit_checks` again while a Phase A run may still be in progress.** Never “retry” by issuing a second tool call while waiting.
- If the tool reports that checks are already running or that a detached worker has started, treat that as “in progress” and do **not** start another run.
- If the result mentions an internal log or result file path under a `.cursor/.../agent-tools/` directory, **do not attempt to read that path**; it is not accessible to the agent. Rely only on the structured JSON result returned by the tool.

**Outcome handling**:

- If `preflight_passed: true`: record `coverage` value, proceed to Phase B.
- If `preflight_passed: false`: call `fix_quality_issues()` to auto-fix, then re-run `execute_pre_commit_checks(phase="A")`. Max 3 iterations. If iteration 2 violations >= iteration 1: STOP (not converging). Before fixing: call `load_context(task_description="Fixing errors and quality issues for commit", token_budget=15000)`.

**GATE**: All checks must pass before proceeding.

## Phase B: Documentation and State

Execute these steps sequentially:

1. **Memory bank**: Call `update_memory_bank(operation="refresh")` or use `manage_file()` to update activeContext.md, progress.md, roadmap.md with current changes. Use `manage_file()` only (never StrReplace/Write/ApplyPatch on memory bank files). Completed items go to activeContext.md; remove them from roadmap.md.

2. **Plan archiving**: Scan `.cortex/plans/` for completed plans. For each: move to `.cortex/plans/archive/`. Verify plan Status uses `Status: VALUE` (not `**VALUE**`; MD036 applies). Report count even if 0.

3. **Validation**: Call `execute_pre_commit_checks(phase="B")`. If `docs_phase_passed: false`, fix and re-run.

4. **Script tracking**: Only if a script was explicitly created or run during this pipeline AND you have the script path and content available, call `manage_session_scripts(operation="capture", script_path="...", script_content="...", task_description="...")`. Skip this step if no scripts were created.

**GATE**: `docs_phase_passed` must be `true`.

## Phase C: Validation — use the `commit-validate` subagent

Use the `commit-validate` subagent to handle timestamps, state consistency, and Synapse submodule. It uses git commands and file reads (no MCP tools needed).

**GATE**: Status must be `passed`. Submodule must not be `dirty_after_commit`.

## Step 12: Final Validation Gate

Call `check_mcp_connection_health()`, then call `execute_pre_commit_checks(phase="A", skip_if_clean=True, test_timeout=600, coverage_threshold=0.90)`.

**Note**: This may take 1-3 minutes and produce large output — wait for completion before parsing results. With `skip_if_clean=True`, unchanged source files skip redundant checks (faster when no code changed since Phase A). As in Phase A, **call `execute_pre_commit_checks` only once for this step** and do **not** issue overlapping retries while a run is active.

**GATE**: All checks must pass.

## Step 13: Commit Creation

**Preconditions** (verify ALL):
1. Step 12 passed
2. Submodule status is non-blocking
3. All phases completed

**Staging**: `git add <path>` for each related file. Never `git add -A`. Never stage `.env*`, credentials, keys, sensitive files.

**Commit message**: Content-descriptive, not process-descriptive. Use conventional commits (`feat:`, `fix:`, `docs:`, `chore:`). Describe WHAT changed. Anti-pattern: "Run full Cortex commit pipeline." Good: "feat: add structured quality config, update activeContext."

**Post-commit**: `git show --stat` to verify.

## Step 14: Push Branch

Push current branch (including `main`) without extra confirmation. Push failures are non-blocking. SSL errors: retry up to 2 times.

## Step 15: Analyze — MANDATORY

Call `analyze(target="context")` then `analyze(target="usage_patterns")`. Non-blocking on connection errors.

---

## Git Safety

- Only commit/push when user explicitly invoked `/cortex/commit`
- Selective staging only (no `git add -A`)
- Verify no sensitive files staged before `git add`

## Failure Handling

- **Phase A fails after 3 fix iterations**: STOP, report unresolvable issues
- **Phase B fails**: Advise `/cortex/fix` with `target=docs`
- **Phase C submodule fails**: STOP, block commit
- **Step 12 fails after 3 iterations**: Block commit
- **MCP disconnects**: Retry once, re-run from last completed phase. Markdown lint fallback: `npx markdownlint-cli2 --fix '**/*.md' '**/*.mdc'`
- **3 consecutive MCP failures**: Circuit-breaker per `shared-conventions.md`. Persist state and stop.
- **On any pipeline failure**: Report phase and error. Offer rollback: `git checkout -- .` or `git stash apply <snapshot_ref>`. Do NOT auto-rollback.

## Success Criteria

- All phases (Preflight, A, B, C) and Step 12 passed
- Commit created with content-descriptive message
- Push completed (or non-blocking failure documented)
- Analyze executed (or non-blocking failure documented)
