/**
 * Cortex commit pipeline — Claude Code Workflow script
 *
 * Replaces commit.md LLM-orchestrated pipeline with deterministic JS control flow.
 *
 * Key improvements over prose instructions:
 *   - Phase A retry loop: while (iterations < MAX_PHASE_A_ITERATIONS) — cannot over/under-run
 *   - Step 12 scope routing: if/else branches (source vs markdown_only vs none) — no mis-routing
 *   - resumeFromRunId: crashed mid-Phase B resumes from failed phase, not Preflight
 *   - Structured subagent returns via schema: typed objects, no string parsing in JS control flow
 *
 * Subagents used (unchanged from commit.md):
 *   @commit-preflight, @commit-phase-a, @commit-phase-b, @commit-phase-c, @commit-final-gate
 */

export const meta = {
  name: "cortex-commit",
  description:
    "Cortex commit pipeline: preflight → A (retry ≤3) → wiki-ingest → B → C → gate → commit → push → cleanup",
  phases: [
    {
      title: "Preflight",
      detail: "MCP health, git status, stash snapshot, synapse pre-stage"
    },
    {
      title: "Phase A",
      detail: "quality gate + autofix retry loop (max 3 iterations)"
    },
    {
      title: "Wiki Ingest",
      detail: "staged docs ingest (inline, runs after Phase A passes)"
    },
    {
      title: "Phase B",
      detail: "docs sync: activeContext, progress, roadmap, archive plans"
    },
    {
      title: "Phase C",
      detail: "validate timestamps + roadmap_sync, synapse submodule commit/push"
    },
    {
      title: "Final Gate",
      detail: "Step 12: scope-routed final quality gate"
    },
    {
      title: "Commit",
      detail: "Step 13: selective git add + content-descriptive git commit"
    },
    {
      title: "Push",
      detail: "Step 14: git push superproject (non-blocking on failure)"
    },
    {
      title: "Cleanup",
      detail: "Step 15: clear commit pipeline state"
    },
    {
      title: "Post-Prompt Hook",
      detail: "Step 16: self-improvement hook (non-blocking)"
    }
  ]
};

// AI: JSON Schema objects for structured subagent returns — loose schemas with
// additionalProperties: true allow current free-text phase outputs while providing
// typed access to the key fields the orchestrator branches on. Tighten after smoke-testing.
const PREFLIGHT_SCHEMA = {
  type: "object",
  properties: {
    passed: { type: "boolean" },
    snapshot_ref: { type: "string" },
    staged_count: { type: "integer" },
    error: { type: "string" },
    changes_detected: { type: "boolean" }
  },
  required: ["passed"],
  additionalProperties: true
};

const PHASE_A_SCHEMA = {
  type: "object",
  properties: {
    passed: { type: "boolean" },
    coverage: { type: ["number", "null"] },
    autofix_ran: { type: "boolean" },
    // AI: scope is derived from what Phase A wrote/modified; commit-phase-a subagent
    // determines this from git diff --name-only and reports it here for Step 12 routing.
    scope: {
      type: "string",
      enum: ["source", "markdown_only", "none", "unknown"]
    },
    fix_iterations: { type: "integer" },
    error: { type: "string" }
  },
  required: ["passed"],
  additionalProperties: true
};

const PHASE_B_SCHEMA = {
  type: "object",
  properties: {
    docs_phase_passed: { type: "boolean" },
    memory_bank_updated: { type: "boolean" },
    plans_archived: { type: "integer" },
    // AI: roadmap_sync_warning=true means roadmap_sync failed but timestamps passed —
    // this is non-blocking per commit.md Phase B spec (roadmap_sync-only failure).
    roadmap_sync_warning: { type: "boolean" },
    error: { type: "string" }
  },
  required: ["docs_phase_passed"],
  additionalProperties: true
};

const PHASE_C_SCHEMA = {
  type: "object",
  properties: {
    timestamps_valid: { type: "boolean" },
    roadmap_sync_valid: { type: "boolean" },
    submodule_status: {
      type: "string",
      enum: ["clean", "committed", "skipped"]
    },
    synapse_commit_sha: { type: ["string", "null"] },
    synapse_push_succeeded: { type: "boolean" },
    error: { type: "string" }
  },
  required: ["timestamps_valid"],
  additionalProperties: true
};

const GATE_SCHEMA = {
  type: "object",
  properties: {
    passed: { type: "boolean" },
    coverage: { type: ["number", "null"] },
    fix_loops_executed: { type: "integer" },
    skipped_checks: { type: "array", items: { type: "string" } },
    error: { type: "string" }
  },
  required: ["passed"],
  additionalProperties: true
};


  // ── Preflight ──────────────────────────────────────────────────────────────
  phase("Preflight");
  const preflight = await agent(
    "Run commit preflight: verify MCP health via session(), check git status, create " +
      "stash snapshot (git stash create + store), pre-stage synapse submodule if " +
      "OUT_OF_SYNC. Write result to pipeline state.",
    { agentType: "commit-preflight", schema: PREFLIGHT_SCHEMA }
  );

  if (!preflight.passed) {
    log(`Preflight failed: ${preflight.error ?? "unknown error"}`);
    return { success: false, phase: "preflight", error: preflight.error };
  }
  if (!preflight.changes_detected) {
    log("Preflight: no changes detected — nothing to commit.");
    return { success: false, phase: "preflight", error: "no_changes" };
  }
  log(
    `Preflight passed. snapshot_ref=${preflight.snapshot_ref}, staged=${preflight.staged_count ?? "?"}`
  );

  // ── Phase A: Quality Gate (retry loop, max 3) ──────────────────────────────
  phase("Phase A");
  // AI: Hard JS while-loop enforces the max-3 cap. The prose instruction in commit.md
  // ("repeat up to 3 times") sometimes ran only 2 iterations or continued past
  // failures. This loop cannot over-run or under-run.
  let phaseA = null;
  let iterations = 0;
  const MAX_PHASE_A_ITERATIONS = 3;

  while (iterations < MAX_PHASE_A_ITERATIONS) {
    phaseA = await agent(
      `Run Phase A quality gate (attempt ${iterations + 1}/${MAX_PHASE_A_ITERATIONS}): ` +
        // AI: preflight context injected here so Phase A agent skips re-checking git status
        // and stash — it already knows what's staged and where the snapshot lives.
        `Preflight context: snapshot_ref=${preflight.snapshot_ref ?? "N/A"}, ` +
        `staged_count=${preflight.staged_count ?? "?"} files staged. ` +
        "call run_quality_gate(); if failed call autofix() and retry. Also run CI parity " +
        "checks (check_file_sizes.py, check_function_lengths.py, build.py, " +
        "check_public_docs.py). Handle markdown lint and submodule hygiene failures inline.",
      { agentType: "commit-phase-a", schema: PHASE_A_SCHEMA }
    );
    iterations++;
    if (phaseA.passed) break;
    if (iterations < MAX_PHASE_A_ITERATIONS) {
      log(
        `Phase A failed (attempt ${iterations}/${MAX_PHASE_A_ITERATIONS}), retrying with autofix...`
      );
    }
  }

  if (!phaseA.passed) {
    log(
      `Phase A failed after ${MAX_PHASE_A_ITERATIONS} attempts. Last error: ${phaseA.error ?? "unknown"}`
    );
    return {
      success: false,
      phase: "phase_a",
      iterations,
      error: phaseA.error
    };
  }
  log(
    `Phase A passed (attempt ${iterations}/${MAX_PHASE_A_ITERATIONS}). ` +
      `coverage=${phaseA.coverage ?? "N/A"}, scope=${phaseA.scope}`
  );

  // ── Wiki Staged Ingest (inline, after Phase A) ─────────────────────────────
  phase("Wiki Ingest");
  // AI: Uses "claude" agent type (not commit-phase-a) because this step needs Bash
  // to run git diff --cached and invoke the Python venv script. Non-blocking:
  // wiki ingest failures are recorded as warnings and never halt the commit.
  const wikiIngest = await agent(
    "Run wiki staged ingest. Steps: " +
      "1. Run `git diff --cached --name-only` to list staged paths. " +
      "2. If any staged paths are under .cortex/wiki/ or docs/, run: " +
      "   cd /Users/i.grechukhin/Repo/EPD-iOS && .venv/bin/python -m cortex.tools.wiki.staged_ingest " +
      "   or equivalent wiki_ingest_staged_docs call. " +
      "3. Run `git add` on any written wiki files. " +
      "4. Return {errors: [], wiki_files_written: []} — never return blocking errors; " +
      "   if ingest fails or no wiki files are staged, return empty arrays and continue.",
    {
      agentType: "claude",
      schema: {
        type: "object",
        properties: {
          errors: { type: "array", items: { type: "string" } },
          wiki_files_written: { type: "array", items: { type: "string" } }
        },
        additionalProperties: true
      }
    }
  );
  // AI: Wiki ingest is non-blocking — log warnings but always continue to Phase B.
  if (wikiIngest && wikiIngest.errors && wikiIngest.errors.length > 0) {
    log(`Wiki ingest warning (non-blocking): ${wikiIngest.errors.join("; ")}`);
  } else {
    log(`Wiki ingest complete. files_written=${wikiIngest?.wiki_files_written?.length ?? 0}`);
  }

  // ── Phase B: Documentation ─────────────────────────────────────────────────
  phase("Phase B");
  const phaseB = await agent(
    "Run Phase B documentation sync: update activeContext, progress, roadmap via " +
      "update_memory_bank(); archive completed plans via plan(operation='archive_completed'); " +
      "call autofix() then run_docs_gate(). Non-blocking if roadmap_sync fails but " +
      "timestamps pass (set roadmap_sync_warning=true and continue). " +
      // AI: Phase A summary injected so Phase B knows which files were changed and
      // what coverage is — avoids redundant git-diff calls and gate re-runs in Phase B.
      `Phase A summary: scope=${phaseA.scope ?? "unknown"}, ` +
      `coverage=${phaseA.coverage != null ? phaseA.coverage : "N/A"}.`,
    { agentType: "commit-phase-b", schema: PHASE_B_SCHEMA }
  );
  // AI: docs_phase_passed: false is only blocking for timestamp failures.
  // roadmap_sync-only failures are recorded as a warning and do not block the commit.
  if (!phaseB.docs_phase_passed && !phaseB.roadmap_sync_warning) {
    log(`Phase B failed: ${phaseB.error ?? "docs gate did not pass"}`);
    return {
      success: false,
      phase: "phase_b",
      error: phaseB.error
    };
  }
  if (phaseB.roadmap_sync_warning) {
    log("Phase B: roadmap_sync warning (non-blocking) — continuing to Phase C.");
  }
  log(
    `Phase B complete. memory_bank_updated=${phaseB.memory_bank_updated}, ` +
      `plans_archived=${phaseB.plans_archived ?? 0}`
  );

  // ── Phase C: Validation & Synapse Submodule ────────────────────────────────
  phase("Phase C");
  const phaseC = await agent(
    "Run Phase C: validate timestamps and roadmap_sync via cortex://validation resource; " +
      "if synapse submodule is dirty: commit inside (`git -C .cortex/synapse add -A && commit`) " +
      "then push (push failure is non-blocking). Stage the updated gitlink in the superproject.",
    { agentType: "commit-phase-c", schema: PHASE_C_SCHEMA }
  );
  if (!phaseC.timestamps_valid) {
    log(`Phase C failed: timestamps invalid — ${phaseC.error ?? "check timestamp format"}`);
    return {
      success: false,
      phase: "phase_c",
      error: "timestamps_invalid"
    };
  }
  log(
    `Phase C passed. submodule=${phaseC.submodule_status}, ` +
      `synapse_sha=${phaseC.synapse_commit_sha ?? "none"}`
  );

  // ── Step 12: Final Gate (scope-routed) ────────────────────────────────────
  phase("Final Gate");
  // AI: Three-branch if/else encodes Step 12 from commit.md deterministically.
  // scope comes from Phase A; "none" skips all checks, "markdown_only" runs
  // markdown lint only (tests trusted from Phase A), "source" runs full gate.
  const scope = phaseA.scope ?? "unknown";
  let finalGate = null;

  if (scope === "none") {
    log("Step 12: scope=none — no changes since Phase A, skipping final gate.");
    finalGate = {
      passed: true,
      skipped_checks: ["all"],
      fix_loops_executed: 0,
      coverage: phaseA.coverage
    };
  } else if (scope === "markdown_only") {
    log("Step 12: scope=markdown_only — running markdown-only final gate.");
    finalGate = await agent(
      "Run Step 12 markdown-only final gate: call autofix() then run_quality_gate() " +
        "with force_fresh=true. Tests from Phase A are still valid — if tests timeout " +
        "but all non-test checks pass, the gate passes (Phase A already proved tests green).",
      { agentType: "commit-final-gate", schema: GATE_SCHEMA }
    );
  } else {
    // scope === "source" or "unknown" — full gate including tests
    log(`Step 12: scope=${scope} — running full source final gate including tests.`);
    finalGate = await agent(
      "Run Step 12 full source final gate: write force_fresh=true + test_timeout=600 " +
        "to pipeline checks config, call run_quality_gate(). If any check fails call " +
        "autofix() and retry (max 3 iterations). Then re-run CI parity checks. " +
        "If any parity check fails, Step 12 is failed — do not commit.",
      { agentType: "commit-final-gate", schema: GATE_SCHEMA }
    );
  }

  if (!finalGate.passed) {
    log(`Step 12 final gate failed: ${finalGate.error ?? "quality checks did not pass"}`);
    return {
      success: false,
      phase: "final_gate",
      scope,
      error: finalGate.error
    };
  }
  log(
    `Step 12 passed. scope=${scope}, coverage=${finalGate.coverage ?? "N/A"}, ` +
      `fix_loops=${finalGate.fix_loops_executed ?? 0}`
  );

  // ── Step 13: Commit ────────────────────────────────────────────────────────
  phase("Commit");
  const commit = await agent(
    "Run Step 13 commit: verify all phases passed in pipeline state. Apply session " +
      "scope split-commit hint. Selectively stage related files (never git add -A; " +
      "never stage .env* or credentials). Stage .cortex/temporal.db if it exists. " +
      "If Phase C submodule_status=committed, stage the synapse gitlink (git add .cortex/synapse). " +
      "Create a content-descriptive commit using conventional commits (feat/fix/docs/chore).",
    {
      agentType: "commit-phase-c",
      schema: {
        type: "object",
        properties: {
          commit_sha: { type: "string" },
          committed: { type: "boolean" },
          error: { type: "string" }
        },
        required: ["committed"],
        additionalProperties: true
      }
    }
  );
  if (!commit.committed) {
    log(`Step 13 commit failed: ${commit.error ?? "commit was not created"}`);
    return { success: false, phase: "commit", error: commit.error };
  }
  log(`Step 13 committed: sha=${commit.commit_sha ?? "unknown"}`);

  // ── Step 14: Push ──────────────────────────────────────────────────────────
  phase("Push");
  // AI: Push failures are explicitly non-blocking per commit.md Step 14.
  // Safety-net: check for unpushed synapse commits before pushing superproject.
  const push = await agent(
    "Run Step 14: safety-net synapse push check — `git log --oneline origin/main..HEAD` " +
      "inside .cortex/synapse; push submodule first if unpushed commits exist. Then push " +
      "the superproject branch including main. SSL errors: retry up to 2 times. " +
      "Push failures are non-blocking — record the error and continue.",
    {
      agentType: "commit-phase-c",
      schema: {
        type: "object",
        properties: {
          pushed: { type: "boolean" },
          remote: { type: "string" },
          error: { type: "string" }
        },
        required: ["pushed"],
        additionalProperties: true
      }
    }
  );
  if (!push.pushed) {
    // AI: Non-blocking — pipeline continues to cleanup regardless of push outcome.
    log(`Step 14 push failed (non-blocking): ${push.error ?? "unknown push error"}`);
  } else {
    log(`Step 14 pushed to ${push.remote ?? "remote"}.`);
  }

  // ── Step 15: Cleanup ───────────────────────────────────────────────────────
  phase("Cleanup");
  await agent(
    "Run Step 15 cleanup: clear the commit pipeline state via " +
      "pipeline_handoff(operation='clear', pipeline='commit').",
    {
      agentType: "commit-preflight",
      schema: {
        type: "object",
        properties: { cleared: { type: "boolean" } },
        required: ["cleared"],
        additionalProperties: true
      }
    }
  );
  log("Step 15: pipeline state cleared.");

  // ── Step 16: Post-Prompt Hook (non-blocking) ───────────────────────────────
  phase("Post-Prompt Hook");
  try {
    await agent(
      "Run Step 16 post-prompt self-improvement hook: read " +
        ".cortex/synapse/prompts/post-prompt-hook.md and execute it to analyze the " +
        "session and emit any applicable Skills, Plans, or Rules. Non-blocking — " +
        "if unavailable or MCP disconnects, record a note and consider the pipeline complete.",
      {
        agentType: "commit-preflight",
        schema: {
          type: "object",
          properties: {
            hook_ran: { type: "boolean" },
            skills_emitted: { type: "integer" }
          },
          additionalProperties: true
        }
      }
    );
    log("Step 16: post-prompt hook complete.");
  } catch (err) {
    log(`Step 16 post-prompt hook failed (non-blocking): ${err?.message ?? err}`);
  }

  return {
    success: true,
    commit_sha: commit.commit_sha,
    pushed: push.pushed,
    phase_a_iterations: iterations,
    coverage: finalGate.coverage ?? phaseA.coverage,
    scope
  };

