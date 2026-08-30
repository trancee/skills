#!/usr/bin/env python3
"""Inspect Kotlin ABI validation configuration and committed dump layout."""

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
LEGACY_PLUGIN_ID = "org.jetbrains.kotlinx.binary-compatibility-validator"
KOTLIN_PLUGIN_IDS = {
    "org.jetbrains.kotlin.jvm", "org.jetbrains.kotlin.multiplatform", "org.jetbrains.kotlin.android",
}
BUILTIN_OPTIONS = {
    "annotatedWith", "binariesSource", "byNames", "enabled", "excluded", "include", "included",
    "keepLocallyUnsupportedTargets", "legacyDump", "referenceDumpDir", "variants",
}
LEGACY_OPTIONS = {
    "apiDumpDirectory", "ignoredClasses", "ignoredPackages", "ignoredProjects", "inputJar", "klib",
    "nonPublicMarkers", "strictValidation", "validationDisabled",
}
TASK_NAMES = {"apiBuild", "apiCheck", "apiDump", "checkKotlinAbi", "updateKotlinAbi"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="project root (default: cwd)")
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    return parser.parse_args()


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def line_numbers(text: str, pattern: re.Pattern[str]) -> list[int]:
    return [number for number, line in enumerate(text.splitlines(), 1) if pattern.search(line)]


def project_files(root: Path) -> tuple[list[Path], list[Path]]:
    configs: list[Path] = []
    dumps: list[Path] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in IGNORED for part in relative.parts) or not path.is_file():
            continue
        if path.name in BUILD_NAMES or path.name.endswith(".gradle.kts"):
            configs.append(path)
        if path.name.endswith((".api", ".abi")):
            dumps.append(path)
    key = lambda item: item.as_posix()
    return sorted(configs, key=key), sorted(dumps, key=key)


def inspect_catalog(path: Path, root: Path) -> tuple[list[dict[str, str]], list[str]]:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        return [], [f"Cannot parse {rel(path, root)}: {error}"]
    versions = data.get("versions", {})
    result: list[dict[str, str]] = []
    for alias, plugin in data.get("plugins", {}).items():
        if not isinstance(plugin, dict):
            continue
        plugin_id = plugin.get("id")
        if plugin_id != LEGACY_PLUGIN_ID and plugin_id not in KOTLIN_PLUGIN_IDS:
            continue
        version = plugin.get("version")
        if isinstance(version, dict):
            reference = version.get("ref")
            version = versions.get(reference, f"version.ref:{reference}")
        result.append({
            "file": rel(path, root),
            "alias": alias,
            "id": plugin_id,
            "version": str(version or "unresolved"),
        })
    return result, []


def option_lines(text: str, names: set[str]) -> dict[str, list[int]]:
    result: dict[str, list[int]] = {}
    for name in sorted(names):
        lines = line_numbers(text, re.compile(rf"\b{re.escape(name)}\b"))
        if lines:
            result[name] = lines
    return result


def inspect(root: Path) -> dict[str, Any]:
    configs, dump_files = project_files(root)
    gradle: list[dict[str, Any]] = []
    catalogs: list[dict[str, str]] = []
    warnings: list[str] = []
    wrapper_versions: set[str] = set()
    kotlin_versions: set[str] = set()
    legacy_versions: set[str] = set()
    modes: set[str] = set()
    root_project_named = False
    android_present = False

    legacy_id_pattern = re.compile(re.escape(LEGACY_PLUGIN_ID))
    legacy_version_pattern = re.compile(
        r"id\s*\(?\s*[\"']org\.jetbrains\.kotlinx\.binary-compatibility-validator[\"']\s*\)?\s*version\s*[\"']([^\"']+)[\"']"
    )
    kotlin_version_patterns = (
        re.compile(r"kotlin\s*\(\s*[\"'][^\"']+[\"']\s*\)\s*version\s*[\"']([^\"']+)[\"']"),
        re.compile(r"id\s*\(?\s*[\"']org\.jetbrains\.kotlin\.[^\"']+[\"']\s*\)?\s*version\s*[\"']([^\"']+)[\"']"),
    )
    built_in_pattern = re.compile(r"\babiValidation\s*(?:\{|\()")
    legacy_config_pattern = re.compile(r"\bapiValidation\s*\{")
    task_pattern = re.compile(r"\b(" + "|".join(sorted(TASK_NAMES)) + r")\b")

    for path in configs:
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.name == "gradle-wrapper.properties":
            wrapper_versions.update(re.findall(r"gradle-([0-9][\w.-]*)-(?:bin|all)\.zip", text))
            continue
        if path.name == "libs.versions.toml":
            found, problems = inspect_catalog(path, root)
            catalogs.extend(found)
            warnings.extend(problems)
            for entry in found:
                if entry["id"] == LEGACY_PLUGIN_ID:
                    legacy_versions.add(entry["version"])
                else:
                    kotlin_versions.add(entry["version"])
            continue
        if path.name == "settings.gradle" or path.name == "settings.gradle.kts":
            root_project_named = root_project_named or bool(re.search(r"\brootProject\.name\s*=", text))
        if path.name == "gradle.properties":
            for match in re.finditer(r"^\s*([^#!][^=]*)=(.*)$", text, re.MULTILINE):
                key, value = match.group(1).strip(), match.group(2).strip()
                if "abi" in key.lower() or "binary" in key.lower():
                    modes.add(f"{key}={value}")
            continue

        built_in = bool(built_in_pattern.search(text))
        legacy = bool(legacy_id_pattern.search(text) or legacy_config_pattern.search(text))
        if not built_in and not legacy and not task_pattern.search(text):
            android_present = android_present or bool(re.search(r"org\.jetbrains\.kotlin\.android|com\.android\.", text))
            continue
        found_legacy_versions = set(legacy_version_pattern.findall(text))
        found_kotlin_versions = {value for pattern in kotlin_version_patterns for value in pattern.findall(text)}
        legacy_versions.update(found_legacy_versions)
        kotlin_versions.update(found_kotlin_versions)
        android_present = android_present or bool(re.search(r"org\.jetbrains\.kotlin\.android|com\.android\.", text))
        gradle.append({
            "file": rel(path, root),
            "built_in": built_in,
            "legacy": legacy,
            "legacy_plugin_lines": line_numbers(text, legacy_id_pattern),
            "legacy_versions": sorted(found_legacy_versions),
            "kotlin_versions": sorted(found_kotlin_versions),
            "experimental_opt_in": "ExperimentalAbiValidation" in text,
            "built_in_options": option_lines(text, BUILTIN_OPTIONS),
            "legacy_options": option_lines(text, LEGACY_OPTIONS),
            "task_mentions": sorted(set(task_pattern.findall(text))),
            "built_in_disabled": bool(re.search(r"\benabled(?:\.set)?\s*\(?\s*false", text)),
            "legacy_disabled": bool(re.search(r"\bvalidationDisabled\s*=\s*true", text)),
            "strict_unsupported_targets": bool(
                re.search(r"keepLocallyUnsupportedTargets(?:\.set)?\s*\(?\s*false", text)
                or re.search(r"strictValidation\s*=\s*true", text)
            ),
            "maven_publications": "MAVEN_PUBLICATIONS" in text,
            "klib_enabled": bool(re.search(r"\bklib\s*\{", text)),
        })

    built_in_entries = [entry for entry in gradle if entry["built_in"]]
    legacy_entries = [entry for entry in gradle if entry["legacy"]]
    dump_summary = [
        {"file": rel(path, root), "bytes": path.stat().st_size, "kind": "klib" if path.name.endswith(".klib.api") else path.suffix[1:]}
        for path in dump_files
    ]

    if not built_in_entries and not legacy_entries:
        warnings.append("No built-in KGP or legacy binary compatibility validation configuration found.")
    if built_in_entries and legacy_entries:
        warnings.append("Built-in and legacy validators are both configured; treat this as temporary migration state.")
    if legacy_entries:
        warnings.append("The external binary-compatibility-validator plugin is in maintenance mode.")
    if any(not entry["experimental_opt_in"] for entry in built_in_entries):
        warnings.append("Built-in ABI validation lacks a local ExperimentalAbiValidation opt-in in at least one file.")
    if any(entry["built_in_disabled"] or entry["legacy_disabled"] for entry in gradle):
        warnings.append("ABI validation is disabled in at least one configuration.")
    if any(entry["strict_unsupported_targets"] for entry in gradle):
        warnings.append("Unsupported-target preservation/inference is disabled; incomplete hosts should fail ABI validation.")
    if any(entry["maven_publications"] for entry in gradle) and android_present:
        warnings.append("MAVEN_PUBLICATIONS is documented as unsupported for Kotlin/Android and KMP-with-Android projects.")
    if any(entry["klib_enabled"] for entry in legacy_entries) and not root_project_named:
        warnings.append("Legacy KLib validation is enabled without an explicit rootProject.name; dump identity may be unstable.")
    if (built_in_entries or legacy_entries) and not dump_files:
        warnings.append("Validation is configured but no committed .api/.abi dump files were found.")
    if dump_files and not built_in_entries and not legacy_entries:
        warnings.append("ABI dump files exist without a detected validator configuration.")
    if len({version for version in legacy_versions if not version.startswith("version.ref:")}) > 1:
        warnings.append("Multiple legacy validator versions found.")

    return {
        "root": str(root),
        "build_files_scanned": len(configs),
        "gradle_wrapper_versions": sorted(wrapper_versions),
        "kotlin_versions": sorted(kotlin_versions),
        "legacy_validator_versions": sorted(legacy_versions),
        "root_project_named": root_project_named,
        "abi_properties": sorted(modes),
        "gradle": gradle,
        "dumps": dump_summary,
        "summary": {
            "built_in_configurations": len(built_in_entries),
            "legacy_configurations": len(legacy_entries),
            "dump_count": len(dump_files),
            "strict_unsupported_target_configurations": sum(entry["strict_unsupported_targets"] for entry in gradle),
        },
        "version_catalog_plugins": catalogs,
        "warnings": sorted(set(warnings)),
    }


def print_human(data: dict[str, Any]) -> None:
    summary = data["summary"]
    print(f"Root: {data['root']}")
    print(f"Build files scanned: {data['build_files_scanned']}")
    print(f"Gradle wrapper: {', '.join(data['gradle_wrapper_versions']) or 'not found'}")
    print(f"Kotlin versions: {', '.join(data['kotlin_versions']) or 'unresolved'}")
    print(f"Legacy validator versions: {', '.join(data['legacy_validator_versions']) or 'none'}")
    print(f"Built-in configs: {summary['built_in_configurations']}; legacy configs: {summary['legacy_configurations']}")
    print(f"ABI dumps: {summary['dump_count']}")
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
