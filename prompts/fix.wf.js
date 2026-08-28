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
    // AI: prior_errors carries the first 20 lines of type/lint/test errors from the
    // coverage pre-flight gate so downstream quality and tests agents can skip their
    // first gate call — they already know what's failing.
    prior_errors: { type: ["string", "null"] },
    // AI: preflight_passed is the raw verdict of the step-1 pre-flight run_quality_gate().
    // files_written=true if this phase (or @fix-coverage) touched ANY file, which makes
    // the pre-flight verdict stale. Both must be DECLARED here or the agent will not
    // return them and the Quality reuse below can never fire.
    preflight_passed: { type: ["boolean", "null"] },
    files_written: { type: ["boolean", "null"] },
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
    // AI: prior_failures echoes back the prior_errors injected into this agent's prompt,
    // confirming the agent received and acted on the pre-flight gate context.
    prior_failures: { type: ["string", "null"] },
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
    // AI: prior_failures echoes back the prior_errors injected into this agent's prompt,
    // confirming the agent received and acted on the pre-flight gate context.
    prior_failures: { type: ["string", "null"] },
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
      "Language coverage is NOT a reason to drop a target: if the Cortex gate does not " +
      "support the changed language (e.g. Swift), still select quality and tests — the " +
      "target agents verify those natively (swift build / swift test). Only omit quality " +
      "and tests when no source file changed at all (markdown_only). " +
      "This applies to the coverage target too. Do NOT drop coverage on the reasoning " +
      "'not a Python project' — Cortex ships a Swift coverage adapter (llvm-cov / SwiftPM " +
      "JSON export, tunable via .cortex/config/swift_coverage.json), so a Swift repo with a " +
      "coverage threshold is measurable and the target is actionable. Select coverage " +
      "whenever source changed and the project defines a coverage threshold, regardless of " +
      "language. Omit coverage only when no source file changed (markdown_only), or when " +
      "you have positively established that no coverage number can be produced for this " +
      "project — and if you omit it, say which of those two applies in diagnosis_note. " +
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
  // AI: priorErrors is populated from the coverage pre-flight gate result so that quality
  // and tests agents receive known failures upfront, skipping their first gate call.
  let priorErrors = null;
  // AI: freshGateSummary is non-null ONLY when the Coverage phase obtained a
  // run_quality_gate() result that is still valid for the current working tree — i.e. the
  // phase ran, reported an explicit preflight verdict, and wrote NO files. Any file write
  // (new coverage tests) makes the result stale and this stays null, so the Quality loop
  // behaves exactly as it does today: it runs the gate itself. Same when Coverage is
  // skipped entirely (markdown_only scope, coverage not in targets).
  let freshGateSummary = null;

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
        "5. Build prior_errors: concatenate the first 20 lines from results.type_check.errors, " +
        "results.quality.errors, and results.tests.errors (each up to 20 lines, joined by newline). " +
        "Return prior_errors as a single string (null if gate passed or no errors). " +
        "6. Return that result as your schema output (status, final_coverage, tests_added, prior_errors, etc.). " +
        "7. Also return preflight_passed (the raw verdict of the pre-flight run_quality_gate()) " +
        "and files_written=true if you or @fix-coverage created or edited ANY file during this " +
        "phase (new tests, fixtures, source). If you are unsure, return files_written=true.",
      {
        agentType: "fix-coverage",
        schema: COVERAGE_SCHEMA
      }
    );

    // AI: priorErrors carries the raw gate output from the coverage pre-flight so quality
    // and tests agents can skip their first gate call — they already know what's failing.
    priorErrors = cov.prior_errors ?? null;

    // AI: Staleness rule decided in JS, not by the model. Reusable only when the agent
    // explicitly reported a PASSING pre-flight AND explicitly reported writing no files.
    // Anything else — undefined, null, false, unknown — falls through and re-runs the gate.
    // preflight_passed=false is excluded on purpose: a red verdict carries no actionable
    // detail on its own (that lives in priorErrors), so suppressing Quality's own gate call
    // on a red-but-clean tree would leave it blind.
    if (cov.preflight_passed === true && cov.files_written === false) {
      freshGateSummary =
        "preflight_passed=true" +
        (typeof cov.final_coverage === "number"
          ? `, coverage=${cov.final_coverage}`
          : "");
    } else {
      log(
        "Coverage: gate result not reusable (files written or verdict unreported) — " +
          "Quality will run its own gate."
      );
    }

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
          // AI: inject prior gate output so quality agent skips the first gate call when
          // the error set is already known from the coverage pre-flight. Re-run gate only
          // if autofix may have changed the error set (i.e., after applying fixes).
          (priorErrors
            ? `Prior gate output (skip re-running gate if these are the only failures — ` +
              `re-run after applying autofix):\n${priorErrors}\n`
            : "") +
          // AI: First iteration only, and only when the Coverage phase handed us a gate
          // result that is still valid for the current tree. run_quality_gate() takes
          // ~100s; this removes one guaranteed back-to-back duplicate run. Later
          // iterations always re-run the gate because fixes were applied in between.
          (iterations === 0 && freshGateSummary
            ? `A run_quality_gate() run just completed in the Coverage phase against this ` +
              `exact working tree, with no files written since: ${freshGateSummary}. ` +
              `Trust it for your initial assessment — do NOT call run_quality_gate() before ` +
              `making changes. You MUST still call run_quality_gate() after applying any ` +
              `fix, and before returning passed=true. `
            : "") +
          (diagnosis.change_scope === "markdown_only"
            ? "Path A (markdown_only): call autofix(), then run_quality_gate(). " +
              "Fix markdown lint errors manually per rule code. Retry (max 3 iterations). "
            : "Path B (source_changed/mixed): call autofix(), then run_quality_gate(). " +
              "Run CI parity scripts (check_file_sizes.py, check_function_lengths.py, build.py). " +
              "Fix type errors, file/function length violations, format issues inline. " +
              "Apply Post-fix validation (py_compile + import check) for Python files. " +
              "SWIFT: run_quality_gate()/autofix() do NOT cover .swift files. If any changed " +
              "file is .swift, you MUST additionally verify them natively via Bash: " +
              "`swift build 2>&1 | tail -40`, plus `swiftformat --lint .` and `swiftlint` " +
              "when those binaries are present. Fix reported errors at the named file:line. " +
              "Never report Swift as passing on the basis that the Cortex gate does not apply " +
              "to it — inapplicable is not passing. ") +
          "Return passed=true only when run_quality_gate() returns preflight_passed=true " +
          "AND all CI parity scripts exit 0 " +
          "AND (no .swift files changed OR `swift build` exited 0).",
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

  // AI: Deliberately NO gate reuse from Quality into Tests. The Tests gate is the last
  // verification before the tree is handed to commit, and the only evidence that Quality's
  // final gate is still valid would be that agent's own self-report about which files it
  // edited after its last gate call. A mis-report there turns tests_passed=true into an
  // unverified claim and lets a broken tree through; the downside is one ~100s gate run.
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
            // AI: inject prior gate output so tests agent skips the first gate call when
            // failing tests are already known from the coverage pre-flight. Re-run gate
            // only after applying fixes to confirm they resolved the failures.
            (priorErrors
              ? `Prior gate output (skip re-running gate if these are the only failures — ` +
                `re-run after applying fixes):\n${priorErrors}\n`
              : "") +
            "1. Call run_quality_gate() to get test results. " +
            "2. Choose branch based on tests_failed: " +
            "Branch A (tests_failed > 0): locate failing tests, debug root cause, " +
            "fix assertion mismatches or implementation bugs. " +
            "Branch B (tests_failed == 0, coverage only): out of scope — return " +
            "passed=true, branch='skipped' (coverage handled by @fix-coverage). " +
            "Branch C (tests_failed == 0, subprocess crash): read results.tests.output " +
            "for build errors and fix at reported line. " +
            "Branch D (Swift): run_quality_gate() does NOT run .swift tests. If any changed " +
            "file is .swift, you MUST run `swift test 2>&1 | tail -60` via Bash and debug " +
            "any failures at the reported file:line. Report the actual test/suite counts. " +
            "An inapplicable Cortex gate is not a passing test run. " +
            "Return passed=true when run_quality_gate() reports results.tests.success=true " +
            "AND (no .swift files changed OR `swift test` exited 0).",
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

