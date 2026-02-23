# Implement Next Roadmap Step

**AI EXECUTION COMMAND**: Read the roadmap, identify the next pending step, and implement it completely.

**CRITICAL**: These steps are for the AI to execute AUTOMATICALLY. DO NOT ask the user for permission or confirmation. Execute immediately.

This step is part of the **compound-engineering loop** (Plan → Work → Review → Compound). When done, update memory bank and run session optimization (analyze prompt) if end-of-session.

**CURSOR COMMAND**: This is a Cursor command from the Synapse prompts directory, NOT a terminal command.

**Tooling Note**: Use standard Cursor tools (`Read`, `ApplyPatch`, `Write`, `LS`, `Glob`, `Grep`) by default; MCP filesystem tools are optional fallbacks only when standard tools are unavailable or explicitly requested. **MANDATORY: Use Cortex MCP tools for all memory bank operations** - do NOT access memory bank files directly via file paths.

**Memory Bank Access**: All memory bank operations MUST use structured Cortex MCP tools:

- `manage_file()` - Read/write individual memory bank files
- `load_context()` - Get optimal context for a task within token budget
- `load_progressive_context()` - Load context progressively based on strategy
- `get_relevance_scores()` - Get relevance scores for memory bank files
- `get_memory_bank_stats()` - Get memory bank statistics

**Memory Bank Update Note**: After implementing the roadmap step, you MUST update memory bank files using `manage_file(operation="write", ...)` to reflect the completed work. **roadmap.md and all other memory bank files** may be updated **only** via Cortex MCP tools (`manage_file`, `remove_roadmap_entry`, `add_roadmap_entry`, `append_progress_entry`, `append_active_context_entry`, etc.); do **not** use Write, StrReplace, or ApplyPatch on memory bank paths.

**Agent Delegation**: This prompt orchestrates roadmap implementation and delegates specialized tasks to dedicated agents in the Synapse agents directory.

- **roadmap-implementer** - Implements the roadmap step with tests and validation
- **memory-bank-updater** - Updates memory bank files after completion
- **plan-archiver** - Archives completed plans to appropriate archive directories

When executing steps, delegate to the appropriate agent for specialized work, then continue with orchestration.

## ⚠️ MANDATORY PRE-ACTION CHECKLIST

**BEFORE executing this command, you MUST:**

0. ✅ **Verify MCP and get session orientation** - Do not proceed without Cortex MCP:
   - **Use Cortex MCP tool `session_start(task_description=None)`** to get a session brief (< 1000 tokens). If this call **fails** (e.g. connection error, tool not found), **STOP**. Report to the user: "Cortex MCP is disconnected or unhealthy. Please reconnect the Cortex MCP server and re-run this command." Do not call any other tools.
   - **After session_start**: Check the brief's **`mcp_healthy`** field. If **`mcp_healthy` is false**, **STOP**. Report to the user: "Cortex MCP is disconnected or unhealthy. Please reconnect the Cortex MCP server and re-run this command." Do not proceed with implementation.
   - The brief also contains: current focus, recent completed work, next work item, health check, git status, actionable suggestions.
   - **Example pattern**: `session_start()` → if brief.mcp_healthy is true → `load_context(task_description=brief.next_work_item, ...)` → implement

1. ✅ **Read the roadmap** - Get next step from implementation sequence:
   - **Use Cortex MCP tool `manage_file(file_name="roadmap.md", operation="read")`** to get the roadmap
   - **Next step** = first PENDING item when reading the roadmap in implementation order (see roadmap intro: Blockers → Active Work → Future Enhancements → Implementation queue / Pending plans). Extract description, plan path if present, and requirements from that entry.
   - Extract the following information from the selected step (blocker or regular item):
     - Description/title of the step
     - Any specific requirements or acceptance criteria
     - Dependencies or prerequisites
     - Estimated scope/complexity

2. ✅ **Load relevant context** - Understand current project context (at step start):
   - **Explicit non-zero token budget (MANDATORY for non-trivial tasks)**: For implement, fix, debug, or refactor tasks, `load_context` MUST be called with an explicit non-zero `token_budget` (e.g. 10,000–15,000 for fix/debug, 20,000–30,000 for implement). For non-trivial tasks the tool returns a validation error when `token_budget` is omitted or set to 0. Zero-files for these tasks also indicates a configuration error.
   - **Budget examples**: INCORRECT: `load_context(task_description="Implement feature X")` (omitting token_budget) or `load_context(..., token_budget=0)` — both return an error for non-trivial tasks. CORRECT for implement: `load_context(task_description="Implement feature X", token_budget=10000)`. CORRECT for fix/debug: `load_context(task_description="Fixing errors", token_budget=15000)`. For non-trivial tasks always pass an explicit token_budget; do not omit it.
   - **Task-type token budget** (use these defaults; see CLAUDE.md and AGENTS.md): implement/add or update/modify → 10,000; fix/debug or other → 15,000; small feature → 20,000–30,000; optimization → 15,000; narrow review/docs → 7,000–8,000; architecture/large design → 40,000–50,000. Do not use zero budget for non-trivial tasks.
   - **AgentRole awareness**: The `load_context` tool automatically detects the agent role (feature/quality/testing/docs/planning/debugging/review) from the task description and uses role-aware context selection. Role-aware statistics are tracked in context-effectiveness analysis and can inform budget recommendations per role. See AGENTS.md for role descriptions and when each role is appropriate.
   - **At step start** (right after reading the roadmap and picking the next step), use the **two-step pattern** for efficient context loading:
     1. **First**: Call `load_context(task_description="[roadmap step description]", depth="metadata_only", token_budget=[task-appropriate budget])` to get a lightweight context map (~500 tokens) with file names, sections, token counts, and relevance scores. This also records the session for end-of-session analyze.
     2. **Then**: Use `manage_file(file_name="[file]", operation="read", sections=["## Section Name"])` to drill into specific relevant sections on demand.
   - **Alternative for full context**: Use `load_context(task_description="[roadmap step description]", token_budget=[task-appropriate budget])` with `depth="full"` or `depth="summary"` for complete context (use when you need all content upfront).
   - **Alternative**: Use `load_progressive_context(task_description="[roadmap step description]")` to load context progressively
   - **Optional**: Use `get_relevance_scores(task_description="[roadmap step description]")` to see which memory bank files are most relevant
   - **Hybrid retrieval**: When `depth="metadata_only"`, essential sections (e.g., "## Current Focus" and "## Next Steps" from activeContext.md) are automatically loaded in full via the hybrid retrieval strategy, while other files return metadata only.
   - The context loading tools will automatically select relevant files (activeContext.md, progress.md, projectBrief.md, systemPatterns.md, techContext.md, etc.) based on the task
   - **DO NOT** read memory bank files directly via file paths - always use Cortex MCP tools

3. ✅ **Read relevant rules** - Understand implementation requirements:
   - **FIRST**: Check rules indexing status by calling `rules(operation="get_relevant", task_description="Implementation, code quality, memory bank, testing, maintainability, helper module extraction")` and inspecting the `rules_manager_status.indexed_files` field in the response.
   - **When rules indexing is enabled and `indexed_files > 0`**: Treat rules as a **first-class source** of coding standards. Use `rules(operation="get_relevant", ...)` as the primary method for loading rules. The indexed rules will be automatically selected based on relevance to the task description.
   - **When `rules()` returns `status: "disabled"` or `indexed_files=0`**: Fall back to reading from the rules directory (path from `get_structure_info()` → `structure_info.paths.rules`) using the Read tool, or use `get_synapse_rules()` for Synapse rules. **MANDATORY**: Read maintainability.mdc for file size limits, function length limits, and helper module extraction pattern.
   - **Troubleshooting**: If rules are enabled (`rules_enabled: true` in optimization.json) but `indexed_files=0`, run `rules(operation="index", force=True)` to index rules, then retry `get_relevant`. If indexing still returns 0 files, check that the `rules_folder` path in optimization.json points to a directory containing `.mdc` rule files.
   - **Language-specific standards**: Load language-specific coding standards via `get_synapse_rules(task_description="[language] standards")` or via `rules(operation="get_relevant", ...)` if indexing is enabled.
   - **Rule discovery fallback**: When `rules()` returns empty results or the task involves tool implementation/refactoring (e.g., implementing MCP tools, refactoring tool parameters), also check `get_synapse_rules(task_description="[language] models, structured data")` for language-specific structured-data standards.
   - **Maintainability rules**: Ensure maintainability.mdc rules are loaded (file size limits, function length limits, helper module extraction pattern). If rules() doesn't return maintainability rules, explicitly load them via `rules(operation="get_relevant", task_description="helper module extraction, file size limits, function length limits")` or read maintainability.mdc directly.
   - Ensure coding standards, language-specific standards, memory-bank workflow, maintainability rules, and testing standards are in context

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

### Step 0: Verify MCP and Get Session Orientation (MANDATORY)

**Call `session_start()` first. Do not proceed if MCP is unhealthy.**

1. **Call `session_start(task_description=None)`**. If the call **fails** (connection error, tool not found, etc.), **STOP**. Tell the user: "Cortex MCP is disconnected or unhealthy. Please reconnect the Cortex MCP server and re-run this command." Do not use other Cortex tools or continue.

2. **Check the brief's `mcp_healthy` field**. If **`mcp_healthy` is false**, **STOP**. Tell the user: "Cortex MCP is disconnected or unhealthy. Please reconnect the Cortex MCP server and re-run this command." Do not proceed.

3. **Use the brief** (current focus, next work item, health check, git status, suggestions) to understand current state.

4. **Then proceed** to Step 1 to read the roadmap (or use `brief.next_work_item` if available).

### Step 1: Read Roadmap and Pick Next Step - **Delegate to `roadmap-implementer` agent**

The **roadmap defines the implementation sequence** (see the "Implementation sequence" note at the top of roadmap.md). You pick the **next** step only—no priority logic in this prompt.

**If you called `session_start()`**: The brief already contains `next_work_item` and `next_work_plan_path`. You can use those directly, but still verify by reading the roadmap entry to get full details.

**Short path for plan-only steps**: When the next step references a plan file and the plan has all steps Done with no code changes (e.g. documentation-only or already-completed work), a short path is acceptable: `session_start()` → read the plan file → `complete_plan(...)` (and optional `load_context` with a small budget for rules only). This avoids full context load and implementation steps when the only action is to move the plan to completed and archive it.

**If you skipped `session_start()`**: Follow the steps below:

1. **Use Cortex MCP tool `manage_file(file_name="roadmap.md", operation="read")`** to get the roadmap content.
2. **Next step** = first PENDING item when reading the roadmap in this order (top to bottom within each section):
   - Blockers (ASAP Priority) — if present
   - Active Work
   - Future Enhancements
   - Implementation queue (section "Pending plans (from .cortex/plans)" or "Implementation queue")
   - **What counts as PENDING**: Any roadmap bullet under "Pending plans" or "Implementation queue" (e.g. under "Features & Enhancements") that contains **"Plan: .cortex/plans/..."** is a pending implementation step. The next step is the **first such bullet** in reading order. The label in the bullet text ("Reference", "Pending", or similar) does **not** exclude the entry—if it has a plan path, it is in the implementation queue and must be picked when it is first in order.
3. **If you found a PENDING step**:
   - If the entry references a plan file (e.g. `Plan: .cortex/plans/phase-XX-....md`): resolve the plan path via `get_structure_info()` → `structure_info.paths.plans`; read the plan file with standard file tools; implement the plan **in sequential step order** (see "Plan step sequence" below).
   - Otherwise implement the step from the roadmap entry (description, requirements).

**Call load_context at step start**: Right after picking the next step (from `session_start()` brief or roadmap), use the two-step pattern: first call `load_context(task_description="[description of roadmap step]", depth="metadata_only", token_budget=[task-appropriate budget])` to get a lightweight context map, then use `manage_file(sections=[...])` to drill into specific sections as needed. This records the session for end-of-session analyze and provides 90%+ token savings. Prefer token-efficient workflow: use task-appropriate token budget; when usage search or fetch-by-ID tools exist, use search → select IDs → fetch instead of loading all.

**⚠️ Explicit budget required for non-trivial tasks**: For refactor/fix/debug/implement, `load_context` requires an explicit non-zero `token_budget`; omitting it or passing 0 returns a validation error. If `load_context` returns `files_selected=0` for a non-trivial task, re-run with an appropriate explicit budget (10k-15k for fix/debug, 20k-30k for implement/add). The end-of-session analysis will flag zero-budget or zero-files in `learned_patterns` warnings. **Example**: `load_context(task_description="Implement feature X", token_budget=10000)` — always pass an explicit token_budget for non-trivial tasks (e.g. 10000, 15000).

**Task-type token budget** (aligns with context-effectiveness insights; see Context budget defaults in CLAUDE.md and AGENTS.md):

- **update/modify, implement/add**: 10,000
- **fix/debug, other**: 15,000
- **small feature**: 20,000–30,000
- **optimization**: 15,000
- **narrow review/documentation**: 7,000–8,000
- **architecture/large design**: 40,000–50,000

**AgentRole-aware budgets**: Context-effectiveness analysis tracks statistics by agent role (feature/quality/testing/docs/planning/debugging/review) and provides role-specific budget recommendations. The `load_context` tool automatically detects roles from task descriptions and uses role-aware file selection. See `analyze_context_effectiveness()` results for role-aware budget recommendations. **Role detection**: Roles are automatically inferred from task descriptions using keyword heuristics (e.g., "test" → testing, "fix" → debugging, "format" → quality, "docs" → docs, "plan" → planning). The detected role is logged in session logs and used for role-aware context selection and statistics. See AGENTS.md for role descriptions and when each role is appropriate.

**Plan step sequence (MANDATORY when implementing a plan)**:

- Execute plan steps **in order** (Step 1, then Step 2, …). The **next step** is the **first uncompleted step**; do not skip or reorder steps. If the session cannot finish all steps, complete as many as possible in order and update the plan file with current status.
- **Architecture/large design**: Use `token_budget=40000-50000` (broad scope)
- **Increase budget only when utilization regularly exceeds ~70%** from previous runs

**Memory Bank File Selection**:

- **High-value files** (always include for fix/debug): `activeContext.md`, `roadmap.md`, `progress.md`, phase-specific plans
- **Moderate-value files** (include when relevant): `systemPatterns.md`, `techContext.md`
- **Lower-relevance files** (optional for fix/debug, include only for exploratory/architectural tasks): `file.md`, `tmp-mcp-test.md`, `projectBrief.md`, `productContext.md`

**Context Loading for Session/Commit-Pipeline Tasks**:

- **For task descriptions containing "Session Optimization", "Commit Pipeline", or "roadmap step"**: When token budget allows (e.g. 10k), consider explicitly including `roadmap.md` and `activeContext.md` in the context to ensure next steps and completed work are both available. The `load_context` tool will automatically select relevant files, but for these task types, these files are particularly valuable for understanding current state and upcoming work.

**Interpreting `file_effectiveness` recommendations**:

- **High relevance**: Prioritize for loading (include in context)
- **Moderate relevance**: Include when task description matches file content
- **Lower relevance**: Consider excluding for narrow fix/debug workflows

1. **Use Cortex MCP tool `load_context()` with two-step pattern** to get optimal context for the implementation task (and to record the session for end-of-session analyze):
   - **Step 1**: Call `load_context(task_description="[description of roadmap step]", depth="metadata_only", token_budget=[task-appropriate budget])` to get a lightweight context map (~500 tokens) with file names, sections, token counts, and relevance scores.
   - **Step 2**: Use `manage_file(file_name="[file]", operation="read", sections=["## Section Name"])` to drill into specific relevant sections on demand.
   - **Alternative**: For full context upfront, use `load_context(task_description="...", depth="full", token_budget=...)` or `depth="summary"` (use when you need all content immediately).
   - Select token budget from the task-type mapping above: update/modify or implement/add → 10,000; fix/debug or other → 15,000; small feature → 20,000–30,000; architecture/large design → 40,000–50,000.
   - This tool will automatically select and return relevant memory bank files based on the task description
   - The returned context will include: current project state, related work, technical constraints, patterns, and any relevant context
   - When using `depth="metadata_only"`, essential sections (e.g., "## Current Focus" and "## Next Steps" from activeContext.md) are automatically loaded in full via hybrid retrieval strategy
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

**Before planning, use the `think` tool to analyze the roadmap step:**

```text
<think_example>
Reading plan step: "Add response_format parameter to manage_file"
- Dependencies: manage_file handler exists in file_operations.py
- Need to: add parameter to schema, handler logic, tests
- Risks: backward compatibility — default must be "detailed" for existing callers
- Testing: unit test for both formats, integration test with real file
</think_example>
```

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
   - **For tool parameters and internal dispatch data**: Use Pydantic `BaseModel` (e.g. `QueryXParams`), not `dict[str, Any]`. Apply when introducing or refactoring tool param objects or internal structured data structures. Check AGENTS.md/CLAUDE.md or language-specific rules for project standards.
   - When adding new functions, keep each under the project limit (≤30 logical lines); if a function grows beyond that, extract helpers before running the full quality gate.
   - **Proactive helper extraction**: When implementing functions, if a function exceeds 25 lines, consider extracting helpers immediately rather than waiting for quality gate violations.
   - **Helper module extraction (quality violations)**: When file size or function length exceeds project limits, apply the **helper module extraction pattern** per maintainability rules. See `rules(operation="get_relevant", task_description="helper module extraction, file size limits, function length limits")` or maintainability.mdc for comprehensive guidance on extracting cohesive function groups to `*_helpers.py` modules, updating imports and tests, and maintaining coverage.
   - Follow language-specific best practices and modern features
   - Keep functions/methods and files within project's length/size limits (check language-specific standards)
   - Use dependency injection (no global state or singletons)
   - **Path and Resource Resolution**:
     - **CRITICAL**: Never hardcode paths. Resolve paths via Cortex MCP tools or project path resolver utilities.
     - **REQUIRED**: Use `get_structure_info()` for structure paths (plans, memory bank, rules); use `manage_file()` for memory bank files; use path resolver utilities in code (e.g., `get_cortex_path()`, `CortexResourceType`)
     - **REQUIRED**: Check existing code for path resolution patterns
   - **FORBIDDEN**: Hardcoding the session directory, memory bank path, or plans path
   - **FORBIDDEN**: String concatenation for paths without using resolver utilities or Cortex tools
   - **Markdown files**: When creating or editing `.md`/`.mdc` files, follow the markdown formatting rule to prevent MD036 and other lint violations. Use `get_synapse_rules(task_description="markdown formatting")` for the rule and see [docs/guides/markdown-formatting.md](docs/guides/markdown-formatting.md) for headings vs emphasis and examples.
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
     - Unused call results: Assign to `_` if intentionally unused (e.g. `_ = path.mkdir(parents=True)` for `reportUnusedCallResult`). Do not suppress the diagnostic; fix by using the return value or assigning to `_`.
     - Missing type annotations: Add explicit types to all functions/methods
   - **If type errors exist**: Fix them immediately, do not continue to test writing
   - **Verification**: Re-run type check via MCP tool or script until 0 errors, 0 warnings
   - **Step 4.3.1 — Async method and test updates (when refactoring to async)**: When you make any method or function async, update all call sites in tests to await the coroutine. Verify all async method calls in tests are awaited. The pre-commit pipeline runs `check_async_tests` to detect unawaited coroutines in test files; run it via `execute_pre_commit_checks(checks=["check_async_tests"])` if you changed async behavior. See [Test maintenance guide](../../../docs/guides/test-maintenance.md).
3.5. **Before writing tests**: Review testing standards to ensure compliance—e.g. call `rules(operation="get_relevant", task_description="testing standards")` or read testing-standards.mdc. In particular: do not test private functions (functions starting with `_`); test through public APIs only.
4. Write or update tests (MANDATORY - comprehensive test coverage required):
   - **Testing standards (MANDATORY)**: Do not test private functions (functions starting with `_`). Test through public APIs only. If private function behavior needs verification, test it indirectly through public API calls.
   - Follow AAA pattern (MANDATORY)
   - No blanket skips (MANDATORY)
   - Target 100% pass rate on project's test suite
   - **Minimum code coverage per project's testing standards (check testing-standards.mdc)**
   - **Test Coverage Planning Checklist** (MANDATORY - plan before writing tests):
     - **Success cases**: Plan tests for all success paths and query types/operations
     - **Error cases**: Plan tests for all error conditions and edge cases
     - **Parameter variations**: Plan tests for all parameter combinations (e.g., `response_format`, `query_type`, optional parameters)
     - **AAA pattern**: Ensure all tests follow Arrange-Act-Assert structure
     - **Code path coverage**: Verify all code paths are covered (success, error, edge cases)
     - **For consolidated tools**: Plan both unit tests (with mocks, 80-90% coverage acceptable) and integration tests (95%+ coverage ideal)
     - **Coverage guidance**: Prioritize files with most uncovered lines (use coverage gap analysis tools if available); focus on error paths, edge cases, and public entry points for quick coverage gains.
   - **Unit tests**: Test all new public functions, methods, and classes individually
   - **Integration tests**: Test component interactions and data flow between modules
   - **Edge cases (MANDATORY)**: Always ensure to cover all edge cases—boundary conditions, error handling, invalid inputs, empty states, min/max values, null/empty collections, and both success and failure paths. Applies to any project/language/code.
   - **Test documentation**: Include clear docstrings explaining test purpose and expected behavior
   - **Pydantic v2 for JSON testing**: When testing MCP tool responses (e.g., `manage_file`, `rules`, `execute_pre_commit_checks`), use Pydantic v2 `BaseModel` types and `model_validate_json()` / `model_validate()` instead of asserting on raw `dict` shapes. See `tests/tools/test_file_operations.py` for examples (e.g., `ManageFileErrorResponse` pattern).
   - **Verify coverage**: Run coverage tool and ensure project's coverage threshold is met before considering implementation complete
5. Fix any errors or issues:
   - **⚠️ MANDATORY: Load Context Before Fixing**: Before applying fixes, you MUST load context and rules so fixes follow all project rules and guidelines:
     - Call `load_context(task_description="Fixing errors and issues during implementation", token_budget=15000)` (15k for fix/debug path)
     - If rules are enabled, call `rules(operation="get_relevant", task_description="Fixing errors, type issues, and quality violations")`; if disabled, read key coding standards from rules directory (path from `get_structure_info()` → `structure_info.paths.rules`)
     - Only after context and rules are loaded, proceed with fixes following project rules
   - Run linters and fix all issues
   - Fix type errors
   - Fix formatting issues using project's code formatter
   - Ensure all tests pass
   - **Before Step 4.5**, run ReadLints on all new/modified files (or call `fix_quality_issues()`) and fix any reported type or lint errors. Note: All Cortex MCP tools resolve project root internally; do NOT pass `project_root` as a parameter.

### Step 4.5: Verify Test Coverage (MANDATORY)

1. **Run coverage analysis**:
   - Use **only** Cortex MCP tool `execute_pre_commit_checks(checks=["tests"], test_timeout=600, coverage_threshold=0.90, strict_mode=False)` or, as fallback, the language-specific run_tests script from the Synapse scripts directory. Do **NOT** run raw `pytest` (or other test commands) in a Shell.
   - Review coverage report for new/modified files
2. **Verify coverage threshold** (per project's testing standards):
   - Check project's testing standards for required coverage threshold
   - Check that ALL new functionality meets the required coverage threshold
   - Identify any uncovered lines or branches in new code
3. **Add missing tests if coverage is below threshold**:
   - **⚠️ MANDATORY: Load Context Before Fixing**: Before adding tests, you MUST load context and rules:
     - Call `load_context(task_description="Fixing test coverage", token_budget=15000)` (15k for fix/debug path)
     - If rules are enabled, call `rules(operation="get_relevant", task_description="Test coverage and testing standards")`; if disabled, read key testing standards from rules directory
     - Only after context and rules are loaded, proceed with test additions following project testing standards
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
   - **⚠️ MANDATORY: Load Context Before Fixing**: Before applying fixes, you MUST load context and rules:
     - Call `load_context(task_description="Fixing code conformance violations", token_budget=15000)` (15k for fix/debug path)
     - If rules are enabled, call `rules(operation="get_relevant", task_description="Fixing code conformance violations")`; if disabled, read key coding standards from rules directory
     - Only after context and rules are loaded, proceed with fixes following project rules
   - If type violations: Add proper type annotations, use concrete types per language standards
   - If data modeling violations: Convert to project-mandated data types per language-specific rules
   - If structural violations: Apply the **helper module extraction pattern** per maintainability rules. Load rules via `rules(operation="get_relevant", task_description="helper module extraction, file size limits, function length limits")` or see maintainability.mdc for comprehensive guidance on extracting cohesive function groups to `*_helpers.py` modules, updating imports and tests, and maintaining coverage.
   - If naming violations: Rename following conventions
6. **BLOCKING**: Do NOT proceed to memory bank updates until all code conforms to rules

### Step 4.7: Run Quality Gate Before Finish (MANDATORY)

**Purpose**: Ensure no rot code is left for the commit pipeline to fix. The same quality gate as the commit pipeline MUST pass before marking the implementation complete. The quality gate includes **quality** (lint, file size, function length) and **type_check** so type diagnostics (e.g. reportRedeclaration) match IDE/CI. This aligns with the phase-based commit pipeline (Phase A); see AGENTS.md "Commit pipeline (phase-based)" for full flow and helper commands (`run_preflight_checks`, `/cortex/fix_tests`, `/cortex/fix-quality`).

1. **Run automated quality check**:
   - Use Cortex MCP tool `execute_pre_commit_checks(checks=["quality"])`. This runs both quality and type_check. Prefer the MCP tool. Do not pass `project_root`; tools resolve the project root internally.
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
5. **Quality gate skipped - environment (doc-only only)**: When the change set is **documentation-only** (no changes under `src/` or `tests/` that affect code behavior) and `execute_pre_commit_checks(checks=["quality"])` fails due to **environment** issues—e.g. "ruff/black not found", "type_check download/certificate" (or similar tool-unavailable or network/certificate failure)—the step may be considered satisfied. Record in your summary: "Quality gate skipped - environment (doc-only session); run full pre-commit before commit." The commit pipeline still requires full checks when run in a healthy environment; this is a session-time relaxation only.

### Step 5: Update Memory Bank - **Delegate to `memory-bank-updater` agent**

**Use the `memory-bank-updater` agent (Synapse agents directory) for this step.**

**CRITICAL – Safe memory bank updates (MANDATORY):** Do NOT use full-content `manage_file(..., operation="write", content=<entire file>)` for roadmap, progress, or activeContext. Use the dedicated MCP tools below to avoid corruption.

- **User-requested fixes**: After applying any user-requested fix that changes public API, type names, or documented behavior, update progress.md (and activeContext.md if the change affects current focus) so memory bank remains consistent with the codebase.
- **Requirement**: All updates to roadmap.md, progress.md, activeContext.md, and any other memory bank file MUST be performed with `manage_file(file_name='...', operation='write', ...)`. Read current content with `manage_file(operation='read')` before writing when building updated content.
- **Prohibition**: Do NOT use Write, StrReplace, or ApplyPatch on files under the memory bank directory (path from `get_structure_info()` → `structure_info.paths.memory_bank`). Using standard file tools for memory bank writes is a **VIOLATION**. Any edit to memory-bank files—including one-line fixes—must use `manage_file(operation='read')` then `manage_file(operation='write', content=...)`; do not use Write, StrReplace, or ApplyPatch on memory-bank paths.
- **Full-content fallback**: If you need to change only one line (e.g. one roadmap entry), read the file via `manage_file(operation='read')`, compute the full updated content (e.g. replace the line in the returned string), then call `manage_file(operation='write', content=updated_content, ...)`. Do not use Write, StrReplace, or ApplyPatch on memory bank paths.

**When the completed step references a plan file (e.g. Plan: .cortex/plans/session-optimization-....md):**

- **PREFERRED:** Call **`complete_plan(plan_title="<step title>", summary="<short summary>", completion_date="YYYY-MM-DD", progress_entry="**Title** - COMPLETE. Summary...", plan_file_name="<plan basename>")`** with the plan file basename (e.g. `session-optimization-roadmap-full-content-enforcement.md`). This single tool: removes the roadmap bullet, appends to activeContext, appends to progress, and **moves (archives) the plan file** to the correct archive directory. No separate archive step is needed for that plan.
- **Progress entry template:** Use this format for `progress_entry` and `entry_text`: `**<Title> (<date>)** - COMPLETE. <summary>.` Example: `**Phase 54 Session Start (2026-02-20)** - COMPLETE. Implemented session_start and doc updates.` The tools validate date (YYYY-MM-DD) and that the title segment is closed before COMPLETE (e.g. ")** - COMPLETE").
- **Alternative:** If you cannot use complete_plan, use the three tools below and then run the plan-archiver agent (Step 6.5) to archive the plan file manually.

**When the step does not reference a plan file, or you use the alternative:**

1. **Remove the completed step from roadmap**
   - **MANDATORY:** Call **`remove_roadmap_entry(entry_contains="<unique substring>")`** with a substring that uniquely identifies the completed roadmap bullet (e.g. the step title or plan name). The tool removes that single bullet and writes the file safely.
   - **Optional – orphan section:** If the last bullet in a subsection was removed and the subsection heading should be removed too, call **`remove_roadmap_section(section_heading_contains="<heading substring>")`** instead of full-content roadmap write.
   - **FORBIDDEN:** Do NOT read roadmap, build updated content, and call `manage_file(roadmap.md, write, content=...)` with full content. That pattern causes corruption.
   - Roadmap records future/upcoming work only; completed work belongs in activeContext only.

2. **Add one progress entry**
   - **MANDATORY:** Call **`append_progress_entry(date_str="YYYY-MM-DD", entry_text="**Title** - COMPLETE. Summary...")`** to add a single entry under the date section. Use today's date (YYYY-MM-DD). The tool appends one bullet safely.
   - **FORBIDDEN:** Do NOT read progress, build full content, and call `manage_file(progress.md, write, content=...)` with full content.

3. **Add completed work to activeContext**
   - **MANDATORY:** Call **`append_active_context_entry(date_str="YYYY-MM-DD", title="<step title>", summary="<short summary>")`** to append one completed entry under ## Completed Work (date). The tool creates the section if needed and appends safely.
   - **FORBIDDEN:** Do NOT read activeContext, build full content, and call `manage_file(activeContext.md, write, content=...)` with full content for this update.
   - **Write quality (before calling append_*):** Verify any coverage percentage in entry text is 0–100 (e.g. 90.01% not 900.01%). Verify phase/label names have no concatenation typos (e.g. "Phase 18 Markdown" not "Phase 18Markdown"). Use date format YYYY-MM-DD only. **Progress entry format:** When generating `progress_entry` or `entry_text`, ensure the phase/title segment is properly closed—e.g. the entry must contain ")** - COMPLETE" (not "COMPLETE" immediately after a date or unclosed parenthesis); malformed example: "20260209COMPLETE". See memory-bank-updater agent write-quality guidance.
   - **Progress entry template:** `**<Title> (<date>)** - COMPLETE. <summary>.` Use YYYY-MM-DD for dates; the tools reject invalid dates and malformed entries.

4. **Optional: Current focus / next steps**
   - If you must update "Current Focus" or "Next Steps" in activeContext (e.g. the completed step was the active focus), prefer a minimal edit (e.g. small search-replace or targeted edit). Only if unavoidable, use read then write with minimal changed content; never build and write the entire file for a single completed-step update.

5. **⚠️ MANDATORY: If the roadmap step references a plan file (e.g., phase-XX-*.md in the plans directory) and the work is too long to complete in one session**:
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

3. **Run roadmap sync validation (MANDATORY)**:
   - Use Cortex MCP validation for roadmap synchronization (either via `validate(check_type="roadmap_sync")` or the dedicated roadmap-sync MCP tool).
   - Treat any `valid: false` result, invalid references, or non-empty `unlinked_plans` as **BLOCKING**: fix roadmap/plan/archive/memory-bank inconsistencies (e.g., completed plans still in `.cortex/plans/`, plans removed from roadmap but not archived, stale plan links) before proceeding to Step 6.5 and Step 7.
   - **⚠️ CRITICAL - Roadmap edit discipline**: When fixing roadmap sync issues (e.g., adding plan links, updating references, removing stale entries), **ALL edits to roadmap.md MUST be performed via `manage_file(operation='write', ...)` after reading current content with `manage_file(operation='read')`**. Do **NOT** use Write, StrReplace, or ApplyPatch on memory-bank paths. For single-entry changes (add/remove), prefer the dedicated roadmap tools (`add_roadmap_entry`, `remove_roadmap_entry`, `register_plan_in_roadmap`) over full-content writes. See memory-bank-updater agent and Step 5 for safe roadmap update patterns.

### Step 6.5: Archive Completed Plans - **Delegate to `plan-archiver` agent**

**Use the `plan-archiver` agent (Synapse agents directory) for this step.**

- **Dependency**: Must run AFTER Step 5 (memory bank updates) and Step 6 (verify completion)
- **If you used `complete_plan(..., plan_file_name=...)` in Step 5:** The plan file was already moved to the archive by that tool; no duplicate should remain in `.cortex/plans/`. Still run the plan-archiver agent to catch any other completed plans (e.g. from previous sessions) and to validate.
- **If you used the three separate tools (remove_roadmap_entry, append_progress_entry, append_active_context_entry):** The plan file was NOT archived; you MUST run the plan-archiver agent to move the plan file to the correct archive directory.
- **Workflow**:
  1. **READ** the plan-archiver agent file (Synapse agents directory: `.cortex/synapse/agents/plan-archiver.md`)
  2. **EXECUTE** all execution steps from the agent file:
     - Detect completed plans in `.cortex/plans/` directory (excluding archive)
     - Archive each completed plan to appropriate archive directory:
       - Phase plans (`phase-X-*.md`): Archive to `archive/PhaseX/`
       - Investigation plans (`phase-investigate-*.md`): Archive to `archive/Investigations/YYYY-MM-DD/`
       - Session optimization plans (`session-optimization-*.md`): Archive to `archive/SessionOptimization/`
     - Update links in memory bank files to point to archive locations
     - Validate links using `validate_links()` MCP tool
     - Validate archive locations (verify zero completed plans remain in `.cortex/plans/`)
     - **Remove duplicate if present**: After each move, if the same plan file still exists in `.cortex/plans/` (root), delete it so only the archived copy remains. Never leave a copy in the plans root.
  3. **Report results**: Count of plans found, archived, links updated, validation status
  4. **If no completed plans found**: Report "0 plans archived" but DO NOT skip this step
- **BLOCKING**: If completed plans are found but not archived, or if link validation fails, or if a duplicate remains in the plans root, this is a violation

### Step 7: Execute end-of-session Analyze (MANDATORY)

- **Dependency**: Must run AFTER Step 6 (verify completion).
- **MANDATORY**: At the end of this prompt, you MUST execute the **Analyze (End of Session)** prompt (`analyze.md` from the Synapse prompts directory). Read and execute that prompt in full: it runs context effectiveness analysis and session optimization, saves a report to the reviews directory, and optionally creates an improvements plan. Do not skip this step.
- **Path**: Resolve the Analyze prompt path via project structure or `get_structure_info()` (e.g. Synapse prompts directory); the prompt file is `analyze.md`.

## IMPLEMENTATION GUIDELINES

### Code Quality

- **Type annotations**: Complete coverage required per language-specific standards
- **Language features**: Use modern language features and built-ins appropriate to the project's language version
- **Concrete types**: Use concrete types instead of generic types wherever possible per language standards
- **Function/method length**: Keep within project's length limits (check language-specific coding standards)
- **File length**: Keep within project's size limits (check language-specific coding standards)
- **Helper module extraction (standard refactoring)**: When file size or function length exceeds project limits, use the **helper module extraction pattern** per maintainability rules. Load rules via `rules(operation="get_relevant", task_description="helper module extraction, file size limits, function length limits")` or see maintainability.mdc for comprehensive guidance. This is the standard approach for resolving quality violations; prefer it over ad-hoc splitting.
- **Incremental validation during refactoring**: When refactoring to fix quality violations, validate each fix incrementally (type check + quality check) before proceeding to next fix. Incremental validation catches new violations immediately and reduces fix iterations.
- **Duplicate detection before extracting helpers**: Before extracting helper functions, search for existing functions with similar names (use Grep tool or grep command). Reuse existing helpers when possible; rename new helpers to avoid duplicates.
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
- **Global `fail-under=95` failures**: When running targeted tests (e.g., via `execute_pre_commit_checks(checks=["tests"], ...)` or the Synapse run_tests script with path args), global coverage failures dominated by untouched modules should be logged as technical debt in progress.md / activeContext.md via `manage_file()` (and, where appropriate, new coverage-raising phases), not "fixed ad hoc" during unrelated, narrow tasks
- **Recording coverage debt**: Document in Memory Bank with wording like: "Global coverage at 21.7% due to untested analysis/structure modules. This is expected legacy debt and does not block focused roadmap sync work. Coverage improvement tracked in Phase XX."
- **Reference coverage plans**: Reference relevant coverage-improvement plan from roadmap entries instead of attempting broad, unscheduled coverage work

### Memory Bank Updates

- **Location**: All memory bank files MUST be accessed via Cortex MCP tool `manage_file()`; do not hardcode the memory bank path (resolve via `get_structure_info()` if needed)
- **Timestamps**: Use YY-MM-DD format only
- **Format**: Keep entries reverse-chronological
- **Completeness**: Update after significant changes (MANDATORY)

## ERROR HANDLING

**Fix-path rule (MANDATORY)**: Whenever the agent encounters a problem and switches to fixing (errors, test failures, quality, type issues, coverage, or conformance), it **must** load context and rules **before** making code or test changes. Call `load_context(task_description="...", token_budget=15000)` (15k for fix/debug) and, when applicable, `rules(operation="get_relevant", task_description="...")` (or read from rules path if disabled). Only after context and rules are loaded, proceed with fixes. This is consistent with load-context-at-step-start; the fix-path load is additional when the agent actually enters fix mode.

If you encounter any issues during implementation:

1. **Roadmap parsing errors**: If the roadmap format is unclear, read it carefully and identify the structure. If still unclear, proceed with the first uncompleted item you can identify.
2. **Implementation blockers**: If you cannot complete the step due to missing information or dependencies, document what is needed and update the roadmap accordingly.
3. **Test failures**: Fix all test failures before considering the step complete. Do not skip tests without justification.
   - **⚠️ MANDATORY: Load Context Before Fixing**: Before fixing test failures, you MUST load context and rules:
     - Call `load_context(task_description="Fixing test failures", token_budget=15000)` (15k for fix/debug path)
     - If rules are enabled, call `rules(operation="get_relevant", task_description="Fixing test failures and ensuring test standards")`; if disabled, read key testing standards from rules directory
     - Only after context and rules are loaded, proceed with fixes following project rules and test standards
4. **Memory bank errors (CRITICAL)**: If Cortex MCP tools crash, disconnect, or exhibit unexpected behavior **on core Memory Bank operations** (e.g. `manage_file`, `load_context`, `validate`):
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
5. **Connection closed during `fix_quality_issues` (special case)**:
   - **When**: `fix_quality_issues` returns an MCP error whose message or code indicates "Connection closed" or "ClosedResourceError" (e.g. `MCP error -32000: Connection closed`) while running as a pre-flight helper (before new work or after code changes).
   - **Action**:
     1. Use `check_mcp_connection_health` to confirm the MCP connection is healthy.
     2. If healthy, **retry `fix_quality_issues` once**.
     3. If the second attempt fails with the same class of error (or "tool not found" immediately after a connection closed error), **do not attempt a shell fallback**; instead:
        - Treat the workspace as potentially stale but **continue the roadmap implementation**, relying on `execute_pre_commit_checks` for strict quality/type/test gates.
        - Note in your summary that "`fix_quality_issues` could not complete due to client connection closure; quality gates were enforced via `execute_pre_commit_checks` only."
   - **Rationale**: `fix_quality_issues` is a convenience helper, not a hard gate. Connection-closed errors here usually indicate client timeout/disconnect rather than a server bug; retry-once then proceed with strict quality gates prevents the implementation flow from being blocked while still enforcing correctness.
6. **Quality gate unavailable (doc-only sessions)**: When the change set is documentation-only (no code under `src/` or `tests/` affecting behavior) and `execute_pre_commit_checks` fails due to environment issues—e.g. ruff/black not found at expected paths, or type_check failing with download/certificate errors—you may treat Step 4.7 as satisfied for this session. Add to your summary: "Quality gate skipped - environment (doc-only session); run full pre-commit before commit." Do **not** skip when code was changed or when the failure is due to actual lint/type errors; only when the failure is clearly tool-unavailable or network/certificate. See also [Troubleshooting: Quality gate unavailable in environment](../../../docs/guides/troubleshooting.md#quality-gate-unavailable-in-environment).

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
- ✅ **Completed plans archived** - Plan archiver agent executed; any completed plans moved to archive directories; links updated and validated
- ✅ **Roadmap sync validation passed** - Roadmap synchronization check (`roadmap_sync`) reports valid, with no unlinked non-archived plans and no invalid references
- ✅ **Analyze prompt executed** - Analyze (End of Session) prompt (`analyze.md`) run to complete context effectiveness and session optimization analysis

## NOTES

- **CRITICAL PRIORITY**: Blockers in "Blockers (ASAP Priority)" section (typically around line 217 in roadmap.md) MUST be handled FIRST before any other roadmap items
- This is a generic command that can be reused for any roadmap step
- The agent should be thorough and complete the entire step, not just part of it
- If a step is too large, break it down into smaller sub-tasks and complete them systematically
- For especially complex or ambiguous steps (e.g. architecture/large design or multi-module refactors), use the `sequentialthinking` MCP tool to structure your reasoning into numbered thoughts before and during implementation.
- **MANDATORY PLAN UPDATES**: If the roadmap step references a plan file (e.g., phase-XX-*.md in the plans directory) and the work cannot be completed in one session, you MUST update the plan file at the end of the session to reflect the current implementation status. Resolve the plans directory path via `get_structure_info()` → `structure_info.paths.plans`. This ensures continuity and allows future sessions to pick up where you left off.
- **MANDATORY PLAN ARCHIVING**: If a plan file is marked as COMPLETE (status changed to COMPLETED/COMPLETE), you MUST archive it immediately using the plan-archiver agent (Step 6.5). Do not leave completed plans in `.cortex/plans/` - archive them as soon as status becomes COMPLETE.
- Always update the memory bank after completing work using Cortex MCP tools
- Follow all workspace rules and coding standards throughout implementation
- **CRITICAL**: Never access memory bank files directly via file paths - always use Cortex MCP tools for structured access
- **Plan files**: Plan files are in the plans directory (path from `get_structure_info()` → `structure_info.paths.plans`) and should be accessed using standard file tools (not MCP tools, as they are not part of the memory bank)
- **Script generation prevention**: Before generating a temporary script, use `suggest_tool_improvements(task_description=...)` to discover existing tools/scripts. If you do create a script, use `capture_session_script` to record it for analysis and potential promotion; use `analyze_session_scripts` and `promote_session_script` to validate and get templates.

## MISSING TOOLS (If Required)

If the following tools would be helpful but are not available, they should be planned for implementation:

- `get_context_for_task(task_description, file_list=None)` - Get context for a specific task, optionally filtering to specific files
- `batch_read_memory_bank_files(file_names)` - Read multiple memory bank files in a single call
- `get_memory_bank_file_list()` - Get list of all available memory bank files with metadata

These tools would provide more efficient and structured access patterns, but the existing tools (`load_context()`, `load_progressive_context()`, `manage_file()`) are sufficient for current needs.
