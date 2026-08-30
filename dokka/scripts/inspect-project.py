#!/usr/bin/env python3
"""Inspect Dokka Gradle, Maven, and CLI configuration without generating docs."""

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
BUILD_NAMES = {
    "build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts",
    "gradle.properties", "gradle-wrapper.properties", "libs.versions.toml", "pom.xml",
}
DOKKA_PLUGIN_IDS = {"org.jetbrains.dokka", "org.jetbrains.dokka-javadoc"}
LEGACY_PATTERNS = {
    "DokkaTask": re.compile(r"\bDokkaTask\b"),
    "DokkaCollectorTask": re.compile(r"\bDokkaCollectorTask\b"),
    "dokkaHtml": re.compile(r"\bdokkaHtml\b"),
    "dokkaHtmlMultiModule": re.compile(r"\bdokkaHtmlMultiModule\b"),
    "pluginsMapConfiguration": re.compile(r"\bpluginsMapConfiguration\b"),
}
OPTION_NAMES = {
    "apiVersion", "classpath", "documentedVisibilities", "failOnWarning", "includes",
    "jdkVersion", "languageVersion", "moduleName", "modulePath", "moduleVersion", "offlineMode",
    "outputDir", "outputDirectory", "perPackageOption", "reportUndocumented", "samples", "skip",
    "skipDeprecated", "sourceLinks", "sourceRoots", "suppressAnnotatedWith", "suppressGeneratedFiles",
    "suppressInheritedMembers", "suppressObviousFunctions",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="project root (default: cwd)")
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    return parser.parse_args()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def line_numbers(text: str, pattern: re.Pattern[str]) -> list[int]:
    return [number for number, line in enumerate(text.splitlines(), 1) if pattern.search(line)]


def project_files(root: Path) -> list[Path]:
    result: list[Path] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in IGNORED for part in relative.parts):
            continue
        if not path.is_file():
            continue
        if path.name in BUILD_NAMES or path.name.endswith(".gradle.kts"):
            result.append(path)
        elif path.suffix == ".json" and "dokka" in path.name.lower():
            result.append(path)
    return sorted(result, key=lambda item: item.as_posix())


def resolve_property(value: str, properties: dict[str, str]) -> tuple[str, bool]:
    match = re.fullmatch(r"\$\{([^}]+)}", value.strip())
    if not match:
        return value.strip(), value.strip() != "unresolved"
    key = match.group(1)
    return (properties[key], True) if key in properties else (value.strip(), False)


def inspect_catalog(path: Path, root: Path) -> tuple[list[dict[str, str]], list[str]]:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        return [], [f"Cannot parse {rel(path, root)}: {error}"]
    versions = data.get("versions", {})
    entries: list[dict[str, str]] = []
    for alias, plugin in data.get("plugins", {}).items():
        if not isinstance(plugin, dict) or plugin.get("id") not in DOKKA_PLUGIN_IDS:
            continue
        version = plugin.get("version")
        if isinstance(version, dict):
            reference = version.get("ref")
            version = versions.get(reference, f"version.ref:{reference}")
        entries.append({
            "file": rel(path, root),
            "alias": alias,
            "id": plugin["id"],
            "version": str(version or "unresolved"),
        })
    return entries, []


def inspect_maven(path: Path, root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    try:
        tree = ET.parse(path)
    except (OSError, ET.ParseError) as error:
        return [], [f"Cannot parse {rel(path, root)}: {error}"]
    root_element = tree.getroot()
    properties: dict[str, str] = {}
    for child in root_element:
        if local_name(child.tag) == "properties":
            properties.update({local_name(item.tag): (item.text or "").strip() for item in child})

    entries: list[dict[str, Any]] = []
    for plugin in root_element.iter():
        if local_name(plugin.tag) != "plugin":
            continue
        children = {local_name(child.tag): child for child in plugin}
        group = (children.get("groupId").text or "").strip() if children.get("groupId") is not None else ""
        artifact = (children.get("artifactId").text or "").strip() if children.get("artifactId") is not None else ""
        if group != "org.jetbrains.dokka" or artifact != "dokka-maven-plugin":
            continue
        raw_version = (children.get("version").text or "unresolved").strip() if children.get("version") is not None else "unresolved"
        version, resolved = resolve_property(raw_version, properties)
        configuration = children.get("configuration")
        config_elements = list(configuration.iter()) if configuration is not None else []
        config_values = {
            local_name(item.tag): (item.text or "").strip()
            for item in config_elements
            if local_name(item.tag) in OPTION_NAMES
        }
        executions = children.get("executions")
        goals = sorted({(item.text or "").strip() for item in executions.iter() if local_name(item.tag) == "goal"}) if executions is not None else []
        dokka_plugins: list[dict[str, str]] = []
        for candidate in config_elements:
            if local_name(candidate.tag) != "plugin":
                continue
            plugin_parts = {local_name(item.tag): (item.text or "").strip() for item in candidate}
            if plugin_parts.get("groupId") == "org.jetbrains.dokka":
                dokka_plugins.append({
                    "artifact": plugin_parts.get("artifactId", "unresolved"),
                    "version": plugin_parts.get("version", "unresolved"),
                })
        entries.append({
            "file": rel(path, root),
            "version": version,
            "version_resolved": resolved,
            "in_plugin_management": any(
                local_name(ancestor.tag) == "pluginManagement" and plugin in list(ancestor.iter())
                for ancestor in root_element.iter()
            ),
            "goals": goals,
            "configuration": dict(sorted(config_values.items())),
            "dokka_plugins": dokka_plugins,
        })
    return entries, []


def inspect_cli_json(path: Path, root: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return None, [f"Cannot parse {rel(path, root)}: {error}"]
    if not isinstance(data, dict):
        return None, [f"Dokka CLI config must be a JSON object: {rel(path, root)}"]
    return {
        "file": rel(path, root),
        "output_dir": data.get("outputDir") or data.get("outputDirectory"),
        "source_set_count": len(data.get("sourceSets", [])) if isinstance(data.get("sourceSets", []), list) else 0,
        "plugin_classpath": data.get("pluginsClasspath", []),
        "fail_on_warning": data.get("failOnWarning"),
        "offline_mode": data.get("offlineMode"),
    }, []


def inspect(root: Path) -> dict[str, Any]:
    files = project_files(root)
    gradle: list[dict[str, Any]] = []
    maven: list[dict[str, Any]] = []
    catalogs: list[dict[str, str]] = []
    cli: list[dict[str, Any]] = []
    warnings: list[str] = []
    versions: set[str] = set()
    wrapper_versions: set[str] = set()
    legacy_apis: set[str] = set()
    modes: set[str] = set()
    output_formats: set[str] = set()
    aggregation_projects: set[str] = set()

    plugin_pattern = re.compile(r"org\.jetbrains\.dokka(?:-javadoc)?")
    version_pattern = re.compile(r"id\s*\(?\s*[\"']org\.jetbrains\.dokka(?:-javadoc)?[\"']\s*\)?\s*version\s*[\"']([^\"']+)[\"']")
    artifact_pattern = re.compile(r"org\.jetbrains\.dokka:([\w.-]+):([0-9][\w.-]*)")
    aggregation_pattern = re.compile(r"\bdokka\s*\(\s*project\s*\(\s*[\"']([^\"']+)[\"']")
    task_pattern = re.compile(r"\b(dokkaGenerate(?:Publication(?:Html|Javadoc))?|dokkaGenerateHtml|dokkaHtml(?:MultiModule)?)\b")
    publication_pattern = re.compile(r"\bdokkaPublications\.(html|javadoc)\b")
    option_pattern = re.compile(r"\b(" + "|".join(sorted(OPTION_NAMES)) + r")\b")
    configuration_pattern = re.compile(
        r"\bdokka\s*(?:\{|\()|\bdokka(?:Publications|SourceSets)\b|\bdokka(?:Generate|Html)\w*\b"
    )

    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.name == "gradle-wrapper.properties":
            wrapper_versions.update(re.findall(r"gradle-([0-9][\w.-]*)-(?:bin|all)\.zip", text))
            continue
        if path.name == "libs.versions.toml":
            found, problems = inspect_catalog(path, root)
            catalogs.extend(found)
            warnings.extend(problems)
            versions.update(entry["version"] for entry in found if not entry["version"].startswith("version.ref:"))
            continue
        if path.name == "pom.xml":
            found, problems = inspect_maven(path, root)
            maven.extend(found)
            warnings.extend(problems)
            for entry in found:
                if entry["version_resolved"]:
                    versions.add(entry["version"])
                versions.update(plugin["version"] for plugin in entry["dokka_plugins"] if plugin["version"] != "unresolved")
                if "dokka" in entry["goals"]:
                    output_formats.add("html")
                if "javadoc" in entry["goals"] or "javadocJar" in entry["goals"]:
                    output_formats.add("javadoc")
            continue
        if path.suffix == ".json":
            found, problems = inspect_cli_json(path, root)
            if found:
                cli.append(found)
            warnings.extend(problems)
            continue
        if path.name == "gradle.properties":
            mode_match = re.search(r"^\s*org\.jetbrains\.dokka\.experimental\.gradle\.pluginMode\s*=\s*(\S+)", text, re.MULTILINE)
            if mode_match:
                modes.add(mode_match.group(1))
            continue
        if not plugin_pattern.search(text) and not configuration_pattern.search(text):
            continue
        literal_versions = set(version_pattern.findall(text))
        artifacts = sorted({f"{name}:{version}" for name, version in artifact_pattern.findall(text)})
        literal_versions.update(version for _, version in artifact_pattern.findall(text))
        versions.update(literal_versions)
        entry_legacy = sorted(name for name, pattern in LEGACY_PATTERNS.items() if pattern.search(text))
        legacy_apis.update(entry_legacy)
        aggregations = sorted(set(aggregation_pattern.findall(text)))
        aggregation_projects.update(aggregations)
        publications = sorted(set(publication_pattern.findall(text)))
        output_formats.update(publications)
        if re.search(r"[\"']org\.jetbrains\.dokka-javadoc[\"']", text):
            output_formats.add("javadoc")
        if re.search(r"[\"']org\.jetbrains\.dokka[\"']", text):
            output_formats.add("html")
        config_values: dict[str, list[int]] = {}
        for option in sorted(set(option_pattern.findall(text))):
            config_values[option] = line_numbers(text, re.compile(rf"\b{re.escape(option)}\b"))
        gradle.append({
            "file": rel(path, root),
            "plugin_lines": line_numbers(text, plugin_pattern),
            "versions": sorted(literal_versions),
            "artifacts": artifacts,
            "legacy_apis": entry_legacy,
            "has_v2_dokka_block": bool(re.search(r"\bdokka\s*\{", text)),
            "publications": publications,
            "aggregation_projects": aggregations,
            "task_mentions": sorted(set(task_pattern.findall(text))),
            "configuration_options": config_values,
            "report_undocumented_true": bool(re.search(r"reportUndocumented(?:\.set)?\s*\(?\s*true", text)),
            "fail_on_warning_true": bool(re.search(r"failOnWarning(?:\.set)?\s*\(?\s*true", text)),
            "offline_mode_true": bool(re.search(r"offlineMode(?:\.set)?\s*\(?\s*true", text)),
        })

    if not gradle and not maven and not catalogs and not cli:
        warnings.append("No Dokka Gradle, Maven, or CLI configuration found.")
    if len({version for version in versions if version != "unresolved"}) > 1:
        warnings.append("Multiple Dokka component versions found; align plugin and Dokka artifacts.")
    if legacy_apis:
        warnings.append("DGP v1 APIs found; migrate task-based configuration to the DGP v2 DSL.")
    if "V2EnabledWithHelpers" in modes:
        warnings.append("DGP v2 migration helpers remain enabled; remove legacy APIs and switch to V2Enabled.")
    if any(entry["report_undocumented_true"] and not entry["fail_on_warning_true"] for entry in gradle):
        warnings.append("reportUndocumented is enabled without failOnWarning in the same Gradle file; warnings may not gate generation.")
    if any(entry["offline_mode_true"] for entry in gradle) or any(entry.get("offline_mode") is True for entry in cli):
        warnings.append("offlineMode is enabled; external declaration links may be unresolved without cached package lists.")
    if any(entry["in_plugin_management"] for entry in maven):
        warnings.append("Dokka Maven plugin is declared in pluginManagement; confirm an active plugin declaration inherits it.")
    if any(entry["configuration"].get("skip", "").lower() == "true" for entry in maven):
        warnings.append("Dokka Maven generation is skipped by configuration.")
    if "javadoc" in output_formats:
        warnings.append("Dokka Javadoc output is Alpha; Maven Javadoc goals are experimental.")
    for entry in cli:
        if not entry["output_dir"] or entry["source_set_count"] == 0 or not entry["plugin_classpath"]:
            warnings.append(f"{entry['file']} lacks outputDir, sourceSets, or pluginsClasspath required for a CLI run.")

    return {
        "root": str(root),
        "build_files_scanned": len(files),
        "gradle_wrapper_versions": sorted(wrapper_versions),
        "gradle_plugin_modes": sorted(modes),
        "gradle": gradle,
        "version_catalog_plugins": catalogs,
        "maven": maven,
        "cli": cli,
        "summary": {
            "versions": sorted(versions),
            "legacy_apis": sorted(legacy_apis),
            "output_formats": sorted(output_formats),
            "aggregation_projects": sorted(aggregation_projects),
        },
        "warnings": sorted(set(warnings)),
    }


def print_human(data: dict[str, Any]) -> None:
    summary = data["summary"]
    print(f"Root: {data['root']}")
    print(f"Build files scanned: {data['build_files_scanned']}")
    print(f"Gradle wrapper: {', '.join(data['gradle_wrapper_versions']) or 'not found'}")
    print(f"Dokka versions: {', '.join(summary['versions']) or 'none'}")
    print(f"Gradle entries: {len(data['gradle'])}; Maven entries: {len(data['maven'])}; CLI configs: {len(data['cli'])}")
    print(f"Formats: {', '.join(summary['output_formats']) or 'none'}")
    print(f"Aggregation projects: {', '.join(summary['aggregation_projects']) or 'none'}")
    print(f"Legacy APIs: {', '.join(summary['legacy_apis']) or 'none'}")
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
