# Prompt Refactoring Summary

## Principle

**Prompts = Orchestration** | **Agents = Implementation**

Prompts focus on workflow orchestration (step order, dependencies, blocking conditions). Agents contain all implementation details (tool calls, validation logic, parsing).

## Refactoring Pattern

Each step follows this pattern:

```markdown
X. **Step Name** - **Delegate to `agent-name` agent**:
   - **Agent**: Use the agent-name agent (Synapse agents directory)
   - **Dependency**: Must run AFTER Step Y (or BEFORE Step Z)
   - **CRITICAL**: Success criteria that affects workflow
   - **BLOCKING**: Conditions that stop the workflow
   - **Output**: Structured result per shared-handoff-schema.md
```

## Shared Infrastructure

### Typed Inter-Agent Handoff (`shared-handoff-schema.md`)

- Defines JSON schemas for every agent-to-orchestrator result
- Orchestrators validate required fields before passing data downstream
- Eliminates state loss from implicit LLM memory

### Common Pre-Action Checklist (`common-checklist.md`)

- Single agent that loads structure, memory bank, rules, and detects primary language
- Referenced by: `create-plan.md`, `review.md`, `implement-next-roadmap-step.md`, `analyze.md`
- Eliminates ~300 lines of duplicated `manage_file` calls across prompts

### Language-Aware Review

- `common-checklist` detects `primary_language` from `techContext.md`
- `bug-detector` agent filters checks by language (Python, Swift, TypeScript, etc.)
- `review.md` passes `primary_language` to all sub-agents

### Conditional Analyze

- `analyze.md` runs only as the **last workflow** in a session (not after every prompt)
- `commit.md` always runs analyze (typically last action)
- Other prompts (`review.md`, `create-plan.md`, `implement-next-roadmap-step.md`) run analyze conditionally
- Prevents redundant 176-line recursive execution

### Simplified Roadmap Registration

- `plan(operation="register")` is the **sole API** for adding new roadmap entries
- Full-content `manage_file(write)` fallback removed from `create-plan.md`
- Eliminates highest-complexity branching path (50+ lines of defensive write guards)

## Status

- ✅ Shared handoff schema created
- ✅ Common checklist agent created
- ✅ create-plan.md simplified (roadmap write path, pre-action checklist, analyze tail)
- ✅ review.md updated (common-checklist, language-aware, conditional analyze)
- ✅ implement-next-roadmap-step.md updated (common-checklist, conditional analyze)
- ✅ analyze.md updated (common-checklist delegation)
- ✅ bug-detector.md rewritten (language-aware)
- ✅ agent-workflow.mdc rule updated (conditional analyze)
