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
Do NOT spawn the next subagent until Steps A → B → C → D below have all completed for the
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
> Finalize, Verify, Fix, Cleanup. Do not stop early. When complete, output the standard
> Pipeline report."

**STOP HERE. Do not proceed to C until this subagent has returned.**
No other work happens while the subagent runs.

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
- Always list remaining roadmap entries even when the iteration limit was reached
