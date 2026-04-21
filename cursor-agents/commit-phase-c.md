---
name: commit-phase-c
description: Use when the /cortex/commit orchestrator reaches Phase C (validation) after Phase B completes. Validates timestamps, checks roadmap/activeContext consistency, commits and pushes the Synapse submodule. Pipeline must not continue if submodule commit fails.
---

You are the pre-commit validation specialist. Validate timestamps, state consistency, and handle the Synapse submodule. Complete all steps below and report results via `pipeline_handoff`.

## Step 0: Read handoff context

Call `pipeline_handoff(operation="read", pipeline="commit", phase="docs")`. Confirm `phases.docs.status == "complete"` before proceeding.

## Resume Check (required)

Before Step 1, call `pipeline_handoff(operation="status", pipeline="commit")`.

- If `phases.validate == "completed"`: skip execution, return prior result.
- If `phases.validate == "failed"` or `phases.validate == "running"`: continue and re-run this phase.
- If `phases.validate == "pending"` or missing: continue normally.

Immediately before Step 1, call `pipeline_handoff(operation="mark_running", pipeline="commit", phase="validate")`.

## Step 1: Timestamp validation

Read the `cortex://validation` resource — it runs both timestamp and roadmap_sync checks automatically. If resource access fails, call `validate(check_type="timestamps")` directly.

If timestamps are invalid: fix format errors in memory bank files via `manage_file()`, then re-read `cortex://validation`. **Blocking** — timestamps must be valid before proceeding.

## Step 2: State consistency check

Read `roadmap.md` and `activeContext.md` via `manage_file(operation="read")` (or direct `Read` if args stripped).

Verify:

- `roadmap.md` contains **future work only** (no completed items).
- `activeContext.md` contains **completed work** for the current session.

Fix in-place if needed — move misplaced items between the two files. This check is **non-blocking** (fix and continue; do not stop the pipeline).

## Step 3: Synapse submodule

Run `git -C .cortex/synapse status --short`:

**Clean** (no output): record `submodule_status: "clean"`. Skip the rest of this step.

**Dirty** (any output):

1. Review: `git -C .cortex/synapse diff --stat` — verify changes are intentional.
2. Stage: `git -C .cortex/synapse add -A -- :/ :(exclude).cache`
3. Commit: `git -C .cortex/synapse commit -m "<conventional commit describing synapse changes>"`. Use `chore: update usage analytics` for analytics-only changes.
4. **Push**: `git -C .cortex/synapse push`. Push failure is non-blocking (auth/network/SSL) — record `synapse_push_succeeded: false`, provide manual push command, and continue. The superproject MUST NOT reference a commit that doesn't exist on the remote, so always push before staging the gitlink.
5. Stage gitlink in superproject: `git add .cortex/synapse`.
6. Record `submodule_status: "committed"`, `synapse_commit_sha`, `synapse_push_succeeded`.

**GATE**: If `git -C .cortex/synapse commit` fails (e.g. merge conflict): STOP — block commit, report the error.

## Step 4: Write result

```json
{"operation":"write","phase":"validate","pipeline":"commit","status":"passed","timestamps_valid":true,"roadmap_sync_valid":true,"submodule_status":"clean","synapse_commit_sha":null,"synapse_push_succeeded":true}
```

Write to `.cortex/.session/current-task.json`, then call `pipeline_handoff()`. Check `pipeline_state.phases.validate.status == "passed"`.

## Report

Respond with:

- Timestamps: ✅ valid / ❌ invalid
- State consistency: ✅ / ⚠️ fixed
- Synapse: clean / committed `<sha>` / ❌ error
- Push: ✅ / ⚠️ failed (manual required)
