# Prompt Refactoring Summary

## Answer to User's Question

**Yes, we should simplify prompts** - they should focus on **orchestration** (order, dependencies, workflow coordination) while agents handle **implementation details**.

## What Changed

### Before (Duplicated Implementation)

- Prompts had detailed MCP tool calls, validation logic, and implementation steps
- Same information existed in both prompts and agents
- Maintenance burden: changes needed in two places

### After (Orchestration Only)

- Prompts focus on workflow orchestration
- Agents contain all implementation details
- Single source of truth for each concern

## Refactoring Pattern Applied

Each step now follows this pattern:

```markdown
X. **Step Name** - **Delegate to `agent-name` agent**:
   - **Agent**: Use `.cortex/synapse/agents/agent-name.md` for implementation details
   - **Dependency**: Must run AFTER Step Y (or BEFORE Step Z)
   - **CRITICAL**: Success criteria that affects workflow
   - **BLOCK COMMIT**: Conditions that stop the workflow
   - **Workflow**: What happens after agent completes
```

## Benefits

1. **Single Source of Truth**: Implementation details live in agents only
2. **Easier Maintenance**: Update agent logic in one place
3. **Clear Separation**: Prompts orchestrate, agents implement
4. **Reduced Duplication**: No repeated instructions
5. **Better Focus**: Prompts focus on workflow, agents focus on tasks

## Status

- ✅ Step 0 (error-fixer) - Refactored
- ✅ Step 1 (code-formatter) - Refactored
- ⚠️ Steps 1.5-14 - Need refactoring (still have detailed implementation)

## Next Steps

Continue refactoring remaining steps to follow the same pattern.
