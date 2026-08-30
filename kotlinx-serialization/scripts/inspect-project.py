#!/usr/bin/env python3
"""Inspect kotlinx.serialization plugins, modules, models, and format policies."""

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
PLUGIN_ID = "org.jetbrains.kotlin.plugin.serialization"
MODULE_PREFIX = "org.jetbrains.kotlinx:kotlinx-serialization-"
ANNOTATIONS = {
    "Serializable", "SerialName", "Transient", "Contextual", "Polymorphic", "UseSerializers",
    "UseContextualSerialization", "EncodeDefault", "Required", "ProtoNumber",
}
CONSTRUCTS = {
    "KSerializer", "SerialDescriptor", "SerializersModule", "serializer", "polymorphic", "subclass",
    "contextual", "Json", "Cbor", "ProtoBuf", "Hocon", "Properties",
}
JSON_OPTIONS = {
    "allowSpecialFloatingPointValues", "allowStructuredMapKeys", "classDiscriminator", "coerceInputValues",
    "encodeDefaults", "exceptionsWithDebugInfo", "explicitNulls", "ignoreUnknownKeys", "isLenient",
    "namingStrategy", "prettyPrint", "serializersModule",
}
EXPERIMENTAL_FORMATS = {"Cbor", "ProtoBuf", "Hocon", "Properties"}


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


def inspect_catalog(path: Path, root: Path) -> tuple[dict[str, Any], list[str]]:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        return {}, [f"Cannot parse {rel(path, root)}: {error}"]
    versions = data.get("versions", {})
    plugins: list[dict[str, Any]] = []
    modules: list[dict[str, Any]] = []
    for alias, entry in data.get("plugins", {}).items():
        if not isinstance(entry, dict):
            continue
        plugin_id = str(entry.get("id", ""))
        if plugin_id == PLUGIN_ID or plugin_id.startswith("org.jetbrains.kotlin."):
            version, resolved = resolve_version(entry.get("version"), versions)
            plugins.append({"alias": alias, "id": plugin_id, "version": version, "version_resolved": resolved})
    for alias, entry in data.get("libraries", {}).items():
        if not isinstance(entry, dict):
            continue
        module = entry.get("module")
        if not module and entry.get("group") and entry.get("name"):
            module = f"{entry['group']}:{entry['name']}"
        if not str(module).startswith(MODULE_PREFIX):
            continue
        version, resolved = resolve_version(entry.get("version"), versions)
        modules.append({"alias": alias, "module": str(module), "version": version, "version_resolved": resolved})
    return {"file": rel(path, root), "plugins": plugins, "modules": modules}, []


def inspect_maven(path: Path, root: Path) -> tuple[dict[str, Any], list[str]]:
    try:
        tree = ET.parse(path)
    except (OSError, ET.ParseError) as error:
        return {}, [f"Cannot parse {rel(path, root)}: {error}"]
    project = tree.getroot()
    properties: dict[str, str] = {}
    for child in project:
        if local_name(child.tag) == "properties":
            properties.update({local_name(item.tag): (item.text or "").strip() for item in child})
    modules: list[dict[str, Any]] = []
    plugin: dict[str, Any] = {}
    for element in project.iter():
        name = local_name(element.tag)
        if name not in {"dependency", "plugin"}:
            continue
        parts = {local_name(child.tag): (child.text or "").strip() for child in element}
        group, artifact = parts.get("groupId"), parts.get("artifactId", "")
        version = parts.get("version", "unresolved")
        resolved = version != "unresolved"
        match = re.fullmatch(r"\$\{([^}]+)}", version)
        if match:
            key = match.group(1)
            if key in properties:
                version = properties[key]
            else:
                resolved = False
        if name == "dependency" and group == "org.jetbrains.kotlinx" and artifact.startswith("kotlinx-serialization-"):
            modules.append({
                "module": f"{group}:{artifact}", "version": version, "version_resolved": resolved,
                "configuration": parts.get("scope", "compile"),
            })
        if name == "plugin" and group == "org.jetbrains.kotlin" and artifact == "kotlin-maven-plugin":
            serialized = ET.tostring(element, encoding="unicode")
            if "kotlinx-serialization" in serialized:
                plugin = {"version": version, "version_resolved": resolved, "compiler_plugin": True}
    return {"file": rel(path, root), "plugin": plugin, "modules": modules}, []


def inspect(root: Path) -> dict[str, Any]:
    build_files, source_files = project_files(root)
    build_entries: list[dict[str, Any]] = []
    catalogs: list[dict[str, Any]] = []
    maven_entries: list[dict[str, Any]] = []
    warnings: list[str] = []
    kotlin_versions: set[str] = set()
    serialization_plugin_versions: set[str] = set()
    runtime_versions: set[str] = set()
    android_present = False

    runtime_pattern = re.compile(r"org\.jetbrains\.kotlinx:(kotlinx-serialization-[\w.-]+):([^\"'\s)]+)")
    kotlin_patterns = (
        re.compile(r"kotlin\s*\(\s*[\"'](?:jvm|multiplatform|android|js)[\"']\s*\)\s*version\s*[\"']([^\"']+)[\"']"),
        re.compile(r"id\s*\(?\s*[\"']org\.jetbrains\.kotlin\.(?:jvm|multiplatform|android|js)[\"']\s*\)?\s*version\s*[\"']([^\"']+)[\"']"),
    )
    serialization_plugin_patterns = (
        re.compile(r"kotlin\s*\(\s*[\"']plugin\.serialization[\"']\s*\)\s*version\s*[\"']([^\"']+)[\"']"),
        re.compile(r"id\s*\(?\s*[\"']org\.jetbrains\.kotlin\.plugin\.serialization[\"']\s*\)?\s*version\s*[\"']([^\"']+)[\"']"),
    )

    modules: list[dict[str, Any]] = []
    for path in build_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.name == "libs.versions.toml":
            catalog, problems = inspect_catalog(path, root)
            if catalog:
                catalogs.append(catalog)
                for plugin in catalog["plugins"]:
                    if plugin["id"] == PLUGIN_ID:
                        serialization_plugin_versions.add(plugin["version"])
                    else:
                        kotlin_versions.add(plugin["version"])
                for module in catalog["modules"]:
                    runtime_versions.add(module["version"])
                    modules.append({**module, "file": rel(path, root), "configuration": f"catalog:{module['alias']}"})
            warnings.extend(problems)
            continue
        if path.name == "pom.xml":
            entry, problems = inspect_maven(path, root)
            if entry:
                maven_entries.append(entry)
                if entry["plugin"]:
                    kotlin_versions.add(entry["plugin"]["version"])
                    serialization_plugin_versions.add(entry["plugin"]["version"])
                for module in entry["modules"]:
                    runtime_versions.add(module["version"])
                    modules.append({**module, "file": rel(path, root)})
            warnings.extend(problems)
            continue
        found_kotlin = {version for pattern in kotlin_patterns for version in pattern.findall(text)}
        found_plugin = {version for pattern in serialization_plugin_patterns for version in pattern.findall(text)}
        kotlin_versions.update(found_kotlin)
        serialization_plugin_versions.update(found_plugin)
        android_present = android_present or bool(re.search(r"org\.jetbrains\.kotlin\.android|com\.android\.", text))
        found_modules: list[dict[str, Any]] = []
        for line_number, line in enumerate(text.splitlines(), 1):
            for artifact, version in runtime_pattern.findall(line):
                configuration_match = re.search(r"\b([\w]+Implementation|api|implementation|compileOnly|runtimeOnly)\s*\(", line)
                module = {
                    "module": f"org.jetbrains.kotlinx:{artifact}", "version": version,
                    "version_resolved": not version.startswith("$"),
                    "configuration": configuration_match.group(1) if configuration_match else "unresolved",
                    "file": rel(path, root), "line": line_number,
                }
                found_modules.append(module)
                modules.append(module)
                runtime_versions.add(version)
        if found_kotlin or found_plugin or found_modules or "kotlinx.serialization" in text:
            build_entries.append({
                "file": rel(path, root), "kotlin_versions": sorted(found_kotlin),
                "serialization_plugin_versions": sorted(found_plugin), "modules": found_modules,
            })

    source_entries: list[dict[str, Any]] = []
    totals = {name: 0 for name in ANNOTATIONS | CONSTRUCTS | JSON_OPTIONS}
    experimental_without_opt_in: list[str] = []
    custom_without_descriptor: list[str] = []
    named_companion_candidates: list[str] = []
    exceptions_debug_true: list[str] = []
    polymorphic_without_module: list[str] = []

    for path in source_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if "kotlinx.serialization" not in text and not re.search(r"@(Serializable|SerialName|Contextual|Polymorphic)\b", text):
            continue
        annotations: dict[str, list[int]] = {}
        constructs: dict[str, list[int]] = {}
        options: dict[str, list[int]] = {}
        for name in ANNOTATIONS:
            pattern = re.compile(rf"@(?:kotlinx\.serialization\.)?{re.escape(name)}\b")
            lines = line_numbers(text, pattern)
            if lines:
                annotations[name] = lines
                totals[name] += sum(1 for _ in pattern.finditer(text))
        for name in CONSTRUCTS:
            pattern = re.compile(rf"\b{re.escape(name)}\b")
            lines = line_numbers(text, pattern)
            if lines:
                constructs[name] = lines
                totals[name] += sum(1 for _ in pattern.finditer(text))
        for name in JSON_OPTIONS:
            pattern = re.compile(rf"\b{re.escape(name)}\s*=")
            lines = line_numbers(text, pattern)
            if lines:
                options[name] = lines
                totals[name] += sum(1 for _ in pattern.finditer(text))
        formats = sorted(EXPERIMENTAL_FORMATS & constructs.keys())
        if formats and "ExperimentalSerializationApi" not in text:
            experimental_without_opt_in.append(rel(path, root))
        if re.search(r"(?:object|class)\s+\w+\s*:\s*KSerializer\s*<", text) and "SerialDescriptor" not in text:
            custom_without_descriptor.append(rel(path, root))
        if annotations.get("Serializable") and re.search(r"companion\s+object\s+\w+", text):
            named_companion_candidates.append(rel(path, root))
        if re.search(r"exceptionsWithDebugInfo\s*=\s*true", text):
            exceptions_debug_true.append(rel(path, root))
        if (annotations.get("Polymorphic") or re.search(r"@Serializable[\s\S]{0,120}\b(?:open|abstract)\s+class\b", text)) and "SerializersModule" not in text:
            polymorphic_without_module.append(rel(path, root))
        source_entries.append({
            "file": rel(path, root), "annotations": dict(sorted(annotations.items())),
            "constructs": dict(sorted(constructs.items())), "json_options": dict(sorted(options.items())),
            "experimental_formats": formats,
        })

    resolved_kotlin = {value for value in kotlin_versions if not value.startswith("version.ref:")}
    resolved_plugins = {value for value in serialization_plugin_versions if not value.startswith("version.ref:")}
    resolved_runtime = {value for value in runtime_versions if not value.startswith("version.ref:") and not value.startswith("$")}
    if source_entries and not serialization_plugin_versions:
        warnings.append("Serialization source found without a detected Kotlin serialization compiler plugin.")
    if resolved_kotlin and resolved_plugins and resolved_kotlin != resolved_plugins:
        warnings.append("Kotlin and serialization compiler plugin versions differ.")
    if len(resolved_runtime) > 1:
        warnings.append("Multiple kotlinx.serialization runtime module versions found; align format/core modules.")
    if source_entries and not modules:
        warnings.append("Serialization source found without a detected kotlinx.serialization runtime/format dependency.")
    if any(not module["version_resolved"] for module in modules):
        warnings.append("At least one serialization runtime version is unresolved; inspect effective dependency resolution.")
    if experimental_without_opt_in:
        warnings.append("Experimental format usage lacks a local ExperimentalSerializationApi opt-in in at least one file.")
    if custom_without_descriptor:
        warnings.append("Custom KSerializer implementation lacks a visible SerialDescriptor in at least one file.")
    if named_companion_candidates and android_present:
        warnings.append("Serializable class with named companion found in Android project; verify R8/ProGuard keep rules.")
    if exceptions_debug_true:
        warnings.append("exceptionsWithDebugInfo=true may expose user input in exception messages.")
    if polymorphic_without_module:
        warnings.append("Open/contextual polymorphism candidate lacks a visible SerializersModule in the same file.")
    if totals["ProtoBuf"] and totals["ProtoNumber"] == 0:
        warnings.append("ProtoBuf usage found without ProtoNumber annotations; verify stable field numbering policy.")

    return {
        "root": str(root), "build_files_scanned": len(build_files), "source_files_scanned": len(source_files),
        "kotlin_versions": sorted(kotlin_versions),
        "serialization_plugin_versions": sorted(serialization_plugin_versions),
        "runtime_versions": sorted(runtime_versions), "modules": sorted(modules, key=lambda item: (item["module"], item["file"])),
        "gradle": build_entries, "version_catalogs": catalogs, "maven": maven_entries,
        "serialization_sources": source_entries,
        "totals": {name: count for name, count in sorted(totals.items()) if count},
        "warnings": sorted(set(warnings)),
    }


def print_human(data: dict[str, Any]) -> None:
    print(f"Root: {data['root']}")
    print(f"Kotlin/plugin/runtime: {', '.join(data['kotlin_versions']) or 'unresolved'} / {', '.join(data['serialization_plugin_versions']) or 'unresolved'} / {', '.join(data['runtime_versions']) or 'unresolved'}")
    for module in data["modules"]:
        print(f"- {module['module']}:{module['version']} ({module['configuration']})")
    print(f"Serialization source files: {len(data['serialization_sources'])}")
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
