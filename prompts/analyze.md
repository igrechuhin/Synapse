# Analyze (End of Session)

**CRITICAL**: Execute ALL steps below AUTOMATICALLY. Do NOT pause, summarize, or ask for confirmation. Start with Step 1 immediately.

## Clean Semantics

For `/cortex/analyze`, **clean** means **analysis-complete** for this session:

- Required analysis steps have run (or explicit unavailability is recorded).
- The session optimization report is written with required sections.
- Compaction/finalization steps are completed when available.

Git cleanliness is not the definition of clean in this prompt.

## Session Discipline

Use a single-goal session pattern to improve completion reliability (aligned with the superproject `CLAUDE.md` **Session Discipline** section):

- Confirm **one primary goal** early in the session and keep work scoped to that goal.
- If unrelated issues appear, note them and defer them to a separate follow-up session.
- If multiple unrelated fixes are already in progress, split execution into separate scoped passes instead of one mixed bundle.

**Step 5** below runs the **session scope risk check** during session optimization so multi-goal work is flagged when analysis data is available.

## START HERE — Pre-Analysis Checklist and First Tool Calls

**Step 1**: Call `session()` to verify MCP health. If unhealthy after retry, continue with available steps (partial analysis is better than none).

**Step 2**: Call `manage_file()` (zero-arg reads activeContext.md) to load session context.

After Step 2, continue to analysis steps below.

---

## Step 4: Context Effectiveness — @analyze-context subagent

Use @analyze-context to handle this step. If the subagent is unavailable, run inline:

Read the `cortex://analysis` resource (defaults to context analysis). Or if resource access fails, note "Context effectiveness analysis unavailable" and continue.

If the tool returns data, record: sessions analyzed, calls analyzed, token utilization, precision/recall, role recommendations, zero-budget warnings.

If `no_data` or connection error: note "Context effectiveness analysis unavailable" and continue.

## Step 5: Session Optimization — @analyze-session subagent

Use @analyze-session to handle this step. If the subagent is unavailable, run inline:

Run usage pattern analysis (set `analysis_target` in session config to "usage_patterns", then read `cortex://analysis` resource).

Record: mistake patterns, root causes, optimization recommendations, tool anomalies.

Session scope risk check: detect multi-goal sessions by scanning for unrelated objective clusters in the same session (for example, infrastructure/tooling fixes mixed with feature implementation or docs rewrites). Treat this as a scope lock violation against the single-goal session pattern.

If detected, add a "Session Scope Risk: multi-goal session" note with:

- one concrete split recommendation (how to split the goals into separate sessions/commits),
- one sentence explaining why the combined scope increased failure risk.

If connection error: note "Session optimization analysis unavailable" and continue.

## Step 6: Tools Optimization — @analyze-tools subagent

Use @analyze-tools to handle this step. If the subagent is unavailable, run inline:

Run tools analysis (set `analysis_target` in session config to "tools", then read `cortex://analysis` resource) if available.

Record: tool budget (registered count vs target of 40), dead tools, duplicates, consolidation candidates. If tool count exceeds 40 target, flag as CRITICAL.

If unavailable: skip and note "Tools optimization skipped (no usage data)".

## Step 6.4: Token Budget

Read the token budget section from `cortex://analysis` (JSON includes `token_budget.markdown`). Flag any memory bank file over 500 words as a compression candidate. If candidates exist, emit a recommendation to run `compress_memory_bank()` and include the token budget table in the session-optimization report (Step 7).

## Step 6.5: Memory Bank Health (non-blocking)

Memory-bank lint runs automatically inside the commit pipeline via `autofix`.
Skip this section — memory-bank health checks are not a separate step here.

## Step 7: Report Assembly — @analyze-compact subagent

Use @analyze-compact to assemble the report, route findings, and compact the memory bank. If the subagent is unavailable, run inline:

1. Generate timestamp: run `date +%Y-%m-%dT%H-%M`.
2. Assemble report combining Steps 4-6 findings using the format below.
3. Write report to `.cortex/reviews/session-optimization-{timestamp}.md`.

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

## Memory Bank Health

- Memory-bank lint runs automatically via `autofix` in the commit pipeline.

### Report Location

Saved to: {reviews_path}/session-optimization-{timestamp}.md
```

## Step 7.5: File Session Analysis Artifact (Always)

After Step 7 assembles and writes the session optimization report, always file it to the memory bank:

1. Call:
   - `manage_file(operation="file_artifact", artifact_type="session_analysis", title="Session Optimization {timestamp}", content="<full session analysis markdown>")`
2. Treat artifact filing as required for successful completion (do not skip based on score).
3. Record the returned memory-bank analyses path in the final `## Output` table. When the attached project has a wiki layout at `.cortex/wiki/`, the same `file_artifact` call also mirrors the artifact into `.cortex/wiki/analyses/`; record that wiki path when present (otherwise note that no wiki mirror applied).

## Step 8: Memory Bank Compaction

Call `session(operation="compact")` to compact memory bank. Record token savings and snapshot paths.

Call `autofix()` to ensure markdown quality on any modified files.

## Step 9a: Skill Router (conditional)

If Steps 4-6 produced recommendations about tool usage patterns, workflow patterns, or missing reusable agent capabilities:

1. Check for an existing skill first via `skill_pack(operation="load", pack_name="<slug>")` so you can merge or update instead of overwriting.
2. Write or update the JSON file using `write_artifact(artifact_type="skill", name="<slug>", content="<json>")`. Schema:

   ```json
   {
     "name": "<slug>",
     "description": "<one-line purpose>",
     "tools": ["<tool1>", "<tool2>"],
     "when_to_use": "<trigger condition>",
     "workflow_sequences": ["tool_a(...) → tool_b(...)"],
     "example_invocations": ["tool_a(param=value)"],
     "troubleshooting_tips": ["If X, do Y."],
     "keywords": ["keyword1", "keyword2"]
   }
   ```

3. Prefer reusable instructions applicable to future sessions, not one-off notes.
4. Record what changed in the final report `## Next` section when relevant.

**Path**: `src/cortex/resources/skills/<name>.json`

If no skill-oriented recommendations exist: skip this step.

## Step 9b: Plan Router (conditional)

If Steps 4-6 produced recommendations about bugs, missing features, or agent/script improvements:

1. Call `plan(operation="create", plan_title="Session improvements from {timestamp}", description="...")`.
2. Call `plan(operation="register", ...)` to add to roadmap.

If no plan-oriented recommendations exist: skip this step.

## Step 9c: Rule Router (conditional)

If Steps 4-6 produced recommendations about recurring standards violations or new enforceable standards:

1. Choose the appropriate subdirectory: `.cortex/synapse/rules/general/` for language-agnostic rules, `.cortex/synapse/rules/python/` (or other language dir) for language-specific ones.
2. Write or update the `.mdc` file using `write_artifact(artifact_type="rule", name="<general|python|...>/<slug>.mdc", content="<mdc>")`. Required frontmatter:

   ```markdown
   ---
   description: <one-line description>
   globs: <file globs this rule applies to, or omit for global>
   alwaysApply: false
   created_by: analyze-feedback-loop
   ---

   <rule body>
   ```

3. Keep rules language-agnostic unless the recommendation is explicitly language-specific.

**Path**: `.cortex/synapse/rules/<general|python|...>/<slug>.mdc`

If no rules-oriented recommendations exist: skip this step.

---

## Connection Error Handling

If any MCP tool fails with "Connection closed" (MCP error -32000):

- The `mcp_tool_wrapper` automatically retries once
- If retry fails, skip that analysis step and continue
- Complete as much analysis as possible

## Final report (required format)

**MANDATORY**: Use the **Artifact** report type from `docs/guides/synapse-final-report-templates.md`.

```markdown
## Result

✅ Analysis complete

## Output

| Field | Value |
|-------|-------|
| Report | `.cortex/reviews/session-optimization-<timestamp>.md` |
| Session artifact | Memory bank: `.cortex/memory-bank/analyses/<file>.md`; wiki mirror (only if `.cortex/wiki/` exists): `.cortex/wiki/analyses/<file>.md` |
| Compaction | <before> → <after> tokens (<n>% reduction) |
| Skill updated | <path OR —> |
| Plan created | <path OR —> |
| Rule created | <path OR —> |

## Next

<action items OR None>
```

**Rules**:

- Session artifact row must list the memory-bank path from the tool response and, when a wiki is present, the mirrored `.cortex/wiki/analyses/` path (or state explicitly that no wiki mirror occurred).
- Include compaction metrics when `session(compact)` ran
- Skill updated row only if Step 9a produced a skill artifact
- Plan created row only if Step 9b produced a plan
- Rule created row only if Step 9c produced a rule file

## Success Criteria

- Steps 4-6 executed (or gracefully skipped on connection errors)
- Report assembled and saved to `.cortex/reviews/`
- Memory bank compaction executed
- Step 9a: Skill updated or created if tool/workflow patterns found
- Step 9b: Plan created and registered if bugs/features/improvements found
- Step 9c: Rule created or updated if recurring violations or new standards found
