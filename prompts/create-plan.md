# Create Plan from Description

**AI EXECUTION COMMAND**: Create a development plan based on user description, add it to the **plans directory**, **and register it in the roadmap**. Plan creation is NOT complete until both (1) the plan file exists in the plans directory and (2) the roadmap contains an entry for that plan. **Resolve paths via Cortex MCP**: use `get_structure_info()` for the plans directory path; use `manage_file()` for the roadmap (memory bank).

Execute AUTOMATICALLY. DO NOT ask the user for permission unless clarification is needed.

## Conventions

Per `shared-conventions.md`. Severity: GATE/CHECK/PREFER. Memory bank writes: per `memory-bank-contract.md`.

**GATE**: When a plan is requested, ALL additional context is INPUT for plan creation, NOT separate issues to fix.

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

## Pre-Action Checklist

Execute standard pre-flight protocol (see `shared-conventions.md`) with agents: `plan-creator.md`, `memory-bank-updater.md`.

**GATE**: Executing this command without running pre-flight first is a violation that blocks proper plan creation.

## EXECUTION STEPS

The steps below define the **implementation sequence**; execute them in order.

**Phases**: (1) Common checklist (via `common-checklist` agent). (2) Existing-plan check — reuse vs new. (3) Create/enrich plan — `plan-creator` agent; **prefer `plan(operation="create", ...)`**. (4) Register in roadmap — `memory-bank-updater` agent; **use `plan(operation="register", ...)`** only. (5) Verify completion.

### Step 1: Check for Existing Related Plans (Phase 2: Reuse vs New)

1. **Discover existing plans**:
   - Use `get_structure_info()` paths (`structure_info.paths.plans`) to locate the plans directory.
   - Use standard tools (`LS`, `Read`, `Grep`) to inspect existing plan files and their titles.
   - Cross-check `roadmap.md` entries (via `manage_file(read)`) for plan titles and short descriptions.
2. **Check for roadmap references to non-existent plans**:
   - **GATE**: If the roadmap references a Phase with status PLANNED but no corresponding plan file exists in the plans directory, you MUST create the plan file now.
   - At minimum, create a plan stub in the plans directory to prevent `roadmap_sync` invalid references.
3. **Check for similar existing plans**:
   - For each existing plan, answer two questions:
     - Does it target the **same component, module, or subsystem**?
     - Does it address the **same type of work** (both fix, both refactor, both add feature, both optimize)?
   - If YES to both questions for any plan, that plan is similar — **enrich it** instead of creating a new one.
   - If multiple plans match, pick the most recently modified one.
   - If uncertain whether a plan is similar, **ask the user**.
   - If no plan matches, proceed with creating a **new** plan.
4. **Record decision**:
   - `similarity_decision`: `"enrich_existing"` | `"create_new"`
   - `target_plan_path`: (if enriching) Path to the chosen plan; `null` if creating new
   - `decision_rationale`: One-sentence explanation
   - **CHECK**: Include the `similarity_decision` in the final `PlanCreatorResult` output.

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

### Step 3: Create or Enrich the Plan (Phase 3) — Delegate to `plan-creator` agent

- **Agent**: plan-creator (Synapse agents directory)
- **Input**: User description, clarifications (if any), all provided context (error logs, code, files), reuse-vs-new decision from Step 1, project context from memory bank
- **GATE**: Plan must include all required sections (see plan-creator agent for full structure)
- **GATE**: Testing strategy with 95% coverage target is mandatory
- **CHECK**: If enriching, merge into existing plan file in-place (no new file)
- **CHECK**: If creating, prefer `plan(operation=”create”, ...)` MCP tool; fallback to `Write` with path from `get_structure_info()`
- **Output**: Plan file path, plan title, plan content validated

### Step 4: Register Plan in Roadmap (Phase 4) — Delegate to `memory-bank-updater` agent

- **Agent**: memory-bank-updater (Synapse agents directory)
- **GATE**: Registering the new plan in the roadmap is **REQUIRED**; every new or enriched plan MUST be registered. Do not skip. **PROHIBITED** for roadmap: **StrReplace** or direct Write on roadmap.md — use MCP tools only. **VIOLATION**: StrReplace or direct Write for roadmap causes corruption.
- **For new plans**: Use `plan(operation=”register”, plan_title=..., description=..., status=”PENDING”, section=...)`. This is the sole API — do NOT fall back to `manage_file(write)`.
- **For enriched plans**: Use `update_memory_bank(operation=”roadmap_add”, ...)` to update the existing entry.
- **GATE**: If `plan(operation=”register”)` fails, STOP and report. No fallback.
- **CHECK**: Never truncate roadmap content; new content must be at least as long as (or as long as) the original; never pass shortened or summarized roadmap content. Pre-write check: when using fallback manage_file write, content must be full, unabridged roadmap (length >= roadmap as read).

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

## GUIDELINES

- **Plan quality**: Completeness, clarity, actionability, measurability, realism — see `plan-creator` agent for full structure
- **Testing**: 95% coverage target, unit/integration/edge case tests — see `plan-creator` agent Phase 3
- **Roadmap integration**: Blockers in Blockers section; normal plans at end of Pending plans; follow existing format
- **Path resolution**: All paths via `get_structure_info()` and `manage_file()`. Never hardcode. See memory-bank-workflow.mdc.

## ERROR HANDLING

- **Path resolution errors**: Check if project initialized; suggest `setup_project_structure`
- **MCP tool crash/disconnect**: STOP, document failure, create investigation plan under Blockers (ASAP Priority), report to user with FIX-ASAP priority
- **Plan file creation errors**: Check permissions, directory existence, filename conflicts
- **Roadmap update errors**: Check format, writability; report specific error

## Verification Checklist

**What to search for**: Plan file in plans directory; roadmap entry. **Search scope**: Full plans directory and roadmap.md. **Files to re-read**: Plan file and roadmap after write. No StrReplace or direct Write for roadmap.

## SUCCESS CRITERIA

- ✅ Plan file created with all required sections (see `plan-creator` agent)
- ✅ Testing strategy with 95% coverage target included
- ✅ Plan registered in roadmap
- ✅ Roadmap entry formatted and linked
- ✅ All paths obtained dynamically

## OUTPUT FORMAT

Report using **PlanCreatorResult** schema (see `shared-handoff-schema.md`):

- Plan creation status, file path, title
- Roadmap update confirmation
- Issues encountered (path, memory bank, creation, roadmap)
