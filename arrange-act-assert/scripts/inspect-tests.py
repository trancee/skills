#!/usr/bin/env python3
"""Inspect test functions for high-signal Arrange-Act-Assert structure hazards."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SUFFIXES = {".cs", ".go", ".java", ".js", ".jsx", ".kt", ".kts", ".py", ".rb", ".rs", ".swift", ".ts", ".tsx"}
IGNORED = {".build", ".cache", ".git", ".gradle", ".idea", ".pytest_cache", ".tox", "build", "dist", "node_modules", "target", "vendor"}
TEST_PATH = re.compile(r"(?:^|/)(?:tests?|specs?|__tests__)(?:/|$)|(?:test|spec)\.[^.]+$|(?:Test|Tests)\.[^.]+$")
START = re.compile(
    r"^\s*(?:"
    r"@Test\b|\[Test(?:Method)?\b|#\s*\[test\]|"
    r"(?:async\s+)?def\s+test_\w+\s*\(|"
    r"(?:public\s+|private\s+|internal\s+|protected\s+)?(?:async\s+)?(?:fun|void|Task|func)\s+`?test\w*|"
    r"func\s+Test\w+\s*\(|"
    r"(?:it|test)\s*\(|"
    r"def\s+test_\w+|it\s+[\"']"
    r")",
    re.IGNORECASE,
)
ANNOTATION_START = re.compile(r"^\s*(?:@Test\b|\[Test(?:Method)?\b|#\s*\[test\])", re.IGNORECASE)
ASSERTION = re.compile(r"\b(?:assert\w*|expect|verify|should|must|fail|XCTAssert\w*|require\.\w+|check\s*\()\b", re.IGNORECASE)
SLEEP = re.compile(r"\b(?:Thread\.sleep|time\.sleep|sleep|delay|setTimeout|Task\.sleep|usleep)\s*\(", re.IGNORECASE)
DISABLED = re.compile(r"@Disabled\b|@Ignore\b|pytest\.mark\.skip|\b(?:xit|xdescribe|xtest)\s*\(|\.(?:skip|todo)\s*\(|\[Ignore\b", re.IGNORECASE)
MARKER = re.compile(r"(?:#|//|/\*)\s*(Arrange|Given|Act|When|Assert|Then)\b", re.IGNORECASE)
PHASE = {"arrange": "arrange", "given": "arrange", "act": "act", "when": "act", "assert": "assert", "then": "assert"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root (default: cwd)")
    parser.add_argument("--path", action="append", default=[], help="relative file/directory to inspect; repeatable")
    parser.add_argument("--max-lines", type=int, default=80, help="warn when a test exceeds nonblank lines (default: 80)")
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    return parser.parse_args()


def is_test_file(path: Path, root: Path) -> bool:
    return path.suffix in SUFFIXES and bool(TEST_PATH.search(path.relative_to(root).as_posix()))


def collect_files(root: Path, requested: list[str]) -> list[Path]:
    candidates: list[Path] = []
    bases = [(root / item).resolve() for item in requested] if requested else [root]
    for base in bases:
        if root not in (base, *base.parents):
            raise ValueError(f"path escapes root: {base}")
        paths = [base] if base.is_file() else base.rglob("*") if base.is_dir() else []
        for path in paths:
            if not path.is_file() or any(part in IGNORED for part in path.relative_to(root).parts):
                continue
            if is_test_file(path, root):
                candidates.append(path)
    return sorted(set(candidates), key=lambda item: item.relative_to(root).as_posix())


def test_chunks(text: str) -> list[tuple[int, list[str]]]:
    lines = text.splitlines()
    raw_starts = [index for index, line in enumerate(lines) if START.search(line)]
    starts: list[int] = []
    for start in raw_starts:
        if starts and start - starts[-1] <= 3 and ANNOTATION_START.search(lines[starts[-1]]) and not ANNOTATION_START.search(lines[start]):
            continue
        starts.append(start)
    chunks: list[tuple[int, list[str]]] = []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        chunks.append((start + 1, lines[start:end]))
    return chunks


def inspect_test(path: Path, root: Path, start_line: int, lines: list[str], max_lines: int, index: int) -> dict[str, Any]:
    text = "\n".join(lines)
    assertions = [start_line + offset for offset, line in enumerate(lines) if ASSERTION.search(line)]
    sleeps = [start_line + offset for offset, line in enumerate(lines) if SLEEP.search(line)]
    markers: list[dict[str, Any]] = []
    for offset, line in enumerate(lines):
        for match in MARKER.finditer(line):
            raw = match.group(1).lower()
            markers.append({"phase": PHASE[raw], "label": match.group(1), "line": start_line + offset})
    phases = [item["phase"] for item in markers]
    nonblank = sum(1 for line in lines if line.strip())
    warnings: list[str] = []
    if not assertions:
        warnings.append("No assertion/oracle candidate detected.")
    if DISABLED.search(text):
        warnings.append("Skipped/disabled/todo test candidate detected.")
    if sleeps:
        warnings.append("Sleep/delay synchronization candidate detected; use clock, idleness, signal, or bounded eventual assertion.")
    if nonblank > max_lines:
        warnings.append(f"Test has {nonblank} nonblank lines, above --max-lines {max_lines}; inspect setup or behavior scope.")
    if markers:
        first = {phase: phases.index(phase) for phase in set(phases)}
        missing = [phase for phase in ("arrange", "act", "assert") if phase not in first]
        if missing:
            warnings.append("Explicit AAA/GWT markers omit phase(s): " + ", ".join(missing) + ".")
        elif not (first["arrange"] < first["act"] < first["assert"]):
            warnings.append("Explicit phase markers are not ordered Arrange/Given -> Act/When -> Assert/Then.")
        if phases.count("act") > 1:
            warnings.append("Multiple explicit Act/When phases detected; split behaviors or use an explicit workflow structure.")
        act_lines = [item["line"] for item in markers if item["phase"] == "act"]
        assert_lines = [item["line"] for item in markers if item["phase"] == "assert"]
        if act_lines and assertions and min(assertions) < min(act_lines):
            warnings.append("Assertion candidate appears before the explicit Act/When phase.")
        if act_lines and assert_lines and max(act_lines) > min(assert_lines):
            warnings.append("Act/When phase appears after Assert/Then began.")
    first_line = next((line.strip() for line in lines if line.strip() and not ANNOTATION_START.search(line)), "")
    name = re.sub(r"\s+", " ", first_line)[:160] or f"test-{index}"
    return {
        "id": f"{path.relative_to(root).as_posix()}:{start_line}", "name": name,
        "start_line": start_line, "nonblank_lines": nonblank, "assertion_lines": assertions,
        "sleep_lines": sleeps, "markers": markers, "warnings": warnings,
    }


def inspect(root: Path, requested: list[str], max_lines: int) -> dict[str, Any]:
    files = collect_files(root, requested)
    results: list[dict[str, Any]] = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        chunks = test_chunks(text)
        tests = [inspect_test(path, root, line, chunk, max_lines, index) for index, (line, chunk) in enumerate(chunks, 1)]
        results.append({"file": path.relative_to(root).as_posix(), "tests": tests})
    warnings = sum(len(test["warnings"]) for item in results for test in item["tests"])
    return {
        "root": str(root), "requested_paths": requested, "files_scanned": len(files),
        "tests_detected": sum(len(item["tests"]) for item in results), "warnings": warnings, "files": results,
    }


def print_human(data: dict[str, Any]) -> None:
    print(f"Root: {data['root']}")
    print(f"Files/tests/warnings: {data['files_scanned']} / {data['tests_detected']} / {data['warnings']}")
    for item in data["files"]:
        for test in item["tests"]:
            for warning in test["warnings"]:
                print(f"- {test['id']}: {warning}")


def main() -> int:
    args = parse_args()
    root = args.root.expanduser().resolve()
    if not root.is_dir():
        print(f"error: repository root is not a directory: {root}", file=sys.stderr)
        return 2
    if args.max_lines <= 0:
        print("error: --max-lines must be greater than zero", file=sys.stderr)
        return 2
    try:
        data = inspect(root, args.path, args.max_lines)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print_human(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
