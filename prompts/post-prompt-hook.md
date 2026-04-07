---
title: "Post-Prompt Hook: Session Analysis Router"
component: synapse
work_type: hook
status: stable
priority: normal
---

## Post-Prompt Hook: Session Analysis Router

**Scope**: This file is a **lightweight post-prompt hook**, not a standalone user-facing prompt. It is intended to run **after another prompt's final report** has been written, in order to analyze the just-completed session and emit self-improvement artifacts.

**Caller guard (recursion safety)**:

- If the current prompt is `/cortex/analyze` (i.e. you are already executing `analyze.md`), **skip this hook entirely** to avoid recursive analysis loops.
- Callers MUST treat this hook as **non-blocking**: if any step fails due to MCP connectivity or other non-critical errors, record the failure in the calling prompt's final report `## Next` section and continue.

---

## Step 4: Context Effectiveness

Read the `cortex://analysis` resource (defaults to context analysis). Or if resource access fails, note "Context effectiveness analysis unavailable" and continue.

If the tool returns data, record: sessions analyzed, calls analyzed, token utilization, precision/recall, role recommendations, zero-budget warnings.

If `no_data` or connection error: note "Context effectiveness analysis unavailable" and continue.

## Step 5: Session Optimization

Run usage pattern analysis (set `analysis_target` in session config to "usage_patterns", then read `cortex://analysis` resource).

Record: mistake patterns, root causes, optimization recommendations, tool anomalies.

Session scope risk check: detect multi-goal sessions by scanning for unrelated objective clusters in the same session (for example, infrastructure/tooling fixes mixed with feature implementation or docs rewrites). Treat this as a scope lock violation against the single-goal session pattern.

If detected, add a "Session Scope Risk: multi-goal session" note with:

- one concrete split recommendation (how to split the goals into separate sessions/commits),
- one sentence explaining why the combined scope increased failure risk.

If connection error: note "Session optimization analysis unavailable" and continue.

## Step 6: Tools Optimization

Run tools analysis (set `analysis_target` in session config to "tools", then read `cortex://analysis` resource) if available.

Record: tool budget (registered count vs target of 40), dead tools, duplicates, consolidation candidates. If tool count exceeds 40 target, flag as CRITICAL.

If unavailable: skip and note "Tools optimization skipped (no usage data)".

## Step 7: Report Assembly

1. Generate timestamp: run `date +%Y-%m-%dT%H-%M`.
2. Assemble analysis notes combining Steps 4–6 findings. You may either:
   - append them to an existing session report created by the calling prompt, or
   - write a separate lightweight report under `.cortex/reviews/` if the calling prompt did not already create one.
3. When writing a new report file, prefer the naming pattern: `.cortex/reviews/post-prompt-analysis-{timestamp}.md`.

The exact report body may be simpler than the full `analyze.md` template, but it should still include:

- a brief summary,
- sections for context effectiveness, session optimization, and tools optimization (even if some are marked unavailable),
- a note of where the report was saved.

## Step 8: Memory Bank Compaction (optional)

If the calling prompt has already run full end-of-session compaction (for example, `/cortex/analyze` called `session(operation="compact")` earlier in the session), **do not run compaction again**.

Otherwise, when appropriate for the calling workflow:

- Call `session(operation="compact")` to compact the memory bank.
- Record token savings and snapshot paths in the report or in the calling prompt's final report `## Output` section.

If compaction is skipped (for example, short/low-impact sessions), record "Compaction skipped (not required for this prompt)."

## Step 9: Improvements Router and Minimal Final Report

This router mirrors the behavior of `analyze.md` Steps 9a (Skill Router), 9b (Plan Router), and 9c (Rule Router), but is invoked from the post-prompt context after another prompt's final report.

If Steps 4–6 produced improvement recommendations:

1. Inspect findings for three categories of improvements:
   - tool/workflow usage patterns or sequences that suggest new or updated Skills,
   - bugs, missing features, or agent improvements that suggest new or updated Plans,
   - recurring rule violations or new standards that suggest new or updated Rules.
2. For each applicable category, create or update artifacts:
   - **Skills** (`src/cortex/resources/skills/<name>.json`): read existing files first, then write/update via `write_artifact(artifact_type="skill", name="<slug>", content="<json>")`. Schema: `{"name","description","tools","when_to_use","workflow_sequences","example_invocations","troubleshooting_tips","keywords"}`.
   - **Plans** (`.cortex/plans/`): call `plan(operation="create", ...)` then `plan(operation="register", ...)`.
   - **Rules** (`.cortex/synapse/rules/<general|python|...>/<slug>.mdc`): write via `write_artifact(artifact_type="rule", name="<general|python|...>/<slug>.mdc", content="<mdc>")` with frontmatter `description`, `alwaysApply: false`, `created_by: analyze-feedback-loop`.

Multiple artifact types are not mutually exclusive — emit **all** that apply.

### Minimal Final Report (Artifact Summary)

At the end of this hook, update the calling prompt's final report (or the hook's own lightweight report) with a minimal artifact summary table:

```markdown
## Post-Prompt Hook Result

| Artifact Type | Produced | Location or Notes |
|---------------|----------|-------------------|
| Skill         | Yes/No   | <path or "—">     |
| Plan          | Yes/No   | <path or "—">     |
| Rule          | Yes/No   | <path or "—">     |
```

If no artifacts were produced, set all rows to `No` and add a short reason (for example, "No actionable recommendations in analysis output").
