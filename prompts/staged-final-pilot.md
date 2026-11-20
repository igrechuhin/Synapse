# Staged-final Swift commit

The diagnostic dry run creates no Git commit and pushes nothing. A real commit
requires an explicit staged-final commit request and the standard commit
authorization. The default two-gate workflow remains unchanged.

A native server may be opted in for one invocation by launching it with
`CORTEX_STAGED_FINAL_SWIFTPM_PROJECT` equal to the exact canonical project root.
Check the effective configuration via the MCP tool; do not write tracked
project configuration just to run a local pilot.

1. Keep one uninterrupted native Cortex MCP connection from checkpoint through
   final verification. Run Preflight from `commit.md` except Synapse pre-stage:
   require the existing Synapse gitlink to be unchanged, the checked-out
   Synapse tree clean and matching the link, and the link already on its remote.
   If any condition cannot be verified, stop without editing Synapse.
2. Run staged wiki ingest, local documentation preparation, docs validation
   and Phase C validation from `commit.md` with normal failure handling.
   Do not commit or push Synapse. Do not write a Phase A checks result.
3. Apply all Step 13 scope, sensitive-file and selective staging rules,
   including temporal memory staging. Write the commit message as text only.
   All formatting, normalization and source/index writes end here.
4. Write the `checks` task with `gate_intent: "staged-final"` for this commit
   run, with no test filter. Call `run_quality_gate()` and poll the same
   running job without edits. The trusted server runs the full checks,
   including applicable CI parity, against the frozen candidate. Require
   status success and `staged_final_authorized: true`. Switch the same task
   intent to `verify-staged-final`, invoke the tool on the same native
   connection and require the same authorization.
5. For a dry run, report the verified staged candidate and stop without a
   commit or push. For an explicitly authorized commit, set the same
   `checks` task's `gate_intent` to `"commit-staged-final"` and provide
   `commit_message`. Call `run_quality_gate()` on the same connection. Require
   returned `commit_sha` and `committed_tree` and verify them with Git.
   The server commits through normal Git hooks with an atomic reference guard;
   do not invoke a separate `git commit`. Push only when separately authorized.
6. Use standard cleanup. Never reuse a previous receipt or skip a guard.
   Report any blocker with the checkpoint reference and preserve working changes.
