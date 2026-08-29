#!/usr/bin/env python3
"""Check structural invariants in Project Wycheproof JSON vector files."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

RESULTS = {"valid", "invalid", "acceptable"}


class DuplicateKeyError(ValueError):
    pass


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def discover(paths: list[Path]) -> list[Path]:
    files: set[Path] = set()
    for path in paths:
        if not path.exists():
            raise ValueError(f"path does not exist: {path}")
        if path.is_file():
            if path.suffix.lower() != ".json":
                raise ValueError(f"expected a JSON vector file or directory: {path}")
            files.add(path.resolve())
            continue
        files.update(candidate.resolve() for candidate in path.rglob("*_test.json") if candidate.is_file())
    if not files:
        raise ValueError("no *_test.json vector files found")
    return sorted(files)


def require(value: object, expected: type, location: str) -> object:
    if type(value) is not expected:
        raise ValueError(f"{location} must be {expected.__name__}")
    return value


def check_file(path: Path, schemas_dir: Path | None) -> Counter[str]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            root = json.load(handle, object_pairs_hook=unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError, DuplicateKeyError) as error:
        raise ValueError(f"{path}: invalid JSON: {error}") from error

    require(root, dict, str(path))
    root = dict(root)
    for field in ("algorithm", "schema", "numberOfTests", "notes", "testGroups"):
        if field not in root:
            raise ValueError(f"{path}: missing root field {field!r}")

    algorithm = require(root["algorithm"], str, f"{path}: algorithm")
    schema = require(root["schema"], str, f"{path}: schema")
    declared_count = require(root["numberOfTests"], int, f"{path}: numberOfTests")
    notes = require(root["notes"], dict, f"{path}: notes")
    groups = require(root["testGroups"], list, f"{path}: testGroups")

    if not algorithm:
        raise ValueError(f"{path}: algorithm must not be empty")
    if not schema or Path(schema).name != schema:
        raise ValueError(f"{path}: schema must be a filename, got {schema!r}")
    if declared_count < 0:
        raise ValueError(f"{path}: numberOfTests must be nonnegative")
    if schemas_dir is not None and not (schemas_dir / schema).is_file():
        raise ValueError(f"{path}: declared schema not found: {schemas_dir / schema}")

    ids: list[int] = []
    counts: Counter[str] = Counter()
    for group_index, group_value in enumerate(groups):
        location = f"{path}: testGroups[{group_index}]"
        group = require(group_value, dict, location)
        group = dict(group)
        group_type = require(group.get("type"), str, f"{location}.type")
        tests = require(group.get("tests"), list, f"{location}.tests")
        if not group_type:
            raise ValueError(f"{location}.type must not be empty")

        for test_index, test_value in enumerate(tests):
            case_location = f"{location}.tests[{test_index}]"
            test = require(test_value, dict, case_location)
            test = dict(test)
            tc_id = require(test.get("tcId"), int, f"{case_location}.tcId")
            result = require(test.get("result"), str, f"{case_location}.result")
            flags = require(test.get("flags"), list, f"{case_location}.flags")
            if tc_id <= 0:
                raise ValueError(f"{case_location}.tcId must be positive")
            if result not in RESULTS:
                raise ValueError(f"{case_location}.result has unknown value {result!r}")
            if not all(isinstance(flag, str) for flag in flags):
                raise ValueError(f"{case_location}.flags must contain only strings")
            unknown_flags = sorted(set(flags) - set(notes))
            if unknown_flags:
                raise ValueError(f"{case_location} references undefined flags: {unknown_flags}")
            ids.append(tc_id)
            counts[result] += 1

    if len(ids) != declared_count:
        raise ValueError(f"{path}: numberOfTests={declared_count}, found {len(ids)} cases")
    if len(set(ids)) != len(ids):
        duplicates = sorted(tc_id for tc_id, count in Counter(ids).items() if count > 1)
        raise ValueError(f"{path}: duplicate tcId values: {duplicates}")
    if ids and sorted(ids) != list(range(1, len(ids) + 1)):
        raise ValueError(f"{path}: tcId values must be continuous from 1 through {len(ids)}")

    print(
        f"PASS: {path} algorithm={algorithm!r} schema={schema!r} "
        f"tests={len(ids)} valid={counts['valid']} invalid={counts['invalid']} "
        f"acceptable={counts['acceptable']}"
    )
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check duplicate keys, counts, IDs, results, flags, and schema filenames in Wycheproof vectors."
    )
    parser.add_argument("paths", nargs="+", type=Path, help="vector JSON files or directories")
    parser.add_argument(
        "--schemas-dir",
        type=Path,
        help="optional directory containing the schema filenames declared by vectors",
    )
    args = parser.parse_args()

    if args.schemas_dir is not None and not args.schemas_dir.is_dir():
        print(f"ERROR: schema directory does not exist: {args.schemas_dir}", file=sys.stderr)
        return 2

    try:
        files = discover(args.paths)
        total: Counter[str] = Counter()
        for path in files:
            total.update(check_file(path, args.schemas_dir))
    except ValueError as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1

    print(
        f"PASS: checked {len(files)} file(s), {sum(total.values())} case(s): "
        f"valid={total['valid']} invalid={total['invalid']} acceptable={total['acceptable']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
