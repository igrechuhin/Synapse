# Implement Next Roadmap Step

**AI EXECUTION COMMAND**: Read the roadmap, identify the next pending step, and implement it completely.

**CRITICAL**: These steps are for the AI to execute AUTOMATICALLY. DO NOT ask the user for permission or confirmation. Execute immediately.

**CURSOR COMMAND**: This is a Cursor command from the Synapse prompts directory, NOT a terminal command.

**Tooling Note**: Use standard Cursor tools (`Read`, `ApplyPatch`, `Write`, `LS`, `Glob`, `Grep`) by default; MCP filesystem tools are optional fallbacks only when standard tools are unavailable or explicitly requested. **MANDATORY: Use Cortex MCP tools for all memory bank operations** - do NOT access memory bank files directly via file paths.

**Memory Bank Access**: All memory bank operations MUST use structured Cortex MCP tools:

- `manage_file()` - Read/write individual memory bank files
- `load_context()` - Get optimal context for a task within token budget
- `load_progressive_context()` - Load context progressively based on strategy
- `get_relevance_scores()` - Get relevance scores for memory bank files
- `get_memory_bank_stats()` - Get memory bank statistics

**Memory Bank Update Note**: After implementing the roadmap step, you MUST update memory bank files using `manage_file(operation="write", ...)` to reflect the completed work.

**Agent Delegation**: This prompt orchestrates roadmap implementation and delegates specialized tasks to dedicated agents in the Synapse agents directory.

- **roadmap-implementer** - Implements the roadmap step with tests and validation
- **memory-bank-updater** - Updates memory bank files after completion

When executing steps, delegate to the appropriate agent for specialized work, then continue with orchestration.

## ⚠️ MANDATORY PRE-ACTION CHECKLIST

**BEFORE executing this command, you MUST:**

1. ✅ **Read the roadmap** - Get next step from implementation sequence:
   - **Use Cortex MCP tool `manage_file(file_name="roadmap.md", operation="read")`** to get the roadmap
   - **Next step** = first PENDING item when reading the roadmap in implementation order (see roadmap intro: Blockers → Active Work → Future Enhancements → Implementation queue / Pending plans). Extract description, plan path if present, and requirements from that entry.
   - Extract the following information from the selected step (blocker or regular item):
     - Description/title of the step
     - Any specific requirements or acceptance criteria
     - Dependencies or prerequisites
     - Estimated scope/complexity

2. ✅ **Load relevant context** - Understand current project context:
   - **Use Cortex MCP tool `load_context(task_description="[roadmap step description]", token_budget=50000)`** to get optimal context for the roadmap step
   - **Alternative**: Use `load_progressive_context(task_description="[roadmap step description]")` to load context progressively
   - **Optional**: Use `get_relevance_scores(task_description="[roadmap step description]")` to see which memory bank files are most relevant
   - The context loading tools will automatically select relevant files (activeContext.md, progress.md, projectBrief.md, systemPatterns.md, techContext.md, etc.) based on the task
   - **DO NOT** read memory bank files directly via file paths - always use Cortex MCP tools

3. ✅ **Read relevant rules** - Understand implementation requirements:
   - Use Cortex MCP tool `rules(operation="get_relevant", task_description="Implementation, code quality, memory bank, testing")` to load rules, or read from the rules directory (path from `get_structure_info()` → `structure_info.paths.rules`)
   - Ensure coding standards, language-specific standards, memory-bank workflow, and testing standards are in context

4. ✅ **Verify implementation against rules and run quality gate** - After implementation, verify conformance:
   - Review all new/modified code to ensure it conforms to coding standards
   - Verify type annotations are complete per language-specific standards
   - Verify structured data types follow project's data modeling standards (check language-specific rules)
   - Verify functions/methods are within project's length limits
   - Verify files are within project's size limits
   - Verify dependency injection patterns are followed (no global state or singletons)
   - Verify naming conventions follow project standards
   - **MANDATORY**: Run the automated quality gate (Step 4.7)—`execute_pre_commit_checks(checks=["quality"])`—and fix any violations before proceeding to memory bank updates. The quality gate runs both quality (lint, file size, function length) and type_check so type diagnostics (e.g. reportRedeclaration) are caught. Do NOT leave lint, function-length, file-size, or type violations for the commit pipeline.
   - **If violations found**: Fix them BEFORE proceeding to memory bank updates

**VIOLATION**: Executing this command without following this checklist is a CRITICAL violation that blocks proper implementation.

## EXECUTION STEPS

### Step 1: Read Roadmap and Pick Next Step - **Delegate to `roadmap-implementer` agent**

The **roadmap defines the implementation sequence** (see the "Implementation sequence" note at the top of roadmap.md). You pick the **next** step only—no priority logic in this prompt.

1. **Use Cortex MCP tool `manage_file(file_name="roadmap.md", operation="read")`** to get the roadmap content.
2. **Next step** = first PENDING item when reading the roadmap in this order (top to bottom within each section):
   - Blockers (ASAP Priority) — if present
   - Active Work
   - Future Enhancements
   - Implementation queue (section "Pending plans (from .cortex/plans)" or "Implementation queue")
3. **If you found a PENDING step**:
   - If the entry references a plan file (e.g. `Plan: .cortex/plans/phase-XX-....md`): resolve the plan path via `get_structure_info()` → `structure_info.paths.plans`; read the plan file with standard file tools; implement the plan (or as much as possible in one session).
   - Otherwise implement the step from the roadmap entry (description, requirements).
4. **If no PENDING step exists** (all items complete in every section):
   - **Plan sync**: Use `get_structure_info()` → `structure_info.paths.plans`. Move unarchived plans that correspond to completed roadmap items to `plans/archive/PhaseNN/`. Update progress.md and activeContext.md via `manage_file` with a short entry (e.g. "Implement run: no pending step; synced plans with roadmap").
   - If no plans need archiving, add a one-line progress entry and set activeContext next focus to "Add a new roadmap entry for next work, or run commit pipeline when ready."
5. Extract from the selected step (for implementation): description/title, requirements, plan path if present, dependencies.

### Step 2: Load Relevant Context

**Task-Aware Token Budget Selection**:

- **Fix/debug tasks**: Use `token_budget=15000` (narrow, focused work)
- **Small feature/refactor**: Use `token_budget=20000-30000` (moderate scope); 20000 or 20000–25000 often sufficient; for narrow implement steps when high-value files (activeContext, roadmap, progress) are sufficient, consider **15000–20000**
- **Architecture/large design**: Use `token_budget=40000-50000` (broad scope)
- **Increase budget only when utilization regularly exceeds ~70%** from previous runs

**Memory Bank File Selection**:

- **High-value files** (always include for fix/debug): `activeContext.md`, `roadmap.md`, `progress.md`, phase-specific plans
- **Moderate-value files** (include when relevant): `systemPatterns.md`, `techContext.md`
- **Lower-relevance files** (optional for fix/debug, include only for exploratory/architectural tasks): `file.md`, `tmp-mcp-test.md`, `projectBrief.md`, `productContext.md`

**Interpreting `file_effectiveness` recommendations**:

- **High relevance**: Prioritize for loading (include in context)
- **Moderate relevance**: Include when task description matches file content
- **Lower relevance**: Consider excluding for narrow fix/debug workflows

1. **Use Cortex MCP tool `load_context(task_description="[description of roadmap step]", token_budget=[task-appropriate budget])`** to get optimal context for the implementation task
   - Select token budget based on task type (fix/debug: 15000, small feature: 20000-30000, architecture: 40000-50000)
   - This tool will automatically select and return relevant memory bank files based on the task description
   - The returned context will include: current project state, related work, technical constraints, patterns, and any relevant context
   - Review `file_effectiveness` recommendations in the response to understand which files are high/moderate/lower relevance
2. **If `load_context()` returns validation error (NON-CRITICAL error per Phase 54)**:
   - **DO NOT stop**: This is a non-critical error with alternative available
   - **Use alternative approach**: Use `manage_file()` to read specific memory bank files directly:
     - `manage_file(file_name="activeContext.md", operation="read")`
     - `manage_file(file_name="progress.md", operation="read")`
     - `manage_file(file_name="systemPatterns.md", operation="read")`
     - `manage_file(file_name="techContext.md", operation="read")`
   - **Document**: Note in implementation that alternative approach was used due to validation error
   - **Continue**: Proceed with implementation using loaded context
3. **Alternative approach**: If you need more control, use `get_relevance_scores(task_description="[description]")` first to see which files are most relevant, then use `manage_file()` to read specific high-relevance files
4. If the roadmap step references other files or documentation, use `manage_file()` to read those specific files
5. Identify any dependencies that must be completed first based on the loaded context

### Step 3: Plan Implementation

1. Break down the roadmap step into concrete implementation tasks
2. Identify which files need to be created, modified, or deleted
3. Determine what tests need to be written or updated
4. Consider any integration points or dependencies

### Step 3.5: Check Existing Data Models (MANDATORY)

Before defining new data structures (classes, types, models, interfaces):

**Pre-Implementation Checklist**:

- [ ] Reviewed existing data model patterns in project
- [ ] Checked language-specific rules for model requirements
- [ ] **FOR PYTHON**: Confirmed all models will use Pydantic BaseModel (NOT TypedDict)
- [ ] Verified model placement follows project structure standards
- [ ] Checked for similar existing models to reuse

**If creating new models, verify**:

- [ ] Using `pydantic.BaseModel` (NOT `TypedDict`)
- [ ] Using Pydantic 2 API (`model_validate()`, `model_dump()`, `ConfigDict`)
- [ ] All fields have explicit type hints
- [ ] Using `Literal` types for status/enum fields

1. **Review existing data model patterns**:
   - Check project's code organization standards for where data models should be defined
   - Review existing data model patterns in the project
   - Verify if similar models already exist
   - Understand project's data modeling standards (check language-specific rules)

2. **Follow project's code organization**:
   - Check language-specific rules for data model organization requirements
   - Ensure data models are placed according to project's file structure standards
   - Use existing model patterns as templates
   - **Run language-specific validation**: Use Cortex MCP tool `execute_pre_commit_checks()` with appropriate checks, or the language-specific validation script from the Synapse scripts directory (path resolved via project structure; prefer MCP tools)

3. **Verify model type compliance**:
   - Check language-specific rules for required model types
   - Ensure new models follow project's data modeling standards
   - Verify model type compliance per language-specific coding standards
   - **CRITICAL FOR PYTHON**:
     - **ALL structured data MUST use Pydantic `BaseModel`** - NO EXCEPTIONS
     - **TypedDict is STRICTLY FORBIDDEN** for new code
     - **Example**: Use `class MergeOpportunity(BaseModel):` NOT `class MergeOpportunity(TypedDict):`
     - **Validation**: Use Cortex MCP tool `execute_pre_commit_checks(checks=["type_check"])` (or the language-specific type-check script from the Synapse scripts directory) and verify no TypedDict usage
     - **BLOCKING**: If TypedDict is detected, convert to Pydantic BaseModel before proceeding
   - **Run language-specific validation**: Use Cortex MCP tool `execute_pre_commit_checks()` with appropriate checks, or the language-specific validation script from the Synapse scripts directory (path resolved via project structure; prefer MCP tools) - will verify data modeling compliance automatically

### Step 4: Implement the Step

1. Execute all implementation tasks:
   - Create/modify/delete files as needed
   - Write or update code according to coding standards
   - Ensure type annotations are complete per language-specific standards
   - Follow language-specific best practices and modern features
   - Keep functions/methods and files within project's length/size limits (check language-specific standards)
   - Use dependency injection (no global state or singletons)
   - **Path and Resource Resolution**:
     - **CRITICAL**: Never hardcode paths. Resolve paths via Cortex MCP tools or project path resolver utilities.
     - **REQUIRED**: Use `get_structure_info()` for structure paths (plans, memory bank, rules); use `manage_file()` for memory bank files; use path resolver utilities in code (e.g., `get_cortex_path()`, `CortexResourceType`)
     - **REQUIRED**: Check existing code for path resolution patterns
     - **FORBIDDEN**: Hardcoding the session directory, memory bank path, or plans path
     - **FORBIDDEN**: String concatenation for paths without using resolver utilities or Cortex tools
2. **MANDATORY: Format code immediately after creation** (before type checking):
   - Use Cortex MCP tool `execute_pre_commit_checks(checks=["format"])` (or the language-specific fix script from the Synapse scripts directory) to format all new/modified files
   - **BLOCKING**: All files MUST be formatted before proceeding to type checking
   - **Verify**: Check formatter output - if files were reformatted, they're already updated
   - **Do not skip**: Formatting is mandatory, not optional - prevents user from having to format manually
3. **MANDATORY: Run type checking immediately after code creation** (before writing tests):
   - **BLOCKING**: Fix ALL type errors before proceeding to test writing
   - **Common type errors to fix**:
     - Unused imports: Remove or use them
     - Type mismatches: Fix parameter types (e.g., `dict_keys` → `set`, `object` → concrete type)
     - Unused call results: Assign to `_` if intentionally unused
     - Missing type annotations: Add explicit types to all functions/methods
   - **If type errors exist**: Fix them immediately, do not continue to test writing
   - **Verification**: Re-run type check via MCP tool or script until 0 errors, 0 warnings
4. Write or update tests (MANDATORY - comprehensive test coverage required):
   - Follow AAA pattern (MANDATORY)
   - No blanket skips (MANDATORY)
   - Target 100% pass rate on project's test suite
   - **Minimum code coverage per project's testing standards (check testing-standards.mdc)**
   - **Unit tests**: Test all new public functions, methods, and classes individually
   - **Integration tests**: Test component interactions and data flow between modules
   - **Edge case tests**: Test boundary conditions, error handling, invalid inputs, and empty states
   - **Test documentation**: Include clear docstrings explaining test purpose and expected behavior
   - **Pydantic v2 for JSON testing**: When testing MCP tool responses (e.g., `manage_file`, `rules`, `execute_pre_commit_checks`), use Pydantic v2 `BaseModel` types and `model_validate_json()` / `model_validate()` instead of asserting on raw `dict` shapes. See `tests/tools/test_file_operations.py` for examples (e.g., `ManageFileErrorResponse` pattern).
   - **Verify coverage**: Run coverage tool and ensure project's coverage threshold is met before considering implementation complete
5. Fix any errors or issues:
   - Run linters and fix all issues
   - Fix type errors
   - Fix formatting issues using project's code formatter
   - Ensure all tests pass
   - **Before Step 4.5**, run ReadLints on all new/modified files (or call `fix_quality_issues(project_root=...)`) and fix any reported type or lint errors.

### Step 4.5: Verify Test Coverage (MANDATORY)

1. **Run coverage analysis**:
   - Use **only** Cortex MCP tool `execute_pre_commit_checks(checks=["tests"], timeout=300, coverage_threshold=0.90)` or, as fallback, the language-specific run_tests script from the Synapse scripts directory. Do **NOT** run raw `pytest` (or other test commands) in a Shell.
   - Review coverage report for new/modified files
2. **Verify coverage threshold** (per project's testing standards):
   - Check project's testing standards for required coverage threshold
   - Check that ALL new functionality meets the required coverage threshold
   - Identify any uncovered lines or branches in new code
3. **Add missing tests if coverage is below threshold**:
   - Write additional unit tests for uncovered code paths
   - Add edge case tests for uncovered branches
   - Add integration tests if component interactions are untested
4. **Re-run coverage** until required threshold is met for all new code
5. **Document coverage**: Note the final coverage percentage in implementation summary
6. **BLOCKING**: Do NOT proceed to memory bank updates until required coverage threshold is achieved

### Step 4.6: Verify Code Conformance to Rules (MANDATORY)

1. **Review all new/modified files** against project rules:
   - Re-read project rules via `rules(operation="get_relevant", ...)` or from the rules directory (path from `get_structure_info()`)
   - Compare each new/modified file against these standards
2. **Verify type system compliance** (per language-specific rules):
   - Type annotations are complete on all new functions, methods, classes
   - Generic/untyped types are avoided per language standards
   - **Multi-line string messages**: Do not use adjacent string literals (implicit concatenation). Use a single f-string or explicit `+` / `str.join()` (Pyright `reportImplicitStringConcatenation` is error).
   - **Structured data types follow project's data modeling standards** (CRITICAL):
     - **MANDATORY CHECK**: Scan code for data structure types - verify they comply with project's required data modeling patterns
     - **MANDATORY CHECK**: Check language-specific coding standards for required data modeling types (e.g., check python-coding-standards.mdc for Python)
     - Check language-specific coding standards for required data modeling patterns
     - Use project-mandated types for structured data (e.g., data classes, models, interfaces)
     - Avoid generic untyped containers when structured alternatives are required
   - **BLOCKING**: If data structures don't comply with project's required modeling standards, this MUST be fixed before proceeding
   - Concrete types are used instead of generic types where possible
   - Modern language features are used per project's language version requirements
3. **Verify structural compliance** (per project standards):
   - All functions/methods are within project's length limits
   - All files are within project's size limits
   - Dependency injection patterns are followed (no global state or singletons)
   - Code organization follows project's file structure standards
   - **Verify code organization** (per project standards):
     - Check language-specific rules for data model organization requirements
     - Ensure data models are placed according to project's file structure standards
     - One public type per file (check project's file organization standards)
     - **Run language-specific validation**: Use Cortex MCP tool `execute_pre_commit_checks()` with appropriate checks, or the language-specific validation script from the Synapse scripts directory (path resolved via project structure; prefer MCP tools)
     - **BLOCKING**: If data models are in wrong files, they MUST be moved to correct location
4. **Verify naming conventions** (per language-specific rules):
   - Check language-specific coding standards for naming requirements
   - Private/internal identifiers follow language conventions
   - Public identifiers follow language conventions
   - Constants follow language conventions
5. **Fix any violations found**:
   - If type violations: Add proper type annotations, use concrete types per language standards
   - If data modeling violations: Convert to project-mandated data types per language-specific rules
   - If structural violations: Extract helper functions, split large files
   - If naming violations: Rename following conventions
6. **BLOCKING**: Do NOT proceed to memory bank updates until all code conforms to rules

### Step 4.7: Run Quality Gate Before Finish (MANDATORY)

**Purpose**: Ensure no rot code is left for the commit pipeline to fix. The same quality gate as the commit pipeline MUST pass before marking the implementation complete. The quality gate includes **quality** (lint, file size, function length) and **type_check** so type diagnostics (e.g. reportRedeclaration) match IDE/CI.

1. **Run automated quality check**:
   - Use Cortex MCP tool `execute_pre_commit_checks(checks=["quality"])`. This runs both quality and type_check. Prefer the MCP tool. Pass `project_root` only if needed (e.g. when not running from repo root).
   - **Scope**: Same as CI (e.g. `src/` and `tests/` for this project). Do NOT skip quality check.
2. **Verify success**:
   - **MUST verify**: Tool returns `status` = "success"
   - **MUST verify**: `results.quality.success` = true; `results.quality.file_size_violations` empty; `results.quality.function_length_violations` empty; no lint errors in quality result
   - **MUST verify**: `results.type_check.success` = true and `results.type_check.errors` empty (type_check runs as part of quality gate)
3. **If any violations**:
   - Fix all reported violations (refactor long functions, split oversized files, fix lint issues, fix type errors)
   - Re-run `execute_pre_commit_checks(checks=["quality"])` until all checks pass
   - Do NOT proceed to Step 5 until the quality gate passes
4. **BLOCKING**: Do NOT proceed to memory bank updates (Step 5) until the quality gate passes. Leaving function-length, file-size, lint, or type violations for the commit pipeline to fix is a violation of this prompt.

### Step 5: Update Memory Bank - **Delegate to `memory-bank-updater` agent**

**Use the `memory-bank-updater` agent (Synapse agents directory) for this step.**

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
10. **⚠️ MANDATORY: If the roadmap step references a plan file (e.g., phase-XX-*.md in the plans directory) and the work is too long to complete in one session**:
    - **Read the plan file** using standard file tools; resolve the plans directory path via `get_structure_info()` → `structure_info.paths.plans` (plans are not in memory bank)
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
   - **Quality gate passed**: Step 4.7 was run and `execute_pre_commit_checks(checks=["quality"])` returned success with zero file-size, function-length, lint, and type_check violations (no rot code left for commit pipeline)
   - Memory bank is updated
   - **If a plan file exists and work is incomplete**: Plan file is updated with current status
2. If the step is not fully complete:
   - **If work cannot be completed in this session**: Ensure the plan file (if referenced) is updated with current status before ending
   - **If work can continue**: Continue implementation until it is complete

## IMPLEMENTATION GUIDELINES

### Code Quality

- **Type annotations**: Complete coverage required per language-specific standards
- **Language features**: Use modern language features and built-ins appropriate to the project's language version
- **Concrete types**: Use concrete types instead of generic types wherever possible per language standards
- **Function/method length**: Keep within project's length limits (check language-specific coding standards)
- **File length**: Keep within project's size limits (check language-specific coding standards)
- **Dependency injection**: All external dependencies MUST be injected via initializers
- **No global state**: NO global state or singletons in production code

### Testing (MANDATORY - Comprehensive Coverage Required)

- **AAA pattern**: Follow Arrange-Act-Assert pattern (MANDATORY)
- **No blanket skips**: No blanket skips (MANDATORY); justify every skip with clear reason and linked ticket
- **Coverage target**: **Minimum code coverage per project's testing standards (MANDATORY - check testing-standards.mdc)**
- **Test execution**: All tests must pass using the project's standard test runner
- **Unit tests**: Every new public function, method, and class MUST have corresponding unit tests
- **Integration tests**: Test interactions between components and modules
- **Edge cases**: Test boundary conditions, error paths, invalid inputs, empty collections, null/None values
- **Regression prevention**: Ensure tests cover scenarios that prevent regressions
- **Coverage verification**: Run coverage report before marking implementation complete; fail if below project's required threshold
- **Test-to-code ratio**: Aim for meaningful test coverage, not just line coverage - test behavior, not implementation

**Coverage Interpretation for Focused Work**:

- **New or modified code**: Must meet ≥95% coverage for Phase 62 changes, even when running focused tests
- **Global `fail-under=90` failures**: When running targeted tests (e.g., via `execute_pre_commit_checks(checks=["tests"], ...)` or the Synapse run_tests script with path args), global coverage failures dominated by untouched modules should be logged as technical debt in progress.md / activeContext.md via `manage_file()` (and, where appropriate, new coverage-raising phases), not "fixed ad hoc" during unrelated, narrow tasks
- **Recording coverage debt**: Document in Memory Bank with wording like: "Global coverage at 21.7% due to untested analysis/structure modules. This is expected legacy debt and does not block focused roadmap sync work. Coverage improvement tracked in Phase XX."
- **Reference coverage plans**: Reference relevant coverage-improvement plan from roadmap entries instead of attempting broad, unscheduled coverage work

### Memory Bank Updates

- **Location**: All memory bank files MUST be accessed via Cortex MCP tool `manage_file()`; do not hardcode the memory bank path (resolve via `get_structure_info()` if needed)
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
   - **Create investigation plan**: Use the create-plan prompt (Synapse prompts directory) to create an investigation plan
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
- ✅ **Code conformance verified**: All new/modified code verified against project rules (Step 4.6)
- ✅ **Quality gate passed (Step 4.7)**: `execute_pre_commit_checks(checks=["quality"])` run and passed—zero lint, file-size, function-length, and type_check violations; no rot code left for the commit pipeline
- ✅ **Type system compliance**: Complete type annotations, proper data modeling per language-specific rules
- ✅ **Structural compliance**: Functions/methods and files within project limits, DI patterns followed
- ✅ All tests pass
- ✅ **Code coverage for new functionality meets project's required threshold (MANDATORY)**
- ✅ **Comprehensive tests exist**: Unit tests, integration tests, and edge case tests for all new code
- ✅ **Coverage verified**: Coverage report generated and reviewed
- ✅ Memory bank is updated
- ✅ The roadmap reflects the completed status

## NOTES

- **CRITICAL PRIORITY**: Blockers in "Blockers (ASAP Priority)" section (typically around line 217 in roadmap.md) MUST be handled FIRST before any other roadmap items
- This is a generic command that can be reused for any roadmap step
- The agent should be thorough and complete the entire step, not just part of it
- If a step is too large, break it down into smaller sub-tasks and complete them systematically
- **MANDATORY PLAN UPDATES**: If the roadmap step references a plan file (e.g., phase-XX-*.md in the plans directory) and the work cannot be completed in one session, you MUST update the plan file at the end of the session to reflect the current implementation status. Resolve the plans directory path via `get_structure_info()` → `structure_info.paths.plans`. This ensures continuity and allows future sessions to pick up where you left off.
- Always update the memory bank after completing work using Cortex MCP tools
- Follow all workspace rules and coding standards throughout implementation
- **CRITICAL**: Never access memory bank files directly via file paths - always use Cortex MCP tools for structured access
- **Plan files**: Plan files are in the plans directory (path from `get_structure_info()` → `structure_info.paths.plans`) and should be accessed using standard file tools (not MCP tools, as they are not part of the memory bank)

## MISSING TOOLS (If Required)

If the following tools would be helpful but are not available, they should be planned for implementation:

- `get_context_for_task(task_description, file_list=None)` - Get context for a specific task, optionally filtering to specific files
- `batch_read_memory_bank_files(file_names)` - Read multiple memory bank files in a single call
- `get_memory_bank_file_list()` - Get list of all available memory bank files with metadata

These tools would provide more efficient and structured access patterns, but the existing tools (`load_context()`, `load_progressive_context()`, `manage_file()`) are sufficient for current needs.
