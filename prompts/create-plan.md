# Create Plan from Description

**AI EXECUTION COMMAND**: Create a development plan based on user description, add it to the plans directory, and update the roadmap.

**CRITICAL**: These steps are for the AI to execute AUTOMATICALLY. DO NOT ask the user for permission or confirmation unless clarification is needed. Execute immediately after gathering necessary information.

**CURSOR COMMAND**: This is a Cursor command located in `.cortex/synapse/prompts/` directory, NOT a terminal command.

**⚠️ MANDATORY: When a plan is requested, ALL additional context is INPUT for plan creation, NOT separate issues to fix.**

- If the user provides error logs, code snippets, or other context along with a plan request, treat ALL of it as input for creating the plan
- DO NOT attempt to fix issues, debug code, or make code changes when a plan is requested
- The ONLY action should be creating a plan that addresses the described issue/problem/feature
- Any errors, logs, or code provided should be analyzed and incorporated into the plan as context, requirements, or constraints

**Tooling Note**: Use standard Cursor tools (`Read`, `ApplyPatch`, `Write`, `LS`, `Glob`, `Grep`) by default; MCP filesystem tools are optional fallbacks only when standard tools are unavailable or explicitly requested. **MANDATORY: Use Cortex MCP tools for all memory bank and structure operations** - do NOT access files directly via hardcoded paths.

**Path Resolution**: All paths MUST be obtained dynamically using Cortex MCP tools:

- Use `get_structure_info()` to get plans directory path (not hardcode `.cortex/plans`)
- Use `manage_file()` to read/write roadmap.md (not hardcode `.cortex/memory-bank/roadmap.md`)

**Sequential Thinking**: If sequential thinking MCP is available, use it to ensure best results when creating the plan.

**Agent Delegation**: This prompt orchestrates plan creation and delegates specialized tasks to dedicated agents in `.cortex/synapse/agents/`:

- **plan-creator** - Creates the development plan from description
- **memory-bank-updater** - Updates roadmap.md with new plan entry

**Existing Plan Reuse (CRITICAL)**: Before creating a brand-new plan, you MUST check whether a same/similar plan already exists.

- If a similar plan already exists, you MUST **enrich and reprioritize the existing plan**, not create a duplicate.
- Only create a new plan when there is no clearly-related existing plan.

When executing steps, delegate to the appropriate agent for specialized work, then continue with orchestration.

## ⚠️ MANDATORY PRE-ACTION CHECKLIST

**BEFORE executing this command, you MUST:**

1. ✅ **Get project structure information** - Obtain paths dynamically:
   - **Use Cortex MCP tool `get_structure_info(project_root=None)`** to get:
     - Plans directory path (`structure_info.paths.plans`)
     - Memory bank path (`structure_info.paths.memory_bank`)
     - Project root path (`structure_info.root`)
   - **DO NOT** hardcode paths like `.cortex/plans` or `.cortex/memory-bank/roadmap.md`
   - Parse the JSON response to extract the actual paths

2. ✅ **Read relevant memory bank files** - Understand current project context:
   - **Use Cortex MCP tool `manage_file(file_name="roadmap.md", operation="read")`** to understand current roadmap structure and priorities
   - **Use Cortex MCP tool `manage_file(file_name="activeContext.md", operation="read")`** to understand current work focus
   - **Use Cortex MCP tool `manage_file(file_name="progress.md", operation="read")`** to see recent achievements
   - **Use Cortex MCP tool `manage_file(file_name="projectBrief.md", operation="read")`** to understand project goals
   - **Use Cortex MCP tool `manage_file(file_name="systemPatterns.md", operation="read")`** to understand architectural patterns

3. ✅ **Check for sequential thinking MCP** - Use if available for better plan quality:
   - Check if sequential thinking MCP server is available (list MCP servers/resources)
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

### Step 1: Get Project Structure and Paths

1. **Use Cortex MCP tool `get_structure_info(project_root=None)`** to get structure information
2. Parse the JSON response to extract:
   - Plans directory path: `structure_info.paths.plans` (e.g., `/path/to/project/.cortex/plans`)
   - Memory bank path: `structure_info.paths.memory_bank` (e.g., `/path/to/project/.cortex/memory-bank`)
   - Project root: `structure_info.root`
3. Verify that the plans directory exists (check `structure_info.exists.plans`)
4. If plans directory doesn't exist, note this in the plan creation process

### Step 2: Load Project Context

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

### Step 2.5: Check for Existing Related Plans (Reuse vs New)

1. **Discover existing plans**:
   - Use `get_structure_info()` paths (`structure_info.paths.plans`) to locate the plans directory.
   - Use standard tools (`LS`, `Read`, `Grep`) to inspect existing plan files and their titles.
   - Cross-check `roadmap.md` entries (via `manage_file(read)`) for plan titles and short descriptions.
2. **Identify same/similar plans**:
   - Compare the user description (title, keywords, problem domain) against:
     - Plan filenames (e.g., `phase-57-fix-markdown-lint-timeout.md`)
     - Plan titles and goals inside existing plan files
     - Roadmap entries that describe similar problems/features.
   - Treat a plan as **similar** if:
     - The main goal/problem matches, or
     - The same component/tool/phase is being improved in a related way.
3. **Decide reuse vs new**:
   - If one or more strong matches exist, select the **closest** existing plan as the **target plan**.
   - If no sufficiently similar plan exists, proceed with creating a **new** plan.
4. **Record decision**:
   - Keep track of whether you are **enriching an existing plan** (with its path) or **creating a new plan**. This decision controls later steps.

### Step 3: Check for Sequential-Thinking MCP

1. **List available MCP resources** to check if sequential-thinking MCP is available
2. If sequential thinking MCP is available:
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

### Step 5: Create or Enrich the Plan - **Delegate to `plan-creator` agent**

**Use the `plan-creator` agent from `.cortex/synapse/agents/plan-creator.md` for this step.**

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
   - **Implementation Steps**: Detailed breakdown of tasks
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

### Step 6: Update Roadmap - **Delegate to `memory-bank-updater` agent**

**Use the `memory-bank-updater` agent from `.cortex/synapse/agents/memory-bank-updater.md` for this step.**

1. **Read current roadmap**:
   - **Use Cortex MCP tool `manage_file(file_name="roadmap.md", operation="read")`** to get current roadmap content

2. **Parse roadmap structure** to understand:
   - Current roadmap format and structure
   - Existing milestones and phases
   - Where to add the new plan entry

3. **Add or update plan entry in roadmap**:
   - **If this is a new plan**:
     - Create a new roadmap entry for the plan.
     - Include plan title, description, status, and priority.
     - Link to the plan file (relative path from memory-bank directory).
     - Add to the appropriate phase/milestone section.
   - **If enriching an existing plan**:
     - Locate the existing roadmap entry that links to the target plan.
     - **Enrich** the entry to reflect the new context and scope (e.g., expand description, reference new constraints or logs).
     - **Increase implementation priority** based on the new request, for example by:
       - Moving the entry into an “Active Work” / higher-priority section, or
       - Upgrading the status (e.g., from PLANNED to IN PROGRESS), and/or
       - Adding a clear urgency marker such as **FIX-ASAP** when appropriate.
     - Ensure the link to the plan file remains correct and roadmap formatting is preserved.

4. **Update roadmap file**:
   - **Use Cortex MCP tool `manage_file(file_name="roadmap.md", operation="write", content="[updated roadmap content]", change_description="Added new plan: [plan title]")`** to save updated roadmap
   - Ensure roadmap formatting is preserved
   - Verify the update was successful

### Step 7: Verify Completion

1. **Verify plan file exists**:
   - Check that plan file was created in the plans directory
   - Verify file content is complete and accurate

2. **Verify roadmap was updated**:
   - **Use Cortex MCP tool `manage_file(file_name="roadmap.md", operation="read")`** to verify roadmap includes the new plan
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

- **Consistency**: Follow existing roadmap format and structure
- **Prioritization**: Add plan to appropriate priority/phase section
- **Linking**: Include proper links to plan file
- **Status**: Set appropriate initial status

### Path Resolution

- **Dynamic paths**: Always use `get_structure_info()` to get paths, never hardcode
- **Relative paths**: Use relative paths in roadmap links when possible
- **Validation**: Verify paths exist before using them

## ERROR HANDLING

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
- ✅ Roadmap updated with new plan entry
- ✅ Roadmap entry properly formatted and linked
- ✅ All paths obtained dynamically using MCP tools
- ✅ Sequential-thinking MCP used if available
- ✅ Clarifying questions asked if needed

## OUTPUT FORMAT

Provide a structured plan creation report:

### **Plan Creation Summary**

- **Status**: Success/Failure status of plan creation
- **Plan File**: Path to created plan file
- **Plan Title**: Title of the created plan
- **Roadmap Updated**: Whether roadmap was successfully updated
- **Clarifying Questions Asked**: List of questions asked (if any)
- **Sequential-Thinking Used**: Whether sequential-thinking MCP was used

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
- Use sequential-thinking MCP if available for better results
- Follow all workspace rules and coding standards throughout plan creation
- **CRITICAL**: When a plan is requested, ALL context (errors, logs, code) is INPUT for plan creation - DO NOT fix issues or make code changes, only create the plan
