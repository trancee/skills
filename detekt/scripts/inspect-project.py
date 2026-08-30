#!/usr/bin/env python3
"""Inspect detekt versions, configuration, baselines, and migration hazards."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

SKIP_DIRS = {".git", ".gradle", ".idea", ".kotlin", "build", "node_modules", "out", "target"}
BUILD_NAMES = {"build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts", "libs.versions.toml"}
PLUGIN_IDS = {"dev.detekt": "2", "io.gitlab.arturbosch.detekt": "1"}
DIRECT_PLUGIN_RE = re.compile(
    r"(?:id\s*\(\s*[\"'](dev\.detekt|io\.gitlab\.arturbosch\.detekt)[\"']\s*\)|"
    r"id\s+[\"'](dev\.detekt|io\.gitlab\.arturbosch\.detekt)[\"'])"
    r"(?:\s*version\s*(?:\(\s*)?[\"']([^\"']+)[\"']\s*\)?)?"
)
ALIAS_RE = re.compile(r"alias\s*\(\s*libs\.plugins\.([A-Za-z0-9_.]+)\s*\)")
TOOL_VERSION_RE = re.compile(r"\btoolVersion\s*(?:=|\.set\s*\()\s*[\"']([^\"']+)")
DETEKT_PLUGIN_RE = re.compile(r"detektPlugins?\s*\(\s*[\"']([^\"']+)[\"']")
CONFIG_RE = re.compile(r"\bconfig\s*\.\s*setFrom\s*\(\s*(?:files?|rootProject\.files?)\s*\(\s*[\"']([^\"']+)")
BASELINE_RE = re.compile(r"\bbaseline\s*(?:\.set\s*\(|=)\s*(?:file\s*\()?\s*[\"']([^\"']+)")
KOTLIN_FILE_RE = re.compile(r"\.kt$")


def walk(root: Path) -> tuple[list[Path], list[Path]]:
    build: list[Path] = []
    all_files: list[Path] = []
    for current, directories, names in os.walk(root):
        directories[:] = sorted(name for name in directories if name not in SKIP_DIRS)
        base = Path(current)
        for name in sorted(names):
            path = base / name
            all_files.append(path)
            if name in BUILD_NAMES:
                build.append(path)
    return build, all_files


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ValueError(f"cannot read {path}: {error}") from error


def relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def alias_accessor(name: str) -> str:
    return re.sub(r"[-_]", ".", name)


def version_value(entry: dict[str, Any], versions: dict[str, Any]) -> str | None:
    value = entry.get("version")
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        ref = value.get("ref")
        if isinstance(ref, str) and isinstance(versions.get(ref), str):
            return versions[ref]
    ref = entry.get("version.ref")
    return versions.get(ref) if isinstance(ref, str) and isinstance(versions.get(ref), str) else None


def catalog_plugins(build_files: list[Path]) -> dict[str, dict[str, str | None]]:
    result: dict[str, dict[str, str | None]] = {}
    for path in build_files:
        if path.name != "libs.versions.toml":
            continue
        try:
            data = tomllib.loads(read_text(path))
        except tomllib.TOMLDecodeError as error:
            raise ValueError(f"cannot parse {path}: {error}") from error
        versions = data.get("versions", {}) if isinstance(data.get("versions"), dict) else {}
        plugins = data.get("plugins", {}) if isinstance(data.get("plugins"), dict) else {}
        for name, entry in plugins.items():
            if not isinstance(name, str) or not isinstance(entry, dict):
                continue
            plugin_id = entry.get("id")
            if plugin_id in PLUGIN_IDS:
                result[alias_accessor(name)] = {"id": plugin_id, "version": version_value(entry, versions)}
    return result


def resolve_literal(root: Path, module: Path, value: str) -> str:
    root_scoped = "$rootDir" in value or "rootProject" in value
    value = value.replace("$rootDir/", "").replace("${rootProject.projectDir}/", "")
    value = value.replace("$projectDir/", "").replace("${project.projectDir}/", "")
    return str(((root if root_scoped else module) / value).resolve())


def inspect(root: Path, expected: str | None) -> dict[str, Any]:
    build_files, all_files = walk(root)
    catalog = catalog_plugins(build_files)
    applications: list[dict[str, Any]] = []
    tool_versions: set[str] = set()
    extension_coordinates: set[str] = set()
    config_paths: set[str] = set()
    baseline_paths: set[str] = set()
    flags = {
        "buildUponDefaultConfig": False,
        "allRules": False,
        "ignoreFailures": False,
        "failNever": False,
        "autoCorrect": False,
        "parallel": False,
        "basePath": False,
    }
    project_kinds: set[str] = set()
    new_report_names = False
    old_report_names = False

    for path in build_files:
        if path.name not in {"build.gradle", "build.gradle.kts"}:
            continue
        source = read_text(path)
        module = path.parent
        module_plugins: list[dict[str, str | None]] = []
        for first, second, version in DIRECT_PLUGIN_RE.findall(source):
            plugin_id = first or second
            module_plugins.append({"id": plugin_id, "version": version or None, "origin": "direct"})
        for alias in ALIAS_RE.findall(source):
            entry = catalog.get(alias)
            if entry:
                module_plugins.append({"id": entry["id"], "version": entry["version"], "origin": f"catalog:{alias}"})
        if module_plugins:
            applications.append(
                {
                    "buildFile": relative(path, root),
                    "module": relative(module, root) if module != root else ".",
                    "plugins": module_plugins,
                }
            )
        tool_versions.update(TOOL_VERSION_RE.findall(source))
        extension_coordinates.update(DETEKT_PLUGIN_RE.findall(source))
        config_paths.update(resolve_literal(root, module, value) for value in CONFIG_RE.findall(source))
        baseline_paths.update(resolve_literal(root, module, value) for value in BASELINE_RE.findall(source))
        flags["buildUponDefaultConfig"] |= bool(re.search(r"\bbuildUponDefaultConfig\s*(?:=|\.set\s*\()\s*true", source))
        flags["allRules"] |= bool(re.search(r"\ballRules\s*(?:=|\.set\s*\()\s*true", source))
        flags["ignoreFailures"] |= bool(re.search(r"\bignoreFailures\s*(?:=|\.set\s*\()\s*true", source))
        flags["failNever"] |= bool(re.search(r"\bfailOnSeverity\s*(?:=|\.set\s*\()[^\n]*Never", source))
        flags["autoCorrect"] |= bool(re.search(r"\bautoCorrect\s*(?:=|\.set\s*\()\s*true|--auto-correct", source))
        flags["parallel"] |= bool(re.search(r"\bparallel\s*(?:=|\.set\s*\()\s*true", source))
        flags["basePath"] |= bool(re.search(r"\bbasePath\s*(?:=|\.set\s*\()", source))
        if "org.jetbrains.kotlin.multiplatform" in source or re.search(r"kotlin\s*\(\s*[\"']multiplatform", source):
            project_kinds.add("multiplatform")
        if re.search(r"com\.android\.(application|library)|kotlin\s*\(\s*[\"']android", source):
            project_kinds.add("android")
        if re.search(r"org\.jetbrains\.kotlin\.jvm|kotlin\s*\(\s*[\"']jvm", source):
            project_kinds.add("jvm")
        new_report_names |= bool(re.search(r"\b(checkstyle|markdown)\.required", source))
        old_report_names |= bool(re.search(r"\b(xml|md)\.required", source))

    plugin_ids = sorted({str(plugin["id"]) for app in applications for plugin in app["plugins"]})
    plugin_versions = sorted({str(plugin["version"]) for app in applications for plugin in app["plugins"] if plugin["version"]})
    majors = {PLUGIN_IDS[plugin_id] for plugin_id in plugin_ids}
    detected_configs = sorted(relative(path, root) for path in all_files if path.name in {"detekt.yml", "detekt.yaml"})
    detected_baselines = sorted(
        relative(path, root) for path in all_files if path.suffix == ".xml" and path.name.startswith("detekt")
    )
    warnings: list[str] = []
    if not applications:
        warnings.append("detekt Gradle plugin not detected.")
    if len(majors) > 1:
        warnings.append("Both detekt 1.x and 2.x plugin IDs are present.")
    if len(plugin_versions) > 1:
        warnings.append(f"Multiple detekt plugin versions detected: {plugin_versions}.")
    if expected and plugin_versions and plugin_versions != [expected]:
        warnings.append(f"Detected detekt versions {plugin_versions}; expected {expected}.")
    if tool_versions and plugin_versions and tool_versions != set(plugin_versions):
        warnings.append(f"toolVersion {sorted(tool_versions)} differs from plugin versions {plugin_versions}.")
    if flags["allRules"]:
        warnings.append("allRules=true enables unstable rules; require an explicit policy.")
    if flags["ignoreFailures"] or flags["failNever"]:
        warnings.append("detekt build failure is disabled; verify CI policy.")
    if flags["autoCorrect"] and (baseline_paths or detected_baselines):
        warnings.append("Auto-correction and baseline are both configured; detekt baseline signatures are unsafe with formatting.")
    if "2" in majors and any(value.startswith("io.gitlab.arturbosch.detekt:") for value in extension_coordinates):
        warnings.append("detekt 2.x plugin uses 1.x extension coordinates.")
    if "1" in majors and any(value.startswith("dev.detekt:") for value in extension_coordinates):
        warnings.append("detekt 1.x plugin uses 2.x extension coordinates.")
    if "2" in majors and old_report_names:
        warnings.append("detekt 2.x build uses 1.x report names xml/md.")
    if "1" in majors and new_report_names:
        warnings.append("detekt 1.x build uses 2.x report names checkstyle/markdown.")
    for value in sorted(config_paths | baseline_paths):
        if not Path(value).exists():
            warnings.append(f"Configured path does not exist: {value}.")

    return {
        "schemaVersion": 1,
        "root": str(root),
        "applications": applications,
        "pluginIds": plugin_ids,
        "pluginVersions": plugin_versions,
        "toolVersions": sorted(tool_versions),
        "extensionCoordinates": sorted(extension_coordinates),
        "projectKinds": sorted(project_kinds),
        "configuredConfigPaths": sorted(config_paths),
        "configuredBaselinePaths": sorted(baseline_paths),
        "detectedConfigs": detected_configs,
        "detectedBaselines": detected_baselines,
        "options": flags,
        "kotlinFileCount": sum(1 for path in all_files if KOTLIN_FILE_RE.search(path.name)),
        "warnings": warnings,
    }


def print_human(report: dict[str, Any]) -> None:
    print(f"Root: {report['root']}")
    print(f"Plugin IDs: {', '.join(report['pluginIds']) or 'none'}")
    print(f"Plugin versions: {', '.join(report['pluginVersions']) or 'unresolved'}")
    print(f"Project kinds: {', '.join(report['projectKinds']) or 'unknown'}")
    print(f"Kotlin files: {report['kotlinFileCount']}")
    print(f"Config files: {', '.join(report['detectedConfigs']) or 'none'}")
    print(f"Baselines: {', '.join(report['detectedBaselines']) or 'none'}")
    for warning in report["warnings"]:
        print(f"WARNING: {warning}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect detekt Gradle versions, configuration, baselines, and migration hazards.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="project root; default: current directory")
    parser.add_argument("--expected-detekt", help="expected detekt plugin/tool version")
    parser.add_argument("--json", action="store_true", help="write JSON report")
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    if not root.is_dir():
        print(f"ERROR: project root is not a directory: {root}", file=sys.stderr)
        return 2
    try:
        report = inspect(root, args.expected_detekt)
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_human(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
