# Commit Changes

**CRITICAL**: Execute ALL phases below AUTOMATICALLY. Do NOT pause, summarize, or ask for confirmation between phases. Start with Preflight immediately.

## Sequential Execution Order

Each phase must complete before the next begins:

1. **Preflight** → 2. **Phase A** → 3. **Phase B** → 4. **Phase C** → 5. **Step 12** → 6. **Step 13** → 7. **Step 14** → 8. **Step 15**

---

## Pipeline Initialization

Before invoking Preflight, call:
```
pipeline_handoff(operation="init", pipeline="commit")
```

This creates `.cortex/.session/{session_id}/commit/` where all phase inputs and outputs are stored.

---

## Preflight — use the `commit-preflight` subagent

Before invoking:
```
pipeline_handoff(operation="write_task", pipeline="commit", phase="preflight",
  data='{}')
```

Use the `commit-preflight` subagent to verify MCP health, load context and rules, confirm changes exist, and create a rollback snapshot.

**GATE**: Read `pipeline_handoff(operation="read_state", pipeline="commit")` and verify `phases.preflight.status == "complete"` before proceeding to Phase A. The subagent writes its result; never infer pass/fail from text output.

---

## Phase A: Pre-Commit Checks — use the `commit-checks` subagent

Before invoking, extract `snapshot_ref` from pipeline state and pass it:
```
pipeline_handoff(operation="write_task", pipeline="commit", phase="checks",
  data='{"coverage_threshold": 0.9, "snapshot_ref": "<value from preflight>"}')
```

Use the `commit-checks` subagent to run all pre-commit quality checks via the job-based API (start + poll). The subagent starts a detached worker and polls for completion — each individual MCP call is short-lived, avoiding connection timeouts.

**GATE**: Read state and verify `phases.checks.status == "passed"` before proceeding to Phase B.

**Validation rules for Phase A**:

- Treat the structured status in `phases.checks` as the **single source of truth** for Phase A.
- **Never** infer that Phase A passed from log snippets, banners (including any `"✅ All quality checks passed!"` messages), or previous runs.
- If the quality result reports any **failed** or **skipped** critical checks, Phase A is considered **failed** and the commit pipeline must **stop without creating a commit**.

---

## Phase B: Documentation and State — use the `commit-docs` subagent

Before invoking:
```
pipeline_handoff(operation="write_task", pipeline="commit", phase="docs",
  data='{"phase_a_coverage": <value from phases.checks.coverage>}')
```

Use the `commit-docs` subagent to update the memory bank (activeContext.md, progress.md, roadmap.md), archive completed plans, and validate documentation. This is the **compound** step of the Plan → Work → Review → Compound loop.

**GATE**: Read state and verify `phases.docs.docs_phase_passed == true` before proceeding to Phase C.

---

## Phase C: Validation — use the `commit-validate` subagent

Before invoking:
```
pipeline_handoff(operation="write_task", pipeline="commit", phase="validate", data='{}')
```

Use the `commit-validate` subagent to handle timestamps, state consistency, and Synapse submodule. It uses git commands and file reads.

**GATE**: Read state and verify `phases.validate.status == "passed"`. Submodule must not be `dirty_after_commit` **except when the only remaining Synapse changes are under `.cache/usage/` (analytics dirt), which is treated as non-blocking**.

---

## Step 12: Final Gate — use the `commit-final-gate` subagent

Before invoking, extract phase_a coverage for comparison:
```
pipeline_handoff(operation="write_task", pipeline="commit", phase="final-gate",
  data='{"phase_a_coverage": <value>, "snapshot_ref": "<value from preflight>"}')
```

Use the `commit-final-gate` subagent to re-run all quality checks after phases B and C may have modified files. The subagent uses the job-based API (start + poll) and always forces a fresh run.

**GATE**: Read state and verify `phases.final-gate.status == "passed"` before proceeding to Step 13.

**Validation rules for Step 12**:

- Rely on `phases.final-gate` structured status, **not** on log snippets or success banners.
- If any critical check fails or is skipped in this final run, Step 12 is **failed** and you must **block commit creation**.

---

## Step 13: Commit Creation

**Preconditions** (verify ALL by reading pipeline state):

1. `phases.final-gate.status == "passed"`
2. `phases.validate.submodule_status` is non-blocking
3. All phases present in state

**Staging**: `git add <path>` for each related file. Never `git add -A`. Never stage `.env*`, credentials, keys, sensitive files.

**Commit message**: Content-descriptive, not process-descriptive. Use conventional commits (`feat:`, `fix:`, `docs:`, `chore:`). Describe WHAT changed. Anti-pattern: "Run full Cortex commit pipeline." Good: "feat: add structured quality config, update activeContext."

**Post-commit**: `git show --stat` to verify.

---

## Step 14: Push Branch

Push current branch (including `main`) without extra confirmation. Push failures are non-blocking. SSL errors: retry up to 2 times.

---

## Step 15: Analyze and Cleanup — MANDATORY

Call `analyze(target="context")` then `analyze(target="usage_patterns")`. Non-blocking on connection errors.

Then clean up the pipeline state:
```
pipeline_handoff(operation="clear", pipeline="commit")
```

---

## Git Safety

- Only commit/push when user explicitly invoked `/cortex/commit`
- Selective staging only (no `git add -A`)
- Verify no sensitive files staged before `git add`

## Failure Handling

- **Preflight fails (MCP unhealthy)**: STOP — MCP required for all phases
- **Preflight fails (no changes)**: STOP — nothing to commit
- **Phase A fails after 3 fix iterations**: STOP, report unresolvable issues
- **Phase B fails**: Advise `/cortex/fix` with `target=docs`
- **Phase C submodule fails**: STOP, block commit
- **Step 12 fails after 3 iterations**: Block commit
- **MCP disconnects**: The start+poll pattern (Phases A and Step 12) makes disconnects non-fatal — each poll call is short. On disconnect during Phase B/C, retry once. Markdown lint fallback: use the fallback command from project rules.
- **3 consecutive MCP failures**: Circuit-breaker per `shared-conventions.md`. Call `pipeline_handoff(operation="read_state", pipeline="commit")` to restore context after reconnect.
- **On any pipeline failure**: Report phase and error. Offer rollback using `snapshot_ref` from `phases.preflight`. Do NOT auto-rollback.

## Resuming After Context Compression

If context is lost mid-pipeline, call:
```
pipeline_handoff(operation="read_state", pipeline="commit")
```
This restores the full record of completed phases, coverage values, snapshot_ref, and submodule status — continue from the first phase not yet in `phases`.

## Success Criteria

- All phases (Preflight, A, B, C) and Step 12 passed
- Commit created with content-descriptive message
- Push completed (or non-blocking failure documented)
- Analyze executed (or non-blocking failure documented)
- Pipeline state cleared
