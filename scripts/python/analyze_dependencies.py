#!/usr/bin/env python3
"""Analyze module dependencies and detect circular references.

This script analyzes Python module dependencies and detects circular
references. It works with any Python project structure.

Configuration:
    SRC_DIR: Source directory path (default: auto-detected)
    PACKAGE_NAME: Package name to analyze (default: auto-detected from src structure)
"""

import ast
import os
import sys
from collections import defaultdict
from pathlib import Path

# Import shared utilities
try:
    from _utils import find_src_directory, get_config_path, get_project_root
except ImportError:
    # Fallback if running from different location
    sys.path.insert(0, str(Path(__file__).parent))
    from _utils import find_src_directory, get_config_path, get_project_root


def detect_package_name(src_dir: Path) -> str:
    """Detect the main package name from source directory structure.

    Args:
        src_dir: Source directory path

    Returns:
        Package name (e.g., 'cortex', 'myapp')
    """
    # Look for the first non-__init__.py Python file or directory
    for item in src_dir.iterdir():
        if item.is_dir() and not item.name.startswith("_"):
            return item.name
        elif item.is_file() and item.suffix == ".py" and item.stem != "__init__":
            # If there are .py files directly in src/, package name might be
            # project name. Return empty string to indicate flat structure
            return ""

    # Fallback: use src directory's parent name
    return src_dir.parent.name.lower().replace("-", "_")


def get_module_imports(file_path: Path, package_name: str) -> set[str]:
    """Extract all package imports from a module.

    Args:
        file_path: Path to Python file
        package_name: Package name to filter imports

    Returns:
        Set of imported layer/module names
    """
    if not package_name:
        return set()

    try:
        with open(file_path) as f:
            tree = ast.parse(f.read())

        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith(package_name):
                    parts = node.module.split(".")
                    if len(parts) >= 2:
                        layer = parts[1] if len(parts) > 1 else parts[0]
                        imports.add(layer)

        return imports
    except Exception as e:
        print(f"Error parsing {file_path}: {e}", file=sys.stderr)
        return set()


def get_module_layer(file_path: Path, src_dir: Path) -> str:
    """Determine which architectural layer a module belongs to.

    Args:
        file_path: Path to Python file
        src_dir: Source directory path

    Returns:
        Layer name (directory name) or 'root'
    """
    try:
        parts = file_path.relative_to(src_dir).parts
    except ValueError:
        return "root"

    if len(parts) == 0 or parts[0].endswith(".py"):
        return "root"

    return parts[0]


def analyze_dependencies(src_dir: Path, package_name: str) -> dict[str, set[str]]:
    """Analyze dependencies between architectural layers.

    Args:
        src_dir: Source directory path
        package_name: Package name to analyze

    Returns:
        Dictionary mapping layer -> set of layers it depends on
    """
    # Get all Python files
    files = list(src_dir.rglob("*.py"))
    files = [f for f in files if "__pycache__" not in str(f)]

    # Map layer -> set of layers it depends on
    layer_deps: dict[str, set[str]] = defaultdict(set)

    for file in files:
        layer = get_module_layer(file, src_dir)
        if layer in ("__init__", "root", "templates", "guides", "resources"):
            continue

        imports = get_module_imports(file, package_name)
        for imported_layer in imports:
            if imported_layer != layer and imported_layer not in (
                "templates",
                "guides",
                "resources",
            ):
                layer_deps[layer].add(imported_layer)

    return layer_deps


def find_circular_dependencies(layer_deps: dict[str, set[str]]) -> list[list[str]]:
    """Find circular dependencies between layers."""
    cycles: list[list[str]] = []

    def dfs(node: str, path: list[str], visited: set[str]) -> None:
        if node in path:
            # Found a cycle
            cycle_start = path.index(node)
            cycle = path[cycle_start:] + [node]
            if cycle not in cycles and list(reversed(cycle)) not in cycles:
                cycles.append(cycle)
            return

        if node in visited:
            return

        visited.add(node)
        path.append(node)

        for neighbor in layer_deps.get(node, set()):
            dfs(neighbor, path.copy(), visited)

    for layer in layer_deps:
        dfs(layer, [], set())

    return cycles


def main():
    """Main analysis function."""
    # Get project root and source directory
    script_path = Path(__file__)
    project_root = get_project_root(script_path)

    # Allow override via environment variable
    src_dir = get_config_path("SRC_DIR")
    if src_dir is None:
        src_dir = find_src_directory(project_root)
    else:
        # Make path relative to project root if not absolute
        if not src_dir.is_absolute():
            src_dir = project_root / src_dir
        else:
            src_dir = Path(src_dir)

    if not src_dir.exists():
        print(f"Error: Source directory {src_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    # Detect package name
    package_name = os.getenv("PACKAGE_NAME")
    if not package_name:
        package_name = detect_package_name(src_dir)

    if not package_name:
        print(
            (
                "Warning: Could not detect package name. "
                + "Set PACKAGE_NAME environment variable."
            ),
            file=sys.stderr,
        )
        print("Dependency analysis may be incomplete.", file=sys.stderr)

    print("Analyzing module dependencies...")
    print(f"Package: {package_name or '(not detected)'}")
    print()

    layer_deps = analyze_dependencies(src_dir, package_name)

    print("=== Layer Dependencies ===")
    print()
    for layer in sorted(layer_deps.keys()):
        deps = sorted(layer_deps[layer])
        print(f"{layer}:")
        for dep in deps:
            print(f"  → {dep}")
        print()

    # Find circular dependencies
    print("=== Circular Dependencies ===")
    print()
    cycles = find_circular_dependencies(layer_deps)
    if cycles:
        print(f"Found {len(cycles)} circular dependency cycle(s):")
        print()
        for i, cycle in enumerate(cycles, 1):
            print(f"{i}. {' → '.join(cycle)}")
    else:
        print("✅ No circular dependencies found!")

    print()


if __name__ == "__main__":
    main()
