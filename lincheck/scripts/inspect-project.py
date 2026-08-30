#!/usr/bin/env python3
"""Inspect Lincheck dependencies, APIs, strategies, and test-model risk sites."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

IGNORED = {".cache", ".git", ".gradle", ".idea", "build", "target", "node_modules", "vendor"}
BUILD_NAMES = {"build.gradle", "build.gradle.kts", "libs.versions.toml", "pom.xml"}
CURRENT_COORD = "org.jetbrains.lincheck:lincheck"
LEGACY_COORD = "org.jetbrains.kotlinx:lincheck"
PATTERNS = {
    "runConcurrentTest": re.compile(r"\bLincheck\.runConcurrentTest\s*(?:\(|\{)"),
    "ModelCheckingOptions": re.compile(r"\bModelCheckingOptions\s*\("),
    "StressOptions": re.compile(r"\bStressOptions\s*\("),
    "Operation": re.compile(r"@Operation\b"),
    "Param": re.compile(r"@Param\b"),
    "Validate": re.compile(r"@Validate\b"),
    "sequentialSpecification": re.compile(r"\.sequentialSpecification\s*\("),
    "verifier": re.compile(r"\.verifier\s*\("),
    "checkObstructionFreedom": re.compile(r"\.checkObstructionFreedom\s*\("),
    "customScenario": re.compile(r"\.addCustomScenario\s*\{"),
    "guarantee": re.compile(r"\.addGuarantee\s*\("),
    "ignoreGuarantee": re.compile(r"\.ignore\s*\("),
    "stdLibAnalysis": re.compile(r"\.stdLibAnalysisEnabled\s*\("),
    "minimizationDisabled": re.compile(r"\.minimizeFailedScenario\s*\(\s*false"),
    "thread": re.compile(r"\bthread\s*\{"),
    "join": re.compile(r"\.join\s*\("),
}
OPTION_NAMES = {
    "actorsAfter", "actorsBefore", "actorsPerThread", "invocationsPerIteration", "iterations",
    "loopBound", "loopIterationsBeforeThreadSwitch", "recursionBound", "threads", "timeoutMs",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="project root (default: cwd)")
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    return parser.parse_args()


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def line_numbers(text: str, pattern: re.Pattern[str]) -> list[int]:
    return [number for number, line in enumerate(text.splitlines(), 1) if pattern.search(line)]


def project_files(root: Path) -> tuple[list[Path], list[Path]]:
    builds: list[Path] = []
    sources: list[Path] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in IGNORED for part in relative.parts) or not path.is_file():
            continue
        if path.name in BUILD_NAMES or path.name.endswith(".gradle.kts"):
            builds.append(path)
        elif path.suffix in {".kt", ".java"}:
            sources.append(path)
    key = lambda item: item.as_posix()
    return sorted(builds, key=key), sorted(sources, key=key)


def resolve_version(value: Any, versions: dict[str, Any]) -> tuple[str, bool]:
    if isinstance(value, dict):
        reference = value.get("ref")
        return (str(versions[reference]), True) if reference in versions else (f"version.ref:{reference}", False)
    if value is None:
        return "unresolved", False
    return str(value), True


def inspect_catalog(path: Path, root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        return [], [f"Cannot parse {rel(path, root)}: {error}"]
    versions = data.get("versions", {})
    result: list[dict[str, Any]] = []
    for alias, entry in data.get("libraries", {}).items():
        if not isinstance(entry, dict):
            continue
        module = entry.get("module")
        if not module and entry.get("group") and entry.get("name"):
            module = f"{entry['group']}:{entry['name']}"
        if module not in {CURRENT_COORD, LEGACY_COORD}:
            continue
        version, resolved = resolve_version(entry.get("version"), versions)
        result.append({
            "module": module, "version": version, "version_resolved": resolved,
            "configuration": f"catalog:{alias}", "file": rel(path, root),
        })
    return result, []


def inspect_maven(path: Path, root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    try:
        tree = ET.parse(path)
    except (OSError, ET.ParseError) as error:
        return [], [f"Cannot parse {rel(path, root)}: {error}"]
    project = tree.getroot()
    properties: dict[str, str] = {}
    for child in project:
        if local_name(child.tag) == "properties":
            properties.update({local_name(item.tag): (item.text or "").strip() for item in child})
    result: list[dict[str, Any]] = []
    for dependency in project.iter():
        if local_name(dependency.tag) != "dependency":
            continue
        parts = {local_name(child.tag): (child.text or "").strip() for child in dependency}
        module = f"{parts.get('groupId', '')}:{parts.get('artifactId', '')}"
        if module not in {CURRENT_COORD, LEGACY_COORD}:
            continue
        version = parts.get("version", "unresolved")
        resolved = version != "unresolved"
        match = re.fullmatch(r"\$\{([^}]+)}", version)
        if match:
            key = match.group(1)
            if key in properties:
                version = properties[key]
            else:
                resolved = False
        result.append({
            "module": module, "version": version, "version_resolved": resolved,
            "configuration": parts.get("scope", "compile"), "file": rel(path, root),
        })
    return result, []


def inspect(root: Path) -> dict[str, Any]:
    build_files, source_files = project_files(root)
    dependencies: list[dict[str, Any]] = []
    warnings: list[str] = []
    coordinate_pattern = re.compile(r"(org\.jetbrains(?:\.lincheck|\.kotlinx)):(lincheck):([^\"'\s)]+)")

    for path in build_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.name == "libs.versions.toml":
            found, problems = inspect_catalog(path, root)
            dependencies.extend(found)
            warnings.extend(problems)
            continue
        if path.name == "pom.xml":
            found, problems = inspect_maven(path, root)
            dependencies.extend(found)
            warnings.extend(problems)
            continue
        for line_number, line in enumerate(text.splitlines(), 1):
            for group, artifact, version in coordinate_pattern.findall(line):
                configuration = re.search(r"\b([\w]+Implementation|api|implementation|compileOnly|runtimeOnly)\s*\(", line)
                dependencies.append({
                    "module": f"{group}:{artifact}", "version": version,
                    "version_resolved": not version.startswith("$"),
                    "configuration": configuration.group(1) if configuration else "unresolved",
                    "file": rel(path, root), "line": line_number,
                })

    totals = {name: 0 for name in PATTERNS}
    source_entries: list[dict[str, Any]] = []
    legacy_imports = 0
    current_imports = 0
    common_test_sites: list[str] = []
    non_test_sites: list[str] = []
    suspend_without_cancellation: list[str] = []
    validate_with_parameters: list[str] = []

    for path in source_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if "lincheck" not in text.lower() and not any(pattern.search(text) for pattern in PATTERNS.values()):
            continue
        found: dict[str, list[int]] = {}
        for name, pattern in PATTERNS.items():
            lines = line_numbers(text, pattern)
            if lines:
                found[name] = lines
                totals[name] += sum(1 for _ in pattern.finditer(text))
        legacy = len(re.findall(r"\borg\.jetbrains\.kotlinx\.lincheck\b", text))
        current = len(re.findall(r"\borg\.jetbrains\.lincheck\b", text))
        legacy_imports += legacy
        current_imports += current
        lowered_parts = [part.lower() for part in path.parts]
        is_test = any(part == "test" or part.endswith("test") for part in lowered_parts)
        is_common_test = "commontest" in lowered_parts
        if is_common_test:
            common_test_sites.append(rel(path, root))
        if not is_test:
            non_test_sites.append(rel(path, root))
        if re.search(r"@Operation(?:\([^)]*\))?\s+suspend\s+fun", text) and "cancellableOnSuspension" not in text:
            suspend_without_cancellation.append(rel(path, root))
        if re.search(r"@Validate\s+(?:public\s+|private\s+|internal\s+)?fun\s+\w+\s*\([^)]*[^\s)]", text):
            validate_with_parameters.append(rel(path, root))
        options = {
            name: line_numbers(text, re.compile(rf"\.{re.escape(name)}\s*\("))
            for name in sorted(OPTION_NAMES)
            if re.search(rf"\.{re.escape(name)}\s*\(", text)
        }
        source_entries.append({
            "file": rel(path, root), "is_test": is_test, "is_common_test": is_common_test,
            "api": "legacy" if legacy and not current else "current" if current and not legacy else "mixed" if legacy and current else "unqualified",
            "constructs": found, "strategy_options": options,
        })

    resolved_versions = {item["version"] for item in dependencies if item["version_resolved"]}
    current_dependencies = [item for item in dependencies if item["module"] == CURRENT_COORD]
    legacy_dependencies = [item for item in dependencies if item["module"] == LEGACY_COORD]
    if source_entries and not dependencies:
        warnings.append("Lincheck source found without a detected Lincheck dependency.")
    if len(resolved_versions) > 1:
        warnings.append("Multiple Lincheck versions found.")
    if any(not item["version_resolved"] for item in dependencies):
        warnings.append("At least one Lincheck dependency version is unresolved.")
    if dependencies and any("test" not in item["configuration"].lower() for item in dependencies):
        warnings.append("Lincheck dependency appears outside a test-scoped configuration.")
    if current_dependencies and legacy_imports:
        warnings.append("Lincheck 3.x coordinates are mixed with legacy org.jetbrains.kotlinx.lincheck imports.")
    if legacy_dependencies or legacy_imports:
        warnings.append("Legacy Lincheck 2.x coordinates/packages found; migrate to org.jetbrains.lincheck for 3.x.")
    if current_imports and legacy_dependencies:
        warnings.append("Current org.jetbrains.lincheck imports are mixed with legacy dependency coordinates.")
    if common_test_sites:
        warnings.append("Lincheck usage appears in commonTest; move execution to a JVM or Android host-test source set.")
    if non_test_sites:
        warnings.append("Lincheck usage appears outside test source sets.")
    if totals["Operation"] and not (totals["ModelCheckingOptions"] or totals["StressOptions"]):
        warnings.append("@Operation methods found without a declarative Lincheck strategy invocation.")
    if totals["runConcurrentTest"] and totals["thread"] > totals["join"]:
        warnings.append("runConcurrentTest creates more threads than visible join calls; inspect thread lifecycle.")
    if suspend_without_cancellation:
        warnings.append("Suspend @Operation lacks cancellableOnSuspension; verify modeled cancellation semantics.")
    if validate_with_parameters:
        warnings.append("@Validate function may declare parameters; validation functions must be argument-free.")
    if totals["checkObstructionFreedom"] and not totals["ModelCheckingOptions"]:
        warnings.append("Obstruction-freedom checking requires model checking.")
    if totals["ignoreGuarantee"]:
        warnings.append("Ignored library methods found; verify guarantees do not remove relevant switch points.")
    if totals["minimizationDisabled"]:
        warnings.append("Failed-scenario minimization is disabled in at least one test.")

    return {
        "root": str(root), "build_files_scanned": len(build_files), "source_files_scanned": len(source_files),
        "dependencies": sorted(dependencies, key=lambda item: (item["module"], item["file"])),
        "lincheck_sources": source_entries,
        "totals": {name: count for name, count in sorted(totals.items()) if count},
        "summary": {
            "current_imports": current_imports, "legacy_imports": legacy_imports,
            "arbitrary_tests": totals["runConcurrentTest"],
            "model_checking_tests": totals["ModelCheckingOptions"],
            "stress_tests": totals["StressOptions"], "operations": totals["Operation"],
        },
        "warnings": sorted(set(warnings)),
    }


def print_human(data: dict[str, Any]) -> None:
    print(f"Root: {data['root']}")
    for item in data["dependencies"]:
        print(f"- {item['module']}:{item['version']} ({item['configuration']})")
    summary = data["summary"]
    print(f"Arbitrary/model/stress tests: {summary['arbitrary_tests']}/{summary['model_checking_tests']}/{summary['stress_tests']}")
    print(f"Operations: {summary['operations']}")
    if data["warnings"]:
        print("Warnings:")
        for warning in data["warnings"]:
            print(f"- {warning}")


def main() -> int:
    args = parse_args()
    root = args.root.expanduser().resolve()
    if not root.is_dir():
        print(f"error: project root is not a directory: {root}", file=sys.stderr)
        return 2
    data = inspect(root)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print_human(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
