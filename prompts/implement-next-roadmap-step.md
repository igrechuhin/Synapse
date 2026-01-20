# Implement Next Roadmap Step

**AI EXECUTION COMMAND**: Read the roadmap, identify the next pending step, and implement it completely.

**CRITICAL**: These steps are for the AI to execute AUTOMATICALLY. DO NOT ask the user for permission or confirmation. Execute immediately.

**CURSOR COMMAND**: This is a Cursor command located in `.cortex/synapse/prompts/` directory, NOT a terminal command.

**Tooling Note**: Use standard Cursor tools (`Read`, `ApplyPatch`, `Write`, `LS`, `Glob`, `Grep`) by default; MCP filesystem tools are optional fallbacks only when standard tools are unavailable or explicitly requested. **MANDATORY: Use Cortex MCP tools for all memory bank operations** - do NOT access memory bank files directly via file paths.

**Memory Bank Access**: All memory bank operations MUST use structured Cortex MCP tools:

- `manage_file()` - Read/write individual memory bank files
- `optimize_context()` - Get optimal context for a task within token budget
- `load_progressive_context()` - Load context progressively based on strategy
- `get_relevance_scores()` - Get relevance scores for memory bank files
- `get_memory_bank_stats()` - Get memory bank statistics

**Memory Bank Update Note**: After implementing the roadmap step, you MUST update memory bank files using `manage_file(operation="write", ...)` to reflect the completed work.

## ⚠️ MANDATORY PRE-ACTION CHECKLIST

**BEFORE executing this command, you MUST:**

1. ✅ **Read the roadmap** - Understand project priorities:
   - **Use Cortex MCP tool `manage_file(file_name="roadmap.md", operation="read")`** to get all roadmap items
   - Parse the roadmap structure to identify:
     - **CRITICAL: Check for "Blockers (ASAP Priority)" section first** (typically around line 217 in roadmap.md)
     - All roadmap items/entries
     - Their current status (pending, in-progress, completed, etc.)
     - **PRIORITY RULE: Blockers MUST be handled before any other roadmap items**
   - **MANDATORY PRIORITY CHECK**:
     - **If blockers exist in "Blockers (ASAP Priority)" section**: Handle the FIRST blocker item (first uncompleted blocker)
     - **Only if NO blockers exist**: Proceed with the next pending step from regular roadmap sections
   - Extract the following information from the selected step (blocker or regular item):
     - Description/title of the step
     - Any specific requirements or acceptance criteria
     - Dependencies or prerequisites
     - Estimated scope/complexity

2. ✅ **Load relevant context** - Understand current project context:
   - **Use Cortex MCP tool `optimize_context(task_description="[roadmap step description]", token_budget=50000)`** to get optimal context for the roadmap step
   - **Alternative**: Use `load_progressive_context(task_description="[roadmap step description]")` to load context progressively
   - **Optional**: Use `get_relevance_scores(task_description="[roadmap step description]")` to see which memory bank files are most relevant
   - The context loading tools will automatically select relevant files (activeContext.md, progress.md, projectBrief.md, systemPatterns.md, techContext.md, etc.) based on the task
   - **DO NOT** read memory bank files directly via file paths - always use Cortex MCP tools

3. ✅ **Read relevant rules** - Understand implementation requirements:
   - Read `.cursor/rules/coding-standards.mdc` for code quality standards
   - Read language-specific coding standards (e.g., `.cursor/rules/python-coding-standards.mdc` for Python)
   - Read `.cursor/rules/memory-bank-workflow.mdc` for memory bank update requirements
   - Read `.cursor/rules/testing-standards.mdc` for testing requirements

**VIOLATION**: Executing this command without following this checklist is a CRITICAL violation that blocks proper implementation.

## EXECUTION STEPS

**⚠️ CRITICAL PRIORITY RULE**: Blockers in the "Blockers (ASAP Priority)" section (typically around line 217 in roadmap.md) MUST be handled FIRST before any other roadmap items. Only proceed with regular roadmap items if no blockers exist.

### Step 1: Read and Parse Roadmap

1. **Use Cortex MCP tool `manage_file(file_name="roadmap.md", operation="read")`** to get the roadmap content
2. Parse the roadmap structure from the returned JSON to identify:
   - **CRITICAL: First check for "Blockers (ASAP Priority)" section** (typically starts around line 217)
   - All roadmap items/entries
   - Their current status (pending, in-progress, completed, etc.)
   - **PRIORITY RULE: Blockers MUST be handled before any other roadmap items**
3. **MANDATORY PRIORITY SELECTION**:
   - **If "Blockers (ASAP Priority)" section exists and contains uncompleted items**:
     - Select the FIRST uncompleted blocker item from that section
     - This is the item you MUST implement (highest priority)
   - **Only if NO blockers exist or all blockers are completed**:
     - Select the next pending step from regular roadmap sections
4. Extract the following information from the selected step (blocker or regular item):
   - Description/title of the step
   - Any specific requirements or acceptance criteria
   - Dependencies or prerequisites
   - Estimated scope/complexity
   - **If it's a blocker**: Note the urgency and impact described in the blocker entry

### Step 2: Load Relevant Context

1. **Use Cortex MCP tool `optimize_context(task_description="[description of roadmap step]", token_budget=50000)`** to get optimal context for the implementation task
   - This tool will automatically select and return relevant memory bank files based on the task description
   - The returned context will include: current project state, related work, technical constraints, patterns, and any relevant context
2. **Alternative approach**: If you need more control, use `get_relevance_scores(task_description="[description]")` first to see which files are most relevant, then use `manage_file()` to read specific high-relevance files
3. If the roadmap step references other files or documentation, use `manage_file()` to read those specific files
4. Identify any dependencies that must be completed first based on the loaded context

### Step 3: Plan Implementation

1. Break down the roadmap step into concrete implementation tasks
2. Identify which files need to be created, modified, or deleted
3. Determine what tests need to be written or updated
4. Consider any integration points or dependencies

### Step 4: Implement the Step

1. Execute all implementation tasks:
   - Create/modify/delete files as needed
   - Write or update code according to coding standards
   - Ensure type hints are complete (100% coverage, follow language-specific type system best practices)
   - Follow language-specific best practices and modern features
   - Keep functions ≤30 lines and files ≤400 lines
   - Use dependency injection (no global state or singletons)
2. Write or update tests:
   - Follow AAA pattern (MANDATORY)
   - No blanket skips (MANDATORY)
   - Target 100% pass rate on project's test suite
   - Minimum 90% coverage for new code
3. Fix any errors or issues:
   - Run linters and fix all issues
   - Fix type errors
   - Fix formatting issues using project's code formatter
   - Ensure all tests pass

### Step 5: Update Memory Bank

1. **Use Cortex MCP tool `manage_file(file_name="roadmap.md", operation="read")`** to get current roadmap content
2. Update the roadmap content:
   - Mark the completed step as "completed" or remove it if appropriate
   - Add completion date/timestamp if the roadmap format requires it
   - Update any status indicators
3. **Use `manage_file(file_name="roadmap.md", operation="write", content="[updated content]", change_description="Marked roadmap step as completed")`** to save the updated roadmap
4. **Use `manage_file(file_name="progress.md", operation="read")`** to get current progress content
5. Update progress content:
   - Add entry describing what was completed
   - Use YY-MM-DD timestamp format
   - Keep entries reverse-chronological
6. **Use `manage_file(file_name="progress.md", operation="write", content="[updated content]", change_description="Added progress entry for completed roadmap step")`** to save the updated progress
7. **Use `manage_file(file_name="activeContext.md", operation="read")`** to get current active context
8. Update active context:
   - Update current work focus if the completed step was the active focus
   - Note any new work that should be prioritized next
9. **Use `manage_file(file_name="activeContext.md", operation="write", content="[updated content]", change_description="Updated active context after roadmap step completion")`** to save the updated active context
10. **⚠️ MANDATORY: If the roadmap step references a plan file (e.g., `.cortex/plans/phase-XX-*.md`) and the work is too long to complete in one session**:
    - **Read the plan file** using standard file tools (plans are in `.cortex/plans/`, not memory bank)
    - **Update the plan file** to reflect the current implementation status:
      - Mark completed steps/tasks as "COMPLETED" or "✅"
      - Mark in-progress steps/tasks as "IN PROGRESS" or "🔄"
      - Add notes about what was accomplished in this session
      - Update any status indicators or progress tracking sections
      - Document any blockers or issues encountered
      - Note what remains to be done in future sessions
    - **Save the updated plan file** using standard file tools
    - This ensures continuity across multiple implementation sessions

### Step 6: Verify Completion

1. Verify the roadmap step is fully implemented:
   - All requirements are met
   - All tests pass
   - Code follows all standards
   - Memory bank is updated
   - **If a plan file exists and work is incomplete**: Plan file is updated with current status
2. If the step is not fully complete:
   - **If work cannot be completed in this session**: Ensure the plan file (if referenced) is updated with current status before ending
   - **If work can continue**: Continue implementation until it is complete

## IMPLEMENTATION GUIDELINES

### Code Quality

- **Type hints**: 100% coverage required; follow language-specific type system best practices
- **Language features**: Use modern language features and built-ins appropriate to the project's language version
- **Concrete types**: Use concrete types instead of generic `object` or `any` types wherever possible
- **Function length**: Keep functions ≤30 lines (logical lines, excluding doc comments & blank lines)
- **File length**: Keep files ≤400 lines (excluding license headers & imports)
- **Dependency injection**: All external dependencies MUST be injected via initializers
- **No global state**: NO global state or singletons in production code

### Testing

- **AAA pattern**: Follow Arrange-Act-Assert pattern (MANDATORY)
- **No blanket skips**: No blanket skips (MANDATORY); justify every skip with clear reason
- **Coverage**: Minimum 90% coverage for new code
- **Test execution**: All tests must pass using the project's standard test runner

### Memory Bank Updates

- **Location**: All memory bank files MUST be in `.cursor/memory-bank/` directory
- **Timestamps**: Use YY-MM-DD format only
- **Format**: Keep entries reverse-chronological
- **Completeness**: Update after significant changes (MANDATORY)

## ERROR HANDLING

If you encounter any issues during implementation:

1. **Roadmap parsing errors**: If the roadmap format is unclear, read it carefully and identify the structure. If still unclear, proceed with the first uncompleted item you can identify.
2. **Implementation blockers**: If you cannot complete the step due to missing information or dependencies, document what is needed and update the roadmap accordingly.
3. **Test failures**: Fix all test failures before considering the step complete. Do not skip tests without justification.
4. **Memory bank errors (CRITICAL)**: If Cortex MCP tools crash, disconnect, or exhibit unexpected behavior:
   - **STOP IMMEDIATELY**: Current process MUST stop - do not continue with implementation
   - **Create investigation plan**: Use the `create-plan.md` prompt (`.cortex/synapse/prompts/create-plan.md`) to create an investigation plan
   - **Link in roadmap**: Add plan to roadmap.md under "Blockers (ASAP Priority)" section
   - **Provide summary to user**: 
     - Description: What tool failed and how (crash, disconnect, unexpected behavior)
     - Impact: What work was blocked
     - Fix Recommendation: Mark as **FIX-ASAP** priority
     - Plan Location: Path to created investigation plan
   - **DO NOT** use standard file tools as fallback - the tool failure must be investigated first
   - **DO NOT** continue with implementation until the tool issue is resolved

## SUCCESS CRITERIA

The roadmap step is considered complete when:

- ✅ All implementation tasks are finished
- ✅ All code follows coding standards
- ✅ All tests pass
- ✅ Memory bank is updated
- ✅ The roadmap reflects the completed status

## NOTES

- **CRITICAL PRIORITY**: Blockers in "Blockers (ASAP Priority)" section (typically around line 217 in roadmap.md) MUST be handled FIRST before any other roadmap items
- This is a generic command that can be reused for any roadmap step
- The agent should be thorough and complete the entire step, not just part of it
- If a step is too large, break it down into smaller sub-tasks and complete them systematically
- **MANDATORY PLAN UPDATES**: If the roadmap step references a plan file (e.g., `.cortex/plans/phase-XX-*.md`) and the work cannot be completed in one session, you MUST update the plan file at the end of the session to reflect the current implementation status. This ensures continuity and allows future sessions to pick up where you left off.
- Always update the memory bank after completing work using Cortex MCP tools
- Follow all workspace rules and coding standards throughout implementation
- **CRITICAL**: Never access memory bank files directly via file paths - always use Cortex MCP tools for structured access
- **Plan files**: Plan files are located in `.cortex/plans/` directory and should be accessed using standard file tools (not MCP tools, as they are not part of the memory bank)

## MISSING TOOLS (If Required)

If the following tools would be helpful but are not available, they should be planned for implementation:

- `get_context_for_task(task_description, file_list=None)` - Get context for a specific task, optionally filtering to specific files
- `batch_read_memory_bank_files(file_names)` - Read multiple memory bank files in a single call
- `get_memory_bank_file_list()` - Get list of all available memory bank files with metadata

These tools would provide more efficient and structured access patterns, but the existing tools (`optimize_context()`, `load_progressive_context()`, `manage_file()`) are sufficient for current needs.
