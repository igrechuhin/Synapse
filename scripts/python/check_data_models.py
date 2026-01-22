#!/usr/bin/env python3
"""Pre-commit hook to check data model compliance.

This script checks for:
1. TypedDict usage when Pydantic models are required
2. Data models defined in wrong files (not in models.py)
3. Other data modeling violations per project standards

Configuration:
    SRC_DIR: Source directory path (default: auto-detected)
"""

import ast
import sys
from pathlib import Path

# Import shared utilities
try:
    from _utils import find_src_directory, get_project_root
except ImportError:
    # Fallback if running from different location
    sys.path.insert(0, str(Path(__file__).parent))
    from _utils import find_src_directory, get_project_root


class DataModelVisitor(ast.NodeVisitor):
    """AST visitor to detect data model violations."""

    def __init__(self, file_path: Path) -> None:
        """Initialize visitor.

        Args:
            file_path: Path to the file being analyzed
        """
        self.file_path = file_path
        self.violations: list[str] = []
        self.has_typeddict = False
        self.has_pydantic = False
        self.typeddict_classes: list[str] = []
        self.pydantic_classes: list[str] = []
        self.class_definitions: list[tuple[str, int]] = []  # (name, line)

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statements."""
        for alias in node.names:
            if alias.name == "typing":
                # For 'import typing', TypedDict would be accessed as typing.TypedDict
                # We'll catch it in visit_ImportFrom instead
                pass
            elif alias.name == "pydantic":
                self.has_pydantic = True
            elif alias.name and alias.name.startswith("pydantic."):
                self.has_pydantic = True

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit import from statements."""
        if node.module == "typing" and node.names:
            for alias in node.names:
                if alias.name == "TypedDict":
                    self.has_typeddict = True
        elif node.module and (
            node.module == "pydantic" or node.module.startswith("pydantic.")
        ):
            self.has_pydantic = True

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definitions."""
        self.class_definitions.append((node.name, node.lineno))

        # Check if class inherits from TypedDict
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "TypedDict":
                self.typeddict_classes.append(node.name)
            elif isinstance(base, ast.Attribute):
                if base.attr == "TypedDict" or (
                    isinstance(base.value, ast.Name) and base.value.id == "TypedDict"
                ):
                    self.typeddict_classes.append(node.name)

        # Check if class inherits from Pydantic BaseModel
        for base in node.bases:
            if isinstance(base, ast.Name):
                if base.id in ("BaseModel", "StrictBaseModel"):
                    self.pydantic_classes.append(node.name)
            elif isinstance(base, ast.Attribute):
                if base.attr in ("BaseModel", "StrictBaseModel"):
                    self.pydantic_classes.append(node.name)

        self.generic_visit(node)

    def check_violations(self) -> None:
        """Check for violations and add to violations list."""
        # Check 1: TypedDict usage when Pydantic is required
        if self.typeddict_classes:
            for class_name in self.typeddict_classes:
                line_num = self._get_class_line(class_name)
                message = (
                    f"{self.file_path}:{line_num}: "
                    + f"TypedDict '{class_name}' used - Pydantic BaseModel required "
                    + "per python-coding-standards.mdc"
                )
                self.violations.append(message)

        # Check 2: Models in wrong file location
        # If file is not models.py but contains class definitions,
        # check if it should be in models.py
        if self.file_path.name != "models.py" and self.class_definitions:
            # Check if any classes look like data models
            # (heuristic: classes that might be data models)
            # This is a conservative check - only flag if we're certain
            if self.typeddict_classes or self.pydantic_classes:
                # If file contains data models but is not models.py,
                # check if there's a models.py in the same directory
                models_file = self.file_path.parent / "models.py"
                if models_file.exists():
                    for class_name, line in self.class_definitions:
                        if (
                            class_name in self.typeddict_classes
                            or class_name in self.pydantic_classes
                        ):
                            relative_path = models_file.relative_to(
                                self.file_path.parent.parent.parent
                            )
                            message = (
                                f"{self.file_path}:{line}: "
                                + f"Data model '{class_name}' defined in wrong file - "
                                + f"should be in {relative_path}"
                            )
                            self.violations.append(message)

    def _get_class_line(self, class_name: str) -> int:
        """Get line number for a class definition.

        Args:
            class_name: Name of the class

        Returns:
            Line number or 0 if not found
        """
        for name, line in self.class_definitions:
            if name == class_name:
                return line
        return 0


def check_file(file_path: Path) -> list[str]:
    """Check a single file for data model violations.

    Args:
        file_path: Path to the file to check

    Returns:
        List of violation messages
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))
        visitor = DataModelVisitor(file_path)
        visitor.visit(tree)
        visitor.check_violations()
        return visitor.violations
    except SyntaxError as e:
        return [f"{file_path}:{e.lineno}: Syntax error: {e.msg}"]
    except Exception as e:
        return [f"{file_path}:1: Error analyzing file: {e}"]


def find_python_files(src_dir: Path) -> list[Path]:
    """Find all Python files in source directory.

    Args:
        src_dir: Source directory path

    Returns:
        List of Python file paths
    """
    python_files: list[Path] = []
    for path in src_dir.rglob("*.py"):
        # Skip test files and scripts
        if "test" in path.parts or "scripts" in path.parts:
            continue
        # Skip __pycache__ and .pyc files
        if "__pycache__" in path.parts:
            continue
        python_files.append(path)
    return sorted(python_files)


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for violations found)
    """
    project_root = get_project_root(Path(__file__))
    src_dir = find_src_directory(project_root)

    python_files = find_python_files(src_dir)
    all_violations: list[str] = []

    for file_path in python_files:
        violations = check_file(file_path)
        all_violations.extend(violations)

    if all_violations:
        print("❌ Data model violations found:\n")
        for violation in all_violations:
            print(f"  {violation}")
        fix_message = (
            "\n💡 Fix violations by:"
            + "\n  1. Replace TypedDict with Pydantic BaseModel"
            + "\n  2. Move data models to models.py file"
            + "\n  3. Check python-coding-standards.mdc for requirements"
        )
        print(fix_message)
        return 1

    print("✅ All data models comply with project standards")
    return 0


if __name__ == "__main__":
    sys.exit(main())
