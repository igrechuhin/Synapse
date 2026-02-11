## Docs & Memory Bank Sync (Helper Command)

**AI EXECUTION COMMAND**: Synchronize documentation and memory bank state using Cortex MCP tools, without running the full commit pipeline. This command is typically called when `/cortex/commit` or `run_docs_and_memory_bank_sync` reports Phase B failures (timestamps or roadmap/memory-bank sync issues).

**CURSOR COMMAND**: This is a Cursor command from the Synapse prompts directory, NOT a terminal command.

### Goals

- Fix discrepancies between roadmap, activeContext, progress, and plans.
- Resolve timestamp and sync validation issues.
- Avoid running tests or performing git operations.

### Tooling Requirements (MANDATORY)

- Prefer these Cortex MCP tools:
  - `run_docs_and_memory_bank_sync()` for aggregated docs/memory validation.
  - `validate(check_type="timestamps")` and `validate(check_type="roadmap_sync")` when deeper inspection is needed.
  - `manage_file()` for reading/writing memory bank and roadmap files via Cortex MCP.
- Use `get_structure_info()` for resolving paths; do **not** hardcode `.cortex/` paths.

### Pre-Action Checklist

Before making changes, you MUST:

1. ✅ **Get structure information**
   - Call `get_structure_info()` to obtain:
     - `structure_info.paths.memory_bank`
     - `structure_info.paths.plans`
   - Use these paths when reading/writing docs and memory-bank files; do **not** hardcode locations.

2. ✅ **Load relevant memory bank files**
   - Use `manage_file()` to read:
     - `roadmap.md`
     - `activeContext.md`
     - `progress.md`
     - `projectBrief.md` and `systemPatterns.md` if needed for context.

3. ✅ **Understand validation failures**

   - If available, inspect the most recent `run_docs_and_memory_bank_sync` result to see:
     - Which checks failed (`timestamps`, `roadmap_sync`, etc.).
     - Any detailed error information included in the response.
   - If no recent result is available, call:
     - `run_docs_and_memory_bank_sync()` and inspect its structured response.

### Execution Steps

1. **Analyze roadmap and plans**
   - Cross-check `roadmap.md` entries against plan files in the plans directory:
     - For each PLANNED or IN PROGRESS item, ensure the referenced plan file exists.
     - Identify any roadmap entries pointing to missing or renamed plans.
   - Plan actions:
     - Create missing plan stubs when roadmap references exist without corresponding files.
     - Update roadmap entries when plans have been completed or moved.

2. **Align activeContext and progress**
   - Ensure that:
     - Completed work is summarized in `activeContext.md` (not future work).
     - Ongoing and future work is recorded in `roadmap.md`.
     - `progress.md` reflects recent achievements linked to plans and roadmap entries.
   - Use `manage_file()` to apply edits, following the project’s memory bank workflow rules.

3. **Fix timestamp and sync issues**
   - Use `validate(check_type="timestamps")` and `validate(check_type="roadmap_sync")` to:
     - Identify mismatched timestamps between roadmap entries and memory bank files.
     - Detect invalid or dangling references.
   - Apply targeted fixes:
     - Update timestamps where work has been completed.
     - Correct or remove invalid references.
     - Ensure entries are in the correct sections and order as required by the project rules.

4. **Re-run docs & memory sync helper**
   - After applying fixes, call `run_docs_and_memory_bank_sync()` again.
   - Confirm that:
     - `status="success"`.
     - `docs_phase_passed` is `True`.
     - Any remaining issues are non-blocking and clearly understood.

5. **Summarize outcomes**
   - Describe the specific docs/memory fixes applied:
     - Roadmap entry corrections.
     - New or updated plan stubs.
     - activeContext/progress updates.
     - Timestamp corrections.
   - Note any follow-up improvements that should be tracked as new plans or roadmap entries.

### Failure Handling

- If sync issues cannot be fully resolved within this command:
  - Clearly explain what remains inconsistent and why.
  - Suggest creating or updating a plan to track more complex memory bank restructuring work.
- Do **not** run tests or git operations here; `/cortex/commit` is responsible for the full commit pipeline and Phase C.
