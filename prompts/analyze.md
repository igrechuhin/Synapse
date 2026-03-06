# Analyze (End of Session)

**AI EXECUTION COMMAND**: Run end-of-session analysis. Check all: (1) context effectiveness, (2) session optimization. Execute automatically; do not ask for permission.

This analysis is the **Compound** step of the Plan -> Work -> Review -> Compound loop; use it to make the next session easier.

**CRITICAL**: This is the single entry point for end-of-session analysis. Run all steps in order. If findings contain improvement recommendations, execute the Plan prompt with the analysis findings as input to create an improvements plan.

**END-TO-END EXECUTION**: Run this analysis from start to finish without stopping to announce the plan or ask for permission. Begin with the Pre-Analysis Checklist (memory bank, rules, structure path), then delegate to agents and assemble the report. Only stop if a tool fails or user input is explicitly required.

**CONNECTION ERROR HANDLING**: If any MCP tool call fails with "Connection closed" (MCP error -32000) or similar connection errors:

- The `mcp_tool_wrapper` decorator automatically retries connection errors once.
- If a tool fails after retry, skip that analysis step and continue with remaining steps.
- For `analyze(target="context")`: If it fails after retry, note "Context effectiveness analysis unavailable due to connection error" in the report and proceed with session optimization analysis.
- Complete as much of the analysis as possible; partial analysis is better than no analysis.

**Tooling**: Use Cortex MCP tools for memory bank, rules, and paths. Resolve paths via `get_structure_info()` (reviews directory, plans directory, memory bank). Use `manage_file()` for memory bank reads/writes. **manage_file contract**: Every `manage_file` call MUST include `file_name` and `operation`; never call `manage_file({})` or omit required parameters -- this causes validation errors. See memory-bank-workflow.mdc and AGENTS.md; do not hardcode `.cortex/` paths. **Memory bank write discipline:** roadmap.md and all other memory bank files may be updated **only** via Cortex MCP tools (`manage_file`, `remove_roadmap_entry`, `add_roadmap_entry`, etc.); do **not** use Write, StrReplace, or ApplyPatch on memory-bank paths.

**Agent Delegation**: This prompt orchestrates end-of-session analysis and delegates specialized tasks to dedicated agents in the Synapse agents directory:

- **common-checklist** -- Pre-analysis: Loads structure, memory bank, rules, and detects primary language
- **context-effectiveness-analyzer** -- Step 1: Context effectiveness evaluation
- **session-optimization-analyzer** -- Step 2: Session optimization and tool anomalies
- **tools-optimizer** -- Step 3: Tool set optimization audit
- **session-compactor** -- Step 4: Memory bank compaction + markdown lint
- **improvements-planner** -- Step 6: Conditional improvements plan creation

**Inter-agent communication**: All agents return structured results per `shared-handoff-schema.md`. The orchestrator validates required fields before assembling the report.

**Subagent execution: STRICTLY SEQUENTIAL.** Run each agent one at a time. Do not proceed to the next until the previous reports completion.

## Purpose

At end of session, run a single "check all" analysis: (1) evaluate `load_context` effectiveness and update statistics; (2) identify mistake patterns, root causes, and Synapse optimization recommendations, then save a report. Running this analysis is the **Compound** step of the loop: it captures mistake patterns, root causes, and recommendations so the next session can avoid repeating them; the session optimization report and memory bank updates are the primary compound artifacts.

## Pre-Analysis Checklist — Delegate to `common-checklist`

**Delegate to `common-checklist` agent** (Synapse agents directory).

The common-checklist agent loads all shared prerequisites:

- Project structure paths (plans, memory bank, reviews, rules)
- All core memory bank files (activeContext, roadmap, progress, systemPatterns, techContext)
- Relevant rules for `task_description="Coding standards, session analysis"`
- Primary language detection from techContext.md

**CRITICAL**: Verify the agent returns `status: "complete"` before proceeding. If `status: "error"`, STOP.

**Additional pre-analysis steps** (orchestrator, after common-checklist completes):

1. **Context-effectiveness recall** (for manual fallback if needed):
   - Recall `load_context` calls this session: task descriptions, files selected, relevance scores, token budget and utilization, agent roles.
   - Identify what context was actually used vs provided vs missing vs unused.

2. **Session scope**: Confirm reviews path is available from common-checklist result (`structure_info.paths.reviews`).

3. **Optional sequential thinking**: For complex sessions, use the `think` MCP tool in full mode to break down root causes before delegating.

After this checklist is satisfied, **continue directly to Step 1 without pausing for user confirmation.**

## Execution Order

### Step 1: Context Effectiveness -- Delegate to `context-effectiveness-analyzer`

- **Agent**: Use the `context-effectiveness-analyzer` agent for evaluating load_context effectiveness, token utilization, and role-aware statistics
- **CRITICAL**: Must complete before Step 2
- **Input**: Memory bank files, rules, reviews path (all loaded in Pre-Analysis Checklist)
- **Output needed**: sessions_analyzed, calls_analyzed, key_metrics, role_recommendations, zero_budget_warnings, status
- **If no_data**: Expected for analysis-only sessions; agent handles gracefully

### Step 2: Session Optimization -- Delegate to `session-optimization-analyzer`

- **Agent**: Use the `session-optimization-analyzer` agent for identifying mistake patterns, root causes, and generating Synapse optimization recommendations
- **CRITICAL**: Must complete before Step 3
- **Input**: Memory bank files, rules, session data (tool outputs, diffs, commit results)
- **Output needed**: mistake_patterns, root_causes, recommendations, tool_anomalies

### Step 3: Tools Optimization -- Delegate to `tools-optimizer`

- **Agent**: Use the `tools-optimizer` agent for auditing tool set budget compliance and optimization opportunities
- **CRITICAL**: If tool count exceeds 40 target, flag as CRITICAL in report
- **Input**: Memory bank context, reviews path
- **Output needed**: tool_budget, dead_tools, duplicates, incomplete_consolidations, consolidation_candidates, total_reduction_potential, actionable_recommendation, report_subsection, status
- **Skip if**: Agent reports `status="unavailable"` (query_usage data not available)

### Report Assembly (orchestrator)

After Steps 1-3 complete, assemble the combined report:

1. Call `get_structure_info()` and use `structure_info.paths.reviews`.
2. Generate timestamp via shell `date +%Y-%m-%dT%H-%M`. **Use real time only.** Do not invent values.
3. Assemble report using Output Format below with outputs from all agents.
4. **Filename**: `session-optimization-YYYY-MM-DDTHH-MM.md`.
5. Write the **full** report to `{reviews_path}/session-optimization-YYYY-MM-DDTHH-MM.md` (no truncation).
6. **MD024 (Duplicate Heading)**: If appending to an existing review file, suffix headings to avoid duplicates.

### Step 4: Maintenance -- Delegate to `session-compactor`

- **Agent**: Use the `session-compactor` agent for memory bank compaction and markdown lint enforcement
- **Input**: Session summary (from Step 2 findings), report file path (from Report Assembly)
- **Output needed**: compaction_status, session_id, token_savings, snapshot_paths, lint_status
- **Note**: Runs AFTER report is written so the report file is included in lint

### Step 5 (Optional): Health / Session Scripts

If project scope includes health check or session-scripts analysis, call relevant tools and include a short subsection in the report. Otherwise omit.

### Step 6: Improvements Plan -- Delegate to `improvements-planner`

- **Agent**: Use the `improvements-planner` agent for creating improvement plans from analysis findings
- **CRITICAL**: Only runs when recommendations exist from Steps 1-3
- **Input**: Full assembled report content, report file location, tools optimization findings, optimization recommendations, context effectiveness recommendations
- **Output needed**: status, plan_file, roadmap_updated
- **Skip if**: No improvement recommendations exist across all analysis steps

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
- Avg Token Utilization / Precision-Recall / Feedback type
- Task patterns and recommendations

## Session Optimization Analysis

### Mistake Patterns Identified
...

### Root Cause Analysis
...

### Optimization Recommendations
...

### Tools optimization (MANDATORY when usage data available)
[tools-optimizer agent output: tool budget, dead tools, duplicates,
incomplete consolidations, consolidation candidates, total reduction potential]

### Tool use anomalies (optional)
[session-optimization-analyzer tool_anomalies output, if available]

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
- Step 1 (context effectiveness) executed via `context-effectiveness-analyzer` agent; tool called and/or manual fallback applied when no_data.
- Step 2 (session optimization) executed via `session-optimization-analyzer` agent; findings collected.
- Step 3 (tools optimization) executed via `tools-optimizer` agent when usage data available; five problem classes checked; Tools optimization subsection added with per-tool call counts and specific actions. If tool count exceeds 40 target, flagged as CRITICAL.
- Report assembled and saved to reviews directory using path from `get_structure_info()`.
- Step 4 (maintenance) executed via `session-compactor` agent; `session(operation="compact")` called, handoff written, token savings reported, markdown lint enforced.
- Step 6: If findings contain improvement recommendations (including tools optimization), `improvements-planner` agent executed; improvements plan created and registered in roadmap. If no recommendations, step skipped.
- No hardcoded `.cortex/` paths; all paths from MCP or `get_structure_info()`.
- Single report produced with both Context Effectiveness and Session Optimization sections.
