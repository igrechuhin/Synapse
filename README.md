# Synapse: Shared Rules, Prompts, and Scripts

Synapse is a git submodule that provides shared development resources across projects.

## Architecture Overview

```text
.cortex/synapse/
├── prompts/           # Language-AGNOSTIC workflow definitions
│   ├── commit.md      # Commit procedure (uses scripts)
│   ├── review.md      # Code review procedure
│   └── ...
├── rules/             # Coding standards and guidelines
│   ├── general/       # Language-agnostic rules
│   ├── python/        # Python-specific rules
│   ├── markdown/      # Markdown formatting rules
│   └── ...
└── scripts/           # Language-SPECIFIC implementations
    └── python/        # Python scripts
        ├── check_formatting.py
        ├── check_linting.py
        ├── check_types.py
        └── ...
```

## Critical Architecture Principle

### Prompts are Language-AGNOSTIC

All prompts in `prompts/` directory MUST be language-agnostic:

- **DO NOT** hardcode language-specific commands (e.g., `ruff`, `black`, `prettier`)
- **DO NOT** reference language-specific paths directly
- **DO** use script references with `{language}` placeholder

**Example - CORRECT**:

```markdown
Run the formatting check:
`.venv/bin/python .cortex/synapse/scripts/{language}/check_formatting.py`
```

**Example - WRONG**:

```markdown
Run the formatting check:
`.venv/bin/black --check src/ tests/`
```

### Scripts are Language-SPECIFIC

Scripts in `scripts/{language}/` contain language-specific implementations:

- Each language has its own directory (e.g., `scripts/python/`, `scripts/typescript/`)
- Scripts auto-detect project structure and appropriate tools
- Scripts handle environment differences (.venv, uv, npm, etc.)
- Scripts match CI workflow behavior automatically

### Rules Can Be Either

Rules in `rules/` directory can be:

- **General** (`rules/general/`) - Language-agnostic standards
- **Language-specific** (`rules/python/`, `rules/typescript/`) - Language-specific guidelines

## Available Scripts (Python)

| Script | Purpose |
|--------|---------|
| `check_formatting.py` | Verify code formatting (black --check) |
| `fix_formatting.py` | Auto-fix formatting issues (black) |
| `check_linting.py` | Check for linting errors (ruff check) |
| `check_types.py` | Run type checker (pyright) |
| `check_file_sizes.py` | Verify files ≤ 400 lines |
| `check_function_lengths.py` | Verify functions ≤ 30 lines |
| `run_tests.py` | Run test suite with coverage |

## Adding Support for New Languages

To add support for a new language:

1. Create a directory: `scripts/{language}/`
2. Implement required scripts:
   - `check_formatting.py` - Format verification
   - `fix_formatting.py` - Format auto-fix
   - `check_linting.py` - Lint checking
   - `check_types.py` - Type checking (if applicable)
   - `check_file_sizes.py` - File size limits
   - `check_function_lengths.py` - Function length limits
   - `run_tests.py` - Test execution
3. Use shared utilities from `_utils.py` for common operations
4. Add language-specific rules in `rules/{language}/`

## Script Conventions

All scripts MUST:

1. **Auto-detect project root** - Work from any directory
2. **Auto-detect tools** - Find `.venv/bin/`, `uv run`, or system tools
3. **Auto-detect directories** - Find `src/`, `tests/`, etc.
4. **Return proper exit codes** - 0 for success, non-zero for failure
5. **Print clear output** - Use ✅/❌ indicators for pass/fail
6. **Be idempotent** - Safe to run multiple times

## Usage in Prompts

When writing prompts, always reference scripts generically:

```markdown
### Step 1: Check Formatting

Run the formatting check script:
`.venv/bin/python .cortex/synapse/scripts/{language}/check_formatting.py`

If formatting fails, run the fix script:
`.venv/bin/python .cortex/synapse/scripts/{language}/fix_formatting.py`
```

The agent executing the prompt will substitute `{language}` with the detected project language (e.g., `python`).
