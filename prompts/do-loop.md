# Do Loop

Execute `/cortex/do` repeatedly via subagents until the roadmap is complete or the iteration
limit is reached. Each subagent runs one full `/cortex/do` pass (Selection → Implementation →
Review Gate → Finalize → Verify → Fix → Cleanup). After each pass the orchestrator checks the
roadmap; if steps remain it spawns a fresh subagent for the next step.

**Maximum iterations**: 5. After 5 passes the loop stops and reports remaining work.

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
   - `max_iterations = 5`
   - `roadmap_complete = false`

---

## Iteration Loop (repeat until `roadmap_complete` or `iteration == max_iterations`)

### Step 1 — Increment and log

Increment `iteration`. Print:

```text
## Iteration <N> / 5
```

### Step 2 — Spawn subagent

Spawn a subagent and instruct it to execute the full `/cortex/do` workflow **inline**:

> "Execute the full `/cortex/do` workflow now. Load and follow `.cortex/synapse/prompts/do.md`
> exactly — run all phases in order: Selection, Implementation (inner loop), Review Gate,
> Finalize, Verify, Fix, Cleanup. Do not stop early. When complete, output the standard
> Pipeline report."

The subagent must:

- Run Selection inline (not delegate it)
- Spawn `@implement-code` for Implementation (inner loop), as specified in `do.md`
- Run Review Gate, Finalize, Verify, Fix, Cleanup inline

Wait for the subagent to return before continuing.

### Step 3 — Check roadmap

After the subagent returns, read `.cortex/memory-bank/roadmap.md` directly.

Count pending steps:

- Any line starting with `- PENDING:` under Blockers, Active Work, or Pending plans sections
- Any `status: PENDING` or `status: IN_PROGRESS` in referenced plan files (optional cross-check)

If **zero pending steps remain**:

- Set `roadmap_complete = true`
- Break the loop

If **pending steps remain** and `iteration < max_iterations`:

- Continue to next iteration

If `iteration == max_iterations` and roadmap is not complete:

- Set stop reason to `iteration_limit_reached`
- Break the loop

### Step 4 — Subagent failure guard

If the subagent returned a failure or the roadmap was unchanged after the iteration
(same PENDING entries as before the subagent ran):

- Increment a `stall_count`
- If `stall_count >= 2` (two consecutive stalls): break the loop with stop reason `stalled`
- Otherwise continue

---

## Final Report

```markdown
## Do Loop Result

**Status**: Roadmap complete ✅ / Iteration limit reached ⚠️ / Stalled ⚠️ / MCP unhealthy ❌

**Iterations run**: <N> / 5

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
