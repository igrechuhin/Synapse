# Ingest

Execute this workflow to ingest an external source into the Cortex memory bank.

## Step 1: Receive source

Collect the ingest input from the user (`/cortex/ingest <path-or-text>`), then decide whether the source type is:

- `markdown_file` for a local markdown path
- `text` for raw text content
- `url` for URL content when available

## Step 2: Store raw source

Call `ingest()` with source type, content, and a human-readable title. Save the returned `IngestJob` fields (`source_path`, `title`, `slug`) for downstream steps.

## Step 3: Read and discuss

Read the source content and produce 2-5 key takeaways. Share a short synthesis with the user and ask for steering notes before filing.

## Step 4: Read context

Read `cortex://context` and identify which memory-bank pages are relevant (for example `techContext.md`, `systemPatterns.md`, `projectBrief.md`, or other active pages).

## Step 5: Write summary page

Create an artifact summary with:

- One-paragraph abstract
- Key takeaways
- Links to related memory-bank pages
- Explicit contradiction notes with existing context
- Open questions and knowledge gaps

Use:

`manage_file(operation="file_artifact", artifact_type="query_result", title="{title} — Ingest Summary", content="...")`

## Step 6: Update existing pages

Append concise cross-reference notes to each relevant existing memory-bank page identified in Step 4 using `manage_file`.

## Step 7: Log ingest operation

Append an ingest operation record:

`update_memory_bank(operation="log_append", operation_type="ingest", title="{title}")`

## Step 8: Report output

Return a concise report that includes:

- Source stored at path
- Summary page path
- Existing pages updated
- Contradictions found (or none)
