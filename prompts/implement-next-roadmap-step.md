# Implement Next Roadmap Step

**AI EXECUTION COMMAND**: Read the roadmap, identify the next pending step, and implement it completely.

**CRITICAL**: These steps are for the AI to execute AUTOMATICALLY. DO NOT ask the user for permission or confirmation. Execute immediately.

This step is part of the **compound-engineering loop** (Plan → Work → Review → Compound). When done, update memory bank and run session optimization (analyze prompt) if end-of-session.

**CURSOR COMMAND**: This is a Cursor command from the Synapse prompts directory, NOT a terminal command.

**IMPORTANT**: This prompt focuses on **orchestration** (order, dependencies, workflow coordination). For **implementation details** (MCP tool calls, validation logic, specific checks), see the referenced agent files in the Synapse agents directory.

**Agent Delegation**: This prompt orchestrates roadmap implementation and delegates specialized tasks to dedicated agents:

- **common-checklist** — Pre-action: Loads structure, memory bank, rules, and detects primary language
- **roadmap-implementer** — Step 1: MCP health check, roadmap reading, step selection, context & rules loading
- **implement-executor** — Step 2: Planning, coding, testing, quality gate
- **implement-finalizer** — Step 3: Memory bank updates, completion verification, plan archiving
- **plan-archiver** — Invoked by implement-finalizer for plan archiving
- **memory-bank-updater** — Reference for memory bank access patterns and safe update tools

**Inter-agent communication**: All agents return structured results per `shared-handoff-schema.md`. The orchestrator validates required fields before passing data downstream.

**Subagent execution: STRICTLY SEQUENTIAL.** Run each agent one at a time. Do not proceed to the next until the previous reports completion.

**Memory Bank Access**: All memory bank operations MUST use Cortex MCP tools (`manage_file`, `roadmap`, `append_entry`, etc.); do **not** use Write, StrReplace, or ApplyPatch on memory bank paths. See memory-bank-updater agent for full details.

## When Executing Steps

For steps that delegate to agents, you MUST:

1. **READ** the agent file from the Synapse agents directory (`{agent-name}.md`)
2. **EXECUTE** all phases/steps from the agent file
3. **VERIFY** success before proceeding to next step

## MANDATORY VERIFICATION GATES (Phase 78)

These gates apply throughout all agent delegations. Agents are expected to honor them, but the orchestrator verifies.

- **Post-edit verification**: After editing a file, re-read it to confirm the edit was applied
- **Post-step verification**: After eliminating a pattern, search the full repository to confirm zero matches
- **Plan-scope verification**: Before marking a plan complete, re-read Success Criteria and provide evidence for each criterion
- **Duplicate-definition search**: Before modifying a function, search for all definitions of that name across the codebase

## EXECUTION STEPS

### Step 0: Pre-Action Checklist — Delegate to `common-checklist`

**Delegate to `common-checklist` agent** (Synapse agents directory).

The agent loads project structure, memory bank files, rules, and detects primary language. Verify it returns `status: "complete"` before proceeding.

Also verify:

1. You are in the correct project directory
2. The Synapse agents directory is accessible
3. Note today's date (for memory bank entries)

After this checklist is satisfied, **continue directly to Step 1 without pausing for user confirmation.**

### Step 1: Select Step and Load Context — Delegate to `roadmap-implementer`

- **Agent**: Use the `roadmap-implementer` agent for MCP health check, roadmap reading, step selection, and context/rules loading
- **CRITICAL**: This step MUST complete successfully before proceeding. If MCP is unhealthy, STOP.
- **Outputs needed for Step 2**: Step description/title, plan file path (if any), loaded context and rules
- **BLOCKING**: If no pending steps found, report "Roadmap complete" and stop
- **Multi-agent**: If task locking detects conflicts, pick an alternative step or report

### Step 2: Implement — Delegate to `implement-executor`

- **Agent**: Use the `implement-executor` agent for planning, coding, testing, and quality gate
- **Input**: Pass the step description, plan file path, and confirm context/rules are loaded from Step 1
- **Dependency**: MUST run AFTER Step 1 completes successfully
- **CRITICAL**: Quality gate (Phase 6 of the agent) MUST pass before proceeding
- **BLOCKING**: If quality gate fails after fix attempts, do NOT proceed to Step 3
- **Outputs needed for Step 3**: Implementation status, files changed, test coverage, quality gate result

### Step 3: Finalize — Delegate to `implement-finalizer`

- **Agent**: Use the `implement-finalizer` agent for memory bank updates, verification, and plan archiving
- **Input**: Pass the step description, plan file path/basename, implementation results from Step 2, today's date
- **Dependency**: MUST run AFTER Step 2 completes with quality gate passed
- **CRITICAL**: Roadmap sync validation MUST pass before proceeding
- **BLOCKING**: If memory bank errors occur (CRITICAL), STOP and create investigation plan
- **Outputs**: Memory bank update status, archive status, roadmap sync result

### Step 4: End-of-Session Analyze (CONDITIONAL)

- **Dependency**: MUST run AFTER Step 3 completes
- **Condition**: Run ONLY if this is the last workflow in the current session. If the user will invoke another prompt (e.g., `/cortex/commit`) afterward, skip this step — that prompt's own session-end hook will handle it.
- **When running**: Execute the **Analyze (End of Session)** prompt (`analyze.md` from the Synapse prompts directory). Read and execute that prompt in full.
- **Path**: Resolve via project structure or `get_structure_info()`

## SUCCESS CRITERIA

The roadmap step is considered complete when:

- ✅ All implementation tasks are finished
- ✅ All code follows coding standards (verified by implement-executor Phase 5)
- ✅ Quality gate passed (implement-executor Phase 6): zero lint, file-size, function-length, and type_check violations
- ✅ All tests pass with required coverage threshold
- ✅ Memory bank is updated (roadmap entry removed, progress added, activeContext updated)
- ✅ Completed plans archived (no completed plans in `.cortex/plans/` root)
- ✅ Roadmap sync validation passed (no unlinked plans, no invalid references)
- ✅ Analyze prompt executed (if end-of-session)

## ERROR HANDLING

- **MCP unhealthy (Step 1)**: STOP immediately, report to user
- **No pending steps (Step 1)**: Report "Roadmap complete" and stop
- **Quality gate fails (Step 2)**: Fix violations and re-run; do NOT proceed until passed
- **Memory bank tool crash (Step 3)**: STOP. Create investigation plan via create-plan prompt. Link in roadmap under "Blockers (ASAP Priority)". Report with FIX-ASAP priority.
- **Connection closed during quality pre-flight**: Retry once. If still fails, continue with quality gate in implement-executor Phase 6.
- **Quality gate unavailable (doc-only sessions)**: When changes are documentation-only and quality gate fails due to environment issues, record: "Quality gate skipped - environment (doc-only session)."

## NOTES

- **CRITICAL PRIORITY**: Blockers in "Blockers (ASAP Priority)" are handled FIRST by the roadmap-implementer agent
- If a step is too large, break it down into smaller sub-tasks within implement-executor
- For complex steps, use the `think` MCP tool in full mode for structured reasoning
- **Incremental validation when refactoring**: Run type check and quality check after each refactor; do not batch all changes then validate at end
- **Duplicate detection before extracting helpers**: Before creating helper functions, search for existing functions with similar names (e.g. use Grep) to avoid duplicates
- **MANDATORY PLAN UPDATES**: If work cannot complete in one session, implement-finalizer updates the plan file with current status
- **MANDATORY PLAN ARCHIVING**: Completed plans MUST be archived immediately via implement-finalizer → plan-archiver
- **Plan files**: Accessed via standard file tools (not MCP), path from `get_structure_info()` → `structure_info.paths.plans`
