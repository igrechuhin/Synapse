---
name: commit-phase-c
description: Use when the /cortex/commit orchestrator reaches Phase C (validation) after Phase B completes. Validates timestamps, checks roadmap/activeContext consistency, commits and pushes the Synapse submodule. Pipeline must not continue if submodule commit fails.
tools: mcp__cortex__*, Bash, Read, Edit, Grep
---

Validate timestamps, state consistency, and Synapse submodule; write result.

## Resume Check (required)

Before Step 1, call `pipeline_handoff(operation="status", pipeline="commit")`.

- If `phases.validate == "completed"`: skip execution, return prior result.
- If `phases.validate == "failed"` or `phases.validate == "running"`: continue and re-run this phase.
- If `phases.validate == "pending"` or missing: continue normally.

Immediately before Step 1, call `pipeline_handoff(operation="mark_running", pipeline="commit", phase="validate")`.

1. **Timestamps**: read `cortex://validation` resource. If `timestamps_result.valid == false`, fix format errors in memory bank files via `manage_file()`, retry. Blocking.
2. **State consistency** (non-blocking): verify `roadmap.md` has future work only; `activeContext.md` has completed work. Fix in-place if misplaced.
3. **Synapse submodule**: run `git -C .cortex/synapse status --short`.
   - Clean → `submodule_status:"clean"`.
   - Dirty → stage (`git -C .cortex/synapse add -A -- :/ :(exclude).cache`), commit (`git -C .cortex/synapse commit -m "<msg>"`). GATE: commit failure is blocking. Push (`git -C .cortex/synapse push`) — push failure is non-blocking, set `synapse_push_succeeded:false`. Stage gitlink: `git add .cortex/synapse`.
4. **Write result** to `.cortex/.session/current-task.json` then call `pipeline_handoff()`:

```json
{"operation":"write","phase":"validate","pipeline":"commit","status":"passed","timestamps_valid":true,"roadmap_sync_valid":true,"submodule_status":"clean","synapse_commit_sha":null,"synapse_push_succeeded":true}
```

Report: Timestamps ✅/❌ · Consistency ✅/⚠️ · Synapse clean/committed `<sha>` · Push ✅/⚠️
