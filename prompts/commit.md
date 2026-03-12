# Commit Changes

**CRITICAL**: Execute ALL phases below AUTOMATICALLY. Do NOT pause, summarize, or ask for confirmation between phases. Start with Preflight immediately.

## Sequential Execution Order

Each phase must complete before the next begins:

1. **Preflight** → 2. **Phase A** → 3. **Phase B** → 4. **Phase C** → 5. **Step 12** → 6. **Step 13** → 7. **Step 14** → 8. **Step 15**

---

## Preflight — use the `commit-preflight` subagent

Use the `commit-preflight` subagent to verify MCP health, load context and rules, confirm changes exist, and create a rollback snapshot.

**GATE**: Must return `status: "complete"` before proceeding to Phase A.

---

## Phase A: Pre-Commit Checks — use the `commit-checks` subagent

Use the `commit-checks` subagent to run all pre-commit quality checks via the job-based API (start + poll). The subagent starts a detached worker and polls for completion — each individual MCP call is short-lived, avoiding connection timeouts.

**GATE**: Must return `status: "passed"` before proceeding to Phase B.

**Validation rules for Phase A**:

- Treat the structured status returned by the `commit-checks` subagent (and its underlying quality job) as the **single source of truth** for Phase A.
- **Never** infer that Phase A passed from log snippets, banners (including any `"✅ All quality checks passed!"` messages), or previous runs.
- If the quality result reports any **failed** or **skipped** critical checks, Phase A is considered **failed** and the commit pipeline must **stop without creating a commit**.

---

## Phase B: Documentation and State — use the `commit-docs` subagent

Use the `commit-docs` subagent to update the memory bank (activeContext.md, progress.md, roadmap.md), archive completed plans, and validate documentation. This is the **compound** step of the Plan → Work → Review → Compound loop.

**GATE**: Must return `docs_phase_passed: true` before proceeding to Phase C.

---

## Phase C: Validation — use the `commit-validate` subagent

Use the `commit-validate` subagent to handle timestamps, state consistency, and Synapse submodule. It uses git commands and file reads (no MCP tools needed).

**GATE**: Status must be `passed`. Submodule must not be `dirty_after_commit` **except when the only remaining Synapse changes are under `.cache/usage/` (analytics dirt), which is treated as non-blocking**.

---

## Step 12: Final Gate — use the `commit-final-gate` subagent

Use the `commit-final-gate` subagent to re-run all quality checks after phases B and C may have modified files. The subagent uses the job-based API (start + poll) and checks for a fresh cached Phase A result before starting a new run.

**GATE**: Must return `status: "passed"` before proceeding to Step 13.

**Validation rules for Step 12**:

- Again, rely on the structured status and per-check outcomes from the quality job, **not** on log snippets or success banners.
- If any critical check fails or is skipped in this final run, Step 12 is **failed** and you must **block commit creation**.

---

## Step 13: Commit Creation

**Preconditions** (verify ALL):
1. Step 12 passed
2. Submodule status is non-blocking
3. All phases completed

**Staging**: `git add <path>` for each related file. Never `git add -A`. Never stage `.env*`, credentials, keys, sensitive files.

**Commit message**: Content-descriptive, not process-descriptive. Use conventional commits (`feat:`, `fix:`, `docs:`, `chore:`). Describe WHAT changed. Anti-pattern: "Run full Cortex commit pipeline." Good: "feat: add structured quality config, update activeContext."

**Post-commit**: `git show --stat` to verify.

---

## Step 14: Push Branch

Push current branch (including `main`) without extra confirmation. Push failures are non-blocking. SSL errors: retry up to 2 times.

---

## Step 15: Analyze — MANDATORY

Call `analyze(target="context")` then `analyze(target="usage_patterns")`. Non-blocking on connection errors.

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
- **3 consecutive MCP failures**: Circuit-breaker per `shared-conventions.md`. Persist state and stop.
- **On any pipeline failure**: Report phase and error. Offer rollback: `git checkout -- .` or `git stash apply <snapshot_ref>`. Do NOT auto-rollback.

## Success Criteria

- All phases (Preflight, A, B, C) and Step 12 passed
- Commit created with content-descriptive message
- Push completed (or non-blocking failure documented)
- Analyze executed (or non-blocking failure documented)
