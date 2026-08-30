#!/usr/bin/env python3
"""Inspect Kotlin Power-assert configuration and call sites."""

from __future__ import annotations

import argparse
import json
import platform
import re
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

IGNORED = {".cache", ".git", ".gradle", ".idea", "build", "node_modules", "target", "vendor"}
BUILD_NAMES = {
    "build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts",
    "gradle.properties", "libs.versions.toml", "pom.xml",
}
CALL_NAMES = ("assert", "assertEquals", "assertTrue", "check", "require")
POWER_PLUGIN_ID = "org.jetbrains.kotlin.plugin.power-assert"


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
        if path.name in BUILD_NAMES or path.name.endswith((".gradle", ".gradle.kts")):
            builds.append(path)
        elif path.suffix == ".kt":
            sources.append(path)
    key = lambda item: item.as_posix()
    return sorted(builds, key=key), sorted(sources, key=key)


def source_set_from_path(path: Path, root: Path) -> str | None:
    parts = path.relative_to(root).parts
    try:
        index = parts.index("src")
    except ValueError:
        return None
    return parts[index + 1] if index + 1 < len(parts) else None


def extract_blocks(text: str, name: str) -> list[str]:
    """Return balanced brace bodies following name, ignoring quoted strings and comments."""
    starts = [match.end() for match in re.finditer(rf"\b{re.escape(name)}\s*\{{", text)]
    blocks: list[str] = []
    for start in starts:
        opening = text.find("{", start - 1)
        depth = 0
        quote: str | None = None
        escaped = False
        line_comment = False
        block_comment = False
        index = opening
        while index < len(text):
            char = text[index]
            next_char = text[index + 1] if index + 1 < len(text) else ""
            if line_comment:
                if char == "\n":
                    line_comment = False
            elif block_comment:
                if char == "*" and next_char == "/":
                    block_comment = False
                    index += 1
            elif quote:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = None
            elif char == "/" and next_char == "/":
                line_comment = True
                index += 1
            elif char == "/" and next_char == "*":
                block_comment = True
                index += 1
            elif char in {'"', "'"}:
                quote = char
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    blocks.append(text[opening + 1:index])
                    break
            index += 1
    return blocks


def string_literals(text: str) -> list[str]:
    return re.findall(r"[\"']([^\"']+)[\"']", text)


def property_literals(block: str, name: str) -> set[str]:
    values: set[str] = set()
    call_pattern = rf"\b{re.escape(name)}\s*\.(?:add(?:All)?|set|value)\s*\((.*?)\)"
    for arguments in re.findall(call_pattern, block, re.DOTALL):
        values.update(string_literals(arguments))
    for expression in re.findall(rf"\b{re.escape(name)}\s*=\s*([^\n]+)", block):
        values.update(string_literals(expression))
    return values


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
        if plugin_id == POWER_PLUGIN_ID or plugin_id.startswith("org.jetbrains.kotlin."):
            version, resolved = resolve(entry)
            plugins.append({"alias": alias, "id": plugin_id, "version": version, "version_resolved": resolved})
    libraries: list[dict[str, Any]] = []
    for alias, entry in sorted(data.get("libraries", {}).items()):
        if not isinstance(entry, dict):
            continue
        module = entry.get("module")
        if not module and entry.get("group") and entry.get("name"):
            module = f"{entry['group']}:{entry['name']}"
        if module and "power-assert" in str(module):
            version, resolved = resolve(entry)
            libraries.append({"alias": alias, "module": str(module), "version": version, "version_resolved": resolved})
    return {"file": rel(path, root), "plugins": plugins, "libraries": libraries}, []


def gradle_versions(text: str) -> tuple[set[str], set[str]]:
    kotlin_patterns = (
        r"kotlin\s*\(\s*[\"'](?!plugin\.power-assert[\"'])[\w.-]+[\"']\s*\)\s*version\s*[\"']([^\"']+)[\"']",
        r"id\s*\(?\s*[\"']org\.jetbrains\.kotlin\.(?!plugin\.power-assert)[\w.-]+[\"']\s*\)?\s*version\s*[\"']([^\"']+)[\"']",
    )
    power_patterns = (
        r"kotlin\s*\(\s*[\"']plugin\.power-assert[\"']\s*\)\s*version\s*[\"']([^\"']+)[\"']",
        rf"id\s*\(?\s*[\"']{re.escape(POWER_PLUGIN_ID)}[\"']\s*\)?\s*version\s*[\"']([^\"']+)[\"']",
    )
    kotlin = {value for pattern in kotlin_patterns for value in re.findall(pattern, text)}
    power = {value for pattern in power_patterns for value in re.findall(pattern, text)}
    return kotlin, power


def inspect_gradle(path: Path, root: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    kotlin_versions, power_versions = gradle_versions(text)
    applied = bool(re.search(r"kotlin\s*\(\s*[\"']plugin\.power-assert[\"']\s*\)|org\.jetbrains\.kotlin\.plugin\.power-assert", text))
    plugin_alias_accessors = sorted(set(re.findall(r"alias\s*\(\s*libs\.plugins\.([\w.]+)\s*\)", text)))
    configured_functions: set[str] = set()
    included_source_sets: set[str] = set()
    filters: set[str] = set()
    add_runtime: bool | None = None
    for block in extract_blocks(text, "powerAssert"):
        configured_functions.update(value for value in property_literals(block, "functions") if "." in value)
        included_source_sets.update(property_literals(block, "includedSourceSets"))
        filters.update(re.findall(r"PowerAssertCompilationFilter\.(TESTS|ALL)", block))
        if re.search(r"\bcompilationFilter\s*\.", block) and not filters:
            filters.add("custom")
        runtime_match = re.search(r"\baddRuntimeDependency\s*(?:\.set\s*\(|\.value\s*\(|=)\s*(true|false)", block)
        if runtime_match:
            add_runtime = runtime_match.group(1) == "true"
    return {
        "file": rel(path, root), "plugin_applied": applied,
        "plugin_alias_accessors": plugin_alias_accessors,
        "kotlin_versions": sorted(kotlin_versions), "power_assert_versions": sorted(power_versions),
        "default_function": "kotlin.assert", "functions": sorted(configured_functions), "compilation_filters": sorted(filters),
        "included_source_sets": sorted(included_source_sets), "add_runtime_dependency": add_runtime,
        "runtime_dependency_declared": "kotlin-power-assert-runtime" in text,
        "experimental_gradle_opt_in": "ExperimentalKotlinGradlePluginApi" in text,
    }


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child_text(element: ET.Element, name: str) -> str | None:
    for child in element:
        if local_name(child.tag) == name:
            return (child.text or "").strip() or None
    return None


def inspect_pom(path: Path, root: Path) -> tuple[dict[str, Any], list[str]]:
    try:
        tree = ET.parse(path)
    except (OSError, ET.ParseError) as error:
        return {}, [f"Cannot parse {rel(path, root)}: {error}"]
    kotlin_plugin: ET.Element | None = None
    dependencies: list[dict[str, str | None]] = []
    for element in tree.iter():
        if local_name(element.tag) == "plugin" and child_text(element, "artifactId") == "kotlin-maven-plugin":
            kotlin_plugin = element
        if local_name(element.tag) == "dependency":
            group = child_text(element, "groupId")
            artifact = child_text(element, "artifactId")
            if group and artifact and "power-assert" in artifact:
                dependencies.append({"group": group, "artifact": artifact, "version": child_text(element, "version")})
    compiler_enabled = False
    options: set[str] = set()
    plugin_dependency = False
    kotlin_version: str | None = None
    if kotlin_plugin is not None:
        kotlin_version = child_text(kotlin_plugin, "version")
        for element in kotlin_plugin.iter():
            text = (element.text or "").strip()
            if local_name(element.tag) == "plugin" and text == "power-assert":
                compiler_enabled = True
            if local_name(element.tag) == "option" and text.startswith("power-assert:function="):
                options.add(text.removeprefix("power-assert:function="))
            if local_name(element.tag) == "dependency" and child_text(element, "artifactId") == "kotlin-maven-power-assert":
                plugin_dependency = True
    return {
        "file": rel(path, root), "kotlin_plugin_version": kotlin_version,
        "compiler_plugin_enabled": compiler_enabled, "plugin_dependency_declared": plugin_dependency,
        "functions": sorted(options), "power_assert_dependencies": dependencies,
    }, []


def inspect_source(path: Path, root: Path) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    calls: dict[str, int] = {}
    for name in CALL_NAMES:
        count = len(re.findall(rf"(?<![\w.]){name}\s*\(", text))
        if count:
            calls[name] = count
    annotated = len(re.findall(r"@(?:kotlin\.powerassert\.)?PowerAssert\b(?!\.)", text))
    explanation = len(re.findall(r"\bPowerAssert\.explanation\b", text))
    ignored = len(re.findall(r"@(?:kotlin\.powerassert\.)?PowerAssert\.Ignore\b", text))
    call_explanation = len(re.findall(r"\bCallExplanation\b", text))
    precomputed: set[str] = set()
    boolean_names = set(re.findall(r"\bval\s+(\w+)\s*(?::\s*Boolean)?\s*=", text))
    for name in boolean_names:
        if re.search(rf"\b(?:{'|'.join(CALL_NAMES)})\s*\(\s*{re.escape(name)}\s*(?:,|\))", text):
            precomputed.add(name)
    if not (calls or annotated or explanation or ignored or call_explanation or precomputed):
        return None
    return {
        "file": rel(path, root), "source_set": source_set_from_path(path, root),
        "calls": dict(sorted(calls.items())), "power_assert_annotations": annotated,
        "explanation_accesses": explanation, "ignored_annotations": ignored,
        "call_explanation_references": call_explanation, "precomputed_condition_candidates": sorted(precomputed),
    }


def alias_accessor(alias: str) -> str:
    return re.sub(r"[-_.]+", ".", alias)


def inspect(root: Path) -> dict[str, Any]:
    build_files, source_files = project_files(root)
    warnings: list[str] = []
    gradle: list[dict[str, Any]] = []
    maven: list[dict[str, Any]] = []
    catalogs: list[dict[str, Any]] = []
    for path in build_files:
        if path.name == "libs.versions.toml":
            catalog, problems = inspect_catalog(path, root)
            if catalog:
                catalogs.append(catalog)
            warnings.extend(problems)
        elif path.name == "pom.xml":
            pom, problems = inspect_pom(path, root)
            if pom:
                maven.append(pom)
            warnings.extend(problems)
        elif path.name.endswith((".gradle", ".gradle.kts")):
            gradle.append(inspect_gradle(path, root))

    sources = [entry for path in source_files if (entry := inspect_source(path, root))]
    catalog_power_plugins = [plugin for catalog in catalogs for plugin in catalog["plugins"] if plugin["id"] == POWER_PLUGIN_ID]
    catalog_kotlin_plugins = [plugin for catalog in catalogs for plugin in catalog["plugins"] if plugin["id"] != POWER_PLUGIN_ID]
    used_aliases = {accessor for entry in gradle for accessor in entry["plugin_alias_accessors"]}
    applied_catalog_power = [plugin for plugin in catalog_power_plugins if alias_accessor(plugin["alias"]) in used_aliases]
    applied_catalog_kotlin = [plugin for plugin in catalog_kotlin_plugins if alias_accessor(plugin["alias"]) in used_aliases]
    applied = any(entry["plugin_applied"] for entry in gradle) or any(entry["compiler_plugin_enabled"] for entry in maven) or bool(applied_catalog_power)
    kotlin_versions = {version for entry in gradle for version in entry["kotlin_versions"]}
    power_versions = {version for entry in gradle for version in entry["power_assert_versions"]}
    kotlin_versions.update(plugin["version"] for plugin in applied_catalog_kotlin if plugin["version_resolved"] and plugin["version"])
    power_versions.update(plugin["version"] for plugin in applied_catalog_power if plugin["version_resolved"] and plugin["version"])
    kotlin_versions.update(entry["kotlin_plugin_version"] for entry in maven if entry["kotlin_plugin_version"])
    power_versions.update(
        dependency["version"]
        for entry in maven for dependency in entry["power_assert_dependencies"]
        if dependency["artifact"] == "kotlin-maven-power-assert" and dependency["version"]
    )
    runtime_declared = any(entry["runtime_dependency_declared"] for entry in gradle)
    runtime_declared = runtime_declared or any(
        dependency["artifact"] == "kotlin-power-assert-runtime"
        for entry in maven for dependency in entry["power_assert_dependencies"]
    )
    has_calls = any(entry["calls"] for entry in sources)
    has_annotations = any(entry["power_assert_annotations"] for entry in sources)
    has_explanation = any(entry["explanation_accesses"] for entry in sources)
    if not applied and (has_calls or has_annotations or has_explanation):
        warnings.append("Power-assert call/API candidates found but no Power-assert compiler plugin application was detected.")
    if applied and not (has_calls or has_annotations):
        warnings.append("Power-assert plugin detected but no assertion call or @PowerAssert candidate was found.")
    if kotlin_versions and power_versions and kotlin_versions != power_versions:
        warnings.append(f"Kotlin versions {sorted(kotlin_versions)} do not exactly match Power-assert versions {sorted(power_versions)}.")
    if any(entry["compilation_filters"] for entry in gradle) and "2.4.10" in power_versions:
        warnings.append("compilationFilter is not available in the Kotlin 2.4.10 Power-assert Gradle plugin; use includedSourceSets.")
    if any("ALL" in entry["compilation_filters"] or any(name.endswith("Main") or name == "main" for name in entry["included_source_sets"]) for entry in gradle):
        warnings.append("Power-assert transforms a production/main source set or compilation; verify Experimental runtime and deployment impact.")
    if any(entry["add_runtime_dependency"] is False for entry in gradle) and not runtime_declared:
        warnings.append("Automatic runtime dependency is disabled but no kotlin-power-assert-runtime dependency was detected.")
    if has_annotations and not runtime_declared and not any(entry["plugin_applied"] and entry["add_runtime_dependency"] is not False for entry in gradle):
        warnings.append("@PowerAssert API found without a detected automatic or explicit runtime dependency.")
    if has_explanation and not has_annotations:
        warnings.append("PowerAssert.explanation is used but no @PowerAssert function was detected in scanned source.")
    if any(entry["precomputed_condition_candidates"] for entry in sources):
        warnings.append("Precomputed assertion-condition candidates found; intermediate expression detail may be hidden.")
    for entry in maven:
        if entry["compiler_plugin_enabled"] and not entry["plugin_dependency_declared"]:
            warnings.append(f"{entry['file']} enables power-assert but lacks kotlin-maven-power-assert under kotlin-maven-plugin dependencies.")
        if entry["plugin_dependency_declared"] and not entry["compiler_plugin_enabled"]:
            warnings.append(f"{entry['file']} declares kotlin-maven-power-assert but does not enable the power-assert compiler plugin.")

    return {
        "root": str(root), "host": {"system": platform.system(), "machine": platform.machine()},
        "build_files_scanned": len(build_files), "source_files_scanned": len(source_files),
        "plugin_detected": applied, "kotlin_versions": sorted(kotlin_versions), "power_assert_versions": sorted(power_versions),
        "gradle": gradle, "maven": maven, "version_catalogs": catalogs, "sources": sources,
        "warnings": sorted(set(warnings)),
    }


def print_human(data: dict[str, Any]) -> None:
    print(f"Root: {data['root']}")
    print(f"Host: {data['host']['system']} {data['host']['machine']}")
    print(f"Power-assert plugin: {'detected' if data['plugin_detected'] else 'not detected'}")
    print(f"Kotlin/Power-assert versions: {', '.join(data['kotlin_versions']) or 'unresolved'} / {', '.join(data['power_assert_versions']) or 'unresolved'}")
    print(f"Relevant Kotlin files: {len(data['sources'])}")
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
