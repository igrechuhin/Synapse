# Prompt Refactoring Guide: Orchestration vs Implementation

## Principle

**Prompts = Orchestration** | **Agents = Implementation**

## What Prompts Should Keep

### ✅ Orchestration Logic

- Step order and dependencies
- Workflow coordination (when to proceed, when to block)
- Error handling between steps
- Critical workflow rules

### ✅ High-Level Descriptions

- What each step accomplishes
- Why steps are in a certain order
- Dependencies between steps

### ✅ Workflow-Specific Rules

- "Step 0 must complete before Step 1"
- "Step 12 must run after Steps 4-11"
- "Block commit if any step fails"

## What Prompts Should Remove

### ❌ Implementation Details

- Specific MCP tool calls and parameters
- Tool response parsing logic
- Detailed validation steps
- Implementation instructions

### ❌ Agent-Specific Logic

- How to use specific tools
- What to check in tool responses
- Detailed error handling for specific tools

## Refactoring Pattern

### Before (Duplicated Implementation)

```markdown
0. **Fix errors and warnings** - **Delegate to `error-fixer` agent**:
   - Use the `error-fixer` agent (Synapse agents directory) for this step
   - The agent will use `execute_pre_commit_checks()` MCP tool:
   - **Call MCP tool**: `execute_pre_commit_checks(checks=["fix_errors"], strict_mode=False)`
   - **CRITICAL - MCP TOOL VALIDATION**: After tool call, validate response:
     - **Automatic validation**: `mcp_tool_wrapper` and `validate_mcp_tool_response()` automatically validate:
       - Response is not None
       - Response is dict (not JSON string)
       - Response has "status" field
       [... 30 more lines of implementation details ...]
```

### After (Orchestration Only)

```markdown
0. **Fix errors and warnings** - **Delegate to `error-fixer` agent**:
   - **Agent**: Use the error-fixer agent (Synapse agents directory) for implementation details
   - **CRITICAL**: This step MUST complete successfully before proceeding to Step 1
   - **BLOCK COMMIT**: If any errors remain after this step, stop immediately
   - **Dependency**: Must run BEFORE all other pre-commit checks
   - **Workflow**: After agent completes, verify zero errors remain before proceeding
```

## Benefits

1. **Single Source of Truth**: Implementation details live in agents only
2. **Easier Maintenance**: Update agent logic in one place
3. **Clear Separation**: Prompts orchestrate, agents implement
4. **Reduced Duplication**: No repeated instructions
5. **Better Focus**: Prompts focus on workflow, agents focus on tasks

## Example: Complete Step Refactoring

### Step 0: Error Fixing

**Orchestration (in prompt):**

- Order: Must be Step 0 (before all other checks)
- Dependency: None (first step)
- Success criteria: Zero errors must remain
- Failure handling: Block commit if errors remain
- Next step: Proceed to Step 1 only if successful

**Implementation (in agent):**

- How to call MCP tool
- Tool parameters
- Response parsing
- Validation logic
- Error reporting

This separation makes the system more maintainable and clear.
