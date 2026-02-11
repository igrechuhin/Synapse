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

**Path Resolution**: Resolve all paths via Cortex MCP tools (see memory-bank-workflow.mdc and AGENTS.md). Use `get_structure_info()` for plans/memory_bank/rules paths; use `manage_file(file_name="roadmap.md", ...)` for roadmap. Do not hardcode `.cortex/` or memory-bank paths.

**Sequential Thinking**: If the `sequentialthinking` tool from Cortex MCP is available, use it to ensure best results when creating the plan.

**Agent Delegation**: This prompt orchestrates plan creation and delegates specialized tasks to dedicated agents in the Synapse agents directory:

- **plan-creator** - Creates the development plan from description
- **memory-bank-updater** - Updates roadmap.md with new plan entry

**Existing Plan Reuse (CRITICAL)**: Before creating a brand-new plan, you MUST check whether a same/similar plan already exists.

- If a similar plan already exists, you MUST **enrich and reprioritize the existing plan**, not create a duplicate.
- Only create a new plan when there is no clearly-related existing plan.

When executing steps, delegate to the appropriate agent for specialized work, then continue with orchestration.

## ⚠️ MANDATORY PRE-ACTION CHECKLIST

**BEFORE executing this command, you MUST:**

1. ✅ **Get project structure information** - Obtain paths dynamically:
   - **Use Cortex MCP tool `get_structure_info()`** to get (project root is resolved internally; do NOT pass it as a parameter):
     - Plans directory path (`structure_info.paths.plans`)
     - Memory bank path (`structure_info.paths.memory_bank`)
     - Project root path (`structure_info.root`)
   - **DO NOT** hardcode paths; use Cortex MCP tools to resolve the **plans directory** and **memory-bank** (roadmap) paths
   - Parse the JSON response from `get_structure_info()` and `manage_file()` to get actual paths

2. ✅ **Read relevant memory bank files** - Understand current project context:
   - **Use Cortex MCP tool `manage_file(file_name="roadmap.md", operation="read")`** to understand current roadmap structure and priorities
   - **Use Cortex MCP tool `manage_file(file_name="activeContext.md", operation="read")`** to understand current work focus
   - **Use Cortex MCP tool `manage_file(file_name="progress.md", operation="read")`** to see recent achievements
   - **Use Cortex MCP tool `manage_file(file_name="projectBrief.md", operation="read")`** to understand project goals
   - **Use Cortex MCP tool `manage_file(file_name="systemPatterns.md", operation="read")`** to understand architectural patterns

3. ✅ **Check for `sequentialthinking` MCP tool** - Use if available for better plan quality:
   - Check if the `sequentialthinking` MCP tool is available (list MCP servers/resources or tools)
   - If available, use it to think through the plan structure and ensure comprehensive coverage
   - If not available, proceed with standard planning approach

4. ✅ **Understand user description and ALL context** - Parse the plan description AND all provided context:
   - Extract key requirements, goals, and scope from the description
   - **Analyze ALL additional context** (error logs, code snippets, file contents, etc.) as INPUT for the plan
   - **DO NOT fix issues** - treat errors/logs as requirements/constraints to address in the plan
   - Identify dependencies and prerequisites
   - Determine estimated complexity and timeline
   - Note any specific constraints or preferences
   - **Remember**: When a plan is requested, everything provided is input for plan creation, not separate tasks to execute

**VIOLATION**: Executing this command without following this checklist is a CRITICAL violation that blocks proper plan creation.

## EXECUTION STEPS

**Phases**: (1) Structure & context load — get paths, read memory bank. (2) Existing-plan check — reuse vs new. (3) Create/enrich plan — plan-creator agent. (4) Register in roadmap — memory-bank-updater agent, prefer `register_plan_in_roadmap`/`add_roadmap_entry`. (5) Verify & Analyze — confirm no truncation, then run Analyze (End of Session) prompt. All paths via `get_structure_info()` and `manage_file()`; see memory-bank-workflow.mdc.

### Step 1: Get Project Structure and Paths (Phase 1)

1. **Use Cortex MCP tool `get_structure_info()`** to get structure information (the tool resolves project root internally)
2. Parse the JSON response to extract:
   - **Plans directory path**: Use the **absolute path** from `structure_info.paths.plans` returned by `get_structure_info()`. Do not hardcode the plans path or derive it from `structure_info.root` plus a segment; the canonical plans path is always `structure_info.paths.plans`.
   - Memory bank path: `structure_info.paths.memory_bank` (use the value returned by `get_structure_info()`; do not hardcode)
   - Project root: `structure_info.root` (note: `structure_info.root` may be the Cortex directory (e.g. `.cortex`) or the project root depending on configuration; the canonical plans path is always `structure_info.paths.plans`)
3. Verify that the plans directory exists (check `structure_info.exists.plans`)
4. If plans directory doesn't exist, note this in the plan creation process
5. **When reporting paths** (e.g. in plan summary or "Issues encountered"), use the value from `get_structure_info()` (e.g. `structure_info.paths.plans`) so it is unambiguous. Do not report a relative or inferred path; report the actual path returned by the Cortex tool.

### Step 2: Load Project Context (Phase 1)

1. **Use Cortex MCP tool `manage_file(file_name="roadmap.md", operation="read")`** to read current roadmap
2. **Use Cortex MCP tool `manage_file(file_name="activeContext.md", operation="read")`** to read active context
3. **Use Cortex MCP tool `manage_file(file_name="progress.md", operation="read")`** to read progress
4. **Use Cortex MCP tool `manage_file(file_name="projectBrief.md", operation="read")`** to read project brief
5. **Use Cortex MCP tool `manage_file(file_name="systemPatterns.md", operation="read")`** to read system patterns
6. Analyze the context to understand:
   - Current project priorities
   - Existing plans and their status
   - Architectural patterns and constraints
   - Recent progress and achievements

### Step 2.5: Check for Existing Related Plans (Phase 2: Reuse vs New)

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

### Step 3: Check for `sequentialthinking` MCP tool

1. **List available MCP resources or tools** to check if the `sequentialthinking` MCP tool is available
2. If the `sequentialthinking` tool is available:
   - Use it to think through the plan structure systematically
   - Ensure comprehensive coverage of all aspects
   - Validate plan completeness and coherence
3. If not available, proceed with standard planning approach

### Step 4: Analyze All Provided Context

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

### Step 5: Create or Enrich the Plan (Phase 3) - **Delegate to `plan-creator` agent**

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
     - Generate a filename based on plan title (sanitize for filesystem)
     - Use standard tools (`Write`) to create the plan file in the plans directory
     - File should be saved as `{plans_dir}/{plan-filename}.md`
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

### Step 6: Register Plan in Roadmap (Phase 4, MANDATORY) - **Delegate to `memory-bank-updater` agent**

**Use the `memory-bank-updater` agent (Synapse agents directory) for this step.**

Every new or enriched plan MUST be registered in the roadmap. Do not skip this step.

1. **Read current roadmap**:
   - **Use Cortex MCP tool `manage_file(file_name="roadmap.md", operation="read")`** to get current roadmap content

2. **Parse roadmap structure** to understand:
   - Current roadmap format and structure
   - **Implementation sequence** (see roadmap intro): section order is Blockers → Active Work → Future Enhancements → Implementation queue (Pending plans). Order within each section is top-to-bottom; the implement command picks the first PENDING item in this order.
   - Where to add the new plan entry so **execution order is correct**: use roadmap structure from `manage_file(read)` to place the entry in the right section and position.

3. **Full-content rule and pre-write check (MANDATORY)**:
   - **Prohibition**: Never pass a shortened, summarized, or placeholder version of the roadmap. The `content` parameter MUST be the complete file content as read in Step 6 (read roadmap). If the content would be larger than a safe payload, do not truncate; use the full content.
   - **Pre-write check**: Before calling `manage_file(roadmap.md, write, content=...)`, confirm that the string length of `content` is at least as long as the roadmap content read in Step 6. If it is shorter, do not write; re-build the full content (current roadmap + new/updated entry only) and try again.
   - **Prefer single-entry tools**: When available, prefer **`register_plan_in_roadmap`** or **`add_roadmap_entry`** for adding a single new plan entry instead of full-content write.

4. **Add or update plan entry in roadmap** (register the plan in correct order for execution):
   - **If this is a new plan**:
     - **REQUIRED for adding a single new plan entry**: Use the Cortex MCP tool **`register_plan_in_roadmap(plan_title=..., description=..., status="PENDING", section=...)`**. Do **not** build full roadmap content or call `manage_file(roadmap.md, write, content=...)` for adding one plan entry—that causes roadmap corruption. Choose `section` from: `blockers` (for ASAP/blocker plans), `active_work`, `future`, or `pending` (default; use for most new plans). The tool performs server-side read-modify-write and inserts the entry in the correct place.
     - **Alternative**: If you need to add a single preformatted bullet line, use **`add_roadmap_entry(section=..., entry_text=..., position=...)`** instead of building full content.
     - **Placement**: (1) If the plan is a blocker, use `section="blockers"`. (2) Otherwise use `section="pending"` so the entry goes into "Pending plans (from .cortex/plans)" at the end. (3) For Active Work or Future Enhancements use `section="active_work"` or `section="future"` as appropriate.
     - **Fallback**: Use `manage_file(file_name="roadmap.md", operation="write", content=<full roadmap>, change_description=...)` **only** when updating multiple entries at once or when `register_plan_in_roadmap` is unavailable; the `content` MUST be the full, unabridged roadmap text. Never truncate.
   - **If enriching an existing plan**:
     - Locate the existing roadmap entry that links to the target plan.
     - **Enrich** the entry to reflect the new context and scope (e.g., expand description, reference new constraints or logs).
     - **Increase implementation priority** based on the new request, for example by:
       - Moving the entry into an “Active Work” / higher-priority section, or
       - Upgrading the status (e.g., from PLANNED to IN PROGRESS), and/or
       - Adding a clear urgency marker such as **FIX-ASAP** when appropriate.
     - For enrich/update that edits a single existing line, prefer a single `manage_file(roadmap.md, write, content=<full roadmap>, ...)` with the complete content if no tool supports in-place line edit; keep that path rare and never truncate.
     - Ensure the link to the plan file remains correct and roadmap formatting is preserved.

5. **Update roadmap file** (mandatory tool usage):
   - **PROHIBITED**: Updating the roadmap during plan creation by StrReplace, direct Write to the roadmap file path, or any edit that bypasses Cortex MCP tools. Using StrReplace or direct Write is a critical violation.
   - **REQUIRED for new plan**: For **adding one new plan entry**, you **must** call **`register_plan_in_roadmap`** (or **`add_roadmap_entry`** for a single formatted line). Do **not** use `manage_file(roadmap.md, write, content=...)` for single-entry adds—that leads to roadmap corruption from full-content string assembly.
   - **Fallback only**: Use `manage_file(file_name="roadmap.md", operation="write", content=<complete resulting text>, change_description=...)` only when (a) updating multiple entries in one go, or (b) enriching an existing entry and no single-entry tool applies, or (c) `register_plan_in_roadmap` is unavailable. When using fallback, the `content` MUST be the full, unabridged roadmap text; never truncate, summarize, or shorten existing bullets. Before calling, verify `len(content) >= len(roadmap_as_read_in_step_6)`; if shorter, do not write—re-build full content and try again.
   - Ensure roadmap formatting is preserved and verify the update was successful

### Step 7: Verify Completion (Phase 5)

1. **Verify plan file exists**:
   - Check that plan file was created in the plans directory
   - Verify file content is complete and accurate

2. **Verify roadmap was updated**:
   - **Re-read roadmap via `manage_file(file_name="roadmap.md", operation="read")`** and confirm: (1) the new or updated plan entry is present and correct, and (2) **all existing roadmap entries are unchanged (no truncation or removal)**. For new plans, registration should have been done via **`register_plan_in_roadmap`** (or **`add_roadmap_entry`**); if the agent used fallback `manage_file(write, ...)` and any existing entry was shortened or removed, restore the full content and repeat the update with complete content—**not** StrReplace or direct Write.
   - Check that roadmap entry is properly formatted and linked

3. **Provide summary**:
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

- Follow **memory-bank-workflow.mdc** and **AGENTS.md**: resolve plans directory via `get_structure_info()` → `structure_info.paths.plans`; roadmap via `manage_file(file_name="roadmap.md", ...)`. Never hardcode `.cortex/` or memory-bank paths. Verify `structure_info.exists.plans` before use. Report paths as returned by Cortex tools.

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
- ✅ **Analyze prompt executed** – Analyze (End of Session) prompt (`analyze.md`) run after plan creation to complete context effectiveness and session optimization analysis

## After creating a plan (MANDATORY): Execute Analyze prompt

- **Dependency**: Must run AFTER the plan file is created and registered in the roadmap (success criteria above).
- **MANDATORY**: At the end of the plan creation workflow, you MUST execute the **Analyze (End of Session)** prompt (`analyze.md` from the Synapse prompts directory). Read and execute that prompt in full: it runs context effectiveness analysis and session optimization, saves a report to the reviews directory, and optionally creates an improvements plan. Do not skip this step.
- **Path**: Resolve the Analyze prompt path via project structure or `get_structure_info()` (e.g. Synapse prompts directory); the prompt file is `analyze.md`.

## OUTPUT FORMAT

Provide a structured plan creation report:

### **Plan Creation Summary**

- **Status**: Success/Failure status of plan creation
- **Plan File**: Path to created plan file
- **Plan Title**: Title of the created plan
- **Roadmap Updated**: Whether roadmap was successfully updated
- **Clarifying Questions Asked**: List of questions asked (if any)
- **Sequentialthinking Tool Used**: Whether the `sequentialthinking` MCP tool was used

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
- Use the `sequentialthinking` tool from Cortex MCP if available for better results
- Follow all workspace rules and coding standards throughout plan creation
- **CRITICAL**: When a plan is requested, ALL context (errors, logs, code) is INPUT for plan creation - DO NOT fix issues or make code changes, only create the plan
