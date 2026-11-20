/**
 * Explicit read-only-to-Git (no commit or push) staged-final pilot.
 * The ordinary commit.wf.js remains the default entry point.
 */

export const meta = {
  name: "cortex-staged-final-pilot",
  description: "Prepare, fully test, and verify an exact staged Swift tree without publishing",
  phases: [
    {
      title: "Staged-final dry run",
      detail: "one MCP owner for preparation, full quality, and exact-tree verification"
    }
  ]
};

phase("Staged-final dry run");
const result = await agent(
  "Read .cortex/synapse/prompts/staged-final-pilot.md and follow it precisely. " +
    "First read project quality configuration and require staged_final_swiftpm_commit true; " +
    "never enable it or switch to the legacy workflow. Keep one native MCP owner throughout. " +
    "Do not create a Git commit or push anything. Return the exact blocker if any guard fails.",
  {
    schema: {
      type: "object",
      properties: {
        verified: { type: "boolean" },
        staged_tree: { type: "string" },
        error: { type: "string" }
      },
      required: ["verified"]
    }
  }
);

return { success: result?.verified === true, dry_run: true, result };
