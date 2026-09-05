#!/usr/bin/env python3
"""Classify and fingerprint libacvp/ACVP JSON without printing field values."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

DEFAULT_MAX_BYTES = 64 * 1024 * 1024
DEFAULT_MAX_DEPTH = 64
DEFAULT_MAX_ITEMS = 1_000_000
DEFAULT_MAX_ISSUES = 100
SENSITIVE_KEYS = {
    "jwt",
    "accesstoken",
    "bearertoken",
    "password",
    "privatekey",
    "privatekeyseed",
    "secretkey",
    "clientsecret",
    "entropyinput",
    "returnedbits",
    "sk",
    "seed",
    "rnd",
}


class DuplicateKeyError(ValueError):
    """Raised when an object contains a repeated member name."""


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Strictly classify libacvp/ACVP JSON, validate vector/group/case IDs, "
            "and emit field/type fingerprints without values."
        )
    )
    parser.add_argument("path", help="JSON artifact to inspect")
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON report")
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=DEFAULT_MAX_BYTES,
        help=f"Maximum input bytes (default: {DEFAULT_MAX_BYTES})",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=DEFAULT_MAX_DEPTH,
        help=f"Maximum JSON nesting depth (default: {DEFAULT_MAX_DEPTH})",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=DEFAULT_MAX_ITEMS,
        help=f"Maximum aggregate array/object members (default: {DEFAULT_MAX_ITEMS})",
    )
    return parser.parse_args()


def json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "unknown"


def walk_limits(value: Any, max_depth: int, max_items: int) -> tuple[int, int]:
    stack: list[tuple[Any, int]] = [(value, 1)]
    deepest = 0
    items = 0
    while stack:
        current, depth = stack.pop()
        deepest = max(deepest, depth)
        if depth > max_depth:
            raise ValueError(f"JSON nesting depth exceeds configured limit {max_depth}")
        if isinstance(current, dict):
            items += len(current)
            stack.extend((child, depth + 1) for child in current.values())
        elif isinstance(current, list):
            items += len(current)
            stack.extend((child, depth + 1) for child in current)
        if items > max_items:
            raise ValueError(f"aggregate JSON member count exceeds configured limit {max_items}")
    return deepest, items


def normalized_key(key: str) -> str:
    return "".join(ch for ch in key.lower() if ch.isalnum())


def collect_sensitive_fields(value: Any) -> dict[str, int]:
    counts: Counter[str] = Counter()
    stack = [value]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            for key, child in current.items():
                if normalized_key(key) in SENSITIVE_KEYS:
                    counts[key] += 1
                stack.append(child)
        elif isinstance(current, list):
            stack.extend(current)
    return dict(sorted(counts.items()))


def is_nonnegative_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def is_metadata_object(value: dict[str, Any]) -> bool:
    return bool({"url", "jwt", "vectorSetUrls", "isSample"} & value.keys()) and "vsId" not in value


def is_protocol_header(value: dict[str, Any]) -> bool:
    return isinstance(value.get("acvVersion"), str)


def add_issue(issues: list[dict[str, str]], code: str, path: str, message: str) -> None:
    if len(issues) < DEFAULT_MAX_ISSUES:
        issues.append({"code": code, "path": path, "message": message})


def merge_types(target: dict[str, set[str]], value: dict[str, Any]) -> None:
    for key, child in value.items():
        target[key].add(json_type(child))


def render_types(fields: dict[str, set[str]]) -> dict[str, list[str]]:
    return {key: sorted(values) for key, values in sorted(fields.items())}


def profile_key(vector: dict[str, Any], group: dict[str, Any]) -> tuple[str, str, str, str]:
    def string_or_missing(obj: dict[str, Any], name: str) -> str:
        value = obj.get(name)
        return value if isinstance(value, str) else "<missing>"

    return (
        string_or_missing(vector, "algorithm"),
        string_or_missing(vector, "mode"),
        string_or_missing(vector, "revision"),
        string_or_missing(group, "testType"),
    )


def validate_vector_sets(
    vector_sets: Iterable[tuple[str, dict[str, Any]]],
    issues: list[dict[str, str]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    seen_vsids: set[int] = set()
    profile_data: dict[tuple[str, str, str, str], dict[str, Any]] = {}

    for path, vector in vector_sets:
        vsid = vector.get("vsId")
        algorithm = vector.get("algorithm")
        groups = vector.get("testGroups")
        if not is_nonnegative_integer(vsid):
            add_issue(issues, "INVALID_VSID", f"{path}.vsId", "vsId must be a nonnegative integer")
        elif vsid in seen_vsids:
            add_issue(issues, "DUPLICATE_VSID", f"{path}.vsId", "vsId must be unique in the artifact")
        else:
            seen_vsids.add(vsid)
        if not isinstance(algorithm, str) or not algorithm:
            add_issue(issues, "INVALID_ALGORITHM", f"{path}.algorithm", "algorithm must be a nonempty string")
        if not isinstance(groups, list):
            add_issue(issues, "INVALID_TEST_GROUPS", f"{path}.testGroups", "testGroups must be an array")
            groups = []

        seen_tgids: set[int] = set()
        seen_tcids: set[int] = set()
        group_count = 0
        case_count = 0
        for group_index, group in enumerate(groups):
            group_path = f"{path}.testGroups[{group_index}]"
            if not isinstance(group, dict):
                add_issue(issues, "INVALID_GROUP", group_path, "test group must be an object")
                continue
            group_count += 1
            tgid = group.get("tgId")
            tests = group.get("tests")
            if not is_nonnegative_integer(tgid):
                add_issue(issues, "INVALID_TGID", f"{group_path}.tgId", "tgId must be a nonnegative integer")
            elif tgid in seen_tgids:
                add_issue(issues, "DUPLICATE_TGID", f"{group_path}.tgId", "tgId must be unique within its vector set")
            else:
                seen_tgids.add(tgid)
            if not isinstance(tests, list):
                add_issue(issues, "INVALID_TESTS", f"{group_path}.tests", "tests must be an array")
                tests = []

            key = profile_key(vector, group)
            profile = profile_data.setdefault(
                key,
                {
                    "vector_fields": defaultdict(set),
                    "group_fields": defaultdict(set),
                    "case_fields": defaultdict(set),
                    "groups": 0,
                    "cases": 0,
                },
            )
            merge_types(profile["vector_fields"], vector)
            merge_types(profile["group_fields"], group)
            profile["groups"] += 1

            for case_index, case in enumerate(tests):
                case_path = f"{group_path}.tests[{case_index}]"
                if not isinstance(case, dict):
                    add_issue(issues, "INVALID_CASE", case_path, "test case must be an object")
                    continue
                case_count += 1
                profile["cases"] += 1
                merge_types(profile["case_fields"], case)
                tcid = case.get("tcId")
                if not is_nonnegative_integer(tcid):
                    add_issue(issues, "INVALID_TCID", f"{case_path}.tcId", "tcId must be a nonnegative integer")
                elif tcid in seen_tcids:
                    add_issue(issues, "DUPLICATE_TCID", f"{case_path}.tcId", "tcId must be unique throughout its vector set")
                else:
                    seen_tcids.add(tcid)

        summaries.append(
            {
                "path": path,
                "vsId": vsid if is_nonnegative_integer(vsid) else None,
                "algorithm": algorithm if isinstance(algorithm, str) else None,
                "mode": vector.get("mode") if isinstance(vector.get("mode"), str) else None,
                "revision": vector.get("revision") if isinstance(vector.get("revision"), str) else None,
                "groups": group_count,
                "cases": case_count,
            }
        )

    profiles: list[dict[str, Any]] = []
    for key in sorted(profile_data):
        algorithm, mode, revision, test_type = key
        data = profile_data[key]
        profiles.append(
            {
                "algorithm": algorithm,
                "mode": mode,
                "revision": revision,
                "testType": test_type,
                "groups": data["groups"],
                "cases": data["cases"],
                "vectorFields": render_types(data["vector_fields"]),
                "groupFields": render_types(data["group_fields"]),
                "caseFields": render_types(data["case_fields"]),
            }
        )
    return summaries, {"profiles": profiles}


def classify(root: Any, issues: list[dict[str, str]]) -> tuple[str, list[tuple[str, dict[str, Any]]], int]:
    if isinstance(root, dict):
        if "vsId" in root:
            return "bare-vector-set", [("$", root)], 0
        if is_metadata_object(root):
            return "session-metadata-object", [], 1
        add_issue(issues, "UNSUPPORTED_ROOT_OBJECT", "$", "object is neither a vector set nor recognized libacvp metadata")
        return "unsupported-object", [], 1

    if not isinstance(root, list):
        add_issue(issues, "INVALID_ROOT", "$", "root must be an object or array")
        return "invalid", [], 0
    if not root:
        add_issue(issues, "EMPTY_ROOT_ARRAY", "$", "root array must not be empty")
        return "empty-array", [], 0

    objects: list[tuple[str, dict[str, Any]]] = []
    for index, item in enumerate(root):
        if isinstance(item, dict):
            objects.append((f"$[{index}]", item))
        else:
            add_issue(issues, "NON_OBJECT_ROOT_ITEM", f"$[{index}]", "supported root arrays contain objects only")

    if not objects:
        return "invalid-array", [], 0

    first_path, first = objects[0]
    if is_protocol_header(first):
        if set(first) != {"acvVersion"}:
            add_issue(issues, "HEADER_EXTRA_FIELDS", first_path, "protocol header contains fields besides acvVersion")
        vectors = [(path, value) for path, value in objects[1:] if "vsId" in value]
        unclassified = len(objects) - 1 - len(vectors)
        return "protocol-envelope", vectors, 1 + unclassified

    if is_metadata_object(first):
        vectors = [(path, value) for path, value in objects[1:] if "vsId" in value]
        unclassified = len(objects) - 1 - len(vectors)
        return "libacvp-bundle", vectors, 1 + unclassified

    vectors = [(path, value) for path, value in objects if "vsId" in value]
    if vectors:
        unclassified = len(objects) - len(vectors)
        if unclassified:
            add_issue(issues, "UNCLASSIFIED_LEADING_OBJECTS", "$", "array contains non-vector objects without a recognized header")
        return "vector-set-array", vectors, unclassified

    add_issue(issues, "UNSUPPORTED_ROOT_ARRAY", "$", "array has no protocol header, libacvp metadata, or vector sets")
    return "unsupported-array", [], len(objects)


def inspect(path: Path, max_bytes: int, max_depth: int, max_items: int) -> tuple[dict[str, Any], int]:
    if max_bytes <= 0 or max_depth <= 0 or max_items <= 0:
        raise ValueError("all configured limits must be positive")
    if not path.exists():
        raise FileNotFoundError(f"input does not exist: {path}")
    if not path.is_file():
        raise ValueError(f"input is not a regular file: {path}")
    size = path.stat().st_size
    if size > max_bytes:
        raise ValueError(f"input size {size} exceeds configured limit {max_bytes}")

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"input is not valid UTF-8: {error}") from error
    try:
        root = json.loads(
            text,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"invalid JSON number: {value}")),
        )
    except (json.JSONDecodeError, DuplicateKeyError, ValueError) as error:
        raise ValueError(f"JSON parse failed: {error}") from error

    depth, items = walk_limits(root, max_depth, max_items)
    issues: list[dict[str, str]] = []
    kind, vector_sets, metadata_objects = classify(root, issues)
    summaries, profile_report = validate_vector_sets(vector_sets, issues)
    issues.sort(key=lambda item: (item["path"], item["code"], item["message"]))
    report = {
        "path": str(path),
        "valid": not issues,
        "kind": kind,
        "input": {"bytes": size, "maxDepth": depth, "aggregateMembers": items},
        "counts": {
            "metadataOrUnclassifiedObjects": metadata_objects,
            "vectorSets": len(summaries),
            "groups": sum(item["groups"] for item in summaries),
            "cases": sum(item["cases"] for item in summaries),
        },
        "sensitiveFields": collect_sensitive_fields(root),
        "vectorSets": summaries,
        **profile_report,
        "issues": issues,
    }
    return report, 0 if not issues else 1


def print_human(report: dict[str, Any]) -> None:
    counts = report["counts"]
    print(f"ACVP JSON: {report['path']}")
    print(f"Kind: {report['kind']} | Valid: {str(report['valid']).lower()}")
    print(
        f"Vector sets: {counts['vectorSets']} | Groups: {counts['groups']} | "
        f"Cases: {counts['cases']}"
    )
    sensitive = report["sensitiveFields"]
    if sensitive:
        names = ", ".join(f"{name}({count})" for name, count in sensitive.items())
        print(f"Sensitive field names present (values redacted): {names}")
    for issue in report["issues"]:
        print(f"ERROR [{issue['code']}] {issue['path']}: {issue['message']}")


def main() -> int:
    args = parse_args()
    try:
        report, status = inspect(
            Path(args.path).expanduser().resolve(),
            args.max_bytes,
            args.max_depth,
            args.max_items,
        )
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    else:
        print_human(report)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
