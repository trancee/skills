#!/usr/bin/env python3
"""Inspect Kotlin Gradle plugin, toolchain, compiler, and cache configuration."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

IGNORED = {".cache", ".git", ".gradle", ".idea", "build", "target", "node_modules", "vendor"}
BUILD_NAMES = {
    "build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts",
    "gradle.properties", "gradle-wrapper.properties", "libs.versions.toml",
}
KOTLIN_PLUGIN_PREFIX = "org.jetbrains.kotlin."
TARGET_CALLS = {
    "androidTarget", "iosArm64", "iosSimulatorArm64", "js", "jvm", "linuxArm64", "linuxX64",
    "macosArm64", "macosX64", "mingwX64", "tvosArm64", "wasmJs", "wasmWasi", "watchosArm64",
}
COMPILER_OPTIONS = {
    "allWarningsAsErrors", "apiVersion", "extraWarnings", "freeCompilerArgs", "javaParameters",
    "jvmDefault", "jvmTarget", "languageVersion", "moduleKind", "optIn", "progressiveMode",
    "sourceMap", "sourceMapEmbedSources", "sourceMapNamesPolicy", "suppressWarnings",
}
PROPERTY_PREFIXES = (
    "kotlin.incremental", "kotlin.caching.enabled", "kotlin.compiler.execution.strategy",
    "kotlin.daemon", "kotlin.build.report", "kotlin.jvm.target.validation.mode",
    "kotlin.stdlib", "kotlin.project.persistent.dir", "kotlin.build.archivesTaskOutputAsFriendModule",
)
SENSITIVE_FRAGMENTS = {"password", "secret", "token", "credential", "user"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="project root (default: cwd)")
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    return parser.parse_args()


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def line_numbers(text: str, pattern: re.Pattern[str]) -> list[int]:
    return [number for number, line in enumerate(text.splitlines(), 1) if pattern.search(line)]


def project_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in IGNORED for part in relative.parts) or not path.is_file():
            continue
        if path.name in BUILD_NAMES or path.name.endswith(".gradle.kts"):
            files.append(path)
    return sorted(files, key=lambda item: item.as_posix())


def version_tuple(value: str) -> tuple[int, ...] | None:
    match = re.match(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?", value)
    if not match:
        return None
    return tuple(int(part or 0) for part in match.groups())


def inspect_catalog(path: Path, root: Path) -> tuple[dict[str, Any], list[str]]:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        return {}, [f"Cannot parse {rel(path, root)}: {error}"]
    versions = data.get("versions", {})

    def resolved(entry: dict[str, Any]) -> str:
        value = entry.get("version")
        if isinstance(value, dict):
            reference = value.get("ref")
            value = versions.get(reference, f"version.ref:{reference}")
        return str(value or "unresolved")

    plugins: list[dict[str, str]] = []
    for alias, entry in data.get("plugins", {}).items():
        if not isinstance(entry, dict):
            continue
        plugin_id = str(entry.get("id", ""))
        if plugin_id.startswith(KOTLIN_PLUGIN_PREFIX) or plugin_id.startswith("com.android."):
            plugins.append({"alias": alias, "id": plugin_id, "version": resolved(entry)})
    libraries: list[dict[str, str]] = []
    for alias, entry in data.get("libraries", {}).items():
        if not isinstance(entry, dict):
            continue
        module = str(entry.get("module", ""))
        if module.startswith("org.jetbrains.kotlin:") or module.startswith("org.jetbrains.kotlinx:"):
            libraries.append({"alias": alias, "module": module, "version": resolved(entry)})
    return {"file": rel(path, root), "plugins": plugins, "libraries": libraries}, []


def parse_properties(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for match in re.finditer(r"^\s*([^#!\s][^=]*)=(.*)$", text, re.MULTILINE):
        key, value = match.group(1).strip(), match.group(2).strip()
        if key.startswith(PROPERTY_PREFIXES):
            result[key] = "<redacted>" if any(fragment in key.lower() for fragment in SENSITIVE_FRAGMENTS) else value
    return dict(sorted(result.items()))


def inspect(root: Path) -> dict[str, Any]:
    files = project_files(root)
    entries: list[dict[str, Any]] = []
    catalogs: list[dict[str, Any]] = []
    warnings: list[str] = []
    wrapper_versions: set[str] = set()
    kgp_versions: set[str] = set()
    agp_versions: set[str] = set()
    stdlib_versions: set[str] = set()
    properties: dict[str, dict[str, str]] = {}
    all_jvm_targets: set[str] = set()
    all_java_targets: set[str] = set()

    kgp_id_pattern = re.compile(r"org\.jetbrains\.kotlin\.(?:jvm|multiplatform|android|js|plugin\.[\w.-]+)")
    kotlin_plugin_pattern = re.compile(r"\bkotlin\s*\(\s*[\"'](?:jvm|multiplatform|android|js|plugin\.[^\"']+)[\"']\s*\)")
    kgp_version_patterns = (
        re.compile(r"kotlin\s*\(\s*[\"'][^\"']+[\"']\s*\)\s*version\s*[\"']([^\"']+)[\"']"),
        re.compile(r"id\s*\(?\s*[\"']org\.jetbrains\.kotlin\.[^\"']+[\"']\s*\)?\s*version\s*[\"']([^\"']+)[\"']"),
    )
    agp_version_pattern = re.compile(r"id\s*\(?\s*[\"']com\.android\.[^\"']+[\"']\s*\)?\s*version\s*[\"']([^\"']+)[\"']")
    kotlin_dependency_pattern = re.compile(r"(org\.jetbrains\.kotlinx?:[\w.-]+):([^\"'\s)]+)")

    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.name == "gradle-wrapper.properties":
            wrapper_versions.update(re.findall(r"gradle-([0-9][\w.-]*)-(?:bin|all)\.zip", text))
            continue
        if path.name == "libs.versions.toml":
            catalog, problems = inspect_catalog(path, root)
            if catalog:
                catalogs.append(catalog)
                for plugin in catalog["plugins"]:
                    if plugin["id"].startswith(KOTLIN_PLUGIN_PREFIX):
                        kgp_versions.add(plugin["version"])
                    elif plugin["id"].startswith("com.android."):
                        agp_versions.add(plugin["version"])
                for library in catalog["libraries"]:
                    if library["module"].startswith("org.jetbrains.kotlin:kotlin-stdlib"):
                        stdlib_versions.add(library["version"])
            warnings.extend(problems)
            continue
        if path.name == "gradle.properties":
            values = parse_properties(text)
            if values:
                properties[rel(path, root)] = values
            continue
        if not kgp_id_pattern.search(text) and not kotlin_plugin_pattern.search(text) and not re.search(r"\bkotlin\s*\{", text):
            continue

        found_kgp = {value for pattern in kgp_version_patterns for value in pattern.findall(text)}
        found_agp = set(agp_version_pattern.findall(text))
        dependencies = sorted({f"{module}:{version}" for module, version in kotlin_dependency_pattern.findall(text)})
        found_stdlib = {version for module, version in kotlin_dependency_pattern.findall(text) if module.startswith("org.jetbrains.kotlin:kotlin-stdlib")}
        kgp_versions.update(found_kgp)
        agp_versions.update(found_agp)
        stdlib_versions.update(found_stdlib)

        jvm_targets = set(re.findall(r"JvmTarget\.JVM_([0-9_]+)", text))
        jvm_targets.update(re.findall(r"jvmTarget(?:\.set)?\s*(?:=|\()\s*[\"']([^\"']+)[\"']", text))
        java_targets = set(re.findall(r"JavaVersion\.VERSION_([0-9_]+)", text))
        java_targets.update(re.findall(r"(?:sourceCompatibility|targetCompatibility)\s*=\s*[\"']([^\"']+)[\"']", text))
        toolchains = set(re.findall(r"jvmToolchain\s*\(\s*(\d+)\s*\)", text))
        toolchains.update(re.findall(r"JavaLanguageVersion\.of\s*\(\s*(\d+)\s*\)", text))
        all_jvm_targets.update(value.replace("_", ".") for value in jvm_targets)
        all_java_targets.update(value.replace("_", ".") for value in java_targets)

        target_calls = sorted(name for name in TARGET_CALLS if re.search(rf"\b{re.escape(name)}\s*(?:\(|\{{)", text))
        source_sets = sorted(set(re.findall(r"\b(?:getByName|named|create|register)\s*\(\s*[\"']([\w-]+(?:Main|Test|test|main)?)['\"]", text)))
        compiler_option_lines = {
            name: line_numbers(text, re.compile(rf"\b{re.escape(name)}\b"))
            for name in sorted(COMPILER_OPTIONS)
            if re.search(rf"\b{re.escape(name)}\b", text)
        }
        entries.append({
            "file": rel(path, root),
            "kgp_versions": sorted(found_kgp),
            "agp_versions": sorted(found_agp),
            "kotlin_targets": target_calls,
            "source_sets": source_sets,
            "toolchain_versions": sorted(toolchains),
            "kotlin_jvm_targets": sorted(value.replace("_", ".") for value in jvm_targets),
            "java_targets": sorted(value.replace("_", ".") for value in java_targets),
            "compiler_options_blocks": len(re.findall(r"\bcompilerOptions\s*\{", text)),
            "deprecated_kotlin_options_lines": line_numbers(text, re.compile(r"\bkotlinOptions\s*\{")),
            "compiler_option_lines": compiler_option_lines,
            "dependencies": dependencies,
            "generated_kotlin_lines": line_numbers(text, re.compile(r"\bgeneratedKotlin\b")),
            "repositories": sorted(set(re.findall(r"\b(mavenCentral|google|gradlePluginPortal)\s*\(", text))),
        })

    resolved_kgp = {value for value in kgp_versions if not value.startswith("version.ref:")}
    resolved_agp = {value for value in agp_versions if not value.startswith("version.ref:")}
    if not entries and not any(catalog["plugins"] for catalog in catalogs):
        warnings.append("No Kotlin Gradle plugin declaration/configuration found.")
    if not wrapper_versions:
        warnings.append("No Gradle wrapper version found.")
    if len(resolved_kgp) > 1:
        warnings.append("Multiple Kotlin Gradle plugin versions found.")
    if any(entry["deprecated_kotlin_options_lines"] for entry in entries):
        warnings.append("Deprecated kotlinOptions DSL found; migrate to typed compilerOptions.")
    if all_jvm_targets and all_java_targets and all_jvm_targets != all_java_targets:
        warnings.append("Kotlin jvmTarget and Java compatibility values differ.")
    for file_values in properties.values():
        validation = file_values.get("kotlin.jvm.target.validation.mode", "").lower()
        if validation in {"warning", "ignore"}:
            warnings.append(f"JVM target validation is weakened to {validation}.")
        if any(key.startswith("kotlin.incremental") and value.lower() == "false" for key, value in file_values.items()):
            warnings.append("Kotlin incremental compilation is disabled.")
        if file_values.get("kotlin.caching.enabled", "").lower() == "false":
            warnings.append("Kotlin task caching is disabled.")
        if file_values.get("kotlin.compiler.execution.strategy", "") == "in-process":
            warnings.append("Kotlin compiler runs in-process instead of the default daemon.")
        if file_values.get("kotlin.daemon.useFallbackStrategy", "").lower() == "true":
            warnings.append("Kotlin daemon fallback is explicitly enabled; CI may silently switch execution strategy.")
        if any(key.startswith("kotlin.build.report.http.") for key in file_values):
            warnings.append("HTTP Kotlin build reports are configured; verify credential and environment redaction.")

    for kgp in resolved_kgp:
        parsed = version_tuple(kgp)
        if parsed and (2, 4, 0) <= parsed <= (2, 4, 10):
            for gradle in wrapper_versions:
                gradle_tuple = version_tuple(gradle)
                if gradle_tuple and not ((7, 6, 3) <= gradle_tuple <= (9, 5, 0)):
                    warnings.append(f"KGP {kgp} is outside its fully supported Gradle range with wrapper {gradle}.")
            for agp in resolved_agp:
                agp_tuple = version_tuple(agp)
                if agp_tuple and not ((8, 5, 2) <= agp_tuple <= (9, 1, 0)):
                    warnings.append(f"KGP {kgp} is outside its fully supported AGP range with AGP {agp}.")
    if len(resolved_kgp) == 1 and stdlib_versions:
        kgp = next(iter(resolved_kgp))
        if any(version != kgp for version in stdlib_versions if not version.startswith("version.ref:")):
            warnings.append("Explicit Kotlin stdlib version differs from the detected KGP version.")

    return {
        "root": str(root),
        "build_files_scanned": len(files),
        "gradle_wrapper_versions": sorted(wrapper_versions),
        "kgp_versions": sorted(kgp_versions),
        "agp_versions": sorted(agp_versions),
        "explicit_stdlib_versions": sorted(stdlib_versions),
        "properties": properties,
        "gradle": entries,
        "version_catalogs": catalogs,
        "summary": {
            "configured_build_files": len(entries),
            "kotlin_jvm_targets": sorted(all_jvm_targets),
            "java_targets": sorted(all_java_targets),
        },
        "warnings": sorted(set(warnings)),
    }


def print_human(data: dict[str, Any]) -> None:
    print(f"Root: {data['root']}")
    print(f"Gradle wrapper: {', '.join(data['gradle_wrapper_versions']) or 'not found'}")
    print(f"KGP: {', '.join(data['kgp_versions']) or 'unresolved'}")
    print(f"AGP: {', '.join(data['agp_versions']) or 'none'}")
    print(f"Configured build files: {data['summary']['configured_build_files']}")
    print(f"Kotlin JVM targets: {', '.join(data['summary']['kotlin_jvm_targets']) or 'none explicit'}")
    print(f"Java targets: {', '.join(data['summary']['java_targets']) or 'none explicit'}")
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
