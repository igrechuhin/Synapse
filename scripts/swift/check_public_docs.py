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
_EXTENSION_PATTERN = re.compile(
    r"^\s+?(?:(?:public|open|internal|fileprivate|private)\s+)?extension\b"
)
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
    lines: list[str], line: str, index: int, member_depth: int
) -> bool:
    declaration_is_public = _is_public_declaration(line)
    # Only flag member declarations that are at the direct member level of a public extension
    # (member_depth == 1 means we are exactly one brace-scope inside a public extension block)
    in_public_extension_scope = (
        member_depth == 1
        and _is_member_declaration(line)
        and not _is_visibility_restricted_declaration(line)
    )
    return (
        declaration_is_public or in_public_extension_scope
    ) and not _has_docc_comment(lines, index)


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

    # Track overall brace depth and public extension scopes.
    # public_ext_entry_depths stores the total_brace_depth value recorded BEFORE the
    # public extension's opening brace is processed.  Direct members of the extension
    # are therefore at `total_brace_depth == entry_depth + 1`; lines inside nested
    # function/closure bodies are at depth >= entry_depth + 2.

    total_brace_depth = 0  # current overall { } depth (after processing this line)

    # Parallel stacks – one entry per { encountered, describing its context.
    # Each entry: (depth_before_open: int, is_pub_ext_open: bool)
    scope_stack: list[tuple[int, bool]] = []

    # Depths (before open) for each public extension block still on the stack.
    public_ext_entry_depths: list[int] = []

    for index, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Evaluate membership BEFORE updating depths for this line.
        # A declaration on this line is a *direct member* of a public extension when
        # total_brace_depth == entry_depth + 1, i.e. member_depth == 1.
        member_depth = 0
        if public_ext_entry_depths:
            member_depth = total_brace_depth - public_ext_entry_depths[-1]

        if _is_undocumented_public_line(lines, line, index, member_depth):
            findings.append(
                UndocumentedDeclaration(
                    path=path,
                    line=index,
                    declaration=stripped,
                )
            )

        # Count braces on this line (approximate: ignores string literals / comments).
        opens = stripped.count("{")
        closes = stripped.count("}")

        # Flag whether the FIRST { on this line belongs to a public extension declaration.
        is_pub_ext = _is_public_extension_declaration(line)

        # Process opens first, then closes (handles same-line open-then-close like closures).
        for _ in range(opens):
            depth_before = total_brace_depth
            total_brace_depth += 1
            scope_stack.append((depth_before, is_pub_ext))
            if is_pub_ext:
                public_ext_entry_depths.append(depth_before)
            is_pub_ext = False  # only the first { on this line is the extension open

        for _ in range(closes):
            if scope_stack:
                depth_before, was_pub_ext = scope_stack.pop()
                if was_pub_ext and public_ext_entry_depths:
                    if public_ext_entry_depths[-1] == depth_before:
                        _ = public_ext_entry_depths.pop()
            if total_brace_depth > 0:
                total_brace_depth -= 1

    return findings


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Count undocumented public/open Swift declarations."
    )
    _ = parser.add_argument(
        "paths",
        nargs="+",
        help="Swift files or directories to scan (for example Sources/Shared).",
    )
    _ = parser.add_argument(
        "--threshold",
        type=int,
        default=0,
        help="Maximum allowed undocumented declarations (default: 0).",
    )
    _ = parser.add_argument(
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

    print(
        f"undocumented_public_declarations={len(findings)} threshold={args.threshold}"
    )
    return 0 if len(findings) <= args.threshold else 1


if __name__ == "__main__":
    raise SystemExit(main())
