# Analyze Context Effectiveness

**AI EXECUTION COMMAND**: Analyze `load_context` effectiveness for the current session.

**CRITICAL**: Execute this automatically. DO NOT ask user for permission.

**Agent Delegation**: This prompt delegates to the **`context-effectiveness-analyzer` agent** (Synapse agents directory) for specialized context analysis.

## Purpose

Analyze the current session's `load_context` (and optionally `load_progressive_context`) calls to evaluate effectiveness, provide structured feedback, and update global statistics for future optimization.

## Pre-Analysis Checklist

**BEFORE running the tool or manual analysis:**

1. **Recall `load_context` / `load_progressive_context` calls** from this session:
   - Task descriptions used
   - Files and sections selected
   - Relevance scores returned
   - Token budget and utilization
2. **Identify what context was actually used** during the session (for manual analysis fallback):
   - Files read (Read tool or equivalent)
   - Files modified (Write / StrReplace / ApplyPatch)
   - Files mentioned in conversation or decisions
   - Files needed but not provided (gaps you had to fetch separately)
   - Files provided but unused (included in context but not used)

## Execution Steps

### Step 1: Run Analysis Tool

Call the `analyze_context_effectiveness` MCP tool:

```python
analyze_context_effectiveness()
```

This tool will:

- Read the current session log from the session directory (path resolved by the tool; e.g. context-session-{session_id}.json)
- Analyze each `load_context` call made in THIS session
- Update global statistics in the session directory (e.g. context-usage-statistics.json)
- Return current session analysis and statistics update status

### Step 2: Review Results

The tool returns:

```json
{
  "status": "success",
  "session_id": "abc123def456",
  "current_session": {
    "calls_analyzed": 3,
    "statistics": {
      "calls_count": 3,
      "avg_token_utilization": 0.45,
      "avg_files_selected": 4.0,
      "avg_relevance_score": 0.78,
      "task_patterns": {
        "fix/debug": 2,
        "implement/add": 1
      }
    },
    "entries": [...]
  },
  "global_statistics_updated": true,
  "new_entries_added": 3,
  "total_sessions": 10,
  "total_entries": 45
}
```

### Step 3: Get Global Statistics (Optional)

For historical statistics across all sessions, call:

```python
get_context_usage_statistics()
```

This returns aggregated statistics and recent entries from all sessions.

To analyze ALL historical sessions (not just current), use:

```python
analyze_context_effectiveness(analyze_all_sessions=True)
```

### Step 4: Report Findings

Based on the statistics, provide insights:

#### Token Utilization Analysis

| Utilization | Interpretation |
|-------------|----------------|
| > 0.8 | Efficient - budget well matched to needs |
| 0.5 - 0.8 | Good - some room for optimization |
| < 0.5 | Low - consider smaller token budgets |

#### Relevance Score Analysis

| Avg Score | Interpretation |
|-----------|----------------|
| > 0.7 | Excellent - files are highly relevant |
| 0.5 - 0.7 | Good - most files are relevant |
| < 0.5 | Needs improvement - many irrelevant files |

#### Task Pattern Insights

Identify which task types:

- Use `load_context` most frequently
- Have highest/lowest relevance scores
- Benefit most from context loading

## Output Format

Provide a brief summary:

```markdown
## Context Effectiveness Analysis

**Sessions Analyzed**: X new, Y total
**Calls Analyzed**: Z

### Key Metrics

- **Avg Token Utilization**: X% [Good/Needs Improvement]
- **Avg Files Selected**: X files
- **Avg Relevance Score**: X [Excellent/Good/Needs Improvement]

### Task Patterns

Most common: [pattern] (X calls)

### Recommendations

1. [Specific recommendation based on data]
2. [Specific recommendation based on data]
```

## When No Data or Qualitative Feedback

If the tool returns `"status": "no_data"` or you need qualitative feedback beyond tool statistics, perform **manual analysis** using session recall:

### Usage Analysis

- **Files used**: From Pre-Analysis Checklist — files read, modified, or mentioned.
- **Files needed but missing**: Files you had to load separately because they were not in `load_context` output.
- **Files provided but unused**: Files in `selected_files` that you did not use.

### Scoring Metrics (Manual)

When computing manually:

- **Precision**: `files_used / files_provided` (higher = less waste)
- **Recall**: `files_used / (files_used + files_needed_but_missing)` (higher = better coverage)
- **F1 Score**: `2 * (precision * recall) / (precision + recall)`
- **Token Efficiency**: `useful_tokens_estimate / total_tokens_provided` (estimate useful tokens from files actually used)
- **Relevance Accuracy**: Whether high relevance scores correlated with files actually used

### Feedback Categories

Classify the context run as one or more of:

| Category | Meaning |
|----------|--------|
| `helpful` | Context was well-selected |
| `over_provisioned` | Too many files provided |
| `under_provisioned` | Missing important files |
| `irrelevant` | Provided files that weren't useful |
| `missed_dependencies` | Didn't include related files |

### Structured Feedback (Manual Output)

When doing manual analysis, output a structured summary that matches the feedback schema (for future storage):

- **provided_files**: List of files `load_context` returned
- **files_read / files_modified / files_mentioned**: What was actually used
- **files_needed_but_missing**: Gaps
- **files_provided_but_unused**: Waste
- **precision, recall, f1_score, token_efficiency**: As above
- **feedback_type**: One of the categories above
- **suggestions**: Short actionable recommendations (e.g. "Include techContext.md for implementation tasks")

If the tool returns `"status": "no_data"` and you do not perform manual analysis:

```markdown
## Context Effectiveness Analysis

**No session logs found.**

To generate data:
1. Use `load_context()` at the start of tasks
2. Complete several sessions
3. Run this analysis again
```

## Data Files

- **Session logs**: Session directory, file pattern `context-session-{session_id}.json` (path resolved by the tool or via `get_structure_info()` if available)
- **Statistics**: Session directory, file `context-usage-statistics.json`

Each session log contains:

```json
{
  "session_id": "abc123def456",
  "session_start": "2026-01-21T10:30",
  "load_context_calls": [
    {
      "timestamp": "2026-01-21T10:35",
      "task_description": "Fix security vulnerabilities",
      "token_budget": 50000,
      "strategy": "dependency_aware",
      "selected_files": ["activeContext.md", "roadmap.md"],
      "selected_sections": {},
      "total_tokens": 3500,
      "utilization": 0.07,
      "excluded_files": ["techContext.md"],
      "relevance_scores": {
        "activeContext.md": 0.85,
        "roadmap.md": 0.72
      }
    }
  ]
}
```

## Feedback Schema (For Future MCP Tool)

When a future `record_context_feedback` tool exists, feedback records will follow this shape (documentation only; no tool yet):

- **session_id**: Unique session identifier
- **timestamp**: ISO format (YYYY-MM-DDTHH:MM)
- **task_description**: What task was being performed
- **provided_files**, **provided_sections**, **relevance_scores**, **total_tokens_provided**: What `load_context` provided
- **files_read**, **files_modified**, **files_mentioned**: What was actually used
- **files_needed_but_missing**, **files_provided_but_unused**: Gaps and waste
- **precision**, **recall**, **f1_score**, **token_efficiency**: Scoring metrics
- **feedback_type**: One of `helpful`, `over_provisioned`, `under_provisioned`, `irrelevant`, `missed_dependencies`
- **suggestions**: List of actionable recommendations; **comment**: Optional free text

## Future Optimization

Statistics collected here will be used to:

1. **Tune relevance scoring** - Improve file selection accuracy
2. **Optimize token budgets** - Suggest appropriate budgets per task type
3. **Identify patterns** - Learn which files are needed for which tasks
4. **Reduce waste** - Minimize unused context tokens
