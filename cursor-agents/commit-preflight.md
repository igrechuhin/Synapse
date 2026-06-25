---
name: commit-preflight
description: Use when the /cortex/commit orchestrator starts and needs to run Preflight. Verifies MCP health, loads rules, confirms staged changes exist, pre-stages the Synapse submodule, and creates a rollback snapshot. Invoke as the first phase of the commit pipeline before Phase A.
tools: mcp__cortex__*, Bash, Read, Edit, Grep
---

Run all steps; write result; report summary.

## Resume Check (required)

Before Step 1, call `pipeline_handoff(operation="status", pipeline="commit")`.

- If `phases.preflight == "completed"`: skip execution, return prior result.
- If `phases.preflight == "failed"` or `phases.preflight == "running"`: continue and re-run this phase.
- If `phases.preflight == "pending"` or missing: continue normally.

Immediately before Step 1, call `pipeline_handoff(operation="mark_running", pipeline="commit", phase="preflight")`.

1. **MCP health**: call `session()`. If unhealthy, STOP with `status:"error", error:"MCP unhealthy"`.
2. **Changes**: run `git status --short`. If empty, STOP with `status:"error", error:"no changes to commit"`.
3. **Synapse pre-stage**: run `git -C .cortex/synapse status --porcelain -- :/ :(exclude).cache`. If dirty: `git -C .cortex/synapse add -A -- :/ :(exclude).cache && git -C .cortex/synapse commit -m "chore: update usage analytics"` then `git add .cortex/synapse`.
4. **Snapshot**: run `git stash create`. If hash returned, run `git stash store -m "cortex-commit-pipeline-snapshot" <hash>`, set `snapshot_ref=<hash>`. If empty or "beyond a symbolic link" error, set `snapshot_ref="HEAD"`.
5. **Write result** to `.cortex/.session/current-task.json` then call `pipeline_handoff()`:

```json
{"operation":"write","phase":"preflight","pipeline":"commit","status":"complete","snapshot_ref":"<value>","rules_loaded":true,"changes_detected":true}
```

Report: MCP ✅/❌ · Changes ✅/❌ · Snapshot `<ref>` · Synapse clean/committed
