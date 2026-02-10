# Analyze (End of Session)

**AI EXECUTION COMMAND**: Run end-of-session analysis. Check all: (1) context effectiveness, (2) session optimization. Execute automatically; do not ask for permission.

**CRITICAL**: This is the single entry point for end-of-session analysis. Run all steps in order. If findings contain improvement recommendations, execute the Plan prompt with the analysis findings as input to create an improvements plan.

**Tooling**: Use Cortex MCP tools for memory bank, rules, and paths. Resolve paths via `get_structure_info()`. Use `manage_file()` for memory bank reads/writes.

## Purpose

At end of session, run a single "check all" analysis: (1) evaluate `load_context` effectiveness and update statistics; (2) identify mistake patterns, root causes, and Synapse optimization recommendations, then save a report. This replaces the former separate "Analyze Context Effectiveness" and "Analyze Session Optimization" prompts.

## Pre-Analysis Checklist

**BEFORE running any analysis step:**

1. **Read relevant memory bank files** (Cortex MCP tool `manage_file`). Read both activeContext and roadmap so end-of-session analysis reflects completed work (activeContext) and current/upcoming work (roadmap):
   - `activeContext.md` – completed work only (for current status and upcoming work see roadmap.md)
   - `roadmap.md` – current status and upcoming work
   - `progress.md` – recent achievements
   - `systemPatterns.md` – architectural patterns
   - `techContext.md` – technical context

2. **Read relevant rules** (Cortex MCP tool `rules(operation="get_relevant", task_description="Coding standards, session analysis")` or rules directory path from `get_structure_info()` → `structure_info.paths.rules`). If rules indexing is disabled (`rules(operation="get_relevant", ...)` returns `status: "disabled"`), read key rules from the Synapse rules directory (path from `get_structure_info()` → `structure_info.paths.rules`) or from AGENTS.md/CLAUDE.md for coding standards and memory bank access.

3. **Context-effectiveness recall** (for manual fallback if needed):
   - Recall `load_context` / `load_progressive_context` calls this session: task descriptions, files selected, relevance scores, token budget and utilization.
   - Identify what context was actually used: files read, modified, mentioned; files needed but missing; files provided but unused.

4. **Session scope**: Confirm current session context and that reviews path is available via `get_structure_info()` → `structure_info.paths.reviews`.

5. **Optional sequential thinking**: For complex sessions with many intertwined issues or recommendations, you may call the `sequentialthinking` MCP tool to break down root causes and optimization steps into numbered thoughts before drafting the final report.

## Execution Order

### Step 1: Context Effectiveness

1. Call `analyze_context_effectiveness()` (default: current session only).
2. If the tool returns `"status": "no_data"` (e.g. no `load_context` calls this session), that is expected for workflow-only sessions; proceed to manual fallback if useful:
   - **Usage analysis**: Files used vs provided vs missing vs unused (from checklist).
   - **Scoring** (if applicable): precision, recall, F1, token efficiency; feedback categories (helpful, over_provisioned, under_provisioned, irrelevant, missed_dependencies).
3. Optionally call `get_context_usage_statistics()` for aggregated stats.
4. Optionally use `analyze_context_effectiveness(analyze_all_sessions=True)` for full history.
5. Summarize in **Context Effectiveness Analysis** (see Output Format below). If no data and no manual analysis, state "No session logs found" and suggest using `load_context()` at task start and re-running later.

### Step 2: Session Optimization

1. Use session data (tool outputs, memory-bank diffs, commit/pre-commit results, code changes) to identify:
   - **Mistake patterns**: type/system violations, code organization, rule compliance, process violations, tool usage, documentation.
   - **Root causes**: missing/unclear guidance, incomplete validation, process gaps, tool limitations.
2. Generate **prioritized recommendations** for Synapse prompts/rules (prompt improvements, rule improvements, process improvements) with target file/section and expected impact.
3. **Save the report**:
   - Call `get_structure_info()` and use `structure_info.paths.reviews` (project root is resolved internally; do NOT pass it as a parameter).
   - **Filename**: `session-optimization-YYYY-MM-DDTHH-MM.md` (e.g. `session-optimization-2026-02-02T17-58.md`).
   - **Timestamp**: Use real time only (e.g. shell `date +%Y-%m-%dT%H-%M` or file mtime). Do not invent values.
   - Write the full report to `{reviews_path}/session-optimization-YYYY-MM-DDTHH-MM.md` (e.g. via Write tool with the resolved path).
4. **MD024 (Duplicate Heading)**: If appending a second pass (e.g. context-effectiveness addendum) to an existing review file, suffix headings (e.g. "(Addendum)", "(Context Effectiveness Pass)") to avoid duplicate headings.

### Step 3 (Optional): Health / Session Scripts

If project scope includes health check or session-scripts analysis, add a step that calls the relevant tools and include a short subsection in the unified report. Otherwise omit.

### Step 4: Improvements Plan (when recommendations exist)

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

### Report Location
Saved to: {reviews_path}/session-optimization-YYYY-MM-DDTHH-MM.md

### Improvements Plan (if recommendations existed)
- Plan prompt executed with analysis findings as input
- Plan file: {plans_path}/{plan-filename}.md
- Roadmap updated with new plan entry
```

## Success Criteria

- Pre-analysis checklist completed.
- Step 1 (context effectiveness) executed; tool called and/or manual fallback applied when no_data.
- Step 2 (session optimization) executed; report saved to reviews directory using path from `get_structure_info()`.
- Step 4: If findings contain improvement recommendations, Plan prompt executed with analysis findings as input; improvements plan created and registered in roadmap. If no recommendations, step skipped.
- No hardcoded `.cortex/` paths; all paths from MCP or `get_structure_info()`.
- Single report produced with both Context Effectiveness and Session Optimization sections.
