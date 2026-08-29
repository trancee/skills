#!/usr/bin/env python3
"""Check structural invariants in legacy NIST CAVS response files."""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ASSIGNMENT = re.compile(r"^([^=]+?)\s*=\s*(.*)$")
HEADER = re.compile(r"^\[(.*)\]$")
HEX = re.compile(r"^[0-9A-Fa-f]*$")


@dataclass
class Case:
    line: int
    fields: list[tuple[str, str, int]]
    markers: list[tuple[str, int]]


def discover(paths: list[Path], include_txt: bool) -> list[Path]:
    files: set[Path] = set()
    suffixes = {".rsp", ".txt"} if include_txt else {".rsp"}
    for path in paths:
        if not path.exists():
            raise ValueError(f"path does not exist: {path}")
        if path.is_file():
            if path.suffix.lower() not in {".rsp", ".txt"}:
                raise ValueError(f"expected an .rsp/.txt file or directory: {path}")
            files.add(path.resolve())
            continue
        files.update(
            candidate.resolve()
            for candidate in path.rglob("*")
            if candidate.is_file() and candidate.suffix.lower() in suffixes
        )
    if not files:
        expected = ".rsp or .txt" if include_txt else ".rsp"
        raise ValueError(f"no {expected} files found")
    return sorted(files)


def parse(path: Path, allowed_markers: set[str]) -> tuple[list[str], list[Case]]:
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as error:
        raise ValueError(f"{path}: cannot read text: {error}") from error

    headers: list[str] = []
    cases: list[Case] = []
    fields: list[tuple[str, str, int]] = []
    markers: list[tuple[str, int]] = []
    start_line = 0

    def flush() -> None:
        nonlocal fields, markers, start_line
        if fields or markers:
            cases.append(Case(start_line, fields, markers))
            fields = []
            markers = []
            start_line = 0

    for line_number, raw in enumerate(lines, 1):
        stripped = raw.strip()
        if not stripped:
            flush()
            continue
        if stripped.startswith("#"):
            continue
        header = HEADER.fullmatch(stripped)
        if header:
            flush()
            value = header.group(1).strip()
            if not value:
                raise ValueError(f"{path}:{line_number}: empty section header")
            headers.append(value)
            continue
        assignment = ASSIGNMENT.fullmatch(stripped)
        if assignment:
            key = assignment.group(1).strip()
            value = assignment.group(2).strip()
            if not key:
                raise ValueError(f"{path}:{line_number}: empty field name")
            if not start_line:
                start_line = line_number
            fields.append((key, value, line_number))
            continue
        if stripped in allowed_markers or stripped.startswith("** "):
            if not start_line:
                start_line = line_number
            markers.append((stripped, line_number))
            continue
        raise ValueError(
            f"{path}:{line_number}: unrecognized line {stripped!r}; "
            "add a documented bare marker with --allow-marker if required"
        )

    flush()
    if not cases:
        raise ValueError(f"{path}: no test cases found")
    return headers, cases


def check_file(
    path: Path,
    allowed_markers: set[str],
    required_fields: set[str],
    hex_fields: set[str],
) -> tuple[int, int, int, int]:
    headers, cases = parse(path, allowed_markers)
    repeated = 0
    marker_count = 0
    assignment_count = 0

    for case_index, case in enumerate(cases):
        names = [key.casefold() for key, _, _ in case.fields]
        counts = Counter(names)
        repeated += sum(count - 1 for count in counts.values() if count > 1)
        assignment_count += len(case.fields)
        marker_count += len(case.markers)

        missing = sorted(required_fields - set(names))
        if missing:
            raise ValueError(
                f"{path}:{case.line}: case {case_index} is missing required fields: {missing}"
            )
        for key, value, line_number in case.fields:
            if key.casefold() not in hex_fields:
                continue
            if len(value) % 2 != 0 or HEX.fullmatch(value) is None:
                raise ValueError(
                    f"{path}:{line_number}: field {key!r} must be an even-length hexadecimal string"
                )

    print(
        f"PASS: {path} headers={len(headers)} cases={len(cases)} "
        f"assignments={assignment_count} markers={marker_count} repeated_fields={repeated}"
    )
    return len(headers), len(cases), assignment_count, marker_count


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check line structure, required fields, selected hex fields, and markers in CAVS .rsp/.txt files."
    )
    parser.add_argument("paths", nargs="+", type=Path, help="response files or directories")
    parser.add_argument("--include-txt", action="store_true", help="include .txt files during directory discovery")
    parser.add_argument(
        "--allow-marker",
        action="append",
        default=[],
        help="additional documented bare marker; may be repeated (FAIL is always allowed)",
    )
    parser.add_argument(
        "--require-field",
        action="append",
        default=[],
        help="field required in every parsed case; case-insensitive and repeatable",
    )
    parser.add_argument(
        "--hex-field",
        action="append",
        default=[],
        help="field required to contain even-length hexadecimal when present; repeatable",
    )
    args = parser.parse_args()

    allowed_markers = {"FAIL", *args.allow_marker}
    required_fields = {field.casefold() for field in args.require_field}
    hex_fields = {field.casefold() for field in args.hex_field}

    try:
        files = discover(args.paths, args.include_txt)
        totals = [0, 0, 0, 0]
        for path in files:
            result = check_file(path, allowed_markers, required_fields, hex_fields)
            totals = [left + right for left, right in zip(totals, result)]
    except ValueError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1

    print(
        f"PASS: checked {len(files)} file(s), headers={totals[0]} cases={totals[1]} "
        f"assignments={totals[2]} markers={totals[3]}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
