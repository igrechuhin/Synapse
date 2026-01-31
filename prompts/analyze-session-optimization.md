# Analyze Session for Synapse Optimization

**AI EXECUTION COMMAND**: Analyze the current session to identify mistakes, anti-patterns, and optimization opportunities. Generate actionable recommendations to improve Synapse prompts and rules to prevent similar issues in future sessions.

**CRITICAL**: This command analyzes the CURRENT session (not historical sessions) to find patterns of mistakes that could be prevented by improving Synapse prompts and rules. Execute all steps AUTOMATICALLY without asking for permission.

**Agent Delegation**: This prompt delegates to the **`session-optimization-analyzer` agent** (Synapse agents directory) for specialized session analysis.

**Tooling Note**: Use Cortex MCP tools for session analysis and memory bank operations. Use standard Cursor tools for file operations outside Cortex structure directories. Resolve paths via `get_structure_info()` and memory bank via `manage_file()`.

## ⚠️ MANDATORY PRE-ACTION CHECKLIST

**BEFORE executing this command, you MUST:**

1. ✅ **Read relevant memory bank files** - Understand current project context:
   - **Use Cortex MCP tool `manage_file(file_name="activeContext.md", operation="read")`** to understand current work focus
   - **Use Cortex MCP tool `manage_file(file_name="progress.md", operation="read")`** to see recent achievements
   - **Use Cortex MCP tool `manage_file(file_name="systemPatterns.md", operation="read")`** to understand architectural patterns
   - **Use Cortex MCP tool `manage_file(file_name="techContext.md", operation="read")`** to understand technical context

2. ✅ **Read relevant rules** - Understand project requirements:
   - Use Cortex MCP tool `rules(operation="get_relevant", task_description="Coding standards, maintainability, session analysis")` or read from the rules directory (path from `get_structure_info()` → `structure_info.paths.rules`)
   - Ensure core coding standards, architecture rules, language-specific standards, and Synapse rules are in context

3. ✅ **Understand session analysis scope**:
   - Identify the current session context (what work was done)
   - Understand what mistakes or issues occurred during the session
   - Check for user comments or feedback about problems

4. ✅ **Verify prerequisites** - Ensure all prerequisites are met:
   - Confirm session logs/transcripts are accessible
   - Verify access to Synapse directory (path from project structure or `get_structure_info()` if available)
   - Check that analysis tools are available

**VIOLATION**: Executing this command without following this checklist is a CRITICAL violation that blocks proper analysis.

## Steps

1. **Load current session data** - Analyze the current session:
   - **Use Cortex MCP tool `analyze_context_effectiveness()`** with `analyze_all_sessions=False` to analyze only the current session
   - **Expected behavior**: `analyze_context_effectiveness()` may return `status: "no_data"` when no `load_context` calls occur in the current session
   - **This is expected** for workflow/quality-only sessions (e.g., `/cortex/commit` that do not call `load_context`)
   - **Fallback signals**: When `status: "no_data"`, use alternative data sources:
     - Commit pipeline tool outputs (pre-commit checks, validations, roadmap sync results)
     - Memory-bank diffs (`activeContext.md`, `progress.md`, `roadmap.md`)
     - Git/file diffs showing code changes
     - Recent MCP tool invocations and their results
   - Review session logs/transcripts if available (path from project structure or IDE)
   - Identify all code changes made during the session
   - Identify all user comments, corrections, or feedback about mistakes

2. **Identify mistake patterns** - Categorize mistakes found:
   - **Type system violations**: Using `TypedDict` instead of Pydantic models, using `dict[str, object]` instead of concrete types, using `Any` types
   - **Code organization violations**: Models in wrong files, functions in wrong modules, missing imports
   - **Rule compliance violations**: Not following project rules (e.g., Pydantic requirements, file size limits, function length limits)
   - **Process violations**: Skipping required steps, not validating results, premature stopping
   - **Tool usage violations**: Not using MCP tools when required, using wrong tools, incorrect tool parameters
   - **Documentation violations**: Missing docstrings, incorrect type hints, unclear code

3. **Analyze root causes** - Determine why mistakes occurred:
   - **Missing guidance**: Were Synapse prompts/rules missing specific instructions that would have prevented the mistake?
   - **Unclear guidance**: Were instructions present but ambiguous or easy to misinterpret?
   - **Incomplete validation**: Were validation steps missing that could have caught the mistake earlier?
   - **Process gaps**: Were required steps missing from the workflow that would have prevented the issue?
   - **Tool limitations**: Were tools not available or not properly documented?

4. **Generate optimization recommendations** - Create specific, actionable recommendations:
   - **For each mistake pattern identified**:
     - Determine which Synapse prompt(s) or rule(s) should be updated
     - Specify the exact change needed (add instruction, clarify existing instruction, add validation step)
     - Prioritize recommendations (critical, high, medium, low)
     - Estimate impact (how many similar mistakes would this prevent?)

5. **Categorize recommendations by target**:
   - **Prompt improvements**: Changes to Synapse prompts directory (prompts/*.md)
     - Add missing validation steps
     - Clarify ambiguous instructions
     - Add examples of correct patterns
     - Add explicit anti-pattern warnings
   - **Rule improvements**: Changes to Synapse rules directory (rules/*.mdc)
     - Add new rules for common mistake patterns
     - Strengthen existing rules with examples
     - Add validation requirements
   - **Process improvements**: Changes to workflow or checklist steps
     - Add mandatory validation steps
     - Reorder steps to catch issues earlier
     - Add explicit "do not" instructions

6. **Create optimization report** - Generate structured report:
   - **Summary**: Brief overview of analysis findings
   - **Mistake patterns**: Detailed list of mistakes found with examples
   - **Root causes**: Analysis of why mistakes occurred
   - **Recommendations**: Prioritized list of specific improvements
   - **Implementation plan**: Suggested order for implementing recommendations
   - **Expected impact**: How each recommendation would prevent future mistakes

7. **Output format** - Present findings in structured format:

   ```markdown
   # Session Optimization Analysis

   ## Summary
   [Brief overview of analysis findings]

   ## Mistake Patterns Identified

   ### Pattern 1: [Name]
   - **Description**: [What mistake occurred]
   - **Examples**: [Specific examples from session]
   - **Frequency**: [How often it occurred]
   - **Impact**: [Severity of the mistake]

   ### Pattern 2: [Name]
   ...

   ## Root Cause Analysis

   ### Cause 1: [Name]
   - **Description**: [Why this mistake occurred]
   - **Contributing factors**: [What made it more likely]
   - **Prevention opportunity**: [How Synapse could prevent this]

   ...

   ## Optimization Recommendations

   ### Recommendation 1: [Title]
   - **Priority**: [Critical/High/Medium/Low]
   - **Target**: [Which prompt/rule file]
   - **Change**: [Specific change needed]
   - **Expected impact**: [How many similar mistakes would this prevent]
   - **Implementation**: [Specific steps to implement]

   ...

   ## Implementation Plan

   1. [First recommendation to implement]
   2. [Second recommendation]
   ...
   ```

**⚠️ MD024 (Duplicate Heading) Prevention**:

- **If adding a second analysis pass** (e.g., context-effectiveness addendum) to an existing review file:
  - **Suffix headings with a qualifier** (e.g., `(Addendum)`, `(Context Effectiveness Pass)`, `(Pass 2)`)
  - **Example**: Instead of `### Mistake Patterns Identified`, use `### Mistake Patterns Identified (Context Effectiveness Pass)`
  - **Prevents**: Markdownlint `MD024` errors that propagate through memory-bank transclusions
  - **Avoid duplicate headings**: Never reuse the same heading at the same level without a suffix when appending addenda

1. **Save analysis report** - Store findings for future reference:
   - **MANDATORY: Use Cortex MCP tools to get the correct path**:
     1. Call `get_structure_info(project_root=None)` MCP tool to get structure information
     2. Extract the reviews directory path from the response: `structure_info.paths.reviews` (use the value returned by the Cortex tool; do not hardcode)
     3. **Canonical filename pattern**: `session-optimization-YYYY-MM-DDTHH-MM.md` (e.g., `session-optimization-2026-01-28T17-58.md`)
     4. **Timestamp format rules** (suffix MUST always be YYYY-MM-DDTHH-mm):
        - **Project rule (real-time-references.mdc)**: ALL time references MUST use real time. Any timestamp must be derived from an actual source (e.g. file mtime, tool that returns session/current time). Do NOT invent a value to satisfy a format. Inventing time is a CRITICAL violation.
        - **Date component**: `YYYY-MM-DD` (e.g., `2026-01-28`)
        - **Time component**: `HH-mm` (hours and minutes, hyphen-separated, e.g., `17-58` for 5:58 PM)
        - **CRITICAL**: The suffix MUST always be `YYYY-MM-DDTHH-mm`. No date-only or other formats.
        - **CRITICAL**: The `T` separator MUST be followed by a full time-of-day component (`HH-mm`), not arbitrary text or counters
        - **Derive from real time only**: Use a real source (e.g. run `date +%Y-%m-%dT%H-%M` in shell, transcript file mtime, or a tool that returns session/current time). Do NOT invent a value (e.g. `15-00`, `T02`). NEVER use fallback or placeholder time (e.g. `T00-00`, "unknown").
        - **Avoid conflicts**: If a file with the same date already exists, use a different time (e.g. run `date` again or use mtime from another file) to make it unique.
     5. Construct the full file path: `{reviews_path}/session-optimization-YYYY-MM-DDTHH-MM.md`
     6. Use the `Write` tool with this dynamically constructed path (it will create parent directories automatically)
   - **NEVER use hardcoded paths** - Always use `get_structure_info()` to get the reviews path dynamically (`structure_info.paths.reviews`)
   - **NEVER use invalid timestamp formats** like `T02`, `T-session`, or `T-{arbitrary-text}` - The `T` separator requires a valid time component (`HH-mm`)
   - **Filename validation**: Before saving, verify the filename matches the canonical pattern; detect malformed filenames (e.g., `TNN` with no minutes) and suggest renaming
   - Include full analysis, recommendations, and implementation suggestions
   - Link report in roadmap if significant improvements are identified

## ⚠️ CRITICAL REQUIREMENTS

- **Focus on prevention**: Recommendations must be actionable changes to Synapse prompts/rules that would prevent similar mistakes
- **Be specific**: Include exact file paths, line numbers, or sections where changes should be made
- **Prioritize**: Focus on high-impact, high-frequency mistakes first
- **Validate recommendations**: Ensure recommendations align with project's coding standards and architecture patterns
- **Consider context**: Recommendations should be appropriate for the project's language, framework, and patterns

## Success Criteria

- ✅ All mistake patterns from the session are identified and categorized
- ✅ Root causes are analyzed for each mistake pattern
- ✅ Specific, actionable recommendations are generated for Synapse improvements
- ✅ Recommendations are prioritized and include expected impact
- ✅ Analysis report is saved for future reference
- ✅ High-priority recommendations are ready for immediate implementation
