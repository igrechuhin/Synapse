# Roadmap Page

**AI EXECUTION COMMAND**: Publish or refresh the visual roadmap artifact so the operator can see
the current plan as a page rather than as a markdown backlog.

`.cortex/memory-bank/roadmap.md` is the single source of truth. This command **renders** it; it
never invents work, never reorders phases, and never records a status the roadmap does not state.
If the page and the roadmap disagree, the roadmap is right and the page is stale.

## When this runs

- On demand, when the operator invokes it.
- Automatically at the end of `/cortex/plan`, `/cortex/commit`, and `/cortex/fix`, because each of
  those can change the roadmap and a page that silently drifts is worse than no page.

## State

The published artifact's URL lives in `.cortex/roadmap-page.json`:

```json
{ "url": "https://claude.ai/code/artifact/<id>", "updated": "YYYY-MM-DD" }
```

**This file is what keeps the link stable.** Publishing without the stored URL creates a *second*
artifact, so the operator's bookmark silently stops updating. Always read it first.

## Steps

1. **Read the state file** `.cortex/roadmap-page.json`. Absent or unreadable → first publish.
2. **Read `.cortex/memory-bank/roadmap.md` in full.** Also read `.cortex/memory-bank/progress.md`
   for the few most recent entries, so the page can state what changed since the last publish.
3. **If a URL is stored, read the live artifact first** (`Artifact` with `action: "read"` and that
   `url`). A publish to an artifact this conversation has not read is refused, and the live version
   may carry edits made elsewhere.
4. **Load the `artifact-design` skill** before writing any HTML. Then write the page to a file.
   Content requirements, in this order:
   - **Where we are**: what runs in production, what is built but unexercised, what is broken.
     Sourced from the roadmap and progress, not from memory of an earlier session.
   - **The blocking item**, stated as a mechanism with its measured evidence — the number, the
     file or host it came from, and the date. A blocker without a measurement behind it is a
     guess and must be labelled as one.
   - **The phase sequence** with each phase's exit gate, and which phases run in parallel.
   - **What the operator must decide or authorize**, separated from what the agent will do alone.
5. **Publish.**
   - No stored URL → `Artifact` with `file_path`, a `favicon`, and a one-sentence `description`.
     Then write the returned URL into `.cortex/roadmap-page.json`.
   - Stored URL → `Artifact` with `file_path` **and** `url` set to the stored value, which
     redeploys in place and keeps the operator's link working. Do not pass `favicon` on a
     redeploy; the artifact keeps the icon it has.
6. **Report the URL** in one line, plus one line naming what changed since the last publish.

## Rules

- **Never fabricate progress.** A phase is complete only when the roadmap says so. Do not infer
  completion from a commit, a passing gate, or an earlier conversation.
- **Distinguish measured from assumed.** Durations in particular: this project's own history
  records estimates wrong by four to eight times, so label them unmeasured rather than presenting
  them as fact.
- **Keep the title stable** across redeploys — it is how the operator finds the page in a gallery.
- **Do not skip the design pass** because it is a routine refresh. The page is read by a person
  making decisions with money at stake; a wall of unstyled text fails that job.
- If `.cortex/memory-bank/roadmap.md` has no phase structure, render its own sections faithfully
  rather than imposing phases it does not have.

## Failure handling

- Publish refused as a conflict → the artifact changed elsewhere. Re-read it, merge the roadmap's
  content onto the live version, publish again. Never pass `force`.
- Artifact tool unavailable → report that plainly and stop. Do not write the page to a file and
  claim it was published.
- State file present but its URL 404s → treat as a first publish, overwrite the state file, and say
  so, since a stale id would otherwise fail every future refresh.
