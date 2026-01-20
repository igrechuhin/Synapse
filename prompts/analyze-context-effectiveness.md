# Analyze Context Effectiveness

**AI EXECUTION COMMAND**: End-of-session analysis to evaluate `optimize_context` effectiveness and provide feedback for improvement.

**CRITICAL**: These steps are for the AI to execute AUTOMATICALLY at the end of a chat session. DO NOT ask the user for permission or confirmation. Execute immediately.

**CURSOR COMMAND**: This is a Cursor command located in `.cortex/synapse/prompts/` directory, NOT a terminal command.

**Purpose**: Analyze how effective the `optimize_context` tool was during this session by comparing what context was provided versus what was actually used. This feedback helps improve future context optimization.

## Core Goal

**Provide the most compact, optimal, and efficient context possible.**

Every token matters. The goal is to:

- Maximize relevance: Only include files that will actually be used
- Minimize waste: Exclude files that won't contribute to the task
- Ensure coverage: Don't miss files that are genuinely needed
- Optimize token budget: Get the best value from every token spent

## When to Use

Run this prompt at the end of ANY chat session to:

### If `optimize_context` WAS Used

- Evaluate context selection effectiveness
- Identify over-provisioning (unused files wasting tokens)
- Identify under-provisioning (missing needed files)
- Generate improvement suggestions
- Build a feedback dataset for optimization

### If `optimize_context` WAS NOT Used

- **Investigate why it wasn't used** - This is a missed optimization opportunity
- Analyze what context was loaded manually or automatically
- Determine if `optimize_context` would have helped
- Identify barriers to using `optimize_context`
- Recommend when to use it in similar future sessions

## Pre-Analysis Checklist

Before starting the analysis, determine which path to follow:

### Path A: optimize_context WAS Used

If `optimize_context` was called during the session, proceed to analyze its effectiveness.

### Path B: optimize_context WAS NOT Used

If `optimize_context` was NOT called, investigate:

1. **What context was loaded instead?**
   - Manual file reads?
   - Automatic context from IDE?
   - Memory bank files read directly?

2. **Why wasn't optimize_context used?**
   - Task seemed too simple?
   - Forgot it was available?
   - Didn't know when to use it?
   - Previous bad experience?

3. **Would optimize_context have helped?**
   - Were multiple files needed?
   - Was there uncertainty about which files to read?
   - Did the session involve exploring unfamiliar code?
   - Was context loading inefficient (reading files that weren't needed)?

4. **Recommendation for future sessions**
   - Should `optimize_context` be used for similar tasks?
   - What task description would have been appropriate?
   - What token budget would have been suitable?

**Skip to the "Path B Analysis" section below if optimize_context was not used.**

---

## Path A: Analyzing optimize_context Effectiveness

### 1. Recall optimize_context Calls

For each `optimize_context` call during the session, identify:

- **Task description** used
- **Files selected** (from `selected_files` in response)
- **Sections selected** (from `selected_sections` in response)
- **Relevance scores** (from `relevance_scores` in response)
- **Total tokens** provided
- **Excluded files** (files not selected)

### 2. Identify Session Activity

Recall what actually happened during the session:

- **Files read**: Which files were actually read/viewed?
- **Files modified**: Which files were edited or created?
- **Files mentioned**: Which files were discussed or referenced?
- **External files**: Were any files outside the provided context needed?

## Analysis Steps

### Step 1: Gather optimize_context Data

List all `optimize_context` calls made during the session:

```markdown
### optimize_context Call #1
- **Task**: [task description]
- **Selected Files**: [list of files]
- **Total Tokens**: [number]
- **Relevance Scores**:
  - file1.md: 0.85
  - file2.md: 0.72
  - ...
```

### Step 2: Analyze Actual Usage

For each optimize_context call, categorize files:

#### Files Actually Used

Files that were:

- Read and referenced in responses
- Modified or edited
- Used to inform decisions or code changes

#### Files Provided But Unused

Files that were:

- Selected by optimize_context
- Never read, referenced, or used
- Could have been excluded to save tokens

#### Files Needed But Missing

Files that were:

- NOT selected by optimize_context
- But were needed during the session
- Had to be read separately or caused gaps in context

### Step 3: Calculate Metrics

Calculate the following effectiveness metrics:

#### Precision (Relevance of Selection)

```
Precision = Files Used / Files Provided
```

- **1.0**: Perfect - every file provided was used
- **0.5**: Half the files were unused (over-provisioning)
- **< 0.3**: Significant over-provisioning

#### Recall (Coverage of Needs)

```
Recall = Files Used / (Files Used + Files Needed But Missing)
```

- **1.0**: Perfect - all needed files were provided
- **0.5**: Half the needed files were missing (under-provisioning)
- **< 0.5**: Significant under-provisioning

#### F1 Score (Balanced Effectiveness)

```
F1 = 2 * (Precision * Recall) / (Precision + Recall)
```

- **> 0.8**: Excellent context selection
- **0.5-0.8**: Good, room for improvement
- **< 0.5**: Needs significant improvement

#### Token Efficiency

```
Token Efficiency = Tokens in Used Files / Total Tokens Provided
```

- **> 0.7**: Efficient token usage
- **0.4-0.7**: Moderate efficiency
- **< 0.4**: Significant token waste

### Step 4: Determine Feedback Category

Based on metrics, categorize the overall effectiveness:

| Category | Criteria | Description |
|----------|----------|-------------|
| **Excellent** | F1 > 0.8, Efficiency > 0.7 | Context selection was highly effective |
| **Good** | F1 > 0.6, Efficiency > 0.5 | Good selection with minor improvements possible |
| **Over-provisioned** | Precision < 0.5 | Too many unused files provided |
| **Under-provisioned** | Recall < 0.5 | Missing important files |
| **Inefficient** | Efficiency < 0.4 | Poor token utilization |
| **Needs Improvement** | F1 < 0.5 | Significant issues with selection |

### Step 5: Generate Improvement Suggestions

Based on the analysis, provide specific suggestions:

#### For Over-provisioning

- Which file types were consistently unused?
- Should relevance threshold be increased?
- Are certain file categories less useful for this task type?

#### For Under-provisioning

- What types of files were missing?
- Were dependencies not followed?
- Should certain files be mandatory for this task type?

#### For Relevance Score Accuracy

- Did high-scored files get used more than low-scored?
- Were any low-scored files actually critical?
- Should scoring weights be adjusted?

---

## Path B Analysis: optimize_context Was NOT Used

If `optimize_context` was not called during this session, provide the following analysis:

### Step B1: Document Context Loading

What context was actually loaded during the session?

```markdown
### Context Loaded (Without optimize_context)

| File | How Loaded | Was It Needed | Tokens (est.) |
|------|------------|---------------|---------------|
| file1.md | Manual read | Yes | ~500 |
| file2.md | IDE auto-context | No | ~800 |
| file3.md | Manual read | Yes | ~300 |
```

### Step B2: Analyze Efficiency

Calculate informal efficiency metrics:

- **Files Read**: Total number of files loaded into context
- **Files Actually Needed**: Files that contributed to the task
- **Estimated Token Waste**: Tokens in files that weren't needed
- **Missing Context**: Files that should have been loaded but weren't

### Step B3: Evaluate optimize_context Opportunity

Would `optimize_context` have improved this session?

| Factor | Assessment |
|--------|------------|
| Multiple files needed? | Yes/No |
| Uncertainty about which files? | Yes/No |
| Token budget concerns? | Yes/No |
| Task complexity | Simple/Medium/Complex |
| **Recommendation** | Should/Could/Shouldn't have used optimize_context |

### Step B4: Generate Recommendations

If `optimize_context` should have been used:

1. **Suggested task description**: "[What task description would have worked]"
2. **Suggested token budget**: [number] tokens
3. **Suggested strategy**: [dependency_aware/priority/section_level/hybrid]
4. **Expected benefit**: [What improvement would have been achieved]

If `optimize_context` was correctly not used:

- Document why (e.g., "Single file task, no optimization needed")
- Note for future reference

---

## Output Format

Provide the analysis in the following structured format:

### Context Effectiveness Analysis Report

```markdown
## Session Summary

- **Date**: [YYYY-MM-DD]
- **optimize_context Used**: [Yes/No]
- **Total optimize_context Calls**: [number or N/A]
- **Overall Effectiveness**: [Excellent/Good/Needs Improvement/Not Applicable]

## Metrics Summary

| Metric | Value | Rating |
|--------|-------|--------|
| Precision | X.XX | [Good/Fair/Poor] |
| Recall | X.XX | [Good/Fair/Poor] |
| F1 Score | X.XX | [Good/Fair/Poor] |
| Token Efficiency | X.XX | [Good/Fair/Poor] |

## Detailed Analysis

### Files Provided vs Used

| File | Relevance Score | Was Used | Notes |
|------|-----------------|----------|-------|
| file1.md | 0.85 | Yes | Core reference |
| file2.md | 0.72 | No | Not relevant to task |
| ... | ... | ... | ... |

### Missing Files

| File | Why Needed | Impact |
|------|------------|--------|
| missing1.md | Contained required API | Had to read separately |
| ... | ... | ... |

## Feedback Category

**[Category]**: [Brief explanation]

## Improvement Suggestions

1. [Specific suggestion 1]
2. [Specific suggestion 2]
3. [Specific suggestion 3]

## Structured Feedback (for storage)

### If optimize_context WAS Used:

```json
{
  "session_date": "YYYY-MM-DD",
  "optimize_context_used": true,
  "task_descriptions": ["task1", "task2"],
  "metrics": {
    "precision": 0.XX,
    "recall": 0.XX,
    "f1_score": 0.XX,
    "token_efficiency": 0.XX
  },
  "feedback_category": "category",
  "files_analysis": {
    "provided": ["file1.md", "file2.md"],
    "used": ["file1.md"],
    "unused": ["file2.md"],
    "missing": ["file3.md"]
  },
  "suggestions": [
    "suggestion1",
    "suggestion2"
  ]
}
```

### If optimize_context WAS NOT Used:

```json
{
  "session_date": "YYYY-MM-DD",
  "optimize_context_used": false,
  "reason_not_used": "Task seemed simple / Forgot / Didn't know when to use",
  "context_loaded_manually": {
    "files_read": ["file1.md", "file2.md"],
    "estimated_tokens": 1500,
    "files_actually_needed": ["file1.md"],
    "estimated_waste_tokens": 800
  },
  "should_have_used_optimize_context": true,
  "recommended_task_description": "Suggested task description for future",
  "recommended_token_budget": 5000,
  "expected_benefit": "Would have saved ~800 tokens and included missing context",
  "suggestions": [
    "Use optimize_context for multi-file tasks",
    "Consider dependency_aware strategy for this task type"
  ]
}
```
```

## Storing Feedback (Optional)

If you want to store the feedback for future analysis:

1. **Use Cortex MCP tool** `manage_file` to append to feedback log:

```
manage_file(
  file_name="context-feedback-log.md",
  operation="write",
  content="[Append analysis report]",
  change_description="Added context effectiveness analysis for [date]"
)
```

2. **Or provide to user** for manual tracking

## Success Criteria

- [ ] All optimize_context calls identified and analyzed
- [ ] Metrics calculated accurately
- [ ] Feedback category determined
- [ ] Specific improvement suggestions provided
- [ ] Structured feedback generated for storage

## Notes

- This analysis relies on AI recall of the session, which may be approximate
- Focus on patterns rather than exact numbers
- The goal is continuous improvement toward **optimal context efficiency**
- Even rough feedback is valuable for identifying trends
- **Every unused token is a missed opportunity** for more relevant context
- **Every missing file is a potential gap** in understanding
- The ideal is: minimal tokens, maximum relevance, zero waste

## Example Analysis

### Example: Good Selection

```
Precision: 0.75 (3/4 files used)
Recall: 1.0 (all needed files provided)
F1: 0.86
Token Efficiency: 0.68

Category: Good
Suggestion: Consider excluding techContext.md for pure bug-fix tasks
```

### Example: Under-provisioned

```
Precision: 1.0 (all provided files used)
Recall: 0.5 (2/4 needed files provided)
F1: 0.67
Token Efficiency: 0.95

Category: Under-provisioned
Suggestion: Include dependency files when systemPatterns.md is selected
```

### Example: optimize_context Not Used (Should Have Been)

```
optimize_context Used: No
Files Read Manually: 5
Files Actually Needed: 2
Estimated Token Waste: ~2000 tokens

Reason Not Used: Forgot it was available
Should Have Used: Yes

Recommended Task Description: "Fix bug in user authentication flow"
Recommended Token Budget: 8000
Recommended Strategy: dependency_aware

Expected Benefit: Would have selected only 2 relevant files instead of 5,
saving ~2000 tokens and providing better focused context.

Suggestion: For debugging tasks, always start with optimize_context
to get targeted context instead of reading files manually.
```

### Example: optimize_context Not Used (Correctly)

```
optimize_context Used: No
Task Type: Single file edit (typo fix)
Files Needed: 1

Should Have Used: No - Task was too simple
Reason: Single file task with clear scope, no context optimization needed.

Note: optimize_context adds overhead for simple tasks.
Use it when multiple files or uncertain scope is involved.
```
