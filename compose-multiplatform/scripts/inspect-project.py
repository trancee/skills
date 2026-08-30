#!/usr/bin/env python3
"""Inspect Compose Multiplatform plugins, targets, source sets, UI code, and resources."""

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

IGNORED = {".cache", ".git", ".gradle", ".idea", "build", "dist", "node_modules", "target", "vendor"}
BUILD_NAMES = {"build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts", "gradle.properties", "libs.versions.toml"}
TARGETS = ("android", "androidLibrary", "androidTarget", "iosArm64", "iosSimulatorArm64", "iosX64", "js", "jvm", "linuxArm64", "linuxX64", "macosArm64", "macosX64", "wasmJs")
COMPOSE_PLUGIN = "org.jetbrains.compose"
COMPILER_PLUGIN = "org.jetbrains.kotlin.plugin.compose"
PLATFORM_IMPORTS = ("android.", "androidx.activity.", "java.", "javax.swing.", "kotlinx.browser.", "platform.")
SOURCE_SIGNALS = {
    "composable": re.compile(r"@Composable\b"),
    "preview": re.compile(r"@Preview\b"),
    "remember": re.compile(r"\bremember\s*\{"),
    "remember_saveable": re.compile(r"\brememberSaveable\b"),
    "mutable_state": re.compile(r"\bmutableStateOf\s*\("),
    "launched_effect": re.compile(r"\bLaunchedEffect\s*\("),
    "disposable_effect": re.compile(r"\bDisposableEffect\s*\("),
    "side_effect": re.compile(r"\bSideEffect\s*\{"),
    "view_model": re.compile(r"\bviewModel\s*\("),
    "lifecycle_collection": re.compile(r"\bcollectAsStateWithLifecycle\s*\("),
    "navigation": re.compile(r"\b(?:NavHost|NavDisplay|rememberNavController)\b"),
    "resources": re.compile(r"\bRes\.(?:drawable|string|font|array|plurals|files)\."),
    "semantics": re.compile(r"\b(?:semantics|contentDescription|stateDescription|Role\.)\b"),
    "test_tag": re.compile(r"\btestTag\s*\("),
    "ui_test": re.compile(r"\brunComposeUiTest\s*\{"),
    "swing_interop": re.compile(r"\b(?:SwingPanel|ComposePanel|ComposeWindow)\b"),
    "web_entry": re.compile(r"\b(?:ComposeViewport|CanvasBasedWindow)\b"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="project root (default: cwd)")
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    return parser.parse_args()


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def project_files(root: Path) -> tuple[list[Path], list[Path], list[Path]]:
    builds: list[Path] = []
    sources: list[Path] = []
    resources: list[Path] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in IGNORED for part in relative.parts) or not path.is_file():
            continue
        if path.name in BUILD_NAMES or path.name.endswith((".gradle", ".gradle.kts")):
            builds.append(path)
        elif path.suffix == ".kt":
            sources.append(path)
        elif "composeResources" in relative.parts:
            resources.append(path)
    key = lambda item: item.as_posix()
    return sorted(builds, key=key), sorted(sources, key=key), sorted(resources, key=key)


def source_set_from_path(path: Path, root: Path) -> str | None:
    parts = path.relative_to(root).parts
    try:
        index = parts.index("src")
    except ValueError:
        return None
    return parts[index + 1] if index + 1 < len(parts) else None


def version_tuple(value: str) -> tuple[int, int, int] | None:
    match = re.match(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?", value)
    if not match:
        return None
    return tuple(int(part or 0) for part in match.groups())


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
        if plugin_id in {COMPOSE_PLUGIN, COMPILER_PLUGIN} or plugin_id.startswith("org.jetbrains.kotlin."):
            version, resolved = resolve(entry)
            plugins.append({"alias": alias, "id": plugin_id, "version": version, "version_resolved": resolved})
    libraries: list[dict[str, Any]] = []
    for alias, entry in sorted(data.get("libraries", {}).items()):
        if not isinstance(entry, dict):
            continue
        module = entry.get("module")
        if not module and entry.get("group") and entry.get("name"):
            module = f"{entry['group']}:{entry['name']}"
        if module and (str(module).startswith("org.jetbrains.compose") or str(module).startswith("org.jetbrains.androidx")):
            version, resolved = resolve(entry)
            libraries.append({"alias": alias, "module": str(module), "version": version, "version_resolved": resolved})
    return {"file": rel(path, root), "plugins": plugins, "libraries": libraries}, []


def applied_direct_plugin(text: str, pattern: str) -> bool:
    return any(re.search(pattern, line) and not re.search(r"\bapply\s+false\b", line) for line in text.splitlines())


def inspect_gradle(path: Path, root: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    is_settings = path.name in {"settings.gradle", "settings.gradle.kts"}
    kotlin_patterns = (
        r"kotlin\s*\(\s*[\"'](?!plugin\.compose[\"'])[\w.-]+[\"']\s*\)\s*version\s*[\"']([^\"']+)[\"']",
        r"id\s*\(?\s*[\"']org\.jetbrains\.kotlin\.(?!plugin\.compose)[\w.-]+[\"']\s*\)?\s*version\s*[\"']([^\"']+)[\"']",
    )
    compose_pattern = r"id\s*\(?\s*[\"']org\.jetbrains\.compose[\"']\s*\)?\s*version\s*[\"']([^\"']+)[\"']"
    compiler_patterns = (
        r"id\s*\(?\s*[\"']org\.jetbrains\.kotlin\.plugin\.compose[\"']\s*\)?\s*version\s*[\"']([^\"']+)[\"']",
        r"kotlin\s*\(\s*[\"']plugin\.compose[\"']\s*\)\s*version\s*[\"']([^\"']+)[\"']",
    )
    kotlin_versions = {value for pattern in kotlin_patterns for value in re.findall(pattern, text)}
    compose_versions = set(re.findall(compose_pattern, text))
    compiler_versions = {value for pattern in compiler_patterns for value in re.findall(pattern, text)}
    aliases = []
    if not is_settings:
        for line in text.splitlines():
            if re.search(r"\bapply\s+false\b", line):
                continue
            aliases.extend(re.findall(r"alias\s*\(\s*libs\.plugins\.([\w.]+)\s*\)", line))
    targets: list[str] = []
    for target in TARGETS:
        count = len(re.findall(rf"\b{re.escape(target)}\s*(?:\([^)]*\))?\s*\{{|\b{re.escape(target)}\s*\([^)]*\)", text))
        targets.extend([target] * count)
    dependencies = sorted(set(re.findall(r"[\"']((?:org\.jetbrains\.compose|org\.jetbrains\.androidx|androidx\.compose)[\w.:-]+)[\"']", text)))
    compose_dsl_candidates = set(re.findall(r"(?<![\w.])compose\.([A-Za-z][\w.]*)", text))
    accessor_roots = {"animation", "animationGraphics", "foundation", "material", "material3", "material3AdaptiveNavigationSuite", "materialIconsExtended", "preview", "runtime", "runtimeSaveable", "ui", "uiTest", "uiTooling", "uiUtil"}
    compose_dsl = sorted(value for value in compose_dsl_candidates if value.split(".", 1)[0] in accessor_roots or value.startswith(("components.", "desktop.", "html.", "web.")))
    source_sets = sorted(set(re.findall(r"\b(?:named|create|getByName)\s*\(\s*[\"']([\w-]+(?:Main|Test|DeviceTest))[\"']", text)))
    source_sets.extend(re.findall(r"\bval\s+(\w+(?:Main|Test|DeviceTest))\s+by\s+(?:sourceSets\.)?(?:getting|creating)", text))
    return {
        "file": rel(path, root), "direct_compose_plugin": not is_settings and applied_direct_plugin(text, r"\bid\s*(?:\(\s*)?[\"']org\.jetbrains\.compose[\"']"),
        "direct_compiler_plugin": not is_settings and applied_direct_plugin(text, r"(?:\bid\s*(?:\(\s*)?[\"']org\.jetbrains\.kotlin\.plugin\.compose[\"']|\bkotlin\s*\(\s*[\"']plugin\.compose[\"'])"),
        "plugin_alias_accessors": sorted(set(aliases)),
        "kotlin_versions": sorted(kotlin_versions), "compose_versions": sorted(compose_versions), "compiler_versions": sorted(compiler_versions),
        "targets": targets, "environments": sorted(name for name in ("browser", "nodejs") if re.search(rf"\b{name}\s*\(", text)),
        "source_sets": sorted(set(source_sets)), "dependencies": dependencies, "compose_dsl_dependencies": compose_dsl,
        "compose_compiler_block": bool(re.search(r"\bcomposeCompiler\s*\{", text)),
        "resource_dependency": "compose.components.resources" in text or any("components-resources" in item for item in dependencies),
        "ui_test_dependency": "compose.uiTest" in text or any(":ui-test" in item for item in dependencies),
        "desktop_distribution": bool(re.search(r"\bnativeDistributions\s*\{|(?<![\w.])compose\.desktop\s*\{", text)),
        "web_compatibility": "composeCompatibilityBrowserDistribution" in text,
        "legacy_compiler_coordinate": "org.jetbrains.compose.compiler:compiler" in text,
        "coroutines_swing": "kotlinx-coroutines-swing" in text,
    }


def inspect_source(path: Path, root: Path) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    source_set = source_set_from_path(path, root)
    signals = {name: len(pattern.findall(text)) for name, pattern in SOURCE_SIGNALS.items()}
    signals = {name: count for name, count in signals.items() if count}
    entry_points = []
    if source_set and source_set.startswith("android") and re.search(r"\bComponentActivity\b.*\bsetContent\s*\{|\bsetContent\s*\{", text, re.DOTALL):
        entry_points.append("android")
    if source_set and source_set.startswith(("ios", "apple")) and re.search(r"\bComposeUIViewController\b", text):
        entry_points.append("ios")
    if source_set and source_set.startswith(("jvm", "desktop")) and re.search(r"\b(?:singleWindowApplication|application)\s*\{", text):
        entry_points.append("desktop")
    if source_set and source_set.startswith(("js", "wasm")) and re.search(r"\b(?:ComposeViewport|CanvasBasedWindow)\s*\(", text):
        entry_points.append("web")
    platform_import_lines = []
    if source_set in {"commonMain", "commonTest"}:
        for number, line in enumerate(text.splitlines(), 1):
            if line.strip().startswith("import ") and any(f"import {prefix}" in line for prefix in PLATFORM_IMPORTS):
                platform_import_lines.append(number)
    blocking_lines = [number for number, line in enumerate(text.splitlines(), 1) if re.search(r"\b(?:runBlocking|Thread\.sleep)\s*(?:\(|\{)", line)]
    global_scope_lines = [number for number, line in enumerate(text.splitlines(), 1) if "GlobalScope" in line]
    reflective_view_model_lines = []
    if source_set in {"commonMain", "commonTest"}:
        reflective_view_model_lines = [number for number, line in enumerate(text.splitlines(), 1) if re.search(r"\bviewModel\s*\(\s*\)", line)]
    if not (signals or entry_points or platform_import_lines or blocking_lines or global_scope_lines or reflective_view_model_lines):
        return None
    return {
        "file": rel(path, root), "source_set": source_set, "signals": signals, "entry_points": entry_points,
        "platform_import_lines": platform_import_lines, "blocking_call_lines": blocking_lines,
        "global_scope_lines": global_scope_lines, "reflective_common_view_model_lines": reflective_view_model_lines,
    }


def inspect_resources(paths: list[Path], root: Path) -> dict[str, Any]:
    by_source_set: dict[str, Counter[str]] = {}
    for path in paths:
        parts = path.relative_to(root).parts
        source_set = source_set_from_path(path, root) or "unknown"
        index = parts.index("composeResources")
        resource_type = parts[index + 1] if index + 1 < len(parts) else "root"
        by_source_set.setdefault(source_set, Counter())[resource_type] += 1
    return {source_set: dict(sorted(counts.items())) for source_set, counts in sorted(by_source_set.items())}


def inspect(root: Path) -> dict[str, Any]:
    build_files, source_files, resource_files = project_files(root)
    warnings: list[str] = []
    catalogs: list[dict[str, Any]] = []
    gradle: list[dict[str, Any]] = []
    for path in build_files:
        if path.name == "libs.versions.toml":
            catalog, problems = inspect_catalog(path, root)
            if catalog:
                catalogs.append(catalog)
            warnings.extend(problems)
        elif path.name.endswith((".gradle", ".gradle.kts")):
            gradle.append(inspect_gradle(path, root))
    alias_plugins = {alias_accessor(plugin["alias"]): plugin for catalog in catalogs for plugin in catalog["plugins"]}
    for entry in gradle:
        alias_ids = {alias_plugins[value]["id"] for value in entry["plugin_alias_accessors"] if value in alias_plugins}
        entry["compose_plugin_applied"] = entry.pop("direct_compose_plugin") or COMPOSE_PLUGIN in alias_ids
        entry["compiler_plugin_applied"] = entry.pop("direct_compiler_plugin") or COMPILER_PLUGIN in alias_ids
        entry["applied_alias_plugin_ids"] = sorted(alias_ids)
    sources = [entry for path in source_files if (entry := inspect_source(path, root))]
    targets = [target for entry in gradle for target in entry["targets"]]
    target_counts = Counter(targets)
    compose_versions = {version for entry in gradle for version in entry["compose_versions"]}
    kotlin_versions = {version for entry in gradle for version in entry["kotlin_versions"]}
    compiler_versions = {version for entry in gradle for version in entry["compiler_versions"]}
    used_aliases = {value for entry in gradle for value in entry["plugin_alias_accessors"]}
    for accessor in used_aliases:
        plugin = alias_plugins.get(accessor)
        if not plugin or not plugin["version_resolved"] or not plugin["version"]:
            continue
        if plugin["id"] == COMPOSE_PLUGIN:
            compose_versions.add(plugin["version"])
        elif plugin["id"] == COMPILER_PLUGIN:
            compiler_versions.add(plugin["version"])
        elif plugin["id"].startswith("org.jetbrains.kotlin."):
            kotlin_versions.add(plugin["version"])
    has_compose_source = any(entry["signals"].get("composable") for entry in sources)
    has_resources = bool(resource_files) or any(entry["signals"].get("resources") for entry in sources)
    if has_compose_source and not any(entry["compose_plugin_applied"] for entry in gradle):
        warnings.append("@Composable source found but no applied org.jetbrains.compose plugin was detected.")
    for entry in gradle:
        if entry["compose_plugin_applied"] and not entry["compiler_plugin_applied"]:
            warnings.append(f"{entry['file']} applies org.jetbrains.compose without org.jetbrains.kotlin.plugin.compose.")
    if kotlin_versions and compiler_versions and kotlin_versions != compiler_versions:
        warnings.append(f"Kotlin versions {sorted(kotlin_versions)} do not exactly match Compose compiler plugin versions {sorted(compiler_versions)}.")
    for compose_version in compose_versions:
        parsed_compose = version_tuple(compose_version)
        if parsed_compose and parsed_compose >= (1, 8, 0):
            for kotlin_version in kotlin_versions:
                parsed_kotlin = version_tuple(kotlin_version)
                if parsed_kotlin and parsed_kotlin < (2, 1, 0):
                    warnings.append(f"Compose Multiplatform {compose_version} requires Kotlin 2.1.0 or newer; found {kotlin_version}.")
    if any(entry["compose_dsl_dependencies"] for entry in gradle) and any((version_tuple(version) or (0, 0, 0)) >= (1, 12, 0) for version in compose_versions):
        warnings.append("Deprecated Compose dependency accessor found for Compose 1.12+; use direct artifact coordinates from the release component table.")
    if any(entry["legacy_compiler_coordinate"] for entry in gradle):
        warnings.append("Legacy org.jetbrains.compose.compiler:compiler coordinate found; use the Kotlin Compose compiler Gradle plugin.")
    if any(entry["platform_import_lines"] for entry in sources):
        warnings.append("Platform-specific imports found in common Compose source sets.")
    if any(entry["reflective_common_view_model_lines"] for entry in sources):
        warnings.append("Parameterless viewModel() found in common code; provide an initializer/factory for non-JVM targets.")
    if any(entry["blocking_call_lines"] for entry in sources):
        warnings.append("Blocking call candidate found in Compose-related source.")
    if any(entry["global_scope_lines"] for entry in sources):
        warnings.append("GlobalScope candidate found in Compose-related source; use lifecycle/composition-owned scope.")
    if has_resources and not any(entry["resource_dependency"] for entry in gradle):
        warnings.append("Compose resources found/used without a detected compose components resources dependency.")
    if any(entry["signals"].get("ui_test") for entry in sources) and not any(entry["ui_test_dependency"] for entry in gradle):
        warnings.append("runComposeUiTest found without a detected Compose UI test dependency.")
    if "jvm" in target_counts and any(entry["signals"].get("view_model") or entry["signals"].get("lifecycle_collection") for entry in sources) and not any(entry["coroutines_swing"] for entry in gradle):
        warnings.append("Desktop ViewModel/lifecycle use found without a detected kotlinx-coroutines-swing dependency.")
    return {
        "root": str(root), "host": {"system": platform.system(), "machine": platform.machine()},
        "build_files_scanned": len(build_files), "source_files_scanned": len(source_files),
        "kotlin_versions": sorted(kotlin_versions), "compose_versions": sorted(compose_versions), "compiler_versions": sorted(compiler_versions),
        "targets": sorted(target_counts), "target_counts": dict(sorted(target_counts.items())),
        "gradle": gradle, "version_catalogs": catalogs, "sources": sources,
        "resources": inspect_resources(resource_files, root), "warnings": sorted(set(warnings)),
    }


def print_human(data: dict[str, Any]) -> None:
    print(f"Root: {data['root']}")
    print(f"Host: {data['host']['system']} {data['host']['machine']}")
    print(f"Kotlin/Compose/compiler: {', '.join(data['kotlin_versions']) or 'unresolved'} / {', '.join(data['compose_versions']) or 'unresolved'} / {', '.join(data['compiler_versions']) or 'unresolved'}")
    print(f"Targets: {', '.join(data['targets']) or 'none'}")
    print(f"Compose source files: {len(data['sources'])}")
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
