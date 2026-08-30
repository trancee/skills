#!/usr/bin/env python3
"""Inspect SKIE placement, versions, and configuration without running Gradle."""

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
DIRECT_SKIE_RE = re.compile(r"id\s*\(\s*[\"']co\.touchlab\.skie[\"']\s*\)(?:\s*version\s*[\"']([^\"']+)[\"'])?")
DIRECT_KOTLIN_RE = re.compile(
    r"(?:kotlin\s*\(\s*[\"']multiplatform[\"']\s*\)|id\s*\(\s*[\"']org\.jetbrains\.kotlin\.multiplatform[\"']\s*\))"
    r"(?:\s*version\s*[\"']([^\"']+)[\"'])?"
)
ANNOTATION_RE = re.compile(r"co\.touchlab\.skie:configuration-annotations:([^\"'\s)]+)")
ALIAS_RE = re.compile(r"alias\s*\(\s*libs\.plugins\.([A-Za-z0-9_.]+)\s*\)")
FRAMEWORK_RE = re.compile(r"\bframework\s*\{|\bbinaries\s*\.\s*framework\b|\bXCFramework\s*\(")
COCOAPODS_RE = re.compile(r"native\.cocoapods|\bcocoapods\s*\{")
GROUP_RE = re.compile(r"\bgroup\s*(?:\(|\{)")


def walk(root: Path) -> list[Path]:
    result: list[Path] = []
    for current, directories, names in os.walk(root):
        directories[:] = sorted(name for name in directories if name not in SKIP_DIRS)
        base = Path(current)
        result.extend(base / name for name in sorted(names) if name in BUILD_NAMES)
    return result


def text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ValueError(f"cannot read {path}: {error}") from error


def relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()

def named_block(source: str, name: str) -> str:
    match = re.search(rf"\b{re.escape(name)}\s*\{{", source)
    if match is None:
        return ""
    start = source.find("{", match.start())
    depth = 0
    for index in range(start, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start + 1 : index]
    return source[start + 1 :]


def version_value(entry: dict[str, Any], versions: dict[str, Any]) -> str | None:
    value = entry.get("version")
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        ref = value.get("ref")
        if isinstance(ref, str) and isinstance(versions.get(ref), str):
            return versions[ref]
    ref = entry.get("version.ref")
    if isinstance(ref, str) and isinstance(versions.get(ref), str):
        return versions[ref]
    return None


def alias_accessor(name: str) -> str:
    return re.sub(r"[-_]", ".", name)


def catalogs(paths: list[Path]) -> dict[str, dict[str, str | None]]:
    plugins: dict[str, dict[str, str | None]] = {}
    for path in paths:
        if path.name != "libs.versions.toml":
            continue
        try:
            data = tomllib.loads(text(path))
        except tomllib.TOMLDecodeError as error:
            raise ValueError(f"cannot parse {path}: {error}") from error
        versions = data.get("versions", {}) if isinstance(data.get("versions"), dict) else {}
        entries = data.get("plugins", {}) if isinstance(data.get("plugins"), dict) else {}
        for name, entry in entries.items():
            if not isinstance(name, str) or not isinstance(entry, dict):
                continue
            plugin_id = entry.get("id")
            if plugin_id in {"co.touchlab.skie", "org.jetbrains.kotlin.multiplatform"}:
                plugins[alias_accessor(name)] = {"id": plugin_id, "version": version_value(entry, versions)}
    return plugins


def stable_tuple(value: str) -> tuple[int, ...] | None:
    match = re.fullmatch(r"(\d+(?:\.\d+)+)", value)
    return tuple(int(part) for part in match.group(1).split(".")) if match else None


def compare_versions(actual: str, minimum: str | None, maximum: str | None) -> list[str]:
    warnings: list[str] = []
    parsed = stable_tuple(actual)
    if parsed is None:
        return warnings
    if minimum and (bound := stable_tuple(minimum)) is not None and parsed < bound:
        warnings.append(f"Kotlin {actual} is below documented minimum {minimum}.")
    if maximum and (bound := stable_tuple(maximum)) is not None and parsed > bound:
        warnings.append(f"Kotlin {actual} is above documented maximum {maximum}.")
    return warnings


def inspect(root: Path, expected_skie: str | None, min_kotlin: str | None, max_kotlin: str | None) -> dict[str, Any]:
    paths = walk(root)
    catalog = catalogs(paths)
    applications: list[dict[str, Any]] = []
    kotlin_versions: set[str] = set()
    annotation_versions: set[str] = set()
    maven_central_plugin_management = False

    for path in paths:
        if path.name not in {"build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts"}:
            continue
        source = text(path)
        if path.name.startswith("settings.gradle"):
            plugin_management = named_block(source, "pluginManagement")
            if re.search(r"\bmavenCentral\s*\(", plugin_management):
                maven_central_plugin_management = True
        kotlin_versions.update(value for value in DIRECT_KOTLIN_RE.findall(source) if value)
        annotation_versions.update(ANNOTATION_RE.findall(source))

        module_plugins: list[tuple[str | None, str]] = [(value or None, "direct") for value in DIRECT_SKIE_RE.findall(source)]
        for alias in ALIAS_RE.findall(source):
            entry = catalog.get(alias)
            if entry and entry["id"] == "co.touchlab.skie":
                module_plugins.append((entry["version"], f"catalog:{alias}"))
            if entry and entry["id"] == "org.jetbrains.kotlin.multiplatform" and entry["version"]:
                kotlin_versions.add(str(entry["version"]))
        skie_config = named_block(source, "skie")
        analytics_config = named_block(skie_config, "analytics")
        if module_plugins:
            applications.append(
                {
                    "buildFile": relative(path, root),
                    "module": path.parent.relative_to(root).as_posix() or ".",
                    "versions": sorted({value for value, _ in module_plugins if value}),
                    "declarations": sorted({origin for _, origin in module_plugins}),
                    "frameworkSignal": bool(FRAMEWORK_RE.search(source) or COCOAPODS_RE.search(source)),
                    "configuration": {
                        "skieBlock": bool(skie_config),
                        "groupCount": len(GROUP_RE.findall(skie_config)),
                        "disabled": bool(re.search(r"\bisEnabled\s*\.\s*set\s*\(\s*false\s*\)", skie_config)),
                        "analyticsUploadDisabled": bool(re.search(r"\bdisableUpload\s*\.\s*set\s*\(\s*true\s*\)", analytics_config)),
                        "analyticsDisabled": bool(re.search(r"\benabled\s*\.\s*set\s*\(\s*false\s*\)", analytics_config)),
                        "distributableFramework": "produceDistributableFramework" in skie_config,
                    },
                }
            )

    skie_versions = sorted({version for item in applications for version in item["versions"]})
    warnings: list[str] = []
    if not applications:
        warnings.append("SKIE plugin not detected.")
    for item in applications:
        if not item["frameworkSignal"]:
            warnings.append(f"{item['buildFile']}: SKIE detected without a local framework or CocoaPods signal; verify module placement.")
    if len(skie_versions) > 1:
        warnings.append(f"Multiple SKIE versions detected: {', '.join(skie_versions)}.")
    if expected_skie and skie_versions and skie_versions != [expected_skie]:
        warnings.append(f"Detected SKIE versions {skie_versions}; expected {expected_skie}.")
    if annotation_versions and skie_versions and annotation_versions != set(skie_versions):
        warnings.append(
            "configuration-annotations versions do not match detected SKIE plugin versions: "
            f"annotations={sorted(annotation_versions)}, plugins={skie_versions}."
        )
    for version in sorted(kotlin_versions):
        warnings.extend(compare_versions(version, min_kotlin, max_kotlin))

    return {
        "schemaVersion": 1,
        "root": str(root),
        "skieApplications": applications,
        "skieVersions": skie_versions,
        "kotlinVersions": sorted(kotlin_versions),
        "annotationVersions": sorted(annotation_versions),
        "pluginManagementMavenCentral": maven_central_plugin_management,
        "warnings": warnings,
    }


def print_human(report: dict[str, Any]) -> None:
    print(f"Root: {report['root']}")
    print(f"SKIE applications: {len(report['skieApplications'])}")
    for item in report["skieApplications"]:
        versions = ",".join(item["versions"]) or "unresolved"
        print(f"- {item['buildFile']}: version={versions} frameworkSignal={str(item['frameworkSignal']).lower()}")
    print(f"Kotlin versions: {', '.join(report['kotlinVersions']) or 'unresolved'}")
    print(f"Annotation versions: {', '.join(report['annotationVersions']) or 'none'}")
    print(f"Plugin-management Maven Central: {str(report['pluginManagementMavenCentral']).lower()}")
    for warning in report["warnings"]:
        print(f"WARNING: {warning}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect SKIE Gradle placement, versions, and configuration without running Gradle.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="project root; default: current directory")
    parser.add_argument("--expected-skie", help="expected SKIE version from current docs")
    parser.add_argument("--min-kotlin", help="minimum supported stable Kotlin version")
    parser.add_argument("--max-kotlin", help="maximum supported stable Kotlin version")
    parser.add_argument("--json", action="store_true", help="write JSON report")
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    if not root.is_dir():
        print(f"ERROR: project root is not a directory: {root}", file=sys.stderr)
        return 2
    try:
        report = inspect(root, args.expected_skie, args.min_kotlin, args.max_kotlin)
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
