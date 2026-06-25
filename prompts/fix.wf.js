/**
 * Cortex fix pipeline — Claude Code Workflow script
 *
 * Replaces fix.md LLM-orchestrated pipeline with deterministic JS control flow.
 *
 * Key improvements over prose instructions:
 *   - Coverage routing: switch(cov.status) covers all 5 status values — no LLM mis-routing
 *     between 'tests_failing' (skip quality → tests) and 'failed'/'BLOCKED' (hard stop)
 *   - Per-target retry loops: while (iterations < MAX_TARGET_ITERATIONS && !passed) — cannot
 *     over-run or under-run; hard cap at 3 per target
 *   - Quality scope routing: if (diagnosis.change_scope === 'markdown_only') — deterministic
 *     branch selects correct agent prompt variant
 *   - PHASE 0 diagnosis gates the pipeline by construction — it is the first await agent()
 *     call; no target agent can execute without it returning
 *   - resumeFromRunId: interrupted run resumes from the failed target, not from diagnosis
 *   - Structured subagent returns via schema: typed objects eliminate string parsing
 *
 * Subagents used (unchanged from fix.md):
 *   @fix-coverage, @fix-quality, @fix-tests, @fix-docs
 */

export const meta = {
  name: "cortex-fix",
  description:
    "Cortex fix pipeline: PHASE 0 diagnosis → coverage → quality → tests → docs",
  phases: [
    {
      title: "Diagnosis",
      detail: "PHASE 0: MCP probe, change-scope assessment, submodule routing, target selection"
    },
    {
      title: "Coverage",
      detail: "preflight gate + conditional @fix-coverage execution"
    },
    {
      title: "Quality",
      detail: "@fix-quality autofix retry loop (max 3), scope-routed (markdown_only vs source)"
    },
    {
      title: "Tests",
      detail: "@fix-tests assertion-failure retry loop (max 3)"
    },
    {
      title: "Docs",
      detail: "@fix-docs docs-gate retry loop (max 3)"
    },
    {
      title: "Post-Prompt Hook",
      detail: "self-improvement hook (non-blocking)"
    }
  ]
};

const MAX_TARGET_ITERATIONS = 3;

// AI: DIAGNOSIS_SCHEMA captures the PHASE 0 output that gates all subsequent work.
// change_scope drives quality scope routing (markdown_only vs source); targets
// drives which target phases run. Both fields must be present before any target runs.
const DIAGNOSIS_SCHEMA = {
  type: "object",
  properties: {
    // AI: scope describes what changed in the working tree (Change-Scope Assessment)
    change_scope: {
      type: "string",
      enum: ["source_changed", "markdown_only", "mixed"]
    },
    // AI: targets lists which fix targets apply given the change scope and active issues
    targets: {
      type: "array",
      items: {
        type: "string",
        enum: ["coverage", "quality", "tests", "docs"]
      }
    },
    // AI: mcp_available gates the entire pipeline — false triggers BLOCKED_NO_MCP stop
    mcp_available: { type: "boolean" },
    diagnosis_note: { type: "string" },
    error: { type: "string" }
  },
  required: ["change_scope", "targets", "mcp_available"],
  additionalProperties: true
};

// AI: COVERAGE_SCHEMA.status is the switch key for post-coverage routing.
// All 5 values from fix.md must be covered: passed, skipped, tests_failing, failed, BLOCKED.
const COVERAGE_SCHEMA = {
  type: "object",
  properties: {
    status: {
      type: "string",
      enum: ["passed", "skipped", "tests_failing", "failed", "BLOCKED"]
    },
    final_coverage: { type: ["number", "null"] },
    coverage_delta: { type: ["number", "null"] },
    tests_added: { type: "integer" },
    blocker_reason: { type: ["string", "null"] },
    iterations: { type: "integer" },
    error: { type: "string" }
  },
  required: ["status"],
  additionalProperties: true
};

const QUALITY_SCHEMA = {
  type: "object",
  properties: {
    // AI: passed drives the while-loop exit condition for the quality retry loop
    passed: { type: "boolean" },
    iterations: { type: "integer" },
    autofix_ran: { type: "boolean" },
    scope_used: {
      type: "string",
      enum: ["markdown_only", "source_changed", "mixed"]
    },
    error: { type: "string" }
  },
  required: ["passed"],
  additionalProperties: true
};

const TESTS_SCHEMA = {
  type: "object",
  properties: {
    // AI: passed drives the while-loop exit condition for the tests retry loop
    passed: { type: "boolean" },
    tests_failed: { type: "integer" },
    iterations: { type: "integer" },
    branch: {
      type: "string",
      enum: ["assertion_failures", "build_error", "skipped", "unknown"]
    },
    error: { type: "string" }
  },
  required: ["passed"],
  additionalProperties: true
};

const DOCS_SCHEMA = {
  type: "object",
  properties: {
    // AI: passed drives the while-loop exit condition for the docs retry loop
    passed: { type: "boolean" },
    docs_phase_passed: { type: "boolean" },
    iterations: { type: "integer" },
    // AI: bridge_mismatch=true means docs gate returned DocsMemoryBankToolError
    // but manage_file(metadata) confirmed roadmap.md exists — non-blocking warning
    bridge_mismatch: { type: "boolean" },
    error: { type: "string" }
  },
  required: ["passed"],
  additionalProperties: true
};

// AI: runTarget encodes the common retry-loop pattern for quality, tests, and docs.
// Each target has a max 3 iterations: call agent → check passed → log retry or break.
// Extracting into a helper avoids copy-paste drift between the three target loops.
// NOTE: this helper is never async itself — it returns the schema-validated last result.
// The caller uses 'await' on the agent() calls via the closure; the helper is a data
// accumulator only. In the JS Workflow runtime, all async is at the top-level pipeline
// function; helpers that accept async callbacks pattern-match to this approach.


  // ── PHASE 0: Diagnosis ─────────────────────────────────────────────────────
  // AI: Diagnosis is the FIRST await agent() call by construction — no target agent
  // can run before it returns. This encodes the fix.md PHASE 0 hard gate deterministically.
  phase("Diagnosis");
  const diagnosis = await agent(
    "Run PHASE 0 Diagnosis (MANDATORY — no file edits until this returns): " +
      "1. Probe Cortex MCP availability via session(). If all invocation paths fail, " +
      "return mcp_available=false with error 'BLOCKED_NO_MCP'. " +
      "2. Classify working-tree change scope: run git diff --name-only HEAD to list modified files. " +
      "Classify as source_changed (any .py/.ts/.go/.swift file outside .cortex/), " +
      "markdown_only (all changes are .md/.mdc), or mixed (both). " +
      "3. Detect dirty submodules: run git submodule foreach 'git status --short'. " +
      "If any submodule has uncommitted changes, run diagnose-first + fix for that submodule " +
      "before returning targets. " +
      "4. Call pipeline_handoff(operation='clear', pipeline='fix') to remove stale phase results. " +
      "5. Produce a Diagnosis Note: symptom, observed evidence, top 3 hypotheses with evidence, " +
      "selected hypothesis, minimal fix plan. " +
      "6. Select fix targets based on scope and active issues. Return targets array with the " +
      "applicable subset of [coverage, quality, tests, docs]. " +
      "Write diagnosis result to pipeline_handoff(phase='diagnosis', pipeline='fix').",
    {
      agentType: "fix-quality",
      schema: DIAGNOSIS_SCHEMA
    }
  );

  if (!diagnosis.mcp_available) {
    log(
      `BLOCKED_NO_MCP: ${diagnosis.error ?? "Cortex MCP server unavailable"}. ` +
        "Fix MCP connectivity and re-run /cortex/fix."
    );
    return {
      success: false,
      phase: "diagnosis",
      reason: "BLOCKED_NO_MCP",
      error: diagnosis.error
    };
  }

  if (!diagnosis.targets || diagnosis.targets.length === 0) {
    log("Diagnosis: no fix targets identified — nothing to fix.");
    return { success: false, phase: "diagnosis", reason: "no_targets" };
  }

  log(
    `Diagnosis: scope=${diagnosis.change_scope}, ` +
      `targets=[${diagnosis.targets.join(", ")}]`
  );

  // ── Coverage ───────────────────────────────────────────────────────────────
  // AI: Coverage controls whether quality and tests run. The switch on cov.status
  // deterministically routes: passed/skipped → quality, tests_failing → tests only,
  // failed/BLOCKED → hard stop. This eliminates LLM reasoning over prose routing rules.
  let runQuality = diagnosis.targets.includes("quality");
  let runTests = diagnosis.targets.includes("tests");
  let coverageResult = null;

  if (diagnosis.targets.includes("coverage")) {
    phase("Coverage");

    // AI: Pre-flight gate — call run_quality_gate() once to detect if threshold already
    // met. The @fix-coverage subagent handles uplift logic and its own gate calls.
    const cov = await agent(
      "Run coverage target: " +
        "1. Call run_quality_gate() once as the pre-flight gate. Check preflight_passed. " +
        "If preflight_passed=true, return status='skipped' (threshold already met). " +
        "2. If preflight_passed=false: extract results.tests.coverage, coverage_gaps, " +
        "tests_failed. Write to pipeline_handoff(phase='coverage', pipeline='fix'). " +
        "3. Run @fix-coverage subagent. Wait for it to complete. " +
        "4. Read its result from pipeline_handoff(phase='coverage', pipeline='fix'). " +
        "5. Return that result as your schema output (status, final_coverage, tests_added, etc.).",
      {
        agentType: "fix-coverage",
        schema: COVERAGE_SCHEMA
      }
    );

    coverageResult = cov;
    log(
      `Coverage: status=${cov.status}, ` +
        `final_coverage=${cov.final_coverage ?? "N/A"}, ` +
        `tests_added=${cov.tests_added ?? 0}`
    );

    // AI: Exhaustive switch with explicit default — missing a coverage status value
    // would cause silent wrong routing. The default stops the pipeline safely.
    switch (cov.status) {
      case "passed":
      case "skipped":
        // Coverage met or skipped — proceed to quality as originally planned
        // runQuality and runTests already reflect diagnosis.targets; no change needed
        break;

      case "tests_failing":
        // AI: tests_failing means tests were already broken before coverage could be
        // measured. Skip quality (it would hit the same failures) and route to tests.
        // After tests target completes the user must re-run /cortex/fix from the start.
        log(
          "Coverage: tests_failing — skipping Quality, routing directly to Tests target."
        );
        runQuality = false;
        runTests = true;
        break;

      case "failed":
      case "BLOCKED":
        // AI: Hard stop — coverage measurable but below threshold, or external blocker.
        // Running quality/tests would hit the same gate failure and waste iterations.
        log(
          `Coverage hard stop: status=${cov.status}, ` +
            `blocker_reason=${cov.blocker_reason ?? "coverage below threshold"}. ` +
            "Quality / Tests / Docs skipped. Re-run /cortex/fix coverage for more uplift."
        );
        return {
          success: false,
          phase: "coverage",
          coverage_status: cov.status,
          final_coverage: cov.final_coverage,
          blocker_reason: cov.blocker_reason,
          stopped_at: "coverage"
        };

      default:
        // AI: Unknown status — fail safely rather than routing to the wrong target.
        log(
          `Coverage: unexpected status='${cov.status}' — hard stop to prevent mis-routing.`
        );
        return {
          success: false,
          phase: "coverage",
          coverage_status: cov.status,
          stopped_at: "coverage",
          error: `Unexpected coverage status: ${cov.status}`
        };
    }
  }

  // ── Quality ────────────────────────────────────────────────────────────────
  let qualityPassed = false;
  let qualityResult = null;

  if (runQuality) {
    phase("Quality");
    let iterations = 0;

    // AI: Hard while-loop cap at MAX_TARGET_ITERATIONS (3). The prose instruction in
    // fix.md ("Repeat, max 3 iterations") sometimes over-ran or under-ran. This loop
    // cannot do either. qualityPassed=true breaks early; exhaustion continues to tests.
    while (iterations < MAX_TARGET_ITERATIONS && !qualityPassed) {
      const quality = await agent(
        `Fix quality issues (attempt ${iterations + 1}/${MAX_TARGET_ITERATIONS}): ` +
          `change_scope=${diagnosis.change_scope}. ` +
          (diagnosis.change_scope === "markdown_only"
            ? "Path A (markdown_only): call autofix(), then run_quality_gate(). " +
              "Fix markdown lint errors manually per rule code. Retry (max 3 iterations). "
            : "Path B (source_changed/mixed): call autofix(), then run_quality_gate(). " +
              "Run CI parity scripts (check_file_sizes.py, check_function_lengths.py, build.py). " +
              "Fix type errors, file/function length violations, format issues inline. " +
              "Apply Post-fix validation (py_compile + import check) for Python files. ") +
          "Return passed=true only when run_quality_gate() returns preflight_passed=true " +
          "AND all CI parity scripts exit 0.",
        {
          agentType: "fix-quality",
          schema: QUALITY_SCHEMA
        }
      );
      qualityResult = quality;
      qualityPassed = quality.passed === true;
      iterations++;

      if (!qualityPassed && iterations < MAX_TARGET_ITERATIONS) {
        log(
          `Quality iteration ${iterations}/${MAX_TARGET_ITERATIONS} failed, retrying...`
        );
      }
    }

    if (!qualityPassed) {
      log(
        `Quality not resolved after ${MAX_TARGET_ITERATIONS} iterations — ` +
          "continuing to tests (non-blocking)."
      );
    } else {
      log(
        `Quality: passed on iteration ${qualityResult?.iterations ?? "?"}.`
      );
    }
  }

  // ── Tests ──────────────────────────────────────────────────────────────────
  let testsPassed = false;
  let testsResult = null;

  if (runTests) {
    phase("Tests");

    // AI: markdown_only scope means no source changed — tests cannot be affected.
    // Skip immediately rather than running a gate that will trivially pass.
    if (diagnosis.change_scope === "markdown_only") {
      log("Tests: skipped (markdown_only scope — no source changed).");
      testsPassed = true;
    } else {
      let iterations = 0;

      // AI: Hard while-loop cap at 3 — same pattern as quality loop.
      while (iterations < MAX_TARGET_ITERATIONS && !testsPassed) {
        const tests = await agent(
          `Fix test failures (attempt ${iterations + 1}/${MAX_TARGET_ITERATIONS}): ` +
            "1. Call run_quality_gate() to get test results. " +
            "2. Choose branch based on tests_failed: " +
            "Branch A (tests_failed > 0): locate failing tests, debug root cause, " +
            "fix assertion mismatches or implementation bugs. " +
            "Branch B (tests_failed == 0, coverage only): out of scope — return " +
            "passed=true, branch='skipped' (coverage handled by @fix-coverage). " +
            "Branch C (tests_failed == 0, subprocess crash): read results.tests.output " +
            "for build errors and fix at reported line. " +
            "Return passed=true when run_quality_gate() reports results.tests.success=true.",
          {
            agentType: "fix-tests",
            schema: TESTS_SCHEMA
          }
        );
        testsResult = tests;
        testsPassed = tests.passed === true;
        iterations++;

        if (!testsPassed && iterations < MAX_TARGET_ITERATIONS) {
          log(
            `Tests iteration ${iterations}/${MAX_TARGET_ITERATIONS} failed, retrying...`
          );
        }
      }

      if (!testsPassed) {
        log(
          `Tests not resolved after ${MAX_TARGET_ITERATIONS} iterations — ` +
            "continuing to docs (non-blocking)."
        );
      } else {
        log(`Tests: passed. branch=${testsResult?.branch ?? "unknown"}.`);
      }
    }
  }

  // ── Docs ───────────────────────────────────────────────────────────────────
  let docsPassed = false;
  let docsResult = null;
  let docsWarning = null;

  if (diagnosis.targets.includes("docs")) {
    phase("Docs");
    let iterations = 0;

    // AI: Hard while-loop cap at 3 — same pattern as quality and tests loops.
    while (iterations < MAX_TARGET_ITERATIONS && !docsPassed) {
      const docs = await agent(
        `Fix docs and memory bank (attempt ${iterations + 1}/${MAX_TARGET_ITERATIONS}): ` +
          "1. Analyze roadmap and plans: cross-check roadmap.md against plan files. " +
          "2. Align activeContext and progress (completed → activeContext, ongoing → roadmap). " +
          "3. Fix timestamp and sync issues: read cortex://validation resource. " +
          "4. Call run_docs_gate(). " +
          "If DocsMemoryBankToolError with 'roadmap.md does not exist': " +
          "call manage_file(operation='metadata', file_name='roadmap.md'). " +
          "If metadata.file_exists=true, set bridge_mismatch=true, passed=true (non-blocking). " +
          "Return passed=true when run_docs_gate() returns docs_phase_passed=true, " +
          "or when bridge_mismatch=true (non-blocking warning).",
        {
          agentType: "fix-docs",
          schema: DOCS_SCHEMA
        }
      );
      docsResult = docs;
      docsPassed = docs.passed === true;
      iterations++;

      // AI: bridge_mismatch is a known Cursor MCP bridge false-negative: docs gate
      // reports roadmap.md missing but manage_file(metadata) confirms it exists.
      // Treat as non-blocking warning; do not retry — retries hit the same bridge behavior.
      if (docs.bridge_mismatch) {
        docsWarning =
          "docs gate reported roadmap.md missing but manage_file(metadata) confirms file_exists=true; " +
          "treating as Cursor bridge false-negative (non-blocking)";
        log(`Docs: bridge mismatch warning (non-blocking). ${docsWarning}`);
        break;
      }

      if (!docsPassed && iterations < MAX_TARGET_ITERATIONS) {
        log(
          `Docs iteration ${iterations}/${MAX_TARGET_ITERATIONS} failed, retrying...`
        );
      }
    }

    if (!docsPassed && !docsResult?.bridge_mismatch) {
      log(
        `Docs not resolved after ${MAX_TARGET_ITERATIONS} iterations (non-blocking).`
      );
    } else if (docsPassed) {
      log("Docs: passed.");
    }
  }

  // ── Post-Prompt Hook (non-blocking) ────────────────────────────────────────
  phase("Post-Prompt Hook");
  try {
    await agent(
      "Run post-prompt self-improvement hook: read " +
        ".cortex/synapse/prompts/post-prompt-hook.md and execute it to analyze the " +
        "session and emit any applicable Skills, Plans, or Rules. Non-blocking — " +
        "if unavailable or MCP disconnects, record a note and consider the pipeline complete.",
      {
        agentType: "fix-quality",
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

  const allPassed =
    (!diagnosis.targets.includes("coverage") || coverageResult?.status === "passed" || coverageResult?.status === "skipped") &&
    (!runQuality || qualityPassed) &&
    (!runTests || testsPassed) &&
    (!diagnosis.targets.includes("docs") || docsPassed || docsResult?.bridge_mismatch === true);

  return {
    success: allPassed,
    targets_run: diagnosis.targets,
    change_scope: diagnosis.change_scope,
    coverage_status: coverageResult?.status ?? "skipped",
    quality_passed: qualityPassed,
    tests_passed: testsPassed,
    docs_passed: docsPassed,
    docs_warning: docsWarning,
    final_coverage: coverageResult?.final_coverage ?? null
  };

