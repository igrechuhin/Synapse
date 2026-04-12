# Ask

**PURPOSE**: Answer questions about the attached project using the **`.cortex/wiki/`** knowledge base — grounded in wiki pages, not guesses.

**CRITICAL**: Execute ALL steps below AUTOMATICALLY. Do NOT pause for confirmation unless the user question is empty, ambiguous in a way that changes scope, or the wiki cannot satisfy the request. Start with Step 1 immediately.

## Clean Semantics

For `/cortex/ask`, **clean** means **answer-complete for this run**:

- The answer is grounded in wiki pages you actually read this run (titles and paths cited).
- If the wiki is empty or missing needed topics, you say so plainly and name the smallest next action (for example seeding the wiki), without inventing project facts.
- Optional filing of a synthesized wiki page happens only after explicit user confirmation (Step 7).

## Preconditions

1. If `.cortex/wiki/` does not exist, stop after a one-line explanation: attach Cortex / ensure `.cortex/` exists, then run the wiki bootstrap workflow described in `.cortex/wiki/schema.md` (or the project plan for the wiki feature).
2. If `index.md` exists but lists no content pages yet, report that the catalog is empty and point to the wiki init workflow; do not fabricate page summaries.

## Cursor Arg-Stripping Protocol

When the MCP bridge strips tool arguments, use zero-arg `session()` after writing routing plus payload to `.cortex/.session/current-task.json` as described in `/cortex/do` and `docs/api/tools.md`.

## Step 1: Session health and rules

1. Call `session()` to verify MCP health. If unhealthy, STOP.
2. Read `cortex://rules` (non-blocking if unavailable).

## Step 2: Receive the question

Take the user text after `/cortex/ask` as the **question**. If it is empty, ask for one concrete question and STOP.

## Step 3: Read the wiki catalog

1. Read `.cortex/wiki/index.md` (the content-oriented catalog).
2. Read `.cortex/wiki/schema.md` when you need category conventions, frontmatter fields, or path rules.

## Step 4: Select relevant pages

Using only what appears in `index.md` (titles, summaries, categories):

1. Shortlist the **3–5** pages most likely to answer the question.
2. If fewer than three plausibly apply, use all that plausibly apply.
3. Record each choice as `{relative_path, one-line reason}` for the final report.

## Step 5: Read selected pages

Open each shortlisted `.md` file under `.cortex/wiki/` (skip `index.md` and `schema.md` themselves unless they are the only relevant sources). Read enough of the body to answer faithfully.

## Step 6: Synthesize the answer

Produce an answer that:

1. **Cites sources**: For every non-trivial claim, point to a wiki page path or title (markdown links relative to the wiki root are fine).
2. **Separates evidence from inference**: Label speculation or gaps explicitly.
3. **Handles conflicts**: If two pages disagree, quote or paraphrase both and state the conflict; do not silently pick one.
4. **Stays concise**: Prefer short sections with bullets when the question is narrow.

## Step 7: Optional — file a new wiki page

If the answer is **novel synthesis** (new narrative not already captured as a single page) and would help future sessions:

1. Offer one sentence: user may confirm to file it.
2. If and only if the user explicitly confirms, write a new markdown page under the appropriate `.cortex/wiki/{category}/` per `schema.md`, with correct frontmatter, and append or rebuild `index.md` so the new page appears in the catalog.
3. If the user declines or does not respond in this turn, skip filing — the run is still **clean**.

## Step 8: Report

Return a compact report:

- **Question** (one line)
- **Pages read** (paths)
- **Answer** (with citations)
- **Gaps** (what the wiki did not cover, if any)
- **Next** (optional one-line suggestion: init wiki, ingest a source, or none)
