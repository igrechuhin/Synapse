# Analyze (End of Session)

**CRITICAL**: Execute ALL steps below AUTOMATICALLY. Do NOT pause, summarize, or ask for confirmation. Start with Step 1 immediately.

## START HERE — Pre-Analysis Checklist and First Tool Calls

**Step 1**: Call `check_mcp_connection_health()`. If unhealthy after retry, continue with available steps (partial analysis is better than none).

**Step 2**: Call `load_context(task_description="End-of-session analysis: context effectiveness, session optimization", token_budget=4000)`.

**Step 3**: Call `manage_file(file_name="activeContext.md", operation="read")` and `manage_file(file_name="progress.md", operation="read")` to load session context.

After Step 3, continue to analysis steps below.

---

## Step 4: Context Effectiveness

Call `analyze(target="context")`.

If the tool returns data, record: sessions analyzed, calls analyzed, token utilization, precision/recall, role recommendations, zero-budget warnings.

If `no_data` or connection error: note "Context effectiveness analysis unavailable" and continue.

## Step 5: Session Optimization

Call `analyze(target="usage_patterns")`.

Record: mistake patterns, root causes, optimization recommendations, tool anomalies.

If connection error: note "Session optimization analysis unavailable" and continue.

## Step 6: Tools Optimization

Call `analyze(target="tools")` if available.

Record: tool budget (registered count vs target of 40), dead tools, duplicates, consolidation candidates. If tool count exceeds 40 target, flag as CRITICAL.

If unavailable: skip and note "Tools optimization skipped (no usage data)".

## Step 7: Report Assembly

1. Call `get_structure_info()` to get `structure_info.paths.reviews`.
2. Generate timestamp: run `date +%Y-%m-%dT%H-%M`.
3. Assemble report combining Steps 4-6 findings using the format below.
4. Write report to `{reviews_path}/session-optimization-{timestamp}.md`.

### Output Format

```markdown
# End-of-Session Analysis

## Summary
[Brief combined overview]

## Context Effectiveness Analysis
**Sessions Analyzed**: X new, Y total (or "No session logs found.")
**Calls Analyzed**: Z
### Key Metrics
- Token utilization, precision/recall, feedback types

## Session Optimization Analysis
### Mistake Patterns Identified
### Root Cause Analysis
### Optimization Recommendations
### Tools Optimization
[Tool budget, dead tools, duplicates, consolidation candidates]

### Report Location
Saved to: {reviews_path}/session-optimization-{timestamp}.md
```

## Step 8: Memory Bank Compaction

Call `session(operation="compact")` to compact memory bank. Record token savings and snapshot paths.

Run `fix_markdown_lint()` on the report file to ensure markdown quality.

## Step 9: Improvements Plan (conditional)

If Steps 4-6 produced improvement recommendations:
1. Call `plan(operation="create", plan_title="Session improvements from {timestamp}", description="...")`.
2. Call `plan(operation="register", ...)` to add to roadmap.

If no recommendations: skip this step.

---

## Connection Error Handling

If any MCP tool fails with "Connection closed" (MCP error -32000):
- The `mcp_tool_wrapper` automatically retries once
- If retry fails, skip that analysis step and continue
- Complete as much analysis as possible

## Success Criteria

- Steps 4-6 executed (or gracefully skipped on connection errors)
- Report assembled and saved to reviews directory
- Memory bank compaction executed
- Improvements plan created if recommendations exist
- All paths from `get_structure_info()` (no hardcoded `.cortex/` paths)
