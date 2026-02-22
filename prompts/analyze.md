# Analyze (End of Session)

**AI EXECUTION COMMAND**: Run end-of-session analysis. Check all: (1) context effectiveness, (2) session optimization. Execute automatically; do not ask for permission.

This analysis is the **Compound** step of the Plan → Work → Review → Compound loop; use it to make the next session easier.

**CRITICAL**: This is the single entry point for end-of-session analysis. Run all steps in order. If findings contain improvement recommendations, execute the Plan prompt with the analysis findings as input to create an improvements plan.

**END-TO-END EXECUTION**: Run this analysis from start to finish without stopping to announce the plan or ask for permission. Begin with the Pre-Analysis Checklist (memory bank, rules, structure path), then run analysis steps and write the report. Only stop if a tool fails or user input is explicitly required.

**CONNECTION ERROR HANDLING**: If any MCP tool call fails with "Connection closed" (MCP error -32000) or similar connection errors:

- The `mcp_tool_wrapper` decorator automatically retries connection errors once.
- If a tool fails after retry, skip that analysis step and continue with remaining steps.
- For `analyze_context_effectiveness`: If it fails after retry, note "Context effectiveness analysis unavailable due to connection error" in the report and proceed with session optimization analysis.
- Complete as much of the analysis as possible; partial analysis is better than no analysis.

**Tooling**: Use Cortex MCP tools for memory bank, rules, and paths. Resolve paths via `get_structure_info()` (reviews directory, plans directory, memory bank). Use `manage_file()` for memory bank reads/writes. **manage_file contract**: Every `manage_file` call MUST include `file_name` and `operation`; never call `manage_file({})` or omit required parameters—this causes validation errors. See memory-bank-workflow.mdc and AGENTS.md; do not hardcode `.cortex/` paths. **Memory bank write discipline:** roadmap.md and all other memory bank files may be updated **only** via Cortex MCP tools (`manage_file`, `remove_roadmap_entry`, `add_roadmap_entry`, etc.); any edit (including one-line fixes) must use `manage_file(operation='read')` then `manage_file(operation='write', content=...)`—do **not** use Write, StrReplace, or ApplyPatch on memory-bank paths.

**Phases**: (1) **Context & rules load** — read memory bank and rules via `manage_file()` and `rules()`/structure path. (2) **Analysis & insights** — `analyze_context_effectiveness()`, session data, `get_context_usage_statistics()`, `get_memory_bank_stats()`, `suggest_refactoring()` as needed. (3) **Outputs & plans** — write report to reviews directory (path from `get_structure_info()` → `structure_info.paths.reviews`); if recommendations exist, run Create Plan prompt. Aligns with Phase D (Session Analysis) in `docs/design/commit-pipeline-phases.md` (runs after successful commit when invoked from commit pipeline).

## Purpose

At end of session, run a single "check all" analysis: (1) evaluate `load_context` effectiveness and update statistics; (2) identify mistake patterns, root causes, and Synapse optimization recommendations, then save a report. This replaces the former separate "Analyze Context Effectiveness" and "Analyze Session Optimization" prompts. Running this analysis is the **Compound** step of the loop: it captures mistake patterns, root causes, and recommendations so the next session can avoid repeating them; the session optimization report and memory bank updates are the primary compound artifacts.

## Pre-Analysis Checklist (Phase 1: Context & Rules Load)

**BEFORE running any analysis step:**

1. **Read relevant memory bank files** (Cortex MCP tool `manage_file`). **Before each manage_file call**: Verify `file_name` and `operation` are set; never call `manage_file({})` or omit required parameters. Read both activeContext and roadmap so end-of-session analysis reflects completed work (activeContext) and current/upcoming work (roadmap):
   - `activeContext.md` – completed work only (for current status and upcoming work see roadmap.md)
   - `roadmap.md` – current status and upcoming work
   - `progress.md` – recent achievements
   - `systemPatterns.md` – architectural patterns
   - `techContext.md` – technical context

2. **Read relevant rules** (Cortex MCP tool `rules(operation="get_relevant", task_description="Coding standards, session analysis")` or rules directory path from `get_structure_info()` → `structure_info.paths.rules`).
   - **FIRST**: Check rules indexing status by inspecting the `rules_manager_status.indexed_files` field in the `rules()` response.
   - **When rules indexing is enabled and `indexed_files > 0`**: Treat rules as a **first-class source** of coding standards. Use `rules(operation="get_relevant", ...)` as the primary method for loading rules. The indexed rules will be automatically selected based on relevance to the task description.
   - **When `rules()` returns `status: "disabled"` or `indexed_files=0`**: Fall back to reading key rules from the Synapse rules directory (path from `get_structure_info()` → `structure_info.paths.rules`) or from AGENTS.md/CLAUDE.md for coding standards and memory bank access.
   - **Troubleshooting**: If rules are enabled (`rules_enabled: true` in optimization.json) but `indexed_files=0`, run `rules(operation="index", force=True)` to index rules, then retry `get_relevant`. If indexing still returns 0 files, check that the `rules_folder` path in optimization.json points to a directory containing `.mdc` rule files.
   - **Rule discovery fallback**: When `rules()` returns empty results or the task involves tool implementation/refactoring, also check `get_synapse_rules(task_description="[language] models, structured data")` or read AGENTS.md/CLAUDE.md for language-specific structured-data standards.

3. **Context-effectiveness recall** (for manual fallback if needed):
   - Recall `load_context` / `load_progressive_context` calls this session: task descriptions, files selected, relevance scores, token budget and utilization, agent roles.
   - Identify what context was actually used: files read, modified, mentioned; files needed but missing; files provided but unused.
   - **AgentRole awareness**: Context-effectiveness analysis tracks statistics by agent role (feature/quality/testing/docs/planning/debugging/review). The `analyze_context_effectiveness()` tool provides role-aware insights and budget recommendations. Roles are automatically detected from task descriptions and logged for analysis.

4. **Session scope**: Confirm current session context and that reviews path is available via `get_structure_info()` → `structure_info.paths.reviews`.

5. **Optional sequential thinking**: For complex sessions with many intertwined issues or recommendations, you may call the `sequentialthinking` MCP tool to break down root causes and optimization steps into numbered thoughts before drafting the final report.

## Execution Order

### Step 1: Context Effectiveness (Phase 2: Analysis & Insights)

**⚠️ Zero-budget/zero-files reminder**: Zero-budget (`token_budget=0`) or zero-files (`files_selected=0`) `load_context` calls are only acceptable for trivial/no-op tasks. For non-trivial tasks (refactor/fix/debug/implement), these indicate a configuration error and the tool returns a validation error when `token_budget=0` is passed. INCORRECT: `load_context(task_description="end-of-session analysis", token_budget=0)`. CORRECT: `load_context(task_description="end-of-session analysis", token_budget=5000)` or `load_context(task_description="end-of-session analysis")` (uses default).

1. Call `analyze_context_effectiveness()` (default: current session only).
2. If the tool returns `"status": "no_data"` (e.g. no `load_context` calls this session), that is expected for **analysis-only sessions** (e.g. when the only action in the session is running this Analyze prompt). Proceed to manual fallback if useful. **Optional**: To record one call for context-effectiveness metrics, the agent may call `session_start()` or `load_context(task_description="end-of-session analysis", token_budget=5000)` before running the analysis steps.
   - **Usage analysis**: Files used vs provided vs missing vs unused (from checklist).
   - **Scoring** (if applicable): precision, recall, F1, token efficiency; feedback categories (helpful, over_provisioned, under_provisioned, irrelevant, missed_dependencies).
   - **Role-aware statistics**: Context-effectiveness analysis breaks down statistics by agent role (feature/quality/testing/docs/planning/debugging/review). Review `role_recommendations` and `role_budget_recommendations` in the insights to understand role-specific patterns and tune budgets per role.
   - **Zero-budget/zero-files detection**: If `learned_patterns` includes warnings about `token_budget=0` or `files_selected=0` for non-trivial tasks (refactor/fix/debug/implement), this is a **configuration error**. Document in the report and recommend re-running `load_context` with appropriate budget (10k-15k for fix/debug, 20k-30k for implement/add).
3. Optionally call `get_context_usage_statistics()` for aggregated stats.
4. Optionally use `analyze_context_effectiveness(analyze_all_sessions=True)` for full history.
5. Summarize in **Context Effectiveness Analysis** (see Output Format below). If no data and no manual analysis, state "No session logs found" and suggest using `load_context()` at task start and re-running later.

### Step 2: Session Optimization (Phase 2 & 3: Analysis, then Outputs)

1. Use session data (tool outputs, memory-bank diffs, commit/pre-commit results, code changes) to identify:
   - **Mistake patterns**: type/system violations, code organization, rule compliance, process violations, tool usage, documentation.
   - **Root causes**: missing/unclear guidance, incomplete validation, process gaps, tool limitations.
   - **Memory bank write discipline**: When reporting mistake patterns related to memory bank edits (e.g., roadmap.md edited via Write/StrReplace instead of `manage_file()`, memory-bank files accessed via hardcoded paths), reference memory-bank-workflow.mdc and the dedicated MCP tools (`manage_file`, `remove_roadmap_entry`, `append_progress_entry`, etc.) to reinforce the correct pattern. All memory-bank file edits—including one-line fixes—must use `manage_file(operation='read')` then `manage_file(operation='write', content=...)`; do not use Write, StrReplace, or ApplyPatch on memory-bank paths.
2. Generate **prioritized recommendations** for Synapse prompts/rules (prompt improvements, rule improvements, process improvements) with target file/section and expected impact.
3. **Save the report** (Phase 3: Outputs):
   - Call `get_structure_info()` and use `structure_info.paths.reviews` (project root is resolved internally; do NOT pass it as a parameter).
   - **Filename**: `session-optimization-YYYY-MM-DDTHH-MM.md` (e.g. `session-optimization-2026-02-02T17-58.md`).
   - **Timestamp**: Use real time only (e.g. shell `date +%Y-%m-%dT%H-%M` or file mtime). Do not invent values.
   - Write the **full** report to `{reviews_path}/session-optimization-YYYY-MM-DDTHH-MM.md` (no truncation; same no-truncation rule as memory-bank writes per memory-bank-workflow.mdc).
4. **MD024 (Duplicate Heading)**: If appending a second pass (e.g. context-effectiveness addendum) to an existing review file, suffix headings (e.g. "(Addendum)", "(Context Effectiveness Pass)") to avoid duplicate headings.
5. **Tool use anomalies (optional)**: Call `get_session_tool_anomalies(hours=24)`. If the tool returns `"status": "success"`, add a **Tool use anomalies** subsection to the report with: tools used in the window (tool name, calls, retries, errors), high-retry tools, and high-error tools. If status is `"unavailable"` (e.g. usage tracker disabled), omit the subsection or note "Tool use anomalies: usage tracker unavailable."

### Step 3: Session Compaction (Phase 56)

**MANDATORY**: At end of session, compact memory bank files to reduce token usage and create session handoff:

1. Call `compact_session(summary="<brief session summary>")` tool:
   - Compacts `activeContext.md` (keeps current date's Completed Work, summarizes older dates)
   - Compacts `progress.md` (applies progressive summarization tiers)
   - Writes session handoff JSON to `.cortex/.cache/session/last_handoff.json`
   - Creates pre-compaction snapshots for rollback safety
   - Reports token savings
2. **Include handoff summary** in the report:
   - Session ID
   - Completed tasks (if extracted from activeContext)
   - Next actions (from summary parameter)
   - Token savings achieved
3. **Error handling**: If compaction fails, note in report but continue with remaining steps. Compaction is non-blocking for analysis completion.

**Note**: The session handoff JSON is automatically read by `session_start` at the beginning of the next session, providing continuity.

### Step 3.5: Markdown Lint Enforcement (Markdownlint CLI parity)

After writing the report and completing compaction, run markdown lint to ensure modified/new markdown files (including the new review) conform to the same rules as the CI quality gate:

1. Call `fix_markdown_lint(include_untracked_markdown=True, dry_run=False)`.
2. If the tool reports any remaining errors or a non-success status:
   - Treat this as a **mistake pattern** in the Session Optimization Analysis
   - Describe the affected files and rules in the report
   - Re-run `fix_markdown_lint` after applying fixes until the summary shows `Summary: 0 error(s)`.
3. **Do not skip this step**: markdownlint errors must be fixed before the session is considered complete so the CI quality gate will pass on push.
4. **Full-repo check** (optional): For comprehensive CI parity, run `node_modules/.bin/markdownlint-cli2 --fix` from the shell.

### Step 4 (Optional): Health / Session Scripts

If project scope includes health check or session-scripts analysis, add a step that calls the relevant tools and include a short subsection in the unified report. Otherwise omit.

### Step 5: Improvements Plan (Phase 3: Outputs & plans; when recommendations exist)

**If** the analysis findings contain **improvement recommendations** (e.g. non-empty **Optimization Recommendations**, context-effectiveness recommendations, or Synapse/prompt/rule improvement items):

1. **Execute the Plan prompt** (Create Plan) to create an improvements plan.
2. **Use the analysis findings as input** for the Plan prompt:
   - **Plan description**: Request an improvements plan based on the end-of-session analysis (e.g. "Create an improvements plan from the following end-of-session analysis").
   - **Additional context**: Provide the full analysis report as input—Summary, Context Effectiveness Analysis, Session Optimization Analysis (mistake patterns, root causes, optimization recommendations), and report location. The Plan prompt treats all of this as input for plan creation; do not fix issues or make code changes, only create the plan.
3. **Outcome**: The Plan prompt will create a plan file in the plans directory and register it in the roadmap. No separate approval step is required; execute the Plan prompt automatically when recommendations exist.

**If** there are no improvement recommendations in the findings, skip this step.

## Output Format

Produce a **single combined report** with clear sections:

```markdown
# End-of-Session Analysis

## Summary
[Brief combined overview]

## Context Effectiveness Analysis

**Sessions Analyzed**: X new, Y total (or "No session logs found.")
**Calls Analyzed**: Z (if any)

### Key Metrics (or Manual Summary)
- Avg Token Utilization / Precision–Recall / Feedback type
- Task patterns and recommendations

## Session Optimization Analysis

### Mistake Patterns Identified
...

### Root Cause Analysis
...

### Optimization Recommendations
...

### Tool use anomalies (optional)
When `get_session_tool_anomalies` was called and returned success: list tools used in the session window, tools with retries, and tools with errors. Omit if unavailable.

### Report Location
Saved to: {reviews_path}/session-optimization-YYYY-MM-DDTHH-MM.md

### Session Compaction
- Compaction executed: token savings, handoff written
- Session ID: {session_id}
- Rollback snapshots: {snapshot_paths}

### Improvements Plan (if recommendations existed)
- Plan prompt executed with analysis findings as input
- Plan file: {plans_path}/{plan-filename}.md
- Roadmap updated with new plan entry
```

## Success Criteria

- Pre-analysis checklist completed.
- Step 1 (context effectiveness) executed; tool called and/or manual fallback applied when no_data.
- Step 2 (session optimization) executed; report saved to reviews directory using path from `get_structure_info()`.
- Step 3 (session compaction) executed; `compact_session` called, handoff written, token savings reported.
- Step 5: If findings contain improvement recommendations, Plan prompt executed with analysis findings as input; improvements plan created and registered in roadmap. If no recommendations, step skipped.
- No hardcoded `.cortex/` paths; all paths from MCP or `get_structure_info()`.
- Single report produced with both Context Effectiveness and Session Optimization sections.
