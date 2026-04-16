# Plan

**PURPOSE**: Create a plan document and register it in the roadmap. **NO CODE CHANGES.** This prompt produces a `.md` plan file only.

**CRITICAL**: Execute ALL steps below AUTOMATICALLY. Do NOT pause, summarize, or ask for confirmation unless clarification is genuinely needed. Start with Step 1 immediately.

**HARD GATE — VIOLATION IF BROKEN**: This prompt ONLY creates a plan file. It does NOT implement features, fix bugs, edit source files, or run quality checks. ALL additional context (error logs, code snippets, file references) is INPUT for plan creation — analyze it to write better implementation steps, DO NOT execute those steps. If you find yourself editing `.py`, `.ts`, or other source files: STOP immediately — you are in the wrong prompt.

**FINITE-TASK GATE — VIOLATION IF BROKEN**: Every plan MUST represent exactly one finite, completable task with a clear done condition. Do NOT create or keep open-ended backlog plans (for example, "continue until all remaining ..."). If incoming scope is broad, split it into multiple finite plans and create/register only the first concrete slice.

## Clean Semantics

For `/cortex/plan`, **clean** means **planning-complete and registration-clean**:

- Plan file is created/enriched with required sections.
- Roadmap registration is complete and consistent.
- No source-code implementation changes are made as part of this workflow.

Git-clean working tree is not required; this prompt is clean when planning artifacts are correct and synchronized.

## START HERE — Execute These Tool Calls Now

**Step 1**: Call `session()` to verify MCP health. If unhealthy, STOP.

**Step 2**: Call `manage_file()` (zero-arg reads activeContext.md for orientation). Then read the roadmap: `manage_file(file_name="roadmap.md", operation="read")`. If Cursor strips args and returns activeContext instead, use `Glob` on `.cortex/memory-bank/roadmap.md` and `Read` it directly.

**Step 3**: Read the `cortex://rules` resource for coding standards (zero-arg, reads task from session config). Non-blocking if unavailable.

After Step 3, continue to Step 4 below before plan creation.

Plans directory: `.cortex/plans/`. Use `Glob` on `.cortex/plans/*.md` for listing.

## Planning depth (fast-forward vs step-by-step)

Before creating a plan in Step 7, choose how much to generate in one pass:

- **Default (no flag)**: call `plan(operation="create", ...)` with `planning_mode="ff"` or omit `planning_mode` — all sections are written in one shot (fast-forward).
- **Explicit `--step` in the user message**: set `planning_mode="step"` on `plan(operation="create", ...)`. Only the Goal section is written to `draft-<slug>.md`; the user reviews before you call `continue_step`, then `approve_step` for each section, and `finalize_step` when every section is approved or skipped.
- **Heuristic**: if the topic mentions architecture, redesign, migration, or security (case-insensitive), suggest step-by-step in your narrative and use `planning_mode="step"` unless the user insists on fast-forward.

**Resuming step-by-step**: read the draft path from the prior tool result, then use `plan(operation="continue_step" | "approve_step" | "finalize_step", ...)` as documented in the plan tool. To inspect or remove abandoned drafts, use `manage_file(operation="list_drafts")` and `manage_file(operation="discard_draft", content='{"plan_slug": "<stem>"}')`.

---

## Step 4: Explore Gate

Before creating any plan, decide whether an explore phase is needed.

**Run `/cortex/explore` first if ANY of these are true:**

- Multiple valid approaches exist with non-obvious trade-offs (e.g. different architectures, libraries, or design patterns)
- The task is novel — no prior plan or roadmap entry covers this area
- The request is ambiguous about scope, tech choice, or design direction
- Complexity or risk is unclear and requires deliberation

**Skip explore and proceed directly to Step 5 if ALL of these are true:**

- The approach is already agreed upon or obvious from context
- A prior explore log exists for this topic (check `.cortex/plans/explore/`)
- The request is a straightforward addition to an existing plan

If explore is needed: run `/cortex/explore`, wait for the user to select an option, then return here with `explore_log_path` set to the generated log. Pass `explore_log_path` to `plan(operation="create")` in Step 7.

---

## Step 5: Plan Creation — @plan-creator subagent

Use @plan-creator to handle Steps 5–9. If the subagent is unavailable, run inline:

### Check for Existing Related Plans

1. List existing plans: use `Glob` on `.cortex/plans/*.md` (excluding archive/).
2. For each existing plan with YAML frontmatter, compute similarity score:
   - Same `component` value: +2
   - Same `work_type` value: +1
   - Title keyword overlap (>50% shared words): +1
3. **Decision**:
   - Score >= 3: **enrich** the existing plan (do not create a duplicate)
   - Score 1-2: ask user whether to enrich or create new
   - Score 0: create new plan
4. Check if roadmap references a Phase with status PLANNED but no corresponding plan file — if so, create the plan file now.

## Step 6: Analyze All Provided Context

1. Parse the user's plan description/request.
2. Analyze ALL attached files, code selections, error logs as INPUT for the plan.
3. Extract requirements, constraints, dependencies, success criteria.
4. If clarification is needed, ask the user specific questions before proceeding.

Use `think` tool for complex plans to scope the approach.

## Step 7: Create or Enrich the Plan

**If creating new**: Prefer `plan(operation="create", title="...", content="...")`.

Before writing the plan body, enforce finite scope:

1. Reject open-ended titles and goals (`continue`, `remaining`, `backlog`, `ongoing`, `as needed`, `until done`).
2. Rewrite scope into one concrete deliverable with measurable completion criteria.
3. Include explicit boundaries (`in_scope`, `out_of_scope`) so completion is binary.
4. If the request contains multiple deliverables, split into separate plans; register each independently.

**FALLBACK — VIOLATION IF ANY SECTION IS OMITTED**: If `plan(operation="create")` fails (Cursor may strip args), write the plan file using `Write` to `.cortex/plans/{slug}.md`. The file MUST contain ALL of the following sections in this exact order — omitting any section is a schema violation and the plan is invalid:

```text
---
title: "<title>"
component: "<component>"
work_type: "fix | refactor | feature | optimize | docs | infrastructure"
status: "PENDING"
priority: "Critical | High | Medium | Low"
created: "<YYYY-MM-DD>"
depends_on: []
---

## Goal
## Context
## Scope
  **in_scope** — bullet list
  **out_of_scope** — bullet list
## Approach
## Implementation Steps
## Verification Checklist
## Dependencies
## Success Criteria
## Testing Strategy
## Risks and Mitigation
```

**Required sections — mandatory, no exceptions:**

| Section | Content |
|---------|---------|
| YAML frontmatter | title, component, work_type, status: PENDING, priority, created, depends_on |
| Goal | Single clear statement of what this plan achieves |
| Context | Why needed, what triggered this, business/technical requirements |
| Scope | `**in_scope**` and `**out_of_scope**` bullet lists — guarantees binary completion |
| Approach | High-level implementation strategy (1–3 paragraphs) |
| Implementation Steps | Numbered, ordered — define the implementation sequence; execute them in order via `/cortex/do` |
| Verification Checklist | Per-step: what to search for, search scope, files to re-read after changes |
| Dependencies | Other plans or external work this depends on |
| Success Criteria | Measurable, binary outcomes |
| Testing Strategy | 95% coverage target, unit/integration/negative cases, AAA pattern |
| Risks and Mitigation | Table of risks with mitigations |

**After writing, self-verify**: Read the file back and confirm every section header above is present. If any is missing, rewrite the file before proceeding. Do NOT report success until this check passes.

**Non-schema sections are forbidden**: Do NOT add sections beyond the 10 listed above (e.g. "Change History", "Notes", "Appendix", "Open Questions"). Extra sections cause schema drift and must be removed before reporting success.

When planning implementation work, note that agents should use `# AI:` comments for non-obvious decisions (why, not what) on their own line above the affected code.

**If enriching existing**: Read the existing plan, merge new requirements, update steps and priorities. Write back using `Write` or `Edit`.

## Step 8: Register Plan in Roadmap

Registering the plan in the roadmap is **REQUIRED** — every new or enriched plan MUST be registered.

Call `plan(operation="register", plan_title="...", description="...", plan_relative_path=".cortex/plans/<filename>.md", status="PENDING", section="...")`.

`plan_relative_path` is REQUIRED for new or enriched plan registrations. Use the canonical `.cortex/plans/<filename>.md` path from the created or updated plan file.

Fallback when MCP arguments are stripped: append `Plan: .cortex/plans/<filename>.md` to `description` (same canonical path; include final punctuation to match roadmap parsing expectations).

**GATE**: If `plan(operation="register")` fails, STOP and report. **PROHIBITED**: using StrReplace, direct Write, string-replace, or direct file-write tools on roadmap.md — this causes corruption and is a VIOLATION. Use MCP tools only.

Fallback for enriched plans: call `update_memory_bank(operation="roadmap_add", section="...", entry_text="...")`. **`manage_file(write)` must not be used for roadmap.md** — it bypasses structured mutation and risks corruption. `manage_file(write)` is for arbitrary wiki pages only (techContext.md, systemPatterns.md, etc.).

If fallback write of roadmap content is ever required, pass **full, unabridged, complete** content only. **Never truncate** and never pass **shortened** or **summarized** roadmap content.

Before any fallback write, run a **pre-write content length** check: the outgoing content must be **at least as long** as the content read from roadmap.md (or **as long as** the original when no intended additions were made). If this check fails, STOP and restore full content before continuing.

## Step 9: Verify Completion

1. Verify plan file exists in plans directory: `Read` the file and re-read to confirm.
2. Verify roadmap was updated: read `.cortex/memory-bank/roadmap.md` and confirm the entry is present.
3. Report: plan file path, plan title, roadmap update status.

---

## Path Resolution

Plans: `.cortex/plans/`. Memory bank: `.cortex/memory-bank/`. Use `manage_file()` for memory bank reads/writes, `Read`/`Write` for plan files.

## Error Handling

- **MCP tool crash/disconnect**: STOP, report with FIX-ASAP priority
- **3 consecutive MCP failures**: Circuit-breaker per `shared-conventions.md`
- **Plan file creation errors**: Check permissions, directory existence
- **Roadmap update errors**: Check format, report specific error

## Step 10: Post-Prompt Hook (Self-Improvement)

After writing the final report for this plan-creation run, invoke the post-prompt self-improvement hook:

- Read `.cortex/synapse/prompts/post-prompt-hook.md` and execute it to analyze the session and emit any applicable Skills, Plans, or Rules.
- Treat this hook as **non-blocking**: if it fails or is unavailable (for example, MCP connection issues), record a brief note in the final report `## Next` section and consider the planning workflow complete.

## Final report (required format)

**MANDATORY**: Use the **Artifact** report type from `docs/guides/synapse-final-report-templates.md`.

```markdown
## Result

✅ Plan created: <filename>.md

## Output

| Field | Value |
|-------|-------|
| Path | `.cortex/plans/<filename>.md` |
| Roadmap | Added to "<section>" |
| Status | PENDING |

## Next

`/cortex/do @.cortex/plans/<filename>.md`
```

**Rules**:

- Roadmap field: section name where registered, or "Not registered" if skipped
- Next: always include do command for new plans

## Success Criteria

- Plan file created with ALL required sections: YAML frontmatter, Goal, Context, Scope (in_scope + out_of_scope), Approach, Implementation Steps, Verification Checklist, Dependencies, Success Criteria, Testing Strategy (95% target), Risks and Mitigation
- Self-verify read-back passed — all 10 section headers confirmed present before reporting success
- Plan registered in roadmap
- All paths obtained dynamically via MCP tools
