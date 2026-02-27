#!/usr/bin/env python3
"""Audit MCP tool docstrings against the altitude rubric.

Checks that each @mcp.tool-decorated function has:
- Purpose (first sentence)
- USE WHEN
- Input expectations (Args)
- RETURNS
- Examples (optional, for score 5)

Scoring (per docs/guides/tool-description-altitude-rubric.md):
- 1-2: Missing multiple criteria
- 3: Purpose and params clear; missing when-to-use, examples, or output
- 4: Purpose, USE WHEN, Args, RETURNS present; may lack examples
- 5: Same as 4, plus EXAMPLES/Example/input_examples

Target: All tools >= 4; 20+ tools with examples (score 5).
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path
from typing import NamedTuple

try:
    from _utils import find_src_directory, get_project_root
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from _utils import find_src_directory, get_project_root


class ToolScore(NamedTuple):
    """Score and criteria for a single tool."""

    module: str
    name: str
    score: int
    has_purpose: bool
    has_use_when: bool
    has_args: bool
    has_returns: bool
    has_examples: bool
    gaps: list[str]


def _has_mcp_tool_decorator(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return True if node is decorated with @mcp.tool."""
    for d in node.decorator_list:
        if isinstance(d, ast.Call):
            if isinstance(d.func, ast.Attribute):
                if getattr(d.func.value, "id", None) == "mcp" and d.func.attr == "tool":
                    return True
        elif isinstance(d, ast.Attribute):
            if getattr(d.value, "id", None) == "mcp" and d.attr == "tool":
                return True
    return False


def _get_docstring(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Extract docstring from function node."""
    if not node.body:
        return ""
    first = node.body[0]
    if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
        if isinstance(first.value.value, str):
            return first.value.value.strip()
    return ""


def _score_docstring(doc: str, module: str, name: str) -> ToolScore:
    """Score a docstring against the altitude rubric."""
    doc_lower = doc.lower()
    gaps: list[str] = []

    has_purpose = bool(doc.strip() and len(doc.split()) >= 5)
    if not has_purpose:
        gaps.append("Purpose (first sentence too short or missing)")

    has_use_when = "use when" in doc_lower
    if not has_use_when:
        gaps.append("USE WHEN")

    has_args = (
        "args:" in doc_lower or "parameters:" in doc_lower or "arguments:" in doc_lower
    )
    if not has_args:
        gaps.append("Input expectations (Args)")

    has_returns = "returns:" in doc_lower or "return:" in doc_lower
    if not has_returns:
        gaps.append("RETURNS")

    has_examples = bool(
        re.search(r"\bexample(s)?\s*[:(]", doc_lower, re.IGNORECASE)
        or "input_examples" in doc
        or ">>>" in doc
    )
    if not has_examples:
        gaps.append("Examples")

    # Compute score
    core_count = sum([has_purpose, has_use_when, has_args, has_returns])
    if core_count < 4:
        score = max(1, core_count)
    elif not has_examples:
        score = 4
    else:
        score = 5

    return ToolScore(
        module=module,
        name=name,
        score=score,
        has_purpose=has_purpose,
        has_use_when=has_use_when,
        has_args=has_args,
        has_returns=has_returns,
        has_examples=has_examples,
        gaps=gaps,
    )


def _resolve_doc_overrides(tree: ast.Module, path: Path) -> dict[str, str]:
    """Resolve func.__doc__ = CONST assignments to actual docstrings."""
    # Map: constant_name -> docstring value (from same file or imported module)
    constants: dict[str, str] = {}
    # Map: func_name -> constant_name from __doc__ assignments
    overrides: dict[str, str] = {}

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute):
                    if target.attr == "__doc__" and isinstance(target.value, ast.Name):
                        func_name = target.value.id
                        if isinstance(node.value, ast.Name):
                            overrides[func_name] = node.value.id
                elif isinstance(target, ast.Name):
                    if isinstance(node.value, ast.Constant) and isinstance(
                        node.value.value, str
                    ):
                        constants[target.id] = node.value.value

    # Resolve overrides via imports (same-package imports)
    imports: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            if node.module and "phase8_structure_docs" in node.module:
                for alias in node.names:
                    if alias.name:
                        imports[alias.name] = alias.name

    # Load constants from phase8_structure_docs if imported
    if imports:
        docs_path = path.parent / "phase8_structure_docs.py"
        if docs_path.exists():
            try:
                docs_tree = ast.parse(docs_path.read_text(encoding="utf-8"))
                for n in docs_tree.body:
                    if (
                        isinstance(n, ast.Assign)
                        and len(n.targets) == 1
                        and isinstance(n.targets[0], ast.Name)
                        and isinstance(n.value, ast.Constant)
                        and isinstance(n.value.value, str)
                    ):
                        constants[n.targets[0].id] = n.value.value
            except Exception:
                pass

    result: dict[str, str] = {}
    for func_name, const_name in overrides.items():
        if const_name in constants:
            result[func_name] = constants[const_name]
    return result


def _find_tools_in_file(path: Path, project_root: Path) -> list[ToolScore]:
    """Find @mcp.tool functions in a file and score their docstrings."""
    try:
        source = path.read_text(encoding="utf-8")
    except Exception:
        return []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    rel = path.relative_to(project_root)
    module = str(rel).replace("/", ".").replace("\\", ".").replace(".py", "")

    doc_overrides = _resolve_doc_overrides(tree, path)

    scores: list[ToolScore] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if _has_mcp_tool_decorator(node):
                doc = doc_overrides.get(node.name) or _get_docstring(node)
                scores.append(_score_docstring(doc, module, node.name))
    return scores


def main() -> int:
    """Run altitude audit on all MCP tools."""
    script_path = Path(__file__).resolve()
    project_root = get_project_root(script_path)
    src_dir = find_src_directory(project_root)
    tools_dir = src_dir / "cortex" / "tools"

    if not tools_dir.exists():
        print(f"Tools directory not found: {tools_dir}", file=sys.stderr)
        return 1

    all_scores: list[ToolScore] = []
    for py in sorted(tools_dir.rglob("*.py")):
        all_scores.extend(_find_tools_in_file(py, project_root))

    below_4 = [s for s in all_scores if s.score < 4]
    with_examples = [s for s in all_scores if s.has_examples]
    score_5 = [s for s in all_scores if s.score == 5]

    print("=" * 60)
    print("Tool Description Altitude Audit")
    print("Per docs/guides/tool-description-altitude-rubric.md")
    print("=" * 60)
    print(f"Total tools: {len(all_scores)}")
    print(f"Score 5 (with examples): {len(score_5)}")
    print(f"Score 4: {len([s for s in all_scores if s.score == 4])}")
    print(f"Below 4: {len(below_4)}")
    print()

    if below_4:
        print("Tools below score 4:")
        for s in sorted(below_4, key=lambda x: (x.score, x.module, x.name)):
            print(f"  [{s.score}] {s.module}.{s.name}")
            for g in s.gaps:
                print(f"       Missing: {g}")
        print()

    if len(with_examples) < 20:
        print(f"Warning: Only {len(with_examples)} tools have examples (target: 20+)")
        print()

    # Target check
    ok = len(below_4) == 0 and len(with_examples) >= 20
    if ok:
        print("Targets met: All tools >= 4, 20+ with examples")
    else:
        print("Targets not met: Fix tools below 4 and/or add examples to reach 20+")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
