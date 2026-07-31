# Do Loop

Execute `/cortex/do` repeatedly via subagents until the roadmap is complete or the iteration
limit is reached. Each subagent runs one full `/cortex/do` pass (Selection → Implementation →
Review Gate → Finalize → Verify → Fix → Cleanup). After each pass the orchestrator checks the
roadmap; if steps remain it spawns a fresh subagent for the next step.

**Maximum iterations**: 10. After 10 passes the loop stops and reports remaining work.

---

## Cursor Arg-Stripping Protocol

Same as `do.md`: embed `operation`, `phase`, and `pipeline` inside the data JSON. Call
`pipeline_handoff()` with no args. Read `.cortex/memory-bank/roadmap.md` directly when
`manage_file` arg-stripping would return the wrong file.

---

## Loop Initialization

1. Call `session()` to verify MCP health. If unhealthy, STOP immediately and report.
2. Read `.cortex/memory-bank/roadmap.md` directly.
3. Scan for any PENDING or in-progress steps (Blockers, Active Work, Pending plans sections).
   - If **no pending steps** exist at start, report "Roadmap already complete" and STOP.
4. Initialize loop state:
   - `iteration = 0`
   - `max_iterations = 10`
   - `roadmap_complete = false`

---

## Iteration Loop

**CRITICAL — strictly sequential, one subagent at a time.**
Do NOT spawn the next subagent until Steps A → B → B2 → C → D below have all completed for the
current iteration. Never spawn two subagents concurrently.

---

### A. Start iteration

Increment `iteration`. Print: `## Iteration <N> / 10`

Record the current PENDING entries from roadmap.md as `pending_before` (used in D).

---

### B. Spawn subagent — BLOCKING

Spawn **one** subagent with this instruction:

> "Execute the full `/cortex/do` workflow now. Load and follow `.cortex/synapse/prompts/do.md`
> exactly — run all phases in order: Selection, Implementation (inner loop), Review Gate,
> Finalize, Verify, Fix, Cleanup. Do not stop early. Passing tests are NOT the completion
> signal — the pass is only done once Finalize has run. When complete, output the standard
> Pipeline report, including the Finalize row (plan archived / updated / kept open)."

**STOP HERE. Do not proceed to C until this subagent has returned.**
No other work happens while the subagent runs.

---

### B2. Finalize checkpoint — BLOCKING

Never evaluate the exit condition on a plan whose Finalize phase was skipped: a plan whose code
and tests landed but whose bookkeeping did not will still look PENDING in C, so the loop
re-selects it and burns an iteration redoing finished work.

Read `pipeline_handoff(operation="read", pipeline="implement")` for the pass that just returned.

- If `phases.code.step_fully_complete == true` and `phases.review.review_outcome == "no_gaps"`,
  the plan MUST be fully finalized: roadmap entry removed, `progress.md` entry appended for
  today, and the plan file moved to `.cortex/plans/archive/`. Verify all three by reading
  `.cortex/memory-bank/roadmap.md`, `.cortex/memory-bank/progress.md`, and listing
  `.cortex/plans/archive/`.
- If any of the three is missing, perform Finalize inline now via
  `plan(operation="complete", plan_title=…, summary=…, plan_file_name=…, progress_entry=…,
  completion_date=…)` — that one call does all three atomically. Record `finalize_repaired`
  for this iteration and surface it in the per-iteration summary.
- If the pass ended partial or `review_outcome == "gaps_found"`, the roadmap entry is expected
  to remain; verify instead that the plan file carries a `## Partial Progress Log` (and, for
  gaps, a `## Review Follow-Up Gaps` section) so the next iteration does not repeat the work.
  Repair inline if absent.

---

### C. Check roadmap

The subagent has returned. Now read `.cortex/memory-bank/roadmap.md` directly.

Count remaining pending steps (lines starting with `- PENDING:` under Blockers, Active Work,
or Pending plans sections). Record as `pending_after`.

- If `pending_after == 0`: set `roadmap_complete = true` → **exit loop**
- If `iteration == max_iterations`: set stop reason `iteration_limit_reached` → **exit loop**

---

### D. Stall guard

Compare `pending_after` to `pending_before`.

- If identical (roadmap did not change) or subagent reported failure with no files changed:
  increment `stall_count`.
  - If `stall_count >= 2`: set stop reason `stalled` → **exit loop**
- Otherwise: reset `stall_count = 0`

---

Proceed to next iteration (back to A).

---

## Final Report

```markdown
## Do Loop Result

**Status**: Roadmap complete ✅ / Iteration limit reached ⚠️ / Stalled ⚠️ / MCP unhealthy ❌

**Iterations run**: <N> / 10

### Per-Iteration Summary

| # | Step implemented | Outcome |
|---|-----------------|---------|
| 1 | <step title> | ✅ complete / ⚠️ partial / ❌ failed |
| … | … | … |

### Remaining work

<List remaining PENDING roadmap entries, or "None — roadmap complete">

### Next

<action items OR "Roadmap is fully complete — nothing left to do">
```

**Rules**:

- Use ✅ when the step was completed and the roadmap entry was removed
- Use ⚠️ for partial progress (roadmap entry remains, partial log appended)
- Use ❌ when the subagent reported failure with no files changed
- Append " (finalize repaired)" to the outcome cell when B2 had to finalize the plan inline —
  a recurring repair means the `/cortex/do` Finalize phase is being skipped and needs fixing
  at the source, not just patching each iteration
- Always list remaining roadmap entries even when the iteration limit was reached
