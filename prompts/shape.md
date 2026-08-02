# Shape

**Internal prompt — invoked automatically by the agent, not by the user.**

## When to invoke

Run this before `/cortex/plan` whenever the task meets any of these conditions:

- The requirements are unknown or under-specified, and only the user can resolve them
- Success conditions, edge cases, or acceptance boundaries are not written down anywhere
- The request names a desired outcome but not the constraints that bound it
- A plan written now would encode guesses about what the user actually wants

Skip shape and go directly to `/cortex/plan` when the requirements are already explicit, or when a shaping record for this topic already exists under `.cortex/plans/shape/`.

**Shape is not explore.** Shape resolves *unknown requirements* by interviewing the user. Explore compares *known approaches* the agent generates. Both may apply; run shape first so exploration is bounded by resolved constraints.

## Goal

Resolve the decision tree for a request without creating a formal plan or roadmap entry. Produce a shaping record under `.cortex/plans/shape/`, then hand its resolved decisions to `/cortex/plan` as fixed constraints via `shape_log_path`.

## Workflow

1. Call `session(operation="start")` for orientation.
2. Read `cortex://context`.
3. Read `cortex://rules`.
4. Enumerate the decisions that would materially change the resulting plan's scope, approach, or success criteria.
5. Run the **Interview Loop** below until the **Termination Condition** is met.
6. Write `shape-<slug>.md` to `.cortex/plans/shape/` using the **Shaping Record Template**.
7. Hand off to `/cortex/plan` with `shape_log_path` set to the record.

## Interview Loop

Each iteration performs exactly these four mechanics, in order:

1. **One question per turn.** Identify the single highest-leverage unresolved decision and address only that one. Never present a numbered list of questions or a questionnaire. This is a hard gate, not a preference.
2. **Codebase-first resolution.** Before asking, attempt to resolve the decision by reading the repository — code, tests, rules, prior plans, memory bank. If the answer is discoverable, record it with `source: codebase` and move to the next decision without spending a user turn.
3. **Propose a recommended answer.** When a question must be asked, state the agent's own recommended answer and its rationale so the user can confirm rather than compose. Ask the question in a form that a one-word confirmation can resolve.
4. **Record the answer.** Append the decision, the resolved answer, and its source to the record before starting the next iteration.

## Termination Condition

The loop terminates when this binary check passes:

> No remaining unresolved decision would change the plan's **scope**, **approach**, or **success criteria**.

Decisions that survive the check but remain unresolved are not questions — record them under **Assumptions** (with the assumed value) or **Open Risks**. Do not continue the loop to resolve cosmetic or implementation-detail choices.

## Guardrails

- Do not create `.cortex/plans/*.md` formal plan files from this command.
- Do not register roadmap entries from this command.
- Do not write or edit source files; shaping is read-only apart from the shaping record.
- Keep records ephemeral and scoped to one topic.
- Never ask a question whose answer is already in the codebase, the memory bank, or an earlier answer in this session.

## Shaping Record Template

```markdown
# Shape: <topic>

## Created

<ISO timestamp>

## Resolved Decisions

- Decision: <the decision that had to be made>
  - Answer: <the resolved value>
  - Source: user | codebase

## Assumptions

- <assumed value, and what would invalidate it>

## Explicitly Out of Scope

- <thing deliberately excluded, and why>

## Open Risks

- <unresolved risk that does not block planning>
```

## Handoff

Pass the record path into plan creation:

```text
plan(operation="create", title="...", content="...", shape_log_path=".cortex/plans/shape/shape-<slug>.md")
```

`plan()` prepends a `## Shaping Constraints` section built from **Resolved Decisions**, **Assumptions**, and **Explicitly Out of Scope**. Downstream planning treats those decisions as fixed — it must not re-derive or override them. A record without a **Resolved Decisions** section contributes nothing and is ignored.
