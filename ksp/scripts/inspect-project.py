#!/usr/bin/env python3
"""Inspect KSP plugin wiring, processor providers, generated outputs, rounds, and incrementality."""

from __future__ import annotations

import argparse
import json
import platform
import re
import sys
import tomllib
from collections import Counter
from pathlib import Path
from typing import Any

IGNORED = {".cache", ".git", ".gradle", ".idea", "build", "node_modules", "target", "vendor"}
BUILD_NAMES = {"build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts", "gradle.properties", "libs.versions.toml"}
SERVICE_PATH = "META-INF/services/com.google.devtools.ksp.processing.SymbolProcessorProvider"
KSP_PLUGIN_ID = "com.google.devtools.ksp"
TARGET_NAMES = ("android", "androidLibrary", "androidTarget", "iosArm64", "iosSimulatorArm64", "iosX64", "js", "jvm", "linuxArm64", "linuxX64", "macosArm64", "macosX64", "mingwX64", "wasmJs", "wasmWasi")
RESOLVER_METHODS = ("getAllFiles", "getNewFiles", "getSymbolsWithAnnotation", "getClassDeclarationByName", "getDeclarationsFromPackage")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="project root (default: cwd)")
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    return parser.parse_args()


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def project_files(root: Path) -> tuple[list[Path], list[Path], list[Path], list[str]]:
    builds: list[Path] = []
    sources: list[Path] = []
    services: list[Path] = []
    generated_dirs: set[str] = set()
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        parts = relative.parts
        if path.is_dir() and len(parts) >= 3 and parts[-3:] == ("generated", "ksp", parts[-1]):
            generated_dirs.add(relative.as_posix())
        if any(part in IGNORED for part in parts) or not path.is_file():
            continue
        if path.name in BUILD_NAMES or path.name.endswith((".gradle", ".gradle.kts")):
            builds.append(path)
        elif path.suffix in {".kt", ".java"}:
            sources.append(path)
        elif relative.as_posix().endswith(SERVICE_PATH):
            services.append(path)
    key = lambda item: item.as_posix()
    return sorted(builds, key=key), sorted(sources, key=key), sorted(services, key=key), sorted(generated_dirs)


def source_set_from_path(path: Path, root: Path) -> str | None:
    parts = path.relative_to(root).parts
    try:
        index = parts.index("src")
    except ValueError:
        return None
    return parts[index + 1] if index + 1 < len(parts) else None


def version_tuple(value: str) -> tuple[int, int, int] | None:
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", value)
    return tuple(int(part) for part in match.groups()) if match else None


def alias_accessor(alias: str) -> str:
    return re.sub(r"[-_.]+", ".", alias)


def inspect_catalog(path: Path, root: Path) -> tuple[dict[str, Any], list[str]]:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        return {}, [f"Cannot parse {rel(path, root)}: {error}"]
    versions = data.get("versions", {})

    def resolve(entry: dict[str, Any]) -> tuple[str | None, bool]:
        version = entry.get("version")
        if isinstance(version, dict):
            reference = version.get("ref")
            return (str(versions[reference]), True) if reference in versions else (f"version.ref:{reference}", False)
        return (str(version), True) if version is not None else (None, False)

    plugins: list[dict[str, Any]] = []
    for alias, entry in sorted(data.get("plugins", {}).items()):
        if not isinstance(entry, dict):
            continue
        plugin_id = str(entry.get("id", ""))
        if plugin_id == KSP_PLUGIN_ID or plugin_id.startswith("org.jetbrains.kotlin."):
            version, resolved = resolve(entry)
            plugins.append({"alias": alias, "id": plugin_id, "version": version, "version_resolved": resolved})
    libraries: list[dict[str, Any]] = []
    for alias, entry in sorted(data.get("libraries", {}).items()):
        if not isinstance(entry, dict):
            continue
        module = entry.get("module")
        if not module and entry.get("group") and entry.get("name"):
            module = f"{entry['group']}:{entry['name']}"
        if module and (str(module).startswith("com.google.devtools.ksp:") or "processor" in alias.lower() or "compiler" in alias.lower()):
            version, resolved = resolve(entry)
            libraries.append({"alias": alias, "module": str(module), "version": version, "version_resolved": resolved})
    return {"file": rel(path, root), "plugins": plugins, "libraries": libraries}, []


def direct_applied(text: str, pattern: str) -> bool:
    return any(re.search(pattern, line) and not re.search(r"\bapply\s+false\b", line) for line in text.splitlines())


def inspect_gradle(path: Path, root: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    is_settings = path.name in {"settings.gradle", "settings.gradle.kts"}
    ksp_version_patterns = (
        r"id\s*\(?\s*[\"']com\.google\.devtools\.ksp[\"']\s*\)?\s*version\s*[\"']([^\"']+)[\"']",
        r"kotlin\s*\(\s*[\"']ksp[\"']\s*\)\s*version\s*[\"']([^\"']+)[\"']",
    )
    kotlin_version_patterns = (
        r"kotlin\s*\(\s*[\"'](?!ksp[\"'])[\w.-]+[\"']\s*\)\s*version\s*[\"']([^\"']+)[\"']",
        r"id\s*\(?\s*[\"']org\.jetbrains\.kotlin\.[\w.-]+[\"']\s*\)?\s*version\s*[\"']([^\"']+)[\"']",
    )
    ksp_versions = {value for pattern in ksp_version_patterns for value in re.findall(pattern, text)}
    kotlin_versions = {value for pattern in kotlin_version_patterns for value in re.findall(pattern, text)}
    aliases = []
    if not is_settings:
        for line in text.splitlines():
            if not re.search(r"\bapply\s+false\b", line):
                aliases.extend(re.findall(r"alias\s*\(\s*libs\.plugins\.([\w.]+)\s*\)", line))
    configurations: list[dict[str, Any]] = []
    for number, line in enumerate(text.splitlines(), 1):
        direct = re.search(r"\b(ksp(?:[A-Z][A-Za-z0-9]*)?)\s*\(\s*([^)]*)\)", line)
        added = re.search(r"\badd\s*\(\s*[\"'](ksp[A-Za-z0-9]*)[\"']\s*,\s*(.+)\)", line)
        if direct:
            configurations.append({"name": direct.group(1), "file": rel(path, root), "line": number})
        elif added:
            configurations.append({"name": added.group(1), "file": rel(path, root), "line": number})
    options = sorted(set(re.findall(r"\barg\s*\(\s*[\"']([^\"']+)[\"']\s*,", text)))
    api_versions = sorted(set(re.findall(r"com\.google\.devtools\.ksp:symbol-processing-api:([^\"'\s)]+)", text)))
    targets: list[str] = []
    for target in TARGET_NAMES:
        count = len(re.findall(rf"\b{re.escape(target)}\s*(?:\([^)]*\))?\s*\{{|\b{re.escape(target)}\s*\([^)]*\)", text))
        targets.extend([target] * count)
    return {
        "file": rel(path, root),
        "direct_ksp_plugin": not is_settings and direct_applied(text, r"\bid\s*(?:\(\s*)?[\"']com\.google\.devtools\.ksp[\"']|\bkotlin\s*\(\s*[\"']ksp[\"']"),
        "plugin_alias_accessors": sorted(set(aliases)), "ksp_versions": sorted(ksp_versions), "kotlin_versions": sorted(kotlin_versions),
        "configurations": configurations, "processor_options": options, "api_versions": api_versions,
        "targets": targets, "kmp_plugin": "org.jetbrains.kotlin.multiplatform" in text or 'kotlin("multiplatform")' in text,
        "kapt": bool(re.search(r"\bkapt\s*\(|org\.jetbrains\.kotlin\.kapt|kotlin-kapt", text)),
        "manual_generated_source": bool(re.search(r"(?:srcDir|source)\s*\([^\n]*build[/\\]generated[/\\]ksp", text)),
    }


def inspect_properties(path: Path, root: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    values = {}
    for key in (
        "ksp.incremental", "ksp.incremental.log", "ksp.incremental.log.graph.origin",
        "ksp.allow.all.target.configuration", "ksp.project.isolation.enabled", "ksp.experimental.psi.resolution",
        "ksp.ksp2.profiling.mode", "ksp.useKSP2", "org.gradle.isolated-projects", "org.gradle.unsafe.isolated-projects",
    ):
        match = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.*?)\s*$", text, re.MULTILINE)
        if match:
            values[key] = match.group(1)
    return {"file": rel(path, root), "values": dict(sorted(values.items()))}


def inspect_source(path: Path, root: Path) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    provider_classes = re.findall(r"\bclass\s+(\w+)\b[^{]{0,1000}?:[^{]{0,500}\bSymbolProcessorProvider\b", text)
    processor_classes = re.findall(r"\bclass\s+(\w+)\b[^{]{0,1000}?:[^{]{0,500}\bSymbolProcessor\b", text)
    resolver_calls = {name: len(re.findall(rf"\b{name}\s*\(", text)) for name in RESOLVER_METHODS}
    resolver_calls = {name: count for name, count in resolver_calls.items() if count}
    dependency_modes = Counter(re.findall(r"Dependencies\s*\(\s*aggregating\s*=\s*(true|false)", text))
    code_generation = len(re.findall(r"\bcreateNewFile(?:ByPath)?\s*\(", text))
    processing = {
        "process_overrides": len(re.findall(r"override\s+fun\s+process\s*\(", text)),
        "validate_calls": len(re.findall(r"\.validate\s*\(", text)),
        "resolve_calls": len(re.findall(r"\.resolve\s*\(", text)),
        "finish_overrides": len(re.findall(r"override\s+fun\s+finish\s*\(", text)),
        "on_error_overrides": len(re.findall(r"override\s+fun\s+onError\s*\(", text)),
        "logger_errors": len(re.findall(r"\blogger\.error\s*\(", text)),
        "environment_options": len(re.findall(r"\benvironment\.options\b|\boptions\s*\[", text)),
    }
    processing = {name: count for name, count in processing.items() if count}
    if not (provider_classes or processor_classes or resolver_calls or dependency_modes or code_generation or processing):
        return None
    return {
        "file": rel(path, root), "source_set": source_set_from_path(path, root),
        "provider_classes": sorted(provider_classes), "processor_classes": sorted(processor_classes),
        "resolver_calls": dict(sorted(resolver_calls.items())), "dependency_modes": dict(sorted(dependency_modes.items())),
        "generated_file_calls": code_generation, "processing_signals": processing,
        "returns_empty_list": bool(re.search(r"return\s+emptyList\s*\(", text)),
        "uses_stream_scope": ".use {" in text or ".close()" in text,
    }


def inspect_services(paths: list[Path], root: Path) -> list[dict[str, Any]]:
    result = []
    for path in paths:
        providers = [line.strip() for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip() and not line.lstrip().startswith("#")]
        result.append({"file": rel(path, root), "providers": providers})
    return result


def inspect(root: Path) -> dict[str, Any]:
    build_files, source_files, service_files, generated_dirs = project_files(root)
    warnings: list[str] = []
    gradle: list[dict[str, Any]] = []
    properties: list[dict[str, Any]] = []
    catalogs: list[dict[str, Any]] = []
    for path in build_files:
        if path.name == "libs.versions.toml":
            catalog, problems = inspect_catalog(path, root)
            if catalog:
                catalogs.append(catalog)
            warnings.extend(problems)
        elif path.name == "gradle.properties":
            properties.append(inspect_properties(path, root))
        elif path.name.endswith((".gradle", ".gradle.kts")):
            gradle.append(inspect_gradle(path, root))
    alias_plugins = {alias_accessor(plugin["alias"]): plugin for catalog in catalogs for plugin in catalog["plugins"]}
    for entry in gradle:
        alias_ids = {alias_plugins[value]["id"] for value in entry["plugin_alias_accessors"] if value in alias_plugins}
        entry["ksp_plugin_applied"] = entry.pop("direct_ksp_plugin") or KSP_PLUGIN_ID in alias_ids
        entry["kmp_plugin_applied"] = entry.pop("kmp_plugin") or "org.jetbrains.kotlin.multiplatform" in alias_ids
        entry["applied_alias_plugin_ids"] = sorted(alias_ids)
    sources = [entry for path in source_files if (entry := inspect_source(path, root))]
    services = inspect_services(service_files, root)
    used_aliases = {value for entry in gradle for value in entry["plugin_alias_accessors"]}
    ksp_versions = {version for entry in gradle for version in entry["ksp_versions"]}
    kotlin_versions = {version for entry in gradle for version in entry["kotlin_versions"]}
    for accessor in used_aliases:
        plugin = alias_plugins.get(accessor)
        if not plugin or not plugin["version_resolved"] or not plugin["version"]:
            continue
        if plugin["id"] == KSP_PLUGIN_ID:
            ksp_versions.add(plugin["version"])
        elif plugin["id"].startswith("org.jetbrains.kotlin."):
            kotlin_versions.add(plugin["version"])
    configurations = [config for entry in gradle for config in entry["configurations"]]
    providers = {name for entry in sources for name in entry["provider_classes"]}
    processors = {name for entry in sources for name in entry["processor_classes"]}
    service_providers = [name for entry in services for name in entry["providers"]]
    if configurations and not any(entry["ksp_plugin_applied"] for entry in gradle):
        warnings.append("KSP processor configurations found but no applied com.google.devtools.ksp plugin was detected.")
    if any(entry["ksp_plugin_applied"] for entry in gradle) and not configurations:
        warnings.append("KSP plugin applied but no ksp* processor dependency configuration was detected.")
    if processors and not providers:
        warnings.append("SymbolProcessor implementation found without a SymbolProcessorProvider implementation.")
    if providers and not services:
        warnings.append("SymbolProcessorProvider implementation found without a META-INF/services registration file.")
    if len(service_providers) != len(set(service_providers)):
        warnings.append("Duplicate SymbolProcessorProvider service entries found.")
    simple_service_names = {name.rsplit(".", 1)[-1] for name in service_providers}
    if service_providers and providers and not simple_service_names.issubset(providers):
        warnings.append("Provider service entry lacks a matching provider class candidate in scanned source.")
    api_versions = {version for entry in gradle for version in entry["api_versions"]}
    api_versions.update(
        library["version"] for catalog in catalogs for library in catalog["libraries"]
        if library["module"] == "com.google.devtools.ksp:symbol-processing-api" and library["version_resolved"] and library["version"]
    )
    if (processors or providers) and not api_versions:
        warnings.append("Owned KSP processor source found without a detected symbol-processing-api dependency.")
    for version in ksp_versions:
        parsed = version_tuple(version)
        if parsed is None or parsed < (2, 3, 0):
            warnings.append(f"KSP version {version} uses legacy/KSP1-era versioning; current KSP is KSP2-only.")
    property_values = {key: value for entry in properties for key, value in entry["values"].items()}
    if "ksp.useKSP2" in property_values:
        warnings.append("Obsolete ksp.useKSP2 property found; current KSP has removed KSP1.")
    if property_values.get("ksp.allow.all.target.configuration", "").lower() == "true":
        warnings.append("Legacy ksp.allow.all.target.configuration=true found; use explicit KMP target configurations.")
    if property_values.get("ksp.incremental", "").lower() == "false":
        warnings.append("KSP incremental processing is disabled; retain only while reproducing an incremental defect.")
    if any(entry["manual_generated_source"] for entry in gradle):
        warnings.append("Manual build/generated/ksp source-set wiring found; KSP normally registers generated outputs automatically.")
    if any(entry["kmp_plugin_applied"] and any(config["name"] == "ksp" for config in entry["configurations"]) for entry in gradle):
        warnings.append("Global ksp configuration found in a KMP project; use explicit ksp<Target> configurations.")
    if any(entry["generated_file_calls"] and not entry["dependency_modes"] for entry in sources):
        warnings.append("CodeGenerator output found without a literal aggregating/isolating Dependencies declaration candidate.")
    if any(entry["generated_file_calls"] and not entry["uses_stream_scope"] for entry in sources):
        warnings.append("Generated file stream lacks a detected use/close operation; verify deterministic closure.")
    if any(entry["resolver_calls"].get("getAllFiles") and entry["dependency_modes"].get("false") for entry in sources):
        warnings.append("getAllFiles() appears with isolating output; verify the output does not depend on the global file set.")
    if any(entry["kapt"] for entry in gradle):
        warnings.append("kapt and KSP coexist; verify each processor is configured exactly once and retain kapt only for unsupported processors.")
    return {
        "root": str(root), "host": {"system": platform.system(), "machine": platform.machine()},
        "build_files_scanned": len(build_files), "source_files_scanned": len(source_files),
        "ksp_versions": sorted(ksp_versions), "kotlin_versions": sorted(kotlin_versions), "api_versions": sorted(api_versions),
        "gradle": gradle, "properties": properties, "version_catalogs": catalogs,
        "processor_sources": sources, "service_registrations": services,
        "existing_generated_ksp_dirs": generated_dirs, "warnings": sorted(set(warnings)),
    }


def print_human(data: dict[str, Any]) -> None:
    print(f"Root: {data['root']}")
    print(f"Host: {data['host']['system']} {data['host']['machine']}")
    print(f"KSP/Kotlin/API versions: {', '.join(data['ksp_versions']) or 'unresolved'} / {', '.join(data['kotlin_versions']) or 'unresolved'} / {', '.join(data['api_versions']) or 'unresolved'}")
    print(f"Processor sources/service registrations: {len(data['processor_sources'])} / {len(data['service_registrations'])}")
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
