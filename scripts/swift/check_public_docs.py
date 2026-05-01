#!/usr/bin/env python3
"""Validate DocC coverage for public/open Swift declarations."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


_DECLARATION_PATTERN = re.compile(
    r"^\s*(?:public|open)\s+(?:final\s+)?(?:class|struct|enum|protocol|actor|typealias|init\b|func\b|var\b|let\b|subscript\b)"
)
_MEMBER_DECLARATION_PATTERN = re.compile(
    r"^\s*(?:final\s+)?(?:class|struct|enum|protocol|actor|typealias|init\b|func\b|var\b|let\b|subscript\b)"
)
_COMMENT_LINE_PATTERN = re.compile(r"^\s*///")
_GENERATED_FILE_MARKERS = ("*.pb.swift", "*.generated.swift")
_SKIPPED_DIRECTORIES = {"Tests", ".build"}
_PUBLIC_EXTENSION_PATTERN = re.compile(r"^\s*(?:public|open)\s+extension\b")
_VISIBILITY_RESTRICTED_PATTERN = re.compile(
    r"^\s*(?:private|fileprivate|internal)\s+(?:final\s+)?(?:class|struct|enum|protocol|actor|typealias|init\b|func\b|var\b|let\b|subscript\b)"
)
_ATTRIBUTE_LINE_PATTERN = re.compile(r"^\s*@")


@dataclass(frozen=True)
class UndocumentedDeclaration:
    path: Path
    line: int
    declaration: str


def _collect_swift_files(root: Path) -> list[Path]:
    if root.is_file() and root.suffix == ".swift":
        return [root]

    swift_files: list[Path] = []
    for path in root.rglob("*.swift"):
        if any(part in _SKIPPED_DIRECTORIES for part in path.parts):
            continue
        if any(path.match(marker) for marker in _GENERATED_FILE_MARKERS):
            continue
        swift_files.append(path)
    return sorted(swift_files)


def _is_public_declaration(line: str) -> bool:
    return _DECLARATION_PATTERN.match(line) is not None


def _is_member_declaration(line: str) -> bool:
    return _MEMBER_DECLARATION_PATTERN.match(line) is not None


def _is_public_extension_declaration(line: str) -> bool:
    return _PUBLIC_EXTENSION_PATTERN.match(line) is not None


def _is_visibility_restricted_declaration(line: str) -> bool:
    return _VISIBILITY_RESTRICTED_PATTERN.match(line) is not None


def _is_undocumented_public_line(
    lines: list[str], line: str, index: int, public_extension_depth: int
) -> bool:
    declaration_is_public = _is_public_declaration(line)
    in_public_extension_scope = (
        public_extension_depth > 0
        and _is_member_declaration(line)
        and not _is_visibility_restricted_declaration(line)
    )
    return (declaration_is_public or in_public_extension_scope) and not _has_docc_comment(
        lines, index
    )


def _update_extension_scope(
    line: str, public_extension_depth: int, extension_depth_stack: list[int]
) -> int:
    stripped_line = line.strip()
    if _is_public_extension_declaration(line):
        extension_depth_stack.append(1)
        public_extension_depth += 1
    elif stripped_line.startswith("extension"):
        extension_depth_stack.append(0)

    if extension_depth_stack:
        closing_braces = stripped_line.count("}")
        while closing_braces > 0 and extension_depth_stack:
            public_extension_depth -= extension_depth_stack.pop()
            closing_braces -= 1

    return public_extension_depth


def _has_docc_comment(lines: list[str], declaration_line: int) -> bool:
    idx = declaration_line - 2
    while idx >= 0:
        previous_line = lines[idx].strip()
        if previous_line == "" or _ATTRIBUTE_LINE_PATTERN.match(previous_line):
            idx -= 1
            continue
        break
    return idx >= 0 and _COMMENT_LINE_PATTERN.match(lines[idx]) is not None


def _find_undocumented_declarations(path: Path) -> list[UndocumentedDeclaration]:
    lines = path.read_text(encoding="utf-8").splitlines()
    findings: list[UndocumentedDeclaration] = []
    public_extension_depth = 0
    extension_depth_stack: list[int] = []
    for index, line in enumerate(lines, start=1):
        if _is_undocumented_public_line(lines, line, index, public_extension_depth):
            findings.append(
                UndocumentedDeclaration(
                    path=path,
                    line=index,
                    declaration=line.strip(),
                )
            )
        public_extension_depth = _update_extension_scope(
            line, public_extension_depth, extension_depth_stack
        )
        if public_extension_depth < 0:
            raise ValueError(
                f"Invalid extension depth while parsing {path} at line {index}"
            )
    return findings


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Count undocumented public/open Swift declarations."
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="Swift files or directories to scan (for example Sources/Shared).",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=0,
        help="Maximum allowed undocumented declarations (default: 0).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-declaration output and print only totals.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    findings: list[UndocumentedDeclaration] = []

    for raw_path in args.paths:
        path = Path(raw_path)
        if not path.exists():
            print(f"ERROR: path does not exist: {raw_path}", file=sys.stderr)
            return 2
        for swift_file in _collect_swift_files(path):
            findings.extend(_find_undocumented_declarations(swift_file))

    if not args.quiet:
        for finding in findings:
            print(f"{finding.path}:{finding.line}: {finding.declaration}")

    print(f"undocumented_public_declarations={len(findings)} threshold={args.threshold}")
    return 0 if len(findings) <= args.threshold else 1


if __name__ == "__main__":
    raise SystemExit(main())
