# Analyze Session for Synapse Optimization

**AI EXECUTION COMMAND**: Analyze the current session to identify mistakes, anti-patterns, and optimization opportunities. Generate actionable recommendations to improve `.cortex/synapse` prompts and rules to prevent similar issues in future sessions.

**CRITICAL**: This command analyzes the CURRENT session (not historical sessions) to find patterns of mistakes that could be prevented by improving Synapse prompts and rules. Execute all steps AUTOMATICALLY without asking for permission.

**Agent Delegation**: This prompt delegates to the **`session-optimization-analyzer` agent** from `.cortex/synapse/agents/session-optimization-analyzer.md` for specialized session analysis.

**Tooling Note**: Use Cortex MCP tools for session analysis and memory bank operations. Use standard Cursor tools for file operations outside `.cortex/` directory.

## ⚠️ MANDATORY PRE-ACTION CHECKLIST

**BEFORE executing this command, you MUST:**

1. ✅ **Read relevant memory bank files** - Understand current project context:
   - **Use Cortex MCP tool `manage_file()`** to read `.cursor/memory-bank/activeContext.md` to understand current work focus
   - **Use Cortex MCP tool `manage_file()`** to read `.cursor/memory-bank/progress.md` to see recent achievements
   - **Use Cortex MCP tool `manage_file()`** to read `.cursor/memory-bank/systemPatterns.md` to understand architectural patterns
   - **Use Cortex MCP tool `manage_file()`** to read `.cursor/memory-bank/techContext.md` to understand technical context

2. ✅ **Read relevant rules** - Understand project requirements:
   - Read `.cursor/rules/coding-standards.mdc` for core coding standards
   - Read `.cursor/rules/maintainability.mdc` for architecture rules
   - Read language-specific coding standards (e.g., `.cursor/rules/python-coding-standards.mdc`) for type system requirements
   - Read `.cortex/synapse/rules/` for existing Synapse rules

3. ✅ **Understand session analysis scope**:
   - Identify the current session context (what work was done)
   - Understand what mistakes or issues occurred during the session
   - Check for user comments or feedback about problems

4. ✅ **Verify prerequisites** - Ensure all prerequisites are met:
   - Confirm session logs/transcripts are accessible
   - Verify access to `.cortex/synapse/` directory
   - Check that analysis tools are available

**VIOLATION**: Executing this command without following this checklist is a CRITICAL violation that blocks proper analysis.

## Steps

1. **Load current session data** - Analyze the current session:
   - **Use Cortex MCP tool `analyze_context_effectiveness()`** with `analyze_all_sessions=False` to analyze only the current session
   - Review session logs/transcripts if available (check `.cursor/agent-transcripts/` or similar)
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
   - **Prompt improvements**: Changes to `.cortex/synapse/prompts/*.md` files
     - Add missing validation steps
     - Clarify ambiguous instructions
     - Add examples of correct patterns
     - Add explicit anti-pattern warnings
   - **Rule improvements**: Changes to `.cortex/synapse/rules/*.mdc` files
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

8. **Save analysis report** - Store findings for future reference:
   - **MANDATORY: Use Cortex MCP tools to get the correct path**:
     1. Call `get_structure_info(project_root=None)` MCP tool to get structure information
     2. Extract the reviews directory path from the response: `structure_info.paths.reviews` (e.g., `/path/to/project/.cortex/reviews`)
     3. Construct the full file path: `{reviews_path}/session-optimization-{timestamp}.md`
     4. Use the `Write` tool with this dynamically constructed path (it will create parent directories automatically)
   - **NEVER use hardcoded paths like `.cortex/reviews/session-optimization-*.md`** - Always use `get_structure_info()` to get the path dynamically
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
