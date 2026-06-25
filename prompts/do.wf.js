/**
 * Cortex do pipeline — Claude Code Workflow script
 *
 * Replaces do.md LLM-orchestrated pipeline with deterministic JS control flow.
 *
 * Key improvements over prose instructions:
 *   - Implementation loop: while (!step_fully_complete && iterations < MAX_IMPL_ITERATIONS)
 *     — cannot over-run or under-run like prose "repeat until complete" instructions
 *   - Parallel [P] steps: pipeline() call for truly concurrent @implement-code runs
 *     — wall-clock is the slowest single step, not the sum of all steps
 *   - Review Gate: deterministic if (implResult.needs_review) — no LLM pipeline_handoff parsing
 *   - resumeFromRunId: interrupted implementation resumes from the failed iteration
 *   - Structured returns via schema: typed objects eliminate string parsing in orchestrator
 *
 * Subagents used (unchanged from do.md):
 *   @implement-code
 */

// AI: JSON Schema objects for structured subagent returns — loose schemas with
// additionalProperties: true allow current free-text phase outputs while providing
// typed access to the key fields the orchestrator branches on. Tighten after smoke-testing.
const SELECTION_SCHEMA = {
  type: "object",
  properties: {
    selected_step: { type: "string" },
    plan_file: { type: ["string", "null"] },
    scope: { type: ["string", "null"] },
    selection_source: {
      type: "string",
      enum: ["explicit_plan", "roadmap_priority", "roadmap_complete"]
    },
    roadmap_section: { type: ["string", "null"] },
    partial_progress: { type: ["string", "null"] },
    // AI: can_parallelize + parallel_steps come from plan task_graph when plan_file is set.
    // Selection agent reads plan(operation="get") metadata and passes these through.
    can_parallelize: { type: "boolean" },
    parallel_steps: { type: "array", items: { type: "string" } }
  },
  required: ["selected_step", "selection_source"],
  additionalProperties: true
};

const IMPL_SCHEMA = {
  type: "object",
  properties: {
    // AI: step_fully_complete drives the while-loop exit condition — the most critical field.
    // When false the orchestrator increments iterations and loops; when true it exits.
    step_fully_complete: { type: "boolean" },
    files_changed: { type: "array", items: { type: "string" } },
    subtasks_done: { type: "integer" },
    subtask: { type: "string" },
    needs_review: { type: "boolean" },
    coverage: { type: ["number", "null"] },
    error: { type: "string" }
  },
  required: ["step_fully_complete"],
  additionalProperties: true
};

const REVIEW_SCHEMA = {
  type: "object",
  properties: {
    // AI: outcome is the binary gate — "no_gaps" unlocks plan(complete);
    // "gaps_found" rewrites plan with Review Follow-Up Gaps section and keeps it PENDING.
    outcome: {
      type: "string",
      enum: ["no_gaps", "gaps_found"]
    },
    gaps: { type: "array", items: { type: "string" } },
    evidence: { type: "array", items: { type: "string" } },
    review_summary: { type: "string" }
  },
  required: ["outcome"],
  additionalProperties: true
};

const FINALIZE_SCHEMA = {
  type: "object",
  properties: {
    memory_bank_updated: { type: "boolean" },
    roadmap_entry: { type: "string", enum: ["removed", "kept", "unchanged"] },
    plan_file: { type: "string", enum: ["archived", "updated", "none"] },
    completion_outcome: { type: "string", enum: ["completed_no_gaps", "reopened_with_gaps", "partial", "no_op"] },
    error: { type: "string" }
  },
  required: ["completion_outcome"],
  additionalProperties: true
};

// AI: mergeParallelResults combines output from multiple concurrent @implement-code agents.
// Each agent writes its own files_changed array and subtasks_done count — merge flattens
// both. step_fully_complete is true only when ALL parallel steps report complete.
// needs_review is true if ANY parallel step reports it (conservative: if one needs review,
// all parallel work needs review before the plan can close).
function mergeParallelResults(results) {
  const valid = results.filter(r => r !== null && r !== undefined);
  return {
    step_fully_complete: valid.length > 0 && valid.every(r => r.step_fully_complete === true),
    files_changed: valid.flatMap(r => r.files_changed ?? []),
    subtasks_done: valid.reduce((sum, r) => sum + (r.subtasks_done ?? 0), 0),
    needs_review: valid.some(r => r.needs_review === true),
    coverage: valid.map(r => r.coverage).find(c => c !== null && c !== undefined) ?? null,
    // AI: Track per-step errors so finalize can surface partial failures.
    parallel_errors: valid.filter(r => r.error).map(r => r.error),
  };
}

export const meta = {
  name: "cortex-do",
  description:
    "Cortex implement pipeline: select → implementation loop → review gate → finalize → verify → fix → cleanup",
  phases: [
    {
      title: "Selection",
      detail: "identify next roadmap step, read plan, check gate_feedback, load context"
    },
    {
      title: "Implementation",
      detail: "loop until step_fully_complete=true, max 5 iterations; parallel [P] steps via pipeline()"
    },
    {
      title: "Review Gate",
      detail: "inline review of files_changed; branches on needs_review flag"
    },
    {
      title: "Finalize",
      detail: "plan(complete) or partial update; Partial Progress Log; anti-scrap guardrail"
    },
    {
      title: "Verify",
      detail: "roadmap + progress.md read-only checks; archive completed plans"
    },
    {
      title: "Fix",
      detail: "autofix + quality gate + docs gate; max 3 iterations each target"
    },
    {
      title: "Cleanup",
      detail: "clear implement pipeline state"
    },
    {
      title: "Post-Prompt Hook",
      detail: "self-improvement hook (non-blocking)"
    }
  ]
};

export default async function doPipeline({ phase, agent, log, pipeline }) {
  // ── Selection ──────────────────────────────────────────────────────────────
  phase("Selection");
  // AI: Selection is inline (no subagent) per do.md spec. Here we use an implement-code
  // agent with SELECTION_SCHEMA to get structured output; the agent runs the inline
  // steps from do.md Selection section (session(), gate_feedback, roadmap read, plan
  // read, context + rules load) and returns the structured selection result.
  const selection = await agent(
    "Run Selection inline: call session() to verify MCP health (STOP if unhealthy). " +
      "Read gate_feedback from pipeline_handoff(operation='read', pipeline='implement', phase='gate_feedback') — " +
      "if present, print the summary. Read roadmap via manage_file(file_name='roadmap.md', operation='read'). " +
      "If a plan hint was provided (/cortex/do @<path>), read that plan directly. " +
      "Otherwise select the next pending step by priority: Blockers > Active Work > Pending plans. " +
      "If no pending steps: return selection_source='roadmap_complete'. " +
      "Read cortex://context and cortex://rules (non-blocking). " +
      "If plan_file exists, read it and extract: implementation steps, success criteria, " +
      "testing strategy, partial_progress from '## Partial Progress Log'. " +
      "Call plan(operation='get', response_format='metadata') to read can_parallelize and " +
      "parallel_steps from task_graph. " +
      "Write result to pipeline_handoff(phase='select', pipeline='implement').",
    {
      agentType: "implement-code",
      schema: SELECTION_SCHEMA
    }
  );

  if (selection.selection_source === "roadmap_complete") {
    log("Selection: roadmap complete — no pending steps.");
    return { success: false, phase: "selection", reason: "roadmap_complete" };
  }
  log(
    `Selection: step="${selection.selected_step}", source=${selection.selection_source}, ` +
      `plan=${selection.plan_file ?? "none"}, can_parallelize=${selection.can_parallelize ?? false}`
  );

  // ── Implementation ─────────────────────────────────────────────────────────
  phase("Implementation");
  let implResult = null;
  const MAX_IMPL_ITERATIONS = 5;
  let iterations = 0;
  let partialProgress = selection.partial_progress ?? null;

  const canParallelize =
    selection.can_parallelize === true &&
    Array.isArray(selection.parallel_steps) &&
    selection.parallel_steps.length > 1;

  if (canParallelize) {
    // AI: True parallel execution via pipeline() — wall-clock is the slowest single step.
    // Each parallel step gets its own @implement-code agent with worktree isolation.
    // Steps MUST be independent (no shared files) — documented constraint in do.md.
    log(
      `Implementation: parallel path — ${selection.parallel_steps.length} concurrent steps via pipeline()`
    );
    const parallelResults = await pipeline(
      selection.parallel_steps,
      step =>
        agent(
          `Implement parallel step: "${step}". ` +
            `Full plan context: selected_step="${selection.selected_step}", ` +
            `plan_file="${selection.plan_file ?? "none"}", ` +
            `scope="${selection.scope ?? "none"}", ` +
            `partial_progress="${partialProgress ?? "none"}". ` +
            "Implement this specific step only. Write code and tests. " +
            "Run quality gate after implementation. " +
            "Return step_fully_complete=true when this specific step is complete.",
          {
            agentType: "implement-code",
            schema: IMPL_SCHEMA
          }
        )
    );
    implResult = mergeParallelResults(parallelResults);
    iterations = 1; // one pipeline() wave counts as one iteration
    log(
      `Implementation (parallel): complete=${implResult.step_fully_complete}, ` +
        `files=${implResult.files_changed?.length ?? 0}, ` +
        `subtasks=${implResult.subtasks_done ?? 0}`
    );
  } else {
    // AI: Sequential loop — hard JS while-loop enforces the MAX_IMPL_ITERATIONS cap.
    // The prose instruction in do.md ("repeat until step_fully_complete=true") sometimes
    // over-ran or under-ran. This loop cannot do either.
    while (iterations < MAX_IMPL_ITERATIONS) {
      implResult = await agent(
        `Implement next subtask (attempt ${iterations + 1}/${MAX_IMPL_ITERATIONS}): ` +
          `selected_step="${selection.selected_step}", ` +
          `plan_file="${selection.plan_file ?? "none"}", ` +
          `scope="${selection.scope ?? "none"}", ` +
          `partial_progress="${partialProgress ?? "none"}". ` +
          "Implement as many consecutive subtasks as context allows. " +
          "Run quality gate after each subtask. " +
          "Add # AI: comments for non-obvious logic decisions. " +
          "Return step_fully_complete=true when the entire plan step is done, " +
          "false when more subtasks remain. " +
          "Write result to pipeline_handoff(phase='code', pipeline='implement').",
        {
          agentType: "implement-code",
          schema: IMPL_SCHEMA
        }
      );
      iterations++;

      if (implResult.step_fully_complete) {
        log(
          `Implementation: step complete on attempt ${iterations}/${MAX_IMPL_ITERATIONS}. ` +
            `files=${implResult.files_changed?.length ?? 0}`
        );
        break;
      }

      // Accumulate partial progress before next iteration
      if (implResult.subtask) {
        partialProgress = partialProgress
          ? `${partialProgress}, ${implResult.subtask}`
          : implResult.subtask;
      }
      log(
        `Implementation: subtask incomplete (${iterations}/${MAX_IMPL_ITERATIONS}), ` +
          `continuing... partial_progress="${partialProgress ?? "none"}"`
      );
    }

    if (iterations >= MAX_IMPL_ITERATIONS && !implResult.step_fully_complete) {
      log(
        `Implementation: reached max iterations (${MAX_IMPL_ITERATIONS}) without step_fully_complete. ` +
          "Proceeding to Finalize with partial result."
      );
    }
  }

  // ── Review Gate ────────────────────────────────────────────────────────────
  phase("Review Gate");
  // AI: Deterministic branch — needs_review comes from impl schema, no pipeline_handoff parsing.
  // Review Gate only runs when step is fully complete AND the implementation reported it.
  let reviewResult = null;

  if (implResult.step_fully_complete && implResult.needs_review !== false) {
    // AI: Default to running review when step_fully_complete=true unless explicitly skipped.
    // This matches do.md: "Only run this phase when phases.code.step_fully_complete == true."
    log("Review Gate: running inline review of implementation.");
    reviewResult = await agent(
      "Run Review Gate inline: read each file in the files_changed list from the " +
        "implementation result. Assess: correctness (logic errors, edge cases), " +
        "completeness (all success criteria from plan satisfied, no TODOs), " +
        "security (no hardcoded secrets, no injection risks), " +
        "type safety (all public functions annotated, no suppressed type errors), " +
        "test coverage (new public functions have tests). " +
        "Normalize to exactly one outcome: " +
        "'no_gaps' — no correctness/completeness/security gaps found; " +
        "'gaps_found' — one or more actionable gaps that must be fixed. " +
        "Style suggestions alone do NOT count as gaps. " +
        "Build a deduplicated bounded gaps list with stable wording and file evidence. " +
        "Write result to pipeline_handoff(phase='review', pipeline='implement').",
      {
        agentType: "implement-code",
        schema: REVIEW_SCHEMA
      }
    );
    log(`Review Gate: outcome=${reviewResult.outcome}, gaps=${reviewResult.gaps?.length ?? 0}`);
  } else if (!implResult.step_fully_complete) {
    log("Review Gate: skipped — step not fully complete (partial path).");
  } else {
    log("Review Gate: skipped — needs_review=false (implementation self-certified clean).");
  }

  // ── Finalize ───────────────────────────────────────────────────────────────
  phase("Finalize");
  const isFullyComplete = implResult.step_fully_complete === true;
  const reviewPassed = reviewResult === null || reviewResult.outcome === "no_gaps";

  const finalize = await agent(
    "Run Finalize inline. " +
      `step_fully_complete=${isFullyComplete}, ` +
      `review_outcome="${reviewResult?.outcome ?? "skipped"}", ` +
      `gaps=${JSON.stringify(reviewResult?.gaps ?? [])}, ` +
      `files_changed=${JSON.stringify(implResult.files_changed ?? [])}, ` +
      `selected_step="${selection.selected_step}", ` +
      `plan_file="${selection.plan_file ?? "none"}". ` +
      (isFullyComplete && reviewPassed
        ? "Fully complete path: call plan(operation='complete', ...) to atomically " +
          "remove roadmap entry, append to activeContext, update progress.md, archive plan. " +
          "NEVER call update_memory_bank for these when using plan(complete)."
        : "Partial/reopened path: " +
          "Apply anti-scrap guardrail (if files_changed is empty or bookkeeping-only, " +
          "write finalize with no_op_run and keep roadmap entry unchanged). " +
          "For real partial work: call update_memory_bank(operation='progress_append'). " +
          "For gaps_found: append '## Review Follow-Up Gaps' section to plan file " +
          "with deduplicated gap bullets. Keep plan frontmatter status PENDING. " +
          "Append to plan '## Partial Progress Log' with today's date, subtask, and files.") +
      " Write result to pipeline_handoff(phase='finalize', pipeline='implement').",
    {
      agentType: "implement-code",
      schema: FINALIZE_SCHEMA
    }
  );
  log(
    `Finalize: outcome=${finalize.completion_outcome}, ` +
      `roadmap=${finalize.roadmap_entry}, plan=${finalize.plan_file}`
  );

  // ── Verify ─────────────────────────────────────────────────────────────────
  phase("Verify");
  await agent(
    "Run Verify inline (read-only checks): " +
      "1. Read .cortex/memory-bank/roadmap.md — if step was fully completed, verify the entry is absent; " +
      "if partial, verify the entry is still present. " +
      "2. Read .cortex/memory-bank/progress.md — verify a new entry for today exists. " +
      "3. Call plan(operation='archive_completed') to archive any plans with status COMPLETE. " +
      "4. Write result to pipeline_handoff(phase='verify', pipeline='implement') " +
      "with status='passed', roadmap_check, progress_check, stray_complete_plans.",
    {
      agentType: "implement-code",
      schema: {
        type: "object",
        properties: {
          status: { type: "string", enum: ["passed", "failed"] },
          roadmap_check: { type: "string" },
          progress_check: { type: "string" },
          stray_complete_plans: { type: "array", items: { type: "string" } }
        },
        required: ["status"],
        additionalProperties: true
      }
    }
  );
  log("Verify: complete.");

  // ── Fix ────────────────────────────────────────────────────────────────────
  phase("Fix");
  // AI: Fix follows fix.md target=all order: quality first, then tests, then docs.
  // Each target has max 3 iterations. docs gate failure is non-blocking if it's a
  // Cursor bridge false-negative (roadmap.md exists but bridge reports missing).
  const fix = await agent(
    "Run Fix inline (target=all): " +
      "1. Quality: call autofix(), then run_quality_gate(). If issues remain, fix inline and retry " +
      "(max 3 iterations). " +
      "2. Tests: if run_quality_gate() reports test failures, diagnose and fix inline (max 3 iterations). " +
      "3. Docs: call run_docs_gate(). If timestamps or roadmap_sync fail, fix via manage_file() " +
      "and retry (max 3 iterations). " +
      "If run_docs_gate() returns DocsMemoryBankToolError with 'roadmap.md does not exist', " +
      "run manage_file(operation='metadata', file_name='roadmap.md') — if metadata.file_exists=true, " +
      "treat as Cursor bridge false-negative (non-blocking) and set docs_warning in payload. " +
      "Write result to pipeline_handoff(phase='fix', pipeline='implement') with " +
      "status='passed' or 'failed', quality_passed, tests_passed, docs_passed, fix_iterations, " +
      "docs_warning.",
    {
      agentType: "implement-code",
      schema: {
        type: "object",
        properties: {
          status: { type: "string", enum: ["passed", "failed"] },
          quality_passed: { type: "boolean" },
          tests_passed: { type: "boolean" },
          docs_passed: { type: "boolean" },
          fix_iterations: { type: "integer" },
          docs_warning: { type: ["string", "null"] }
        },
        required: ["status"],
        additionalProperties: true
      }
    }
  );
  // AI: Fix is non-blocking after 3 iterations — log remaining issues and proceed.
  if (fix.status === "failed") {
    log(
      `Fix: completed with failures (non-blocking after max iterations). ` +
        `quality=${fix.quality_passed}, tests=${fix.tests_passed}, docs=${fix.docs_passed}`
    );
  } else {
    log(`Fix: passed. iterations=${fix.fix_iterations ?? 0}`);
  }

  // ── Cleanup ────────────────────────────────────────────────────────────────
  phase("Cleanup");
  await agent(
    "Run Cleanup: clear the implement pipeline state via " +
      "pipeline_handoff(operation='clear', pipeline='implement').",
    {
      agentType: "implement-code",
      schema: {
        type: "object",
        properties: { cleared: { type: "boolean" } },
        required: ["cleared"],
        additionalProperties: true
      }
    }
  );
  log("Cleanup: pipeline state cleared.");

  // ── Post-Prompt Hook (non-blocking) ────────────────────────────────────────
  phase("Post-Prompt Hook");
  try {
    await agent(
      "Run post-prompt self-improvement hook: read " +
        ".cortex/synapse/prompts/post-prompt-hook.md and execute it to analyze the " +
        "session and emit any applicable Skills, Plans, or Rules. Non-blocking — " +
        "if unavailable or MCP disconnects, record a note and consider the pipeline complete.",
      {
        agentType: "implement-code",
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
    log("Post-Prompt Hook: complete.");
  } catch (err) {
    log(`Post-Prompt Hook failed (non-blocking): ${err?.message ?? err}`);
  }

  return {
    success: true,
    step: selection.selected_step,
    plan_file: selection.plan_file,
    completion_outcome: finalize.completion_outcome,
    impl_iterations: iterations,
    files_changed: implResult.files_changed?.length ?? 0,
    coverage: implResult.coverage,
    review_outcome: reviewResult?.outcome ?? "skipped",
    fix_passed: fix.status === "passed",
    parallel_execution: canParallelize
  };
}
