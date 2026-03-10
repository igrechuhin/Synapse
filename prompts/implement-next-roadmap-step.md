# Implement Next Roadmap Step

**CRITICAL**: Execute ALL steps below AUTOMATICALLY. Do NOT pause, summarize, or ask for confirmation. Start with Step 1 immediately.

This is part of the **compound-engineering loop** (Plan → Work → Review → Compound). Memory bank updates in the Finalize section are the Compound step.

## START HERE — Execute These Tool Calls Now

**Step 1**: Call `check_mcp_connection_health()`. If unhealthy, STOP.

**Step 2**: Call `manage_file(file_name="roadmap.md", operation="read")` to read the roadmap.

**Step 3**: Identify the next pending step from the roadmap. Priority order: Blockers (ASAP) first, then Active Work, then Pending plans. If no pending steps: report "Roadmap complete" and STOP.

**Step 4**: Call `load_context(task_description="Implementing: {step_description}", token_budget=15000)`.

**Step 5**: Call `rules(operation="get_relevant", task_description="Implementation, coding standards, testing, quality")`. If `disabled`, read rules via `get_structure_info()`.

After Step 5, continue to Implementation below.

---

## Implementation

### Step 6: Plan

If a plan file exists for the selected roadmap step (check `.cortex/plans/` via `get_structure_info()`):
- Read the plan file for implementation details, success criteria, and testing strategy.

If no plan file: create an implementation plan based on the roadmap step description.

Use `think` tool for complex steps to break down the approach.

### Step 7: Code

Implement the changes:
- Follow coding standards from loaded rules (functions <= 30 lines, files <= 400 lines)
- Use dependency injection for external dependencies
- Write tests alongside implementation (AAA pattern, >= 95% coverage for new code)
- **After each file edit**: re-read the file to confirm the edit was applied
- **Before creating helpers**: search for existing functions with similar names (`Grep`) to avoid duplicates
- **Incremental validation**: after each refactor, run type check and quality check — do not batch

### Step 8: Quality Gate

Call `execute_pre_commit_checks(phase="A", test_timeout=300, coverage_threshold=0.90, strict_mode=False)`.

- If `preflight_passed: true`: proceed to Finalize.
- If `preflight_passed: false`: call `fix_quality_issues()`, then re-run. Max 3 iterations. If not converging (iteration 2 violations >= iteration 1): STOP.

**GATE**: Quality gate must pass before proceeding.

---

## Finalize

### Step 9: Memory Bank Updates

1. Call `update_memory_bank(operation="progress_append", date_str="YYYY-MM-DD", entry_text="**{step_title}** - COMPLETE. {summary}")` to add progress entry.
2. Call `update_memory_bank(operation="active_context_append", date_str="YYYY-MM-DD", title="{step_title}", summary="{summary}")` to update activeContext.
3. Call `update_memory_bank(operation="roadmap_remove", entry_contains="{unique roadmap entry substring}")` to remove the completed step from roadmap.

Use `manage_file()` only for memory bank writes — never StrReplace/Write/ApplyPatch on memory bank paths.

### Step 10: Plan Archiving

If a plan file was used:
1. Scan `.cortex/plans/` for the plan file. Verify its Status is COMPLETE.
2. Move to `.cortex/plans/archive/{category}/` (PhaseX/ for phase plans, Investigations/YYYY-MM-DD/ for investigations).
3. Verify the plan no longer exists in `.cortex/plans/` root.

### Step 11: Verification

1. Call `manage_file(file_name="roadmap.md", operation="read")` — verify the completed step is removed.
2. Call `manage_file(file_name="progress.md", operation="read")` — verify the completion entry exists.
3. Confirm no completed plans remain in `.cortex/plans/` root.

---

## Verification Gates

- **Post-edit**: After editing a file, re-read it to confirm the edit applied
- **Post-step**: After eliminating a pattern, search the full repository to confirm zero matches
- **Plan-scope**: Before marking complete, re-read Success Criteria and provide evidence for each
- **Duplicate-definition search**: Before modifying a function, search for all definitions of that name

## Error Handling

- **MCP unhealthy**: STOP immediately
- **No pending steps**: Report "Roadmap complete" and STOP
- **Quality gate fails after 3 iterations**: STOP, report unresolvable issues
- **Memory bank tool crash**: STOP, report with FIX-ASAP priority
- **Quality gate unavailable (doc-only sessions)**: Record "Quality gate skipped — environment (doc-only session)"

## Success Criteria

- Implementation complete and all tests pass
- Quality gate passed (zero lint, file-size, function-length, type_check violations)
- Coverage >= 90% global, >= 95% for new/modified code
- Memory bank updated (roadmap entry removed, progress added, activeContext updated)
- Completed plans archived
