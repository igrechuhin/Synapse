# Init Wiki

**PURPOSE**: Seed and maintain `.cortex/wiki/` for the attached project — a durable, interlinked knowledge base alongside the memory bank.

**CRITICAL**: Execute ALL steps below AUTOMATICALLY. Do NOT pause for confirmation unless a blocking ambiguity exists (for example conflicting doc roots). Start with Step 1 immediately.

## Clean Semantics

For `/cortex/init-wiki`, **clean** means **wiki-bootstrap-complete for this run**:

- `.cortex/wiki/` matches the normative layout (see `.cortex/wiki/schema.md` or bundled `src/cortex/wiki/default_wiki_schema.md`).
- Every discovered seed document has a corresponding wiki page (or a logged skip with reason).
- `index.md` lists all new or updated pages for this run.
- No source-code changes are required; this prompt may create and edit markdown under `.cortex/wiki/` only.

## Cursor Arg-Stripping Protocol

When the MCP bridge strips tool arguments, use zero-arg `session()`, `ingest()`, `manage_file()`, and `pipeline_handoff()` after writing routing plus payload to `.cortex/.session/current-task.json` as described in `/cortex/do` and `docs/api/tools.md`.

## Step 1: Session health and rules

1. Call `session()` to verify MCP health. If unhealthy, STOP.
2. Read `cortex://rules` (non-blocking if unavailable).

## Step 2: Discover seed documents

Scan the **attached project root** (not only the Cortex package) for existing documentation. Include at minimum:

- `README.md` at repo root (and `readme.md` if present)
- Everything under `docs/` when that directory exists
- Paths matching `**/adr/**/*.md`, `**/ADRs/**/*.md`, `**/*adr*.md` at shallow depth (cap breadth if the tree is huge — prefer top-level and `docs/` first)
- `CHANGELOG.md` / `CHANGES.md` when present
- Architecture or design markdown under `design/`, `architecture/`, or similar conventional folders

Build an ordered list: `{path, suggested_category}`. Map content to categories using `schema.md`:

- Product overview, glossary → `concepts`
- Modules, services, packages → `entities`
- ADRs and explicit design choices → `decisions`
- Pipelines, how-to-run, end-to-end flows → `workflows`

If no seed files exist, report that fact, ensure the wiki directory layout exists (Step 3), and STOP after updating `index.md` with a note — do not invent sources.

## Step 3: Ensure wiki directory layout

1. Read `.cortex/wiki/schema.md`. If it is missing, create the full layout per that document’s tree: `concepts/`, `entities/`, `decisions/`, `workflows/`, `sources/`, `analyses/`, plus `index.md` and `schema.md`.
2. Category folder names MUST match the schema (lowercase plural directory names).
3. Optional empty markers: keep existing `.gitkeep` files; do not delete user content.

**Normative reference implementation** (for humans and agents maintaining parity): `cortex.wiki.layout.ensure_default_wiki_layout` in the Cortex codebase — on-disk result should match what that helper would create.

## Step 4: Ingest raw snapshots and author wiki pages

For each seed document from Step 2:

### 4a. Store raw source

1. Call `ingest()` with the file path or text so the raw source is staged under the ingest pipeline (same primitive as `/cortex/ingest`).
2. Preserve returned identifiers (`source_path`, `title`, `slug`) for citations.

### 4b. Synthesize a wiki page

Adapt the spirit of **Step 4–5** in `.cortex/synapse/prompts/ingest.md`:

- Read the source body.
- Produce: one-paragraph abstract, key takeaways, links to sibling wiki pages when relevant, contradictions with existing wiki pages (or none), open questions.

### 4c. Write the wiki page file

Write markdown under `.cortex/wiki/{category}/` (not under `memory-bank/`):

- Filename: kebab-case from title, ASCII preferred, `.md` extension.
- Leading YAML frontmatter per `schema.md`: `title`, `category`, optional `tags`, `source_count`, `last_updated` (ISO date).

### 4d. Immutable `sources/`

If ingest does not yet copy raw bytes into `.cortex/wiki/sources/`, add an immutable snapshot file under `sources/` for this run (append-only): include provenance path, ingest date, and the raw or lightly-normalized text. Do not overwrite existing source snapshots; use a new filename if a collision occurs.

## Step 5: Rebuild `index.md`

1. Enumerate all wiki pages (all `*.md` under category directories; exclude `schema.md` and `index.md` themselves).
2. Rebuild the catalog table defined in `schema.md`:

   `| Page | Category | Summary | Sources |`

3. **Page** column: relative markdown link from `index.md` to each page.
4. **Summary**: one line per page.
5. **Sources**: path under `sources/` or external path / “ingest slug”.

## Step 6: Optional schema customization

If this project needs conventions beyond the default (extra frontmatter keys, naming rules), append a short “Local overrides” section to `schema.md`. Otherwise skip.

## Step 7: Final report

Return a concise markdown report:

- Wiki root path
- Layout: created vs skipped paths
- Seed files processed (path → wiki page link)
- `index.md` row count added or updated
- Suggested next actions (for example run `/cortex/ingest` for new URLs, or `/cortex/query` once pages exist)

## Verification checklist (self-check before exit)

- [ ] `schema.md` and `index.md` exist and are readable.
- [ ] At least one category directory contains a page when seed docs existed.
- [ ] Frontmatter on every new page includes `title` and `category`.
- [ ] `index.md` table references every new page.
