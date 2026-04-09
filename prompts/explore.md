# Explore

**Internal prompt — invoked automatically by the agent, not by the user.**

## When to invoke

Run this before `/cortex/plan` whenever the task meets any of these conditions:

- Multiple valid architectures or approaches exist with non-obvious trade-offs
- The task is novel (no prior roadmap entry or plan for this area)
- The request is ambiguous about scope, tech choice, or design direction
- Complexity or risk level is unclear

Skip explore and go directly to `/cortex/plan` when the approach is already obvious and agreed upon.

## Goal

Explore options without creating a formal plan or roadmap entry. Produce an ephemeral explore decision log under `.cortex/plans/explore/`, then hand selected direction to `/cortex/plan` once user confirms.

## Workflow

1. Call `session(operation="start")` for orientation.
2. Read `cortex://context`.
3. Read `cortex://rules`.
4. Use `think()` to generate 2-5 distinct approaches for the user topic.
5. Build an `ExploreSession` shape with `ExploreOption` entries:
   - title, description, pros, cons, complexity, risk
6. Write `decision-log-<slug>.md` to `.cortex/plans/explore/`.
7. Present options with one recommendation and explicit trade-offs.
8. If user selects an option:
   - record the decision in the same explore log
   - pass the selected option into `/cortex/plan` context (use `explore_log_path`)

## Guardrails

- Do not create `.cortex/plans/*.md` formal plan files from this command.
- Do not register roadmap entries from this command.
- Keep logs ephemeral and scoped to exploration only.

## Explore Log Template

```markdown
# Explore: <topic>

## Created

<ISO timestamp>

## Options

### 1) <option title>

- Description: <text>
- Pros: <bullet list>
- Cons: <bullet list>
- Complexity: low|medium|high
- Risk: low|medium|high

## Recommendation

<recommended option and rationale>

## Selected Option

<filled only after user chooses; include why>
```
