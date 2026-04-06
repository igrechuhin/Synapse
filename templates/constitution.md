# Project Constitution

<!-- AI: Template for per-project governance; teams replace placeholders and keep this under memory bank version control. -->

This document captures **immutable** architectural principles for this repository. Planning tools may flag plans that appear to conflict with these rules. Update `last_updated` in frontmatter when you change substance (not typos-only).

## Principles

<!-- List non-negotiable design rules: one bullet per principle. Use "No …" or "Must …" for clarity. -->

- No use of dynamically typed escape hatches where static types are required by project standards.
- Prefer small, composable units over large monoliths.
- Preserve backward compatibility for public MCP tool contracts unless versioned.

## Tech stack

<!-- Allowed languages, frameworks, and runtimes. -->

- Python 3.13+ with Pydantic v2 for structured data.
- Markdown for memory bank and plans; YAML only where schemas require it.

## Hard limits

<!-- Quantitative or procedural limits (line counts, timeouts, forbidden patterns). -->

- Functions stay within the project's line-count standards (see coding rules).
- No hardcoded secrets or credentials in source or memory bank.

## Compliance requirements

<!-- What planning and delivery must include (reviews, gates, docs). -->

- Plans reference real paths and avoid placeholder backlog when claiming completion.
- Breaking changes to agent-facing workflows require documentation updates in the same change.
