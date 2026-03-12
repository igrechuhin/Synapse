# Create Plan from Description

**PURPOSE**: Create a plan document and register it in the roadmap. **NO CODE CHANGES.** This prompt produces a `.md` plan file only.

**CRITICAL**: Execute ALL steps below AUTOMATICALLY. Do NOT pause, summarize, or ask for confirmation unless clarification is genuinely needed. Start with Step 1 immediately.

**HARD GATE — VIOLATION IF BROKEN**: This prompt ONLY creates a plan file. It does NOT implement features, fix bugs, edit source files, or run quality checks. ALL additional context (error logs, code snippets, file references) is INPUT for plan creation — analyze it to write better implementation steps, DO NOT execute those steps. If you find yourself editing `.py`, `.ts`, or other source files: STOP immediately — you are in the wrong prompt.

## START HERE — Execute These Tool Calls Now

**Step 1**: Call `check_mcp_connection_health()`. If unhealthy, STOP.

**Step 2**: Call `get_structure_info()` to get `structure_info.paths.plans` (absolute path). Use this canonical path for all plan file operations. Do not hardcode `.cortex/plans/` or infer from `structure_info.root` — hardcoding paths is a VIOLATION.

**Step 3**: Call `manage_file(file_name="roadmap.md", operation="read")` to load current roadmap.

**Step 4**: Call `rules(operation="get_relevant", task_description="Plan creation, development planning")`. If `disabled`, read rules via the paths from Step 2.

After Step 4, continue to plan creation below. The steps below define the **implementation sequence**; execute them in order.

---

## Step 5: Check for Existing Related Plans

1. List existing plans: use `Glob` on `{plans_path}/*.md` (excluding archive/).
2. For each existing plan with YAML frontmatter, compute similarity score:
   - Same `component` value: +2
   - Same `work_type` value: +1
   - Title keyword overlap (>50% shared words): +1
3. **Decision**:
   - Score >= 3: **enrich** the existing plan (do not create a duplicate)
   - Score 1-2: ask user whether to enrich or create new
   - Score 0: create new plan
4. Check if roadmap references a Phase with status PLANNED but no corresponding plan file — if so, create the plan file now.

## Step 6: Analyze All Provided Context

1. Parse the user's plan description/request.
2. Analyze ALL attached files, code selections, error logs as INPUT for the plan.
3. Extract requirements, constraints, dependencies, success criteria.
4. If clarification is needed, ask the user specific questions before proceeding.

Use `think` tool for complex plans to scope the approach.

## Step 7: Create or Enrich the Plan

**If creating new**: Prefer `plan(operation="create", plan_title="...", description="...", component="...", work_type="...", priority="...", steps=[...])`.

Fallback if `plan(operation="create")` is unavailable: write the plan file using `Write` to `{plans_path}/{slug}.md` with this structure:
- YAML frontmatter (title, component, work_type, status: PENDING, priority, created, depends_on)
- Goal, Context, Implementation Steps
- Verification Checklist per step: What to search for | Search scope | Files to re-read
- Dependencies, Success Criteria
- Testing Strategy (95% coverage target)

**If enriching existing**: Read the existing plan, merge new requirements, update steps and priorities. Write back using `Write` or `Edit`.

## Step 8: Register Plan in Roadmap

Registering the plan in the roadmap is **REQUIRED** — every new or enriched plan MUST be registered.

Call `plan(operation="register", plan_title="...", description="...", status="PENDING", section="...")`.

**GATE**: If `plan(operation="register")` fails, STOP and report. **PROHIBITED**: StrReplace or direct Write on roadmap.md — this causes corruption and is a VIOLATION. Use MCP tools only.

Fallback for enriched plans: call `update_memory_bank(operation="roadmap_add", section="...", entry_text="...")`. When using fallback `manage_file(write)`, content must be full, unabridged roadmap (pre-write check: content length must be at least as long as the roadmap as read). Never truncate, never pass shortened or summarized roadmap content.

## Step 9: Verify Completion

1. Verify plan file exists in plans directory: `Read` the file and re-read to confirm.
2. Verify roadmap was updated: call `manage_file(file_name="roadmap.md", operation="read")` and confirm the entry is present.
3. Report: plan file path, plan title, roadmap update status.

---

## Path Resolution

All paths via `get_structure_info()` and `manage_file()`. Use the absolute path from `structure_info.paths.plans`. Never hardcode `.cortex/` paths.

## Error Handling

- **MCP tool crash/disconnect**: STOP, report with FIX-ASAP priority
- **3 consecutive MCP failures**: Circuit-breaker per `shared-conventions.md`
- **Plan file creation errors**: Check permissions, directory existence
- **Roadmap update errors**: Check format, report specific error

## Success Criteria

- Plan file created with all required sections (frontmatter, goal, steps, Verification Checklist, testing strategy with 95% coverage target)
- Plan registered in roadmap
- All paths obtained dynamically via MCP tools
