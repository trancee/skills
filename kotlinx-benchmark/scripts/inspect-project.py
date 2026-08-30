#!/usr/bin/env python3
"""Inspect kotlinx-benchmark Gradle configuration and benchmark sources."""

from __future__ import annotations

import argparse
import json
import platform
import re
import shutil
import sys
import tomllib
from pathlib import Path
from typing import Any

IGNORED = {".cache", ".git", ".gradle", ".idea", "build", "target", "node_modules", "vendor"}
BUILD_NAMES = {
    "build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts",
    "gradle.properties", "gradle-wrapper.properties", "libs.versions.toml",
}
PLUGIN_ID = "org.jetbrains.kotlinx.benchmark"
RUNTIME_MODULE = "org.jetbrains.kotlinx:kotlinx-benchmark-runtime"
PROFILE_OPTIONS = {
    "exclude", "include", "iterationTime", "iterationTimeUnit", "iterations", "mode",
    "outputTimeUnit", "param", "reportFormat", "warmups",
}
ADVANCED_OPTIONS = {"jmhIgnoreLock", "jsUseBridge", "jvmForks", "nativeFork", "nativeGCAfterIteration"}
TARGET_CALLS = {
    "androidTarget", "iosArm64", "iosSimulatorArm64", "js", "jvm", "linuxArm64", "linuxX64",
    "macosArm64", "macosX64", "mingwX64", "tvosArm64", "wasmJs", "wasmWasi", "watchosArm64",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="project root (default: cwd)")
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    return parser.parse_args()


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


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


def matching_brace(text: str, opening: int) -> int | None:
    depth = 0
    quote: str | None = None
    escaped = False
    line_comment = False
    block_comment = False
    index = opening
    while index < len(text):
        char = text[index]
        nxt = text[index + 1] if index + 1 < len(text) else ""
        if line_comment:
            if char == "\n":
                line_comment = False
        elif block_comment:
            if char == "*" and nxt == "/":
                block_comment = False
                index += 1
        elif quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        elif char in {"'", '"'}:
            quote = char
        elif char == "/" and nxt == "/":
            line_comment = True
            index += 1
        elif char == "/" and nxt == "*":
            block_comment = True
            index += 1
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None


def blocks(text: str, name: str) -> list[str]:
    result: list[str] = []
    pattern = re.compile(rf"\b{re.escape(name)}\s*\{{")
    for match in pattern.finditer(text):
        opening = text.find("{", match.start())
        closing = matching_brace(text, opening)
        if closing is not None:
            result.append(text[opening + 1:closing])
    return result


def values_in_blocks(text: str, parent: str) -> set[str]:
    values: set[str] = set()
    for body in blocks(text, parent):
        values.update(re.findall(r"\b(?:register|named)\s*\(\s*[\"']([^\"']+)[\"']", body))
        values.update(re.findall(r"\b(?:register|named)\s+[\"']([^\"']+)[\"']", body))
    return values


def inspect_catalog(path: Path, root: Path) -> tuple[dict[str, Any], list[str]]:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        return {}, [f"Cannot parse {rel(path, root)}: {error}"]
    versions = data.get("versions", {})

    def resolve(entry: dict[str, Any]) -> str:
        value = entry.get("version")
        if isinstance(value, dict):
            reference = value.get("ref")
            value = versions.get(reference, f"version.ref:{reference}")
        return str(value or "unresolved")

    plugins = []
    for alias, entry in data.get("plugins", {}).items():
        if isinstance(entry, dict) and (entry.get("id") == PLUGIN_ID or str(entry.get("id", "")).startswith("org.jetbrains.kotlin")):
            plugins.append({"alias": alias, "id": entry["id"], "version": resolve(entry)})
    libraries = []
    for alias, entry in data.get("libraries", {}).items():
        if isinstance(entry, dict) and entry.get("module") == RUNTIME_MODULE:
            libraries.append({"alias": alias, "module": entry["module"], "version": resolve(entry)})
    return {"file": rel(path, root), "plugins": plugins, "libraries": libraries}, []


def inspect(root: Path) -> dict[str, Any]:
    build_files, source_files = project_files(root)
    entries: list[dict[str, Any]] = []
    catalogs: list[dict[str, Any]] = []
    warnings: list[str] = []
    wrapper_versions: set[str] = set()
    plugin_versions: set[str] = set()
    runtime_versions: set[str] = set()
    kotlin_versions: set[str] = set()
    benchmark_targets: set[str] = set()
    kotlin_targets: set[str] = set()
    profiles: set[str] = set()
    jmh_versions: set[str] = set()
    all_open = False

    plugin_pattern = re.compile(re.escape(PLUGIN_ID))
    plugin_version_pattern = re.compile(
        r"id\s*\(?\s*[\"']org\.jetbrains\.kotlinx\.benchmark[\"']\s*\)?\s*version\s*[\"']([^\"']+)[\"']"
    )
    runtime_pattern = re.compile(r"org\.jetbrains\.kotlinx:kotlinx-benchmark-runtime:([^\"'\s)]+)")
    kotlin_version_patterns = (
        re.compile(r"kotlin\s*\(\s*[\"'][^\"']+[\"']\s*\)\s*version\s*[\"']([^\"']+)[\"']"),
        re.compile(r"id\s*\(?\s*[\"']org\.jetbrains\.kotlin\.[^\"']+[\"']\s*\)?\s*version\s*[\"']([^\"']+)[\"']"),
    )

    for path in build_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.name == "gradle-wrapper.properties":
            wrapper_versions.update(re.findall(r"gradle-([0-9][\w.-]*)-(?:bin|all)\.zip", text))
            continue
        if path.name == "libs.versions.toml":
            catalog, problems = inspect_catalog(path, root)
            if catalog:
                catalogs.append(catalog)
                for plugin in catalog["plugins"]:
                    if plugin["id"] == PLUGIN_ID:
                        plugin_versions.add(plugin["version"])
                    else:
                        kotlin_versions.add(plugin["version"])
                runtime_versions.update(library["version"] for library in catalog["libraries"])
            warnings.extend(problems)
            continue
        if path.name in {"settings.gradle", "settings.gradle.kts", "gradle.properties"}:
            continue
        if not plugin_pattern.search(text) and RUNTIME_MODULE not in text and not re.search(r"\bbenchmark\s*\{", text):
            continue
        found_plugins = set(plugin_version_pattern.findall(text))
        found_runtime = set(runtime_pattern.findall(text))
        found_kotlin = {value for pattern in kotlin_version_patterns for value in pattern.findall(text)}
        plugin_versions.update(found_plugins)
        runtime_versions.update(found_runtime)
        kotlin_versions.update(found_kotlin)
        benchmark_bodies = blocks(text, "benchmark")
        found_targets: set[str] = set()
        found_profiles: set[str] = set()
        for body in benchmark_bodies:
            found_targets.update(values_in_blocks(body, "targets"))
            found_profiles.update(values_in_blocks(body, "configurations"))
        benchmark_targets.update(found_targets)
        profiles.update(found_profiles)
        found_kotlin_targets = {
            name for name in TARGET_CALLS if re.search(rf"\b{re.escape(name)}\s*(?:\(|\{{)", text)
        }
        found_kotlin_targets.update(re.findall(r"\bsourceSets\.(?:create|register)\s*\(\s*[\"']([^\"']+)[\"']", text))
        kotlin_targets.update(found_kotlin_targets)
        found_jmh = set(re.findall(r"\bjmhVersion\s*=\s*[\"']([^\"']+)[\"']", text))
        jmh_versions.update(found_jmh)
        advanced = {
            name: sorted(set(re.findall(rf"advanced\s*\(\s*[\"']{re.escape(name)}[\"']\s*,\s*([^\n)]+)", text)))
            for name in ADVANCED_OPTIONS
            if re.search(rf"[\"']{re.escape(name)}[\"']", text)
        }
        profile_options = {
            name: len(re.findall(rf"\b{re.escape(name)}\s*(?:=|\()", "\n".join(benchmark_bodies)))
            for name in PROFILE_OPTIONS
            if re.search(rf"\b{re.escape(name)}\s*(?:=|\()", "\n".join(benchmark_bodies))
        }
        file_all_open = bool(
            re.search(r"allOpen\s*\{", text)
            and "org.openjdk.jmh.annotations.State" in text
        )
        all_open = all_open or file_all_open
        entries.append({
            "file": rel(path, root),
            "plugin_versions": sorted(found_plugins),
            "runtime_versions": sorted(found_runtime),
            "kotlin_versions": sorted(found_kotlin),
            "benchmark_targets": sorted(found_targets),
            "kotlin_targets_or_source_sets": sorted(found_kotlin_targets),
            "profiles": sorted(found_profiles),
            "profile_options": profile_options,
            "advanced_options": advanced,
            "jmh_versions": sorted(found_jmh),
            "all_open_for_jmh_state": file_all_open,
            "native_debug_build": bool(re.search(r"buildType\s*=\s*NativeBuildType\.DEBUG", text)),
        })

    source_entries: list[dict[str, Any]] = []
    total_benchmarks = 0
    state_benchmarks = 0
    for path in source_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        count = len(re.findall(r"@(?:kotlinx\.benchmark\.)?Benchmark\b", text))
        if not count:
            continue
        state = len(re.findall(r"@(?:kotlinx\.benchmark\.)?State\b", text))
        total_benchmarks += count
        state_benchmarks += state
        source_entries.append({
            "file": rel(path, root),
            "benchmark_methods": count,
            "state_annotations": state,
            "param_annotations": len(re.findall(r"@(?:kotlinx\.benchmark\.)?Param\b", text)),
            "uses_blackhole": bool(re.search(r"\bBlackhole\b", text)),
            "explicit_open": bool(re.search(r"\bopen\s+(?:class|fun)\b", text)),
        })

    resolved_plugins = {value for value in plugin_versions if not value.startswith("version.ref:")}
    resolved_runtime = {value for value in runtime_versions if not value.startswith("version.ref:")}
    if not entries and not any(catalog["plugins"] for catalog in catalogs):
        warnings.append("No kotlinx-benchmark plugin/configuration found.")
    if not plugin_versions:
        warnings.append("Benchmark plugin version is unresolved or absent.")
    if not runtime_versions:
        warnings.append("kotlinx-benchmark-runtime dependency is unresolved or absent.")
    if resolved_plugins and resolved_runtime and resolved_plugins != resolved_runtime:
        warnings.append("Benchmark plugin and runtime versions differ.")
    if not benchmark_targets:
        warnings.append("No benchmark target registration found.")
    if total_benchmarks == 0 and (entries or plugin_versions):
        warnings.append("No @Benchmark methods found outside ignored/generated directories.")
    jvm_registered = any("jvm" in target.lower() or target == "main" for target in benchmark_targets)
    if jvm_registered and state_benchmarks and not all_open and not any(entry["explicit_open"] for entry in source_entries):
        warnings.append("JVM state benchmarks are not explicitly open and no JMH State all-open configuration was found.")
    wasm_registered = any("wasm" in target.lower() for target in benchmark_targets)
    if wasm_registered and "0.4.19" in resolved_plugins and any(version != "2.2.0" for version in kotlin_versions if not version.startswith("version.ref:")):
        warnings.append("kotlinx-benchmark 0.4.19 Wasm support requires Kotlin 2.2.0 exactly.")
    if len(jmh_versions) > 1:
        warnings.append("Multiple JMH versions found; different versions across JVM benchmark targets are unsupported.")
    if any("0" in values for entry in entries for key, values in entry["advanced_options"].items() if key == "jvmForks"):
        warnings.append("jvmForks is zero in at least one profile; JVM process isolation is disabled.")
    if any(entry["native_debug_build"] for entry in entries):
        warnings.append("A Native benchmark target uses DEBUG build type; do not compare it with release measurements.")

    return {
        "root": str(root),
        "build_files_scanned": len(build_files),
        "source_files_scanned": len(source_files),
        "host": {"system": platform.system(), "machine": platform.machine()},
        "executables": {"java": shutil.which("java"), "node": shutil.which("node")},
        "gradle_wrapper_versions": sorted(wrapper_versions),
        "plugin_versions": sorted(plugin_versions),
        "runtime_versions": sorted(runtime_versions),
        "kotlin_versions": sorted(kotlin_versions),
        "benchmark_targets": sorted(benchmark_targets),
        "kotlin_targets_or_source_sets": sorted(kotlin_targets),
        "profiles": sorted(profiles),
        "jmh_versions": sorted(jmh_versions),
        "gradle": entries,
        "version_catalogs": catalogs,
        "benchmark_sources": source_entries,
        "summary": {
            "benchmark_methods": total_benchmarks,
            "state_annotations": state_benchmarks,
            "configured_modules": len(entries),
        },
        "warnings": sorted(set(warnings)),
    }


def print_human(data: dict[str, Any]) -> None:
    print(f"Root: {data['root']}")
    print(f"Gradle wrapper: {', '.join(data['gradle_wrapper_versions']) or 'not found'}")
    print(f"Plugin/runtime: {', '.join(data['plugin_versions']) or 'unresolved'} / {', '.join(data['runtime_versions']) or 'unresolved'}")
    print(f"Kotlin: {', '.join(data['kotlin_versions']) or 'unresolved'}")
    print(f"Targets: {', '.join(data['benchmark_targets']) or 'none'}")
    print(f"Profiles: {', '.join(data['profiles']) or 'main only/unresolved'}")
    print(f"Benchmark methods: {data['summary']['benchmark_methods']}")
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
