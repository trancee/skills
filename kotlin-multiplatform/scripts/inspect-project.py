#!/usr/bin/env python3
"""Inspect Kotlin Multiplatform targets, source sets, hierarchy, declarations, and publications."""

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

IGNORED = {".cache", ".git", ".gradle", ".idea", "build", "target", "node_modules", "vendor"}
BUILD_NAMES = {
    "build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts",
    "gradle.properties", "gradle-wrapper.properties", "libs.versions.toml",
}
TARGET_NAMES = (
    "android", "androidTarget", "iosArm64", "iosSimulatorArm64", "iosX64", "js", "jvm",
    "linuxArm64", "linuxX64", "macosArm64", "macosX64", "mingwX64", "tvosArm64",
    "tvosSimulatorArm64", "wasmJs", "wasmWasi", "watchosArm64", "watchosSimulatorArm64",
)
APPLE_TARGETS = {name for name in TARGET_NAMES if name.startswith(("ios", "macos", "tvos", "watchos"))}
PLATFORM_IMPORTS = ("java.", "javax.", "android.", "platform.", "kotlinx.browser.", "node.")


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
        elif path.suffix == ".kt":
            sources.append(path)
    key = lambda item: item.as_posix()
    return sorted(builds, key=key), sorted(sources, key=key)


def version_tuple(value: str) -> tuple[int, ...] | None:
    match = re.match(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?", value)
    return tuple(int(part or 0) for part in match.groups()) if match else None


def inspect_catalog(path: Path, root: Path) -> tuple[dict[str, Any], list[str]]:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        return {}, [f"Cannot parse {rel(path, root)}: {error}"]
    versions = data.get("versions", {})

    def resolve(entry: dict[str, Any]) -> tuple[str, bool]:
        value = entry.get("version")
        if isinstance(value, dict):
            reference = value.get("ref")
            return (str(versions[reference]), True) if reference in versions else (f"version.ref:{reference}", False)
        return (str(value), True) if value is not None else ("unresolved", False)

    plugins = []
    for alias, entry in data.get("plugins", {}).items():
        if not isinstance(entry, dict):
            continue
        plugin_id = str(entry.get("id", ""))
        if plugin_id == "org.jetbrains.kotlin.multiplatform" or plugin_id.startswith("com.android."):
            version, resolved = resolve(entry)
            plugins.append({"alias": alias, "id": plugin_id, "version": version, "version_resolved": resolved})
    libraries = []
    for alias, entry in data.get("libraries", {}).items():
        if not isinstance(entry, dict):
            continue
        module = entry.get("module")
        if not module and entry.get("group") and entry.get("name"):
            module = f"{entry['group']}:{entry['name']}"
        if not module:
            continue
        version, resolved = resolve(entry)
        libraries.append({"alias": alias, "module": str(module), "version": version, "version_resolved": resolved})
    return {"file": rel(path, root), "plugins": plugins, "libraries": libraries}, []


def source_set_from_path(path: Path, root: Path) -> str | None:
    parts = path.relative_to(root).parts
    try:
        index = parts.index("src")
    except ValueError:
        return None
    return parts[index + 1] if index + 1 < len(parts) else None


def inspect(root: Path) -> dict[str, Any]:
    build_files, source_files = project_files(root)
    build_entries: list[dict[str, Any]] = []
    catalogs: list[dict[str, Any]] = []
    warnings: list[str] = []
    wrapper_versions: set[str] = set()
    kmp_versions: set[str] = set()
    agp_versions: set[str] = set()
    targets: list[str] = []
    environments: set[str] = set()
    source_set_names: set[str] = set()
    depends_on_edges: list[dict[str, Any]] = []
    manual_depends_on = False
    default_template_applied = False
    default_template_disabled = False
    with_java = False
    embed_bitcode = False
    android_target = False
    publications = False
    cinterop_or_cocoapods = False

    kmp_patterns = (
        re.compile(r"kotlin\s*\(\s*[\"']multiplatform[\"']\s*\)\s*version\s*[\"']([^\"']+)[\"']"),
        re.compile(r"id\s*\(?\s*[\"']org\.jetbrains\.kotlin\.multiplatform[\"']\s*\)?\s*version\s*[\"']([^\"']+)[\"']"),
    )
    agp_pattern = re.compile(r"id\s*\(?\s*[\"']com\.android\.[^\"']+[\"']\s*\)?\s*version\s*[\"']([^\"']+)[\"']")

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
                    if plugin["id"] == "org.jetbrains.kotlin.multiplatform":
                        kmp_versions.add(plugin["version"])
                    else:
                        agp_versions.add(plugin["version"])
            warnings.extend(problems)
            continue
        if path.name == "gradle.properties":
            if re.search(r"^\s*kotlin\.mpp\.applyDefaultHierarchyTemplate\s*=\s*false", text, re.MULTILINE):
                default_template_disabled = True
            continue
        if path.name in {"settings.gradle", "settings.gradle.kts"}:
            continue
        found_versions = {value for pattern in kmp_patterns for value in pattern.findall(text)}
        found_agp = set(agp_pattern.findall(text))
        found_targets: list[str] = []
        for name in TARGET_NAMES:
            count = len(re.findall(rf"\b{re.escape(name)}\s*(?:\([^)]*\))?\s*\{{|\b{re.escape(name)}\s*\([^)]*\)", text))
            found_targets.extend([name] * count)
        found_source_sets = set(re.findall(r"\b(?:sourceSets\.)?(?:named|create|register|getByName)\s*\(\s*[\"']([\w-]+)[\"']", text))
        found_source_sets.update(re.findall(r"\bval\s+(\w+(?:Main|Test))\s+by\s+(?:sourceSets\.)?(?:getting|creating)", text))
        edges = []
        for number, line in enumerate(text.splitlines(), 1):
            match = re.search(r"\bdependsOn\s*\(\s*(\w+)\s*\)", line)
            if match:
                edges.append({"file": rel(path, root), "line": number, "parent": match.group(1)})
        found_dependencies = sorted(set(re.findall(r"([\w.-]+:[\w.-]+):([^\"'\s)]+)", text)))
        kmp_versions.update(found_versions)
        agp_versions.update(found_agp)
        targets.extend(found_targets)
        source_set_names.update(found_source_sets)
        depends_on_edges.extend(edges)
        manual_depends_on = manual_depends_on or bool(edges)
        default_template_applied = default_template_applied or "applyDefaultHierarchyTemplate" in text
        environments.update(name for name in ("browser", "nodejs") if re.search(rf"\b{name}\s*\(", text))
        with_java = with_java or bool(re.search(r"\bwithJava\s*\(", text))
        embed_bitcode = embed_bitcode or "embedBitcode" in text or "-Xembed-bitcode" in text
        android_target = android_target or bool(re.search(r"\bandroidTarget\s*(?:\(|\{)", text))
        publications = publications or "maven-publish" in text or bool(re.search(r"\bpublishing\s*\{", text))
        cinterop_or_cocoapods = cinterop_or_cocoapods or bool(re.search(r"\bcinterops\b|\bcocoapods\s*\{", text))
        if found_versions or found_targets or found_source_sets or edges:
            build_entries.append({
                "file": rel(path, root), "kmp_versions": sorted(found_versions), "agp_versions": sorted(found_agp),
                "targets": found_targets, "source_sets": sorted(found_source_sets), "depends_on": edges,
                "dependencies": [{"module": module, "version": version} for module, version in found_dependencies],
                "environments": sorted(name for name in ("browser", "nodejs") if re.search(rf"\b{name}\s*\(", text)),
                "default_hierarchy_applied": "applyDefaultHierarchyTemplate" in text,
                "with_java": bool(re.search(r"\bwithJava\s*\(", text)),
                "android_target": bool(re.search(r"\bandroidTarget\s*(?:\(|\{)", text)),
                "publishing": "maven-publish" in text or bool(re.search(r"\bpublishing\s*\{", text)),
            })

    source_sets: dict[str, dict[str, Any]] = {}
    declarations: list[dict[str, Any]] = []
    common_platform_imports: list[dict[str, Any]] = []
    for path in source_files:
        source_set = source_set_from_path(path, root)
        if source_set:
            info = source_sets.setdefault(source_set, {"files": 0, "tests": source_set.endswith("Test"), "expect": 0, "actual": 0})
            info["files"] += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        package_match = re.search(r"^\s*package\s+([\w.]+)", text, re.MULTILINE)
        package_name = package_match.group(1) if package_match else ""
        declaration_pattern = re.compile(r"\b(expect|actual)\s+(?:(annotation|enum|value|data)\s+)?(class|interface|object|fun|val|var|typealias)\s+(\w+)")
        for kind, modifier, declaration_kind, name in declaration_pattern.findall(text):
            record = {
                "file": rel(path, root), "source_set": source_set, "kind": kind,
                "declaration": " ".join(part for part in (modifier, declaration_kind) if part),
                "package": package_name, "name": name,
            }
            declarations.append(record)
            if source_set:
                source_sets[source_set][kind] += 1
        if source_set in {"commonMain", "commonTest"}:
            lines = []
            for number, line in enumerate(text.splitlines(), 1):
                if line.strip().startswith("import ") and any(f"import {prefix}" in line for prefix in PLATFORM_IMPORTS):
                    lines.append(number)
            if lines:
                common_platform_imports.append({"file": rel(path, root), "lines": lines})

    expects = {(item["package"], item["name"]) for item in declarations if item["kind"] == "expect"}
    actuals = {(item["package"], item["name"]) for item in declarations if item["kind"] == "actual"}
    target_counts = Counter(targets)
    distinct_targets = sorted(target_counts)
    if not kmp_versions and not build_entries:
        warnings.append("No Kotlin Multiplatform plugin configuration found.")
    if len(distinct_targets) < 2:
        warnings.append("Fewer than two distinct KMP targets found; verify multiplatform plugin is appropriate.")
    if any(count > 1 for count in target_counts.values()):
        warnings.append("Multiple similar target declarations found in one project; split same-platform variants into projects.")
    if manual_depends_on and not default_template_applied and not default_template_disabled:
        warnings.append("Manual dependsOn edges can disable the default hierarchy template; remove them or make template ownership explicit.")
    if default_template_disabled:
        warnings.append("Default hierarchy template is disabled; the project owns the complete source-set graph.")
    if with_java:
        warnings.append("withJava() is deprecated in current KMP; verify whether Gradle Java-plugin integration still requires it.")
    if embed_bitcode:
        warnings.append("Bitcode embedding configuration is obsolete and unsupported in current Kotlin/Native.")
    if android_target:
        warnings.append("androidTarget usage has version-dependent deprecation; review migration to Google's KMP Android plugin/current android DSL.")
    if common_platform_imports:
        warnings.append("Platform-specific imports found in common source sets.")
    if expects - actuals:
        warnings.append("Expect declarations lack a matching actual package/name candidate in scanned source.")
    if actuals - expects:
        warnings.append("Actual declarations lack a matching expect package/name candidate in scanned source.")
    if any(target in APPLE_TARGETS for target in distinct_targets) and platform.system() != "Darwin":
        warnings.append("Apple targets are configured on a non-macOS host; final binaries/tests and cinterop are not fully verifiable.")
    if cinterop_or_cocoapods and any(target in APPLE_TARGETS for target in distinct_targets) and platform.system() != "Darwin":
        warnings.append("Apple cinterop/CocoaPods requires macOS; cross-compilation is disabled for affected targets.")
    if publications and platform.system() != "Darwin" and any(target in APPLE_TARGETS for target in distinct_targets):
        warnings.append("Publishing Apple targets from this host may omit cinterop/final artifacts; publish all coordinates from one capable workflow.")
    resolved_kmp = {value for value in kmp_versions if not value.startswith("version.ref:")}
    for version in resolved_kmp:
        parsed = version_tuple(version)
        if parsed and (2, 4, 0) <= parsed <= (2, 4, 10):
            for gradle in wrapper_versions:
                g = version_tuple(gradle)
                if g and not ((7, 6, 3) <= g <= (9, 5, 0)):
                    warnings.append(f"KMP {version} is outside its fully supported Gradle range with {gradle}.")
            for agp in agp_versions:
                a = version_tuple(agp)
                if a and not ((8, 5, 2) <= a <= (9, 1, 0)):
                    warnings.append(f"KMP {version} is outside its fully supported AGP range with {agp}.")

    return {
        "root": str(root), "host": {"system": platform.system(), "machine": platform.machine()},
        "build_files_scanned": len(build_files), "source_files_scanned": len(source_files),
        "gradle_wrapper_versions": sorted(wrapper_versions), "kmp_versions": sorted(kmp_versions), "agp_versions": sorted(agp_versions),
        "targets": distinct_targets, "target_counts": dict(sorted(target_counts.items())), "environments": sorted(environments),
        "source_sets": dict(sorted(source_sets.items())), "configured_source_sets": sorted(source_set_names),
        "depends_on_edges": depends_on_edges, "expect_actual": declarations,
        "common_platform_imports": common_platform_imports,
        "publishing": publications, "cinterop_or_cocoapods": cinterop_or_cocoapods,
        "gradle": build_entries, "version_catalogs": catalogs,
        "warnings": sorted(set(warnings)),
    }


def print_human(data: dict[str, Any]) -> None:
    print(f"Root: {data['root']}")
    print(f"Host: {data['host']['system']} {data['host']['machine']}")
    print(f"KMP/Gradle: {', '.join(data['kmp_versions']) or 'unresolved'} / {', '.join(data['gradle_wrapper_versions']) or 'no wrapper'}")
    print(f"Targets: {', '.join(data['targets']) or 'none'}")
    print(f"Source sets: {', '.join(data['source_sets']) or 'none'}")
    print(f"Expect/actual declarations: {len(data['expect_actual'])}")
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
