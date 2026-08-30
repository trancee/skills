#!/usr/bin/env python3
"""Inspect kotlinx.coroutines dependencies and structured-concurrency risk sites."""

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
SOURCE_PATTERNS = {
    "GlobalScope": re.compile(r"\bGlobalScope\b"),
    "CoroutineScope_constructor": re.compile(r"\bCoroutineScope\s*\("),
    "MainScope": re.compile(r"\bMainScope\s*\("),
    "launch": re.compile(r"\blaunch\s*(?:\([^{}\n]*\)\s*)?\{"),
    "async": re.compile(r"\basync\s*(?:\([^{}\n]*\)\s*)?\{"),
    "await": re.compile(r"\.await\s*\("),
    "runBlocking": re.compile(r"\brunBlocking\s*(?:<[^>]+>)?\s*\{"),
    "runInterruptible": re.compile(r"\brunInterruptible\s*\{"),
    "Thread.sleep": re.compile(r"\bThread\.sleep\s*\("),
    "newSingleThreadContext": re.compile(r"\bnewSingleThreadContext\s*\("),
    "Dispatchers.Default": re.compile(r"\bDispatchers\.Default\b"),
    "Dispatchers.IO": re.compile(r"\bDispatchers\.IO\b"),
    "Dispatchers.Main": re.compile(r"\bDispatchers\.Main\b"),
    "Dispatchers.Unconfined": re.compile(r"\bDispatchers\.Unconfined\b"),
    "flow": re.compile(r"\bflow(?:<[^>\n]+>)?\s*\{"),
    "flowOn": re.compile(r"\.flowOn\s*\("),
    "channelFlow": re.compile(r"\bchannelFlow\s*\{"),
    "StateFlow": re.compile(r"\b(?:Mutable)?StateFlow\b"),
    "SharedFlow": re.compile(r"\b(?:Mutable)?SharedFlow\b"),
    "stateIn": re.compile(r"\.stateIn\s*\("),
    "shareIn": re.compile(r"\.shareIn\s*\("),
    "Channel": re.compile(r"\bChannel\s*<|\bChannel\s*\("),
    "produce": re.compile(r"\bproduce(?:<[^>\n]+>)?\s*\{"),
    "consumeEach": re.compile(r"\.consumeEach\s*\{"),
    "Mutex": re.compile(r"\bMutex\s*\("),
    "select": re.compile(r"\bselect\s*(?:<[^>]+>)?\s*\{"),
    "runTest": re.compile(r"\brunTest\s*(?:\([^{}\n]*\)\s*)?\{"),
    "backgroundScope": re.compile(r"\bbackgroundScope\b"),
    "setMain": re.compile(r"\bDispatchers\.setMain\s*\("),
    "resetMain": re.compile(r"\bDispatchers\.resetMain\s*\("),
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
        elif path.suffix == ".kt":
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
        if not str(module).startswith("org.jetbrains.kotlinx:kotlinx-coroutines-"):
            continue
        version, resolved = resolve_version(entry.get("version"), versions)
        result.append({
            "module": str(module), "version": version, "version_resolved": resolved,
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
        group, artifact = parts.get("groupId"), parts.get("artifactId", "")
        if group != "org.jetbrains.kotlinx" or not artifact.startswith("kotlinx-coroutines-"):
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
            "module": f"{group}:{artifact}", "version": version, "version_resolved": resolved,
            "configuration": parts.get("scope", "compile"), "file": rel(path, root),
        })
    return result, []


def inspect(root: Path) -> dict[str, Any]:
    build_files, source_files = project_files(root)
    dependencies: list[dict[str, Any]] = []
    warnings: list[str] = []
    kotlin_versions: set[str] = set()
    targets: set[str] = set()

    coordinate_pattern = re.compile(r"org\.jetbrains\.kotlinx:(kotlinx-coroutines-[\w.-]+):([^\"'\s)]+)")
    kotlin_patterns = (
        re.compile(r"kotlin\s*\(\s*[\"'][^\"']+[\"']\s*\)\s*version\s*[\"']([^\"']+)[\"']"),
        re.compile(r"id\s*\(?\s*[\"']org\.jetbrains\.kotlin\.[^\"']+[\"']\s*\)?\s*version\s*[\"']([^\"']+)[\"']"),
    )
    target_names = ("jvm", "js", "wasmJs", "wasmWasi", "androidTarget", "linuxX64", "linuxArm64", "iosArm64", "iosSimulatorArm64", "macosX64", "macosArm64")

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
        kotlin_versions.update(value for pattern in kotlin_patterns for value in pattern.findall(text))
        targets.update(name for name in target_names if re.search(rf"\b{re.escape(name)}\s*(?:\(|\{{)", text))
        for line_number, line in enumerate(text.splitlines(), 1):
            for artifact, version in coordinate_pattern.findall(line):
                configuration_match = re.search(r"\b([\w]+Implementation|api|implementation|compileOnly|runtimeOnly)\s*\(", line)
                dependencies.append({
                    "module": f"org.jetbrains.kotlinx:{artifact}",
                    "version": version,
                    "version_resolved": not version.startswith("$"),
                    "configuration": configuration_match.group(1) if configuration_match else "unresolved",
                    "file": rel(path, root),
                    "line": line_number,
                })

    occurrences: list[dict[str, Any]] = []
    totals = {name: 0 for name in SOURCE_PATTERNS}
    broad_catches = 0
    detached_jobs = 0
    flow_context_candidates = 0
    coroutine_files = 0
    main_run_blocking = 0
    set_main = 0
    reset_main = 0
    new_threads_without_close = 0

    for path in source_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        found: dict[str, list[int]] = {}
        for name, pattern in SOURCE_PATTERNS.items():
            lines = line_numbers(text, pattern)
            if lines:
                found[name] = lines
                totals[name] += sum(1 for _ in pattern.finditer(text))
        if not found and "kotlinx.coroutines" not in text:
            continue
        coroutine_files += 1
        catch_lines = line_numbers(text, re.compile(r"catch\s*\([^:]+:\s*(?:Exception|Throwable)\b"))
        broad_catches += len(catch_lines)
        detached_lines = line_numbers(text, re.compile(r"\b(?:launch|async)\s*\(\s*(?:Job|SupervisorJob)\s*\("))
        detached_jobs += len(detached_lines)
        flow_context = bool(re.search(r"\bflow\s*\{", text) and re.search(r"\bwithContext\s*\(", text) and re.search(r"\bemit\s*\(", text))
        flow_context_candidates += int(flow_context)
        is_test = any(part.lower().endswith("test") or part.lower() == "test" for part in path.parts)
        if not is_test:
            main_run_blocking += len(found.get("runBlocking", []))
        set_main += len(found.get("setMain", []))
        reset_main += len(found.get("resetMain", []))
        if found.get("newSingleThreadContext") and not re.search(r"\.use\s*\{|\.close\s*\(", text):
            new_threads_without_close += 1
        occurrences.append({
            "file": rel(path, root), "is_test": is_test, "occurrences": found,
            "broad_catch_lines": catch_lines, "detached_job_lines": detached_lines,
            "flow_with_context_emit_candidate": flow_context,
        })

    versions = {item["version"] for item in dependencies if item["version_resolved"]}
    core_dependencies = [
        item for item in dependencies
        if item["module"].split(":")[-1].startswith("kotlinx-coroutines-core")
    ]
    test_dependencies = [item for item in dependencies if "kotlinx-coroutines-test" in item["module"]]
    if not dependencies and coroutine_files:
        warnings.append("Coroutine source found without a detected kotlinx.coroutines dependency.")
    if len(versions) > 1:
        warnings.append("Multiple kotlinx.coroutines module versions found; align all modules.")
    if any(not item["version_resolved"] for item in dependencies):
        warnings.append("At least one coroutines dependency version is unresolved; inspect effective dependency resolution.")
    if totals["runTest"] and not test_dependencies:
        warnings.append("runTest usage found without a detected kotlinx-coroutines-test dependency.")
    if test_dependencies and any(not ("test" in item["configuration"].lower()) for item in test_dependencies):
        warnings.append("kotlinx-coroutines-test appears outside a test-scoped configuration.")
    if totals["GlobalScope"]:
        warnings.append("GlobalScope usage found; verify deliberate process-lifetime ownership and failure handling.")
    if detached_jobs:
        warnings.append("launch/async receives a new Job or SupervisorJob; this can detach the child from its parent.")
    if totals["async"] > totals["await"]:
        warnings.append("More async builders than await calls found; inspect every Deferred consumer.")
    if main_run_blocking:
        warnings.append("runBlocking appears in non-test source; verify it is an actual blocking boundary, not called from suspend code.")
    if totals["Thread.sleep"] and coroutine_files:
        warnings.append("Thread.sleep appears in coroutine-related source; use a suspending or interruptible boundary where appropriate.")
    if broad_catches:
        warnings.append("Broad Exception/Throwable catches found; verify CancellationException is rethrown.")
    if flow_context_candidates:
        warnings.append("flow builder, withContext, and emit appear together; inspect for Flow context invariant violations.")
    if new_threads_without_close:
        warnings.append("newSingleThreadContext appears without a visible use/close in the same file.")
    if set_main > reset_main:
        warnings.append("Dispatchers.setMain calls outnumber resetMain calls; verify test teardown restores Main.")
    if dependencies and not core_dependencies:
        warnings.append("Coroutines integration modules found without a detected base core dependency; verify transitive/runtime intent.")

    return {
        "root": str(root),
        "build_files_scanned": len(build_files),
        "source_files_scanned": len(source_files),
        "kotlin_versions": sorted(kotlin_versions),
        "targets": sorted(targets),
        "dependencies": sorted(dependencies, key=lambda item: (item["module"], item["file"], item.get("line", 0))),
        "source_sites": occurrences,
        "totals": {name: value for name, value in totals.items() if value},
        "summary": {
            "coroutine_source_files": coroutine_files,
            "broad_catches": broad_catches,
            "detached_jobs": detached_jobs,
            "flow_context_candidates": flow_context_candidates,
        },
        "warnings": sorted(set(warnings)),
    }


def print_human(data: dict[str, Any]) -> None:
    print(f"Root: {data['root']}")
    print(f"Kotlin: {', '.join(data['kotlin_versions']) or 'unresolved'}")
    print(f"Targets: {', '.join(data['targets']) or 'unresolved'}")
    for item in data["dependencies"]:
        print(f"- {item['module']}:{item['version']} ({item['configuration']})")
    print(f"Coroutine source files: {data['summary']['coroutine_source_files']}")
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
