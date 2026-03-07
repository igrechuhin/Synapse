---
name: memory-bank-contract
description: Defines the strict write discipline for memory bank files. All orchestration prompts and agents must follow this contract to prevent inter-session corruption.
---

# Memory Bank Write Contract

The memory bank is the **sole inter-session continuity mechanism**. Corruption, truncation, or stale data breaks the entire Plan -> Work -> Review -> Compound loop. This contract is non-negotiable.

## Allowed Write Tools

Only these tools may modify memory bank files:

| Tool | Use Case |
|---|---|
| `manage_file(file_name="...", operation="write", content="...")` | General memory bank file writes |
| `add_roadmap_entry(...)` | Add new roadmap entries |
| `remove_roadmap_entry(...)` | Remove completed roadmap entries |
| `update_memory_bank(operation="...", ...)` | Structured memory bank updates |
| `plan(operation="register", ...)` | Register plans in roadmap |

## Forbidden Write Tools

**GATE**: These tools must NEVER be used on memory bank paths:

| Tool | Why Forbidden |
|---|---|
| `Write` / file write | Bypasses MCP validation and versioning |
| `Edit` / `StrReplace` / `ApplyPatch` | Partial edits risk truncation and corruption |
| Shell `echo >` / `sed` / `cat >` | No validation, no history |

## Post-Write Verification (GATE)

After every memory bank write to `roadmap.md`:

1. Re-read the file: `manage_file(file_name="roadmap.md", operation="read")`
2. Verify content length >= original content length (no truncation)
3. Verify the intended change is present
4. If verification fails, STOP and report corruption

For other memory bank files, post-write verification is CHECK (recommended but non-blocking).

## Content Integrity Rules

- **Never truncate**: New content must be >= length of original. Never pass shortened or summarized content.
- **Never overwrite with partial data**: If you read a file and modify it, write back the complete file.
- **Roadmap = future work only**: No completed work in roadmap.md.
- **ActiveContext = completed work only**: No in-progress or future work in activeContext.md.
- **No overlap**: Never duplicate the same work item in both roadmap and activeContext.

## Integrity Check (at session start)

The `common-checklist` agent verifies memory bank integrity before any session proceeds:

1. Each core file (roadmap.md, activeContext.md, progress.md) must be non-empty
2. Each core file must contain at least one markdown heading (`#`)
3. If any core file fails integrity check, report `status: "error"` with details
