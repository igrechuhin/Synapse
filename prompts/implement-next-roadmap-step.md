# Implement Next Roadmap Step

**CRITICAL**: Execute ALL phases below AUTOMATICALLY. Do NOT pause, summarize, or ask for confirmation between phases. Start with Selection immediately. When a roadmap item is too large to finish in one session, make concrete, high-impact partial progress and update plans/status accordingly instead of stopping with no changes.

This is part of the **compound-engineering loop** (Plan → Work → Review → Compound). The Finalize phase is the Compound step.

## Sequential Execution Order

Each phase must complete before the next begins:

1. **Selection** → 2. **Implementation** → 3. **Finalize** → 4. **Verify**

---

## Selection — use the `implement-select` subagent

Use the `implement-select` subagent to read the roadmap, identify the next pending step by priority (Blockers first, then Active Work, then Pending plans), load implementation context and rules, and read the plan file if one exists.

**GATE**: Must return `status: "complete"` before proceeding. If `status: "roadmap_complete"`: report "Roadmap complete" and STOP.

---

## Implementation — use the `implement-code` subagent

Use the `implement-code` subagent to scope the smallest meaningful subtask, implement it with tests, and run the quality gate via the job-based API (start + poll). The subagent uses `start_pre_commit_job(phase="A")` and polls `get_pre_commit_job_status` so each MCP call is short-lived.

Pass to the subagent:

- Selected step title and description (from Selection)
- Plan file contents (from Selection)
- Rules loaded (from Selection)

**GATE**: Must return `quality gate: passed` before proceeding to Finalize.

---

## Finalize — use the `implement-finalize` subagent

Use the `implement-finalize` subagent to update the memory bank (activeContext.md, progress.md, roadmap.md) and handle the plan file (archive if complete, mark IN_PROGRESS if partial).

Pass to the subagent:

- Step fully complete: yes | no (from Implementation)
- Subtask description, files changed, coverage (from Implementation)
- Plan file path and selected step title (from Selection)

**GATE**: Must return `status: "complete"` before proceeding to Verify.

---

## Verify — use the `implement-verify` subagent

Use the `implement-verify` subagent to confirm the roadmap and progress entries are correct and no stray COMPLETE plans remain in the plans root. Read-only.

**GATE**: Must return `status: "passed"`. If stray COMPLETE plans are reported: archive them before declaring the pipeline complete.

---

## Error Handling

- **Selection fails (MCP unhealthy)**: STOP immediately
- **Selection returns roadmap_complete**: Report "Roadmap complete" and STOP
- **Quality gate fails after 3 iterations**: STOP, report unresolvable issues
- **Finalize fails (memory bank crash)**: STOP, report with FIX-ASAP priority
- **Quality gate unavailable (doc-only sessions)**: Record "Quality gate skipped — doc-only session" and proceed to Finalize

## Success Criteria

- Implementation complete and all tests pass
- Quality gate passed (zero lint, file-size, function-length, type_check violations)
- Coverage >= 90% global, >= 95% for new/modified code
- Memory bank updated (roadmap entry removed or retained correctly, progress added, activeContext updated)
- Completed plans archived; partial plans marked IN_PROGRESS
