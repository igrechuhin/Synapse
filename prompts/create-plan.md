# Create Plan from Description

**AI EXECUTION COMMAND**: Create a development plan based on user description, add it to the **plans directory**, **and register it in the roadmap**. Plan creation is NOT complete until both (1) the plan file exists in the plans directory and (2) the roadmap contains an entry for that plan. **Resolve paths via Cortex MCP**: use `get_structure_info()` for the plans directory path; use `manage_file()` for the roadmap (memory bank).

**CRITICAL**: These steps are for the AI to execute AUTOMATICALLY. DO NOT ask the user for permission or confirmation unless clarification is needed. Execute immediately after gathering necessary information.

**CURSOR COMMAND**: This is a Cursor command from the Synapse prompts directory, NOT a terminal command.

**⚠️ MANDATORY: When a plan is requested, ALL additional context is INPUT for plan creation, NOT separate issues to fix.**

- If the user provides error logs, code snippets, or other context along with a plan request, treat ALL of it as input for creating the plan
- DO NOT attempt to fix issues, debug code, or make code changes when a plan is requested
- The ONLY action should be creating a plan that addresses the described issue/problem/feature
- Any errors, logs, or code provided should be analyzed and incorporated into the plan as context, requirements, or constraints

**Tooling Note**: Use standard Cursor tools (`Read`, `ApplyPatch`, `Write`, `LS`, `Glob`, `Grep`) by default; MCP filesystem tools are optional fallbacks only when standard tools are unavailable or explicitly requested. **MANDATORY: Use Cortex MCP tools for all memory bank and structure operations** - do NOT access files directly via hardcoded paths.

**Path Resolution**: Resolve all paths via Cortex MCP tools (see memory-bank-workflow.mdc and AGENTS.md). Use `get_structure_info()` for plans/memory_bank/rules paths; use `manage_file(file_name="roadmap.md", ...)` for roadmap. Use the **absolute path** from `structure_info.paths.plans`; do not hardcode `.cortex/` or `structure_info.root` or memory-bank paths. Use canonical paths from the tool only.

**Sequential Thinking**: If the `think` tool from Cortex MCP is available, use it in full mode (thought_number, total_thoughts, next_thought_needed) to ensure best results when creating the plan.

**Agent Delegation**: This prompt orchestrates plan creation and delegates specialized tasks to dedicated agents in the Synapse agents directory:

- **common-checklist** - Loads project structure, memory bank, rules, and detects primary language
- **plan-creator** - Creates the development plan from description
- **memory-bank-updater** - Updates roadmap.md with new plan entry

**Inter-agent communication**: All agents return structured results per `shared-handoff-schema.md`. The orchestrator validates required fields before passing data downstream.

**Existing Plan Reuse (CRITICAL)**: Before creating a brand-new plan, you MUST check whether a same/similar plan already exists.

- If a similar plan already exists, you MUST **enrich and reprioritize the existing plan**, not create a duplicate.
- Only create a new plan when there is no clearly-related existing plan.

When executing steps, delegate to the appropriate agent for specialized work, then continue with orchestration.

## ⚠️ MANDATORY PRE-ACTION CHECKLIST

**Delegate to `common-checklist` agent** (Synapse agents directory).

The common-checklist agent loads all shared prerequisites:

- Project structure paths (plans, memory bank, reviews, rules)
- All core memory bank files (activeContext, roadmap, progress, systemPatterns, techContext)
- Relevant rules for `task_description="Plan creation and roadmap management"`
- Primary language detection from techContext.md

**CRITICAL**: Verify the agent returns `status: "complete"` before proceeding. If `status: "error"`, STOP and report the failure.

**VIOLATION**: Executing this command without running `common-checklist` first is a CRITICAL violation that blocks proper plan creation.

## EXECUTION STEPS

**Phases**: (1) Common checklist (via `common-checklist` agent). (2) Existing-plan check — reuse vs new. (3) Create/enrich plan — `plan-creator` agent; **prefer `plan(operation="create", ...)`**. (4) Register in roadmap — `memory-bank-updater` agent; **use `plan(operation="register", ...)`** only. (5) Verify completion.

### Step 1: Check for Existing Related Plans (Phase 2: Reuse vs New)

1. **Discover existing plans**:
   - Use `get_structure_info()` paths (`structure_info.paths.plans`) to locate the plans directory.
   - Use standard tools (`LS`, `Read`, `Grep`) to inspect existing plan files and their titles.
   - Cross-check `roadmap.md` entries (via `manage_file(read)`) for plan titles and short descriptions.
2. **Check for roadmap references to non-existent plans**:
   - **CRITICAL**: If the roadmap (read via `manage_file(file_name="roadmap.md", operation="read")`) references a Phase with status PLANNED but no corresponding plan file exists in the **plans directory** (path from `get_structure_info()` → `structure_info.paths.plans`), you MUST create the plan file now.
   - At minimum, create a plan stub such as `phase-XX-<slug>.plan.md` in the plans directory; use DRY transclusion where appropriate to avoid duplicated content.
   - This prevents `roadmap_sync` from reporting `invalid_references` for missing plans.
3. **Identify same/similar plans**:
   - Compare the user description (title, keywords, problem domain) against:
     - Plan filenames (e.g., `phase-57-fix-markdown-lint-timeout.md`)
     - Plan titles and goals inside existing plan files
     - Roadmap entries that describe similar problems/features.
   - Treat a plan as **similar** if:
     - The main goal/problem matches, or
     - The same component/tool/phase is being improved in a related way.
4. **Decide reuse vs new**:
   - If one or more strong matches exist, select the **closest** existing plan as the **target plan**.
   - If no sufficiently similar plan exists, proceed with creating a **new** plan.
5. **Record decision**:
   - Keep track of whether you are **enriching an existing plan** (with its path) or **creating a new plan**. This decision controls later steps.

### Step 2: Analyze All Provided Context

**Use the `think` tool (if available) to scope the plan before analyzing.**

1. **Analyze the user's plan description AND all additional context**:
   - Parse the explicit plan description/request
   - **Analyze ALL attached files, code selections, error logs, etc. as INPUT for the plan**
   - Extract requirements, constraints, and context from error messages, logs, code snippets
   - Identify ambiguities or unclear requirements
   - Note missing information (scope, timeline, dependencies, success criteria)
   - Identify potential conflicts with existing plans or priorities
   - Extract technical constraints or preferences from provided context
   - **CRITICAL**: Treat errors/logs as requirements to address in the plan, NOT as issues to fix immediately

2. **If clarification is needed**, ask the user specific questions:
   - What is the primary goal of this plan?
   - What are the success criteria?
   - Are there any dependencies on other work?
   - What is the estimated timeline or priority?
   - Are there any technical constraints or preferences?
   - Who are the stakeholders or users affected?

3. **Wait for user responses** before proceeding to plan creation
4. **If no clarification is needed**, proceed directly to plan creation

### Step 3: Create or Enrich the Plan (Phase 3) - **Delegate to `plan-creator` agent**

**Use the `plan-creator` agent (Synapse agents directory) for this step.**

1. **Generate plan content** based on:
   - User's description (and clarifications if any)
   - **ALL provided context** (error logs, code snippets, file contents) as requirements/constraints
   - Project context from memory bank files
   - Architectural patterns and constraints
   - Best practices for plan structure
   - **CRITICAL**: Incorporate analysis of errors/logs into the plan as investigation steps, root cause analysis, or implementation requirements - do NOT fix them directly

2. **Use appropriate plan template** (if templates exist):
   - Check if plan templates exist in `{plans_dir}/templates/`
   - Use appropriate template (feature.md, bugfix.md, refactoring.md, research.md, etc.)
   - Customize template with plan-specific information

3. **Plan structure should include**:
   - **Title**: Clear, descriptive name for the plan
   - **Status**: Initial status (e.g., "Planning", "Pending")
   - **Goal**: Clear statement of what this plan achieves
   - **Context**: Why this plan is needed, user needs, business requirements
   - **Approach**: High-level implementation strategy
   - **Implementation Steps**: Detailed breakdown of tasks. Steps define an **implementation sequence** (like the roadmap): the implement command will execute them in order (Step 1, then Step 2, then Step 3, …). Number steps clearly and list them in the order they should be implemented; do not rely on agents to reorder or skip steps.
   - **Verification Checklist** (MANDATORY when steps eliminate or replace patterns): For each implementation step that removes or replaces something (e.g. remove `exec()`, replace string matching), define:
     - **What to search for**: Pattern that should be eliminated (e.g. `exec(`)
     - **Search scope**: Full repo, specific directory, or specific files
     - **Expected result**: Zero matches, specific count, or documented exception
     - **Files to re-read**: Which files must be re-read after editing to confirm the change
   - **Dependencies**: Dependencies on other plans or external work
   - **Success Criteria**: Measurable outcomes
   - **Technical Design**: Architecture, data model, UI/UX changes (if applicable)
   - **Testing Strategy (MANDATORY)**: Comprehensive testing requirements:
     - **Coverage Target**: Minimum 95% code coverage for ALL new functionality (MANDATORY)
     - **Unit Tests**: Test all public functions, methods, and classes individually
     - **Integration Tests**: Test component interactions and data flow
     - **Edge Cases**: Test boundary conditions, error handling, and invalid inputs
     - **Regression Tests**: Ensure existing functionality remains unaffected
     - **Test Documentation**: Document test scenarios and expected behaviors
     - **AAA Pattern**: All tests MUST follow Arrange-Act-Assert pattern
     - **No Blanket Skips**: Every skip MUST have justification and linked ticket
     - **Pydantic v2 for JSON Testing**: When testing MCP tool responses (e.g., `manage_file`, `rules`, `execute_pre_commit_checks`), use Pydantic v2 `BaseModel` types and `model_validate_json()` / `model_validate()` instead of asserting on raw `dict` shapes. See `tests/tools/test_file_operations.py` for examples (e.g., `ManageFileErrorResponse` pattern).
   - **Risks & Mitigation**: Potential risks and how to address them
   - **Timeline**: Estimated timeline or sprint breakdown
   - **Notes**: Additional context, decisions, open questions

4. **Create or update plan file**:
   - **If creating a new plan**:
     - **Prefer**: Use the Cortex MCP tool **`plan(operation="create", title=..., content=..., slug=...)`** when available. It resolves the plans directory, sanitizes the filename, and writes the file; no path hardcoding.
     - **Fallback**: If `plan(operation="create")` is unavailable or fails, generate a filename from the plan title (sanitize for filesystem), resolve plans path via `get_structure_info()` → `structure_info.paths.plans`, and use standard tools (`Write`) to create the plan file at `{plans_dir}/{plan-filename}.md`.
   - **If enriching an existing plan**:
     - Use `Read` to load the existing plan file identified in Step 2.5.
     - Merge the new description and context into the existing plan:
       - Update **Context**, **Goal**, **Approach**, **Implementation Steps**, and **Testing Strategy** to incorporate the new requirements/findings.
       - Optionally add a short dated sub-section (e.g., “### New Input (2026-01-28)”) summarizing the new request and how it affects the plan.
     - Use `Write` to save the updated plan file in-place (same path, no new file).

5. **Validate plan file**:
   - Verify file was created successfully
   - Check file content is complete and well-structured
   - Ensure all required sections are present

### Step 4: Register Plan in Roadmap (Phase 4, MANDATORY) - **Delegate to `memory-bank-updater` agent**

**Use the `memory-bank-updater` agent (Synapse agents directory) for this step.**

Every new or enriched plan MUST be registered in the roadmap. Do not skip this step.

**Never truncate** roadmap content when updating. Never pass **shortened** or **summarized** roadmap content to the write; the content written must be the full roadmap. **Pre-write content length check**: Before calling the write tool, verify that the new content length (e.g. string length or `len(content)`) is **at least as long** as the roadmap as read.

**PROHIBITED**: Using StrReplace, direct Write, or any edit that bypasses Cortex MCP tools on roadmap files is a critical violation.

1. **If this is a new plan** (sole API):
   - **REQUIRED**: Call `plan(operation=”register”, plan_title=..., description=..., status=”PENDING”, section=...)`.
   - Choose `section` from: `blockers` | `active_work` | `future` | `pending` (default).
   - The tool performs server-side read-modify-write and inserts the entry in the correct place. It automatically includes the plan file link for `roadmap_sync` validation.
   - **If `plan(operation=”register”)` fails**: STOP and report error. Do NOT fall back to `manage_file(write)` for single-entry adds — that path causes roadmap corruption from full-content string assembly.

2. **If enriching an existing plan**:
   - Use `update_memory_bank(operation=”roadmap_add”, section=..., entry_text=..., position=...)` to update the existing entry.
   - Expand the description, update priority/status, add urgency markers as needed.
   - Ensure the link to the plan file remains correct.

### Step 5: Verify Completion (Phase 5)

1. **Verify plan file exists**:
   - Check that plan file was created in the plans directory
   - Verify file content is complete and accurate

2. **Verify roadmap was updated**:
   - Re-read roadmap via `manage_file(file_name=”roadmap.md”, operation=”read”)`
   - Confirm the new or updated plan entry is present and correct
   - Check that roadmap entry is properly formatted and linked

3. **Provide summary** using **PlanCreatorResult** schema (see `shared-handoff-schema.md`):
   - Report plan creation status
   - Provide plan file path
   - Confirm roadmap update
   - Note any issues or warnings

## IMPLEMENTATION GUIDELINES

### Plan Quality

- **Completeness**: Ensure all required sections are present and filled
- **Clarity**: Use clear, concise language
- **Actionability**: Include specific, actionable steps
- **Measurability**: Define clear success criteria
- **Realism**: Set achievable timelines and scope

### Testing Requirements (MANDATORY)

- **Coverage**: Every plan MUST include a testing strategy targeting minimum 95% code coverage for new functionality
- **Test Types**: Plans MUST specify required unit tests, integration tests, and edge case tests
- **Test-First Consideration**: Plans SHOULD consider test cases during design phase (TDD approach encouraged)
- **Acceptance Criteria**: Each implementation step SHOULD have associated test verification criteria
- **No Implementation Without Tests**: Plans MUST NOT be considered complete without comprehensive test specifications

### Roadmap Integration

- **Implementation sequence**: The roadmap defines execution order (see roadmap intro). Place new plans so that order is preserved: blockers in Blockers (ASAP Priority); normal plans at the end of Implementation queue (Pending plans); phase-specific plans in the correct phase section in order.
- **Consistency**: Follow existing roadmap format and structure
- **Linking**: Include proper links to plan file (e.g. `.cortex/plans/<name>.md`)
- **Status**: Set appropriate initial status (e.g. PENDING for new plans)

### Path Resolution

- Follow **memory-bank-workflow.mdc** and **AGENTS.md**: resolve plans directory via `get_structure_info()` → `structure_info.paths.plans` (use absolute path from tool only); roadmap via `manage_file(file_name="roadmap.md", ...)`. Do not hardcode `.cortex/`, `structure_info.root`, or memory-bank paths; use canonical paths from Cortex tools. Verify `structure_info.exists.plans` before use. **VIOLATION**: Hardcoding or inferring the plans path is a path resolution violation. Report paths as returned by Cortex tools.

## ERROR HANDLING

**Path resolution**: Resolve via `get_structure_info()` and `manage_file()`; see Path Resolution in Implementation Guidelines and memory-bank-workflow.mdc. Do not hardcode paths.

If you encounter any issues during plan creation:

1. **Path resolution errors**: If `get_structure_info()` fails:
   - Check if project structure is initialized
   - Suggest running `setup_project_structure` if needed
   - Use fallback path resolution only as last resort

2. **Memory bank errors (CRITICAL)**: If Cortex MCP tools crash, disconnect, or exhibit unexpected behavior during plan creation:
   - **STOP IMMEDIATELY**: Current plan creation process MUST stop
   - **Document the failure**: Record what tool failed, how it failed (crash, disconnect, unexpected behavior), and what operation was attempted
   - **Create manual investigation plan**: If possible, create a basic plan file manually documenting:
     - Problem statement describing the tool failure
     - Affected tools and operations
     - Error messages or tool responses
     - Investigation approach
   - **Link in roadmap**: Add plan to roadmap.md under "Blockers (ASAP Priority)" section (if roadmap can be accessed)
   - **Provide summary to user**:
     - Description: What tool failed and how
     - Impact: Plan creation was blocked
     - Fix Recommendation: Mark as **FIX-ASAP** priority
     - Plan Location: Path to investigation plan (if created)
   - **DO NOT** use standard file tools as fallback - the tool failure must be investigated first
   - **Note**: If plan creation itself fails due to MCP tool errors, provide the summary directly to the user with all available information

3. **Plan creation errors**: If plan file cannot be created:
   - Check write permissions on plans directory
   - Verify plans directory exists
   - Check for filename conflicts
   - Report specific error and suggest resolution

4. **Roadmap update errors**: If roadmap cannot be updated:
   - Verify roadmap file is writable
   - Check roadmap format is valid
   - Ensure proper JSON/Markdown structure
   - Report specific error and suggest resolution

## SUCCESS CRITERIA

The plan creation is considered complete when:

- ✅ Plan file created successfully in plans directory
- ✅ Plan content is complete with all required sections
- ✅ **Testing strategy included with 95% coverage target (MANDATORY)**
- ✅ **Test specifications defined for all new functionality (MANDATORY)**
- ✅ **Plan registered in roadmap (MANDATORY)** – roadmap updated with new or updated plan entry; plan is not complete until registered
- ✅ Roadmap entry properly formatted and linked to the plan file
- ✅ All paths obtained dynamically using MCP tools
- ✅ Sequential-thinking MCP used if available
- ✅ Clarifying questions asked if needed
- ✅ **Analyze prompt executed (conditional)** – If this is the last workflow in the session, Analyze (End of Session) prompt (`analyze.md`) run after plan creation

## After creating a plan (CONDITIONAL): Execute Analyze prompt

- **Condition**: Run ONLY if this is the last workflow in the current session. If the user will invoke another prompt (e.g., `/cortex/commit`, `/cortex/implement`) afterward, skip this step — that prompt's own session-end hook will handle it.
- **When running**: Execute the **Analyze (End of Session)** prompt (`analyze.md` from the Synapse prompts directory). Read and execute that prompt in full.
- **Path**: Resolve via project structure or `get_structure_info()`.

## OUTPUT FORMAT

Provide a structured plan creation report:

### **Plan Creation Summary**

- **Status**: Success/Failure status of plan creation
- **Plan File**: Path to created plan file
- **Plan Title**: Title of the created plan
- **Roadmap Updated**: Whether roadmap was successfully updated
- **Clarifying Questions Asked**: List of questions asked (if any)
- **Think Tool Used**: Whether the `think` MCP tool was used (lightweight or full mode)

### **Plan Details**

- **Title**: Plan title
- **Status**: Initial status
- **Goal**: Primary goal of the plan
- **Scope**: Scope of work covered
- **Timeline**: Estimated timeline (if provided)
- **Dependencies**: List of dependencies (if any)

### **Roadmap Entry**

- **Location**: Where plan was added in roadmap
- **Phase/Milestone**: Phase or milestone section
- **Priority**: Priority level (if applicable)
- **Status**: Initial roadmap status

### **Issues Encountered**

- **Path Resolution Issues**: Any issues getting paths dynamically
- **Memory Bank Issues**: Any issues reading/updating memory bank files
- **Plan Creation Issues**: Any issues creating plan file
- **Roadmap Update Issues**: Any issues updating roadmap

## NOTES

- This is a generic command that can be used for any plan description
- The agent should be thorough and create a complete, actionable plan
- Always use Cortex MCP tools for path resolution and memory bank operations
- Ask clarifying questions proactively to ensure plan quality
- Use the `think` tool from Cortex MCP (full mode) if available for better results
- Follow all workspace rules and coding standards throughout plan creation
- **CRITICAL**: When a plan is requested, ALL context (errors, logs, code) is INPUT for plan creation - DO NOT fix issues or make code changes, only create the plan
