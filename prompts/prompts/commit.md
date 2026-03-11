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

**Phase A contract (MUST):**

- Phase A **MUST** treat the **structured Phase A quality job result** (via `start_pre_commit_job` + `get_pre_commit_job_status`) as the **single source of truth** for all quality checks.
- Phase A **MUST** run the same Phase A quality job that the GitHub `Code Quality` workflow uses (formatting, linting, type_check, file sizes, function lengths, spelling, markdown lint, tests, evals, etc.).
- When any critical check fails or is skipped, the subagent **MUST**:
  - Load context for fixes (e.g. `load_context(task_description="Fixing errors and quality issues for commit", ...)`).
  - Invoke Synapse-backed fix tooling (e.g. `fix_quality_issues()`) that can modify code and configuration.
  - **Re-run the full Phase A quality job from the beginning** on the updated working tree.
- Phase A **MUST** repeat this loop — `{Phase A quality job → structured result → fix tooling → Phase A quality job}` — until either:
  - **All critical checks are green** (no failing or skipped critical checks on the final structured result), or
  - A hard limit on fix iterations or convergence is reached (e.g. violation counts are no longer decreasing).

**GATE**: Phase A is considered **passed** only when the final Phase A structured result for the current working tree reports:

- `preflight_passed: true`, **and**
- Every critical check outcome is `"passed"` (no `"failed"` or `"skipped"`).

If, after the allowed number of fix iterations, any critical check remains failing or skipped, Phase A is **failed** and the commit pipeline must **stop without creating a commit**.

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

**GATE**: Status must be `passed`. Submodule must not be `dirty_after_commit`.

---

## Step 12: Final Gate — use the `commit-final-gate` subagent

Use the `commit-final-gate` subagent to re-run all quality checks after phases B and C may have modified files. The subagent uses the job-based API (start + poll) and checks for a fresh cached Phase A result before starting a new run.

**Step 12 contract (MUST):**

- Step 12 **MUST** ensure that a **fresh Phase A quality job result** exists that fully reflects all changes made in Phases B and C.
- If any files within the Phase A scope (code, tests, Synapse scripts, relevant docs) were modified after the last passing Phase A run, Step 12 **MUST** start a new Phase A quality job and wait for its structured result.
- Step 12 **MUST NOT** rely solely on historical or cached results when the working tree has changed since that run.
- The success and failure rules for the final Phase A run are identical to those in Phase A above:
  - Success only when all critical checks are `"passed"` (no `"failed"` or `"skipped"`).
  - Any failing or skipped critical check blocks commit creation.

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
