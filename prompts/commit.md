# Commit Changes

**AI EXECUTION COMMAND**: Execute the mandatory commit procedure with all required pre-commit checks, including testing of all runnable project tests.

**CRITICAL**: ONLY run this commit workflow when the user explicitly invoked `/cortex/commit` (or equivalent commit command). NEVER commit or push based on implicit assumptions. Invoking this command IS an explicit commit request per `no-auto-commit.mdc` rule. Once invoked, execute all steps AUTOMATICALLY without asking for additional permission or confirmation.

**END-TO-END EXECUTION**: Run from start to finish without pausing. Begin immediately with the Pre-Action Checklist and tool calls. When a step fails, apply fixes automatically and re-run validation — do NOT stop merely to report the failure. Only stop when: (1) a step fails after genuine fix attempts, (2) a Cortex MCP tool returns a hard failure, or (3) user input is explicitly required.

## Conventions

Per `shared-conventions.md`. Severity: GATE/CHECK/PREFER. Memory bank writes: per `memory-bank-contract.md`.

## Architecture

### Prompts = Orchestration | Agents = Implementation

This prompt focuses on **step order, dependencies, and workflow coordination**. For implementation details (MCP tool calls, validation logic, response parsing), see the referenced agent files. For known error patterns, see `error-pattern-detector.md`.

**Pipeline state**: The `commit-state-tracker` agent maintains a checkpoint file across the pipeline. Delegate to it after Phase A and before Step 12 to persist/recall step outcomes.

## Agents Used

| Step | Agent | Purpose |
|---|---|---|
| Pre-Step | common-checklist | Load structure, memory bank, rules, language |
| State | commit-state-tracker | Pipeline state checkpointing |
| 0 | error-fixer | Fix errors and warnings |
| 0.5 | quality-checker | Quality preflight (fail-fast) |
| 1 | code-formatter | Code formatting |
| 1.5 | markdown-linter | Markdown linting |
| 2 | type-checker | Type checking |
| 3 | quality-checker | Code quality checks |
| 4 | test-executor | Test execution |
| 5-6 | memory-bank-updater | Memory bank and roadmap updates |
| 7-8 | plan-archiver | Plan archiving and validation |
| 9 | timestamp-validator | Timestamp validation |
| 11 | submodule-handler | Synapse submodule handling |
| 12 | final-gate-validator | Final validation gate (all re-checks) |
| — | error-pattern-detector | Reference catalog for error detection |

**Steps without dedicated agents** (handled in orchestration): 10 (state check), 13 (commit), 14 (push), 15 (analyze).

**Inter-agent communication**: All agents return structured results per `shared-handoff-schema.md`. Validate required fields before proceeding.

**When executing steps**: Agent availability is verified by the pre-flight health check. READ the agent file, EXECUTE all steps from it, VERIFY success before proceeding.

## Execution Strategy

### Concurrency rules

- **Steps 0-8**: Strictly sequential (state-changing, dependencies)
- **Steps 9-11**: Strictly sequential (deterministic execution; no conditional parallelism)
- **Steps 12-15**: Strictly sequential

## Pre-Action Checklist

Execute standard pre-flight protocol (see `shared-conventions.md`) with all agents from the "Agents Used" table.

Additionally, the orchestrator MUST verify:

0. **GATE**: Call `check_mcp_connection_health()`. If unhealthy, STOP.
1. **CHECK**: Load memory bank files (essential: activeContext, roadmap, progress). Token budget 3000-4000 for commit pipeline.
2. **GATE**: Load rules via `rules(operation="get_relevant", task_description="Commit pipeline, test coverage, type fixes, and visibility rules")`. Pipeline MUST NOT proceed without rules.
3. **CHECK**: Verify code conforms to loaded rules before running checks
4. **CHECK**: Confirm changes exist to commit
5. **CHECK**: Scan recent MCP tool responses for validation errors

**PREFER**: Use `think` tool to plan which checks apply to current changes.

When `rules()` returns status `disabled` or indexed_files=0, read rule files from the rules directory (Read tool) and record "Rules loaded: Yes (via file read)". Use `get_structure_info()` for paths.

After checklist passes, delegate to `commit-state-tracker` (checkpoint_write) to record initial state.

## Pre-Step: Load Rules (GATE — before Step 0)

Call `rules(operation="get_relevant", task_description="Commit pipeline, test coverage, type fixes, and visibility rules")`. If disabled, read rules from rules directory (path from `get_structure_info()` -> `structure_info.paths.rules`). Record "Rules loaded: Yes" in state.

**Fix-path rule**: When ANY step fails and you apply fixes, you MUST load context and rules BEFORE making changes: `load_context(task_description="Fixing errors and quality issues for commit", token_budget=15000)`.

**Zero-budget reminder**: Zero-budget or zero-files `load_context` calls are only acceptable for trivial/no-op tasks. For commit work use non-zero budget (10k-15k).

## Phase A: Pre-Commit Checks (Steps 0-4)

**GATE**: Fix loops in Phase A are limited to **3 iterations** per step (see `shared-conventions.md` Max-Retry Limits). After 3 failed fix attempts on any step, STOP and report unresolvable issues.

**PREFER**: Use `execute_pre_commit_checks(phase="A", test_timeout=300, coverage_threshold=0.90, strict_mode=False)` as single entry point. If `preflight_passed: true`, proceed to Step 5. If `preflight_passed: false`, delegate to individual agents below to fix, then point user to `/cortex/fix` with `target=tests` or `target=quality` for targeted follow-up if needed.

### Step 0: Fix errors — Delegate to `error-fixer`

- **GATE**: Must complete successfully before Step 1
- **Dependency**: Rules must be loaded (Pre-Step)
- **Output**: Zero errors remaining

### Step 0.5: Quality preflight — Delegate to `quality-checker`

- **GATE**: Must complete before Step 1
- **Purpose**: Fail-fast on quality violations

### Step 1: Formatting — Delegate to `code-formatter`

- **GATE**: Formatting check must pass before Step 1.5
- **Dependency**: After Step 0

### Step 1.5: Markdown linting — Delegate to `markdown-linter`

- **GATE**: Zero markdown lint errors before Step 2
- **Dependency**: After Step 1
- **PREFER**: Pre-commit hook also runs markdown lint on staged files

### Step 2: Type checking — Delegate to `type-checker`

- **Conditional**: Only if project uses a type system
- **GATE**: Zero type errors AND zero warnings
- **Dependency**: After Step 1.5

### Step 3: Code quality — Delegate to `quality-checker`

- **GATE**: Zero file size violations AND zero function length violations
- **Dependency**: After Step 2
- **PREFER**: Run type+quality after EACH refactor (incremental validation)

### Step 3.5-3.6: Intermediate validation and duplicate detection (PREFER)

- Run type+quality check after each refactor during Step 3
- Before creating helpers, search for existing functions with similar names

### Step 4: Tests — Delegate to `test-executor`

- **GATE**: 100% pass rate AND coverage >= threshold
- **Coverage threshold**: Default 90%. For brownfield bootstrapping (first commits on projects with large untested codebases), check if `progress.md` or `techContext.md` contains a `coverage_threshold: <value>` override. If present, use that value instead of 90%. This prevents deadlock on initial commits while tracking the debt.
- **Dependency**: After Steps 0-3 pass
- **PREFER**: Call `check_mcp_connection_health()` before if pipeline has been running long

After Phase A passes, delegate to `commit-state-tracker` (checkpoint_write) to record Phase A results.

## Phase B: Documentation and State (Steps 5-8)

### Step 5: Memory bank — Delegate to `memory-bank-updater`

- **Dependency**: After Step 4
- Updates activeContext.md, progress.md, roadmap.md
- **CHECK**: Use `manage_file()` only for memory bank writes (never StrReplace/Write/ApplyPatch)

### Step 6: Roadmap updates — Delegate to `memory-bank-updater`

- **Dependency**: Part of Step 5
- **CHECK**: Never truncate roadmap content; new content must be >= length of original

### Step 7: Archive completed plans — Delegate to `plan-archiver`

- **GATE**: All completed plans must be archived
- **Dependency**: After Step 5
- **CHECK**: Step must execute even if 0 plans found (report "0 plans archived")

### Step 8: Validate archive locations — Part of `plan-archiver`

- **GATE**: No completed plans remain in plans directory
- **Dependency**: Part of Step 7

After Phase B, run `execute_pre_commit_checks(phase="B")` to validate timestamps and roadmap sync. If `docs_phase_passed: false`, fix using `/cortex/fix` with `target=docs`.

## Phase C: Validation and Git (Steps 9-15)

**Execution order**: Steps 0-8 strictly sequential. Steps 9, 10, 11 strictly sequential. Steps 12-14 strictly sequential (Step 15 analyze after).

### Steps 9-11: Validation block

Execute Steps 9, 10, 11 sequentially. If ANY fails, do not proceed to Step 12.

**Step 9: Timestamps — Delegate to `timestamp-validator`**

- **GATE**: All timestamps YYYY-MM-DD format
- **Dependency**: After Step 5

### Step 10: Ensure roadmap/activeContext reflect actual state

- **Dependency**: After Steps 5-6
- Read roadmap.md and activeContext.md via `manage_file`
- Verify: roadmap = future work only, activeContext = completed work only
- Fix if needed: move completed items from roadmap to activeContext
- **No codebase scan**: Do NOT run `validate(check_type="roadmap_sync")`. No TODO matching.
- **Non-blocking**: State consistency check only

**Step 11: Submodule handling — Delegate to `submodule-handler`**

- **GATE**: Step 11 CANNOT be skipped. Must execute every run.
- **Agent**: submodule-handler (Synapse agents directory)
- **Input**: `synapse_path` resolved via `get_structure_info()` or project-relative path
- **Output**: `SubmoduleHandlerResult` — check `status` field
- **GATE**: If `status` is `dirty_after_commit` or `commit_failed`, block commit

### Step 12: Final validation gate — Delegate to `final-gate-validator`

- **GATE**: Must execute in full. Phase A results are NOT sufficient.
- **Dependency**: After Steps 9-11 ALL complete
- **PREFER**: Call `check_mcp_connection_health()` before starting
- The agent runs all re-verification with fix-loop state machine and **dirty-state optimization (Phase 89)**: for source-dependent checks (format, type_check, quality, tests), the agent passes `skip_if_clean=True` to `execute_pre_commit_checks`. When no source files changed since Phase A, those checks may be skipped and reported as e.g. "Step 12.7: Skipped (no changes since Phase A)."
- **Output**: `FinalGateValidatorResult` with all phases passed/failed; optional `dirty_state_skips` lists any skipped checks
- **GATE**: If `status != "passed"`, block commit

Before Step 12, delegate to `commit-state-tracker` (checkpoint_read) to recall Phase A outcomes.

### Step 13: Commit creation

- **Dependency**: After Step 12 passes
- **GATE — Preconditions** (verify ALL before executing):
  1. User explicitly requested commit (via `/cortex/commit`)
  2. Step 11 `submodule-handler` returned non-blocking status
  3. Step 12 `final-gate-validator` returned `status: "passed"`
  4. Pipeline state shows all steps completed
- **Staging**: `git add <path>` for each related file. Never `git add -A`. Never stage `.env*`, credentials, keys.
- **Commit message**: Content-descriptive, not process-descriptive. Use conventional commits (`feat:`, `fix:`, `docs:`, `chore:`). Describe WHAT changed. Anti-pattern: "Run full Cortex commit pipeline." Good: "feat: Phase 70-78 plans, update activeContext."
- **Includes**: All changes from Steps 0-11, including submodule reference
- **Post-commit**: `git show --stat` to verify

### Step 14: Push branch

- **Dependency**: After Step 13
- **GATE**: Verify user requested push (via `/cortex/commit`)
- Push current branch (including `main`) without extra confirmation
- **Non-blocking**: Push failures do not invalidate the commit
- **SSL errors**: Retry up to 2 times; if persistent, provide manual push instructions and link to troubleshooting

After commit+push, delegate to `commit-state-tracker` (checkpoint_clear).

### Step 15: Analyze (end-of-session) — MANDATORY

- **Dependency**: After Step 14
- Execute the **Analyze prompt** (`analyze.md`) in full, OR call `analyze(target="context")` then `analyze(target="usage_patterns")`
- **Non-blocking on connection errors**: If analysis fails after retry, record failure but do not invalidate commit

## Synapse Architecture (when modifying Synapse files)

- **Prompts**: Language-agnostic, project-agnostic. Use Cortex MCP tools, not raw commands.
- **Rules**: Language-specific rules allowed in `rules/{language}/`
- **Scripts**: Language-specific implementations in `scripts/{language}/`

## Git Safety

- **GATE**: Only commit/push when user explicitly invoked `/cortex/commit`
- Push current branch including `main` without extra confirmation
- Before `git add`: verify no sensitive files staged
- Selective staging only (no `git add -A`)

## Script Tracking

**Script use**: If any script is created or executed during this pipeline, MUST call `manage_session_scripts(operation="capture"|"analyze"|"suggest")`. Use script tooling whenever a script was run.

**COMMON ERRORS TO CATCH**: Script run without analysis (script executed but manage_session_scripts not called).

## Compound Engineering

This commit is the **Work** step of Plan -> Work -> Review -> Compound. Steps 5-6 and Step 15 are the **Compound** step: memory bank updates and session optimization.

**Compound checklist**:

1. Memory bank writes via `manage_file()` only
2. Roadmap edits via MCP tools only
3. Markdown lint early when editing markdown
4. Task-type-based token budgets in `load_context`
5. Connection closed: retry once, then use `execute_pre_commit_checks` for gates

## Failure Handling

- **Phase A fails**: Delegate to individual agents to fix, then re-run Phase A
- **Phase B fails**: Use `/cortex/fix` with `target=docs` to fix sync issues
- **Step 12 fails**: Fix within final-gate-validator (state machine fix loop); block commit if unresolvable
- **MCP disconnects**: Retry once (automatic via wrapper). To reconnect Cortex MCP, re-establish connection; then re-run the commit command from last checkpoint. See docs/guides/troubleshooting.md (mcp-disconnect-runbook-commit). MCP connection closed; fallback used when running checks via execute_pre_commit_checks. For markdown lint fallback when fix_markdown_lint unavailable: `npx markdownlint-cli2 --fix '**/*.md' '**/*.mdc'` (or markdownlint-cli2 from shell).
- **Step 12 fix loop**: If Step 12.2 (type) or 12.3 (quality/lint) fails after an edit, re-run Step 12.3 (and 12.1 if format changed). Verify `results.quality.success` and zero errors before proceeding. Do NOT proceed to Step 12.4 until Step 12.3 has been run again. Type or lint fixes can introduce new lint (e.g. E402).
- **Plan Status**: When delegating to plan-archiver, verify plan Status: VALUE (not **VALUE**); MD036 applies. For tests with side-effect imports use _ = module (or suppress reportUnusedImport) so linter is satisfied.
- **Intermediate Validation During Refactoring**: Run type+quality after each refactor; do not batch all changes then validate at end.
- **Duplicate Detection Before Creating Helpers**: Before creating helper functions, search for existing functions with similar names.
- **Context insufficient**: Provide comprehensive summary, advise re-running pipeline

## Success Criteria

- All steps 0-12 completed and passed
- Final gate validator returned `status: "passed"`
- Commit created with content-descriptive message
- Push completed (or non-blocking push failure documented)
- Analyze executed (or non-blocking analysis failure documented)
- Pipeline state checkpoint cleared
