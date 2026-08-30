#!/usr/bin/env python3
"""Inspect Spotless Gradle and Maven configuration without running the build."""

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
    "build.gradle",
    "build.gradle.kts",
    "settings.gradle",
    "settings.gradle.kts",
    "libs.versions.toml",
    "pom.xml",
    "gradle-wrapper.properties",
}
PLUGIN_IDS = {"com.diffplug.spotless", "com.diffplug.gradle.spotless"}
LANGUAGES = {
    "antlr4", "cpp", "flexmark", "freshmark", "gherkin", "go", "groovy", "groovyGradle",
    "java", "javascript", "json", "kotlin", "kotlinGradle", "markdown", "pom", "protobuf",
    "python", "rdf", "scala", "scss", "shell", "sql", "typescript", "yaml",
}
FORMATTER_STEPS = {
    "adocfmt", "biome", "black", "clangFormat", "cleanthat", "dbeaverSql", "diktat",
    "eclipse", "eclipseCdt", "eclipseWtp", "endWithNewline", "eslint", "flexmark",
    "forbidModuleImports", "forbidRegex", "forbidWildcardImports", "formatAnnotations",
    "gofmt", "googleJavaFormat", "greclipse", "idea", "importOrder", "indent", "jackson",
    "ktfmt", "ktlint", "licenseHeader", "nativeCmd", "palantirJavaFormat", "prettier",
    "princeOfSpace", "removeUnusedImports", "replace", "replaceRegex", "scalafmt", "shfmt",
    "shortenFullyQualifiedTypes", "sortPom", "tableTestFormatter", "toggleOffOn",
    "trimTrailingWhitespace", "tsfmt", "versionCatalog",
}
VERSIONED_STEPS = {
    "adocfmt", "biome", "black", "clangFormat", "cleanthat", "dbeaverSql", "diktat",
    "eclipse", "eclipseCdt", "eclipseWtp", "eslint", "flexmark", "googleJavaFormat",
    "greclipse", "idea", "ktfmt", "ktlint", "palantirJavaFormat", "prettier",
    "princeOfSpace", "scalafmt", "shfmt", "tableTestFormatter", "tsfmt",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="project root (default: cwd)")
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    return parser.parse_args()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def project_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in IGNORED for part in relative.parts):
            continue
        if path.is_file() and (path.name in BUILD_NAMES or path.name.endswith(".gradle.kts")):
            files.append(path)
    return sorted(files, key=lambda item: item.as_posix())


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def line_numbers(text: str, pattern: re.Pattern[str]) -> list[int]:
    return [number for number, line in enumerate(text.splitlines(), 1) if pattern.search(line)]


def add_unique(target: set[str], values: list[str]) -> None:
    target.update(value.strip() for value in values if value.strip())


def resolve_property(value: str, properties: dict[str, str]) -> tuple[str, bool]:
    match = re.fullmatch(r"\$\{([^}]+)}", value.strip())
    if not match:
        return value.strip(), True
    name = match.group(1)
    return (properties[name], True) if name in properties else (value.strip(), False)


def inspect_version_catalog(path: Path) -> list[dict[str, Any]]:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return []
    versions = data.get("versions", {})
    result: list[dict[str, Any]] = []
    for alias, entry in data.get("plugins", {}).items():
        if isinstance(entry, str):
            continue
        plugin_id = entry.get("id")
        if plugin_id not in PLUGIN_IDS:
            continue
        version = entry.get("version")
        if isinstance(version, dict):
            ref = version.get("ref")
            version = versions.get(ref, f"version.ref:{ref}")
        result.append({"alias": alias, "id": plugin_id, "version": str(version or "unresolved")})
    return result


def inspect_maven(path: Path, root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    try:
        tree = ET.parse(path)
    except (OSError, ET.ParseError) as error:
        return [], [f"Cannot parse {rel(path, root)}: {error}"]
    root_element = tree.getroot()
    properties: dict[str, str] = {}
    for child in root_element:
        if local_name(child.tag) == "properties":
            properties.update({local_name(item.tag): (item.text or "").strip() for item in child})
    property_skips = sorted(
        f"{name}={properties[name]}"
        for name in ("spotless.skip", "spotless.check.skip", "spotless.apply.skip")
        if name in properties
    )

    found: list[dict[str, Any]] = []
    for plugin in root_element.iter():
        if local_name(plugin.tag) != "plugin":
            continue
        children = {local_name(child.tag): child for child in plugin}
        group = (children.get("groupId").text or "").strip() if children.get("groupId") is not None else ""
        artifact = (children.get("artifactId").text or "").strip() if children.get("artifactId") is not None else ""
        if group != "com.diffplug.spotless" or artifact != "spotless-maven-plugin":
            continue
        raw_version = (children.get("version").text or "unresolved").strip() if children.get("version") is not None else "unresolved"
        version, resolved = resolve_property(raw_version, properties)
        config = children.get("configuration")
        elements = list(config.iter()) if config is not None else []
        tags = [local_name(item.tag) for item in elements]
        values = {(local_name(item.tag), (item.text or "").strip()) for item in elements}
        formatter_elements = [item for item in elements if local_name(item.tag) in FORMATTER_STEPS]
        unpinned_steps = sorted({
            local_name(item.tag)
            for item in formatter_elements
            if local_name(item.tag) in VERSIONED_STEPS
            and not any(local_name(child.tag) == "version" and (child.text or "").strip() for child in item)
        })
        executions = children.get("executions")
        goals = sorted({(item.text or "").strip() for item in executions.iter() if local_name(item.tag) == "goal"}) if executions is not None else []
        found.append({
            "file": rel(path, root),
            "version": version,
            "version_resolved": resolved,
            "in_plugin_management": any(local_name(ancestor.tag) == "pluginManagement" and plugin in list(ancestor.iter()) for ancestor in root_element.iter()),
            "formats": sorted((set(tags) & LANGUAGES) | ({"generic"} if "format" in tags else set())),
            "formatter_steps": sorted(set(tags) & FORMATTER_STEPS),
            "possibly_unpinned_steps": unpinned_steps,
            "goals": goals,
            "ratchet_refs": sorted(value for tag, value in values if tag == "ratchetFrom" and value),
            "skip_settings": property_skips,
            "has_includes": "includes" in tags,
            "has_excludes": "excludes" in tags,
            "has_lint_suppressions": "lintSuppressions" in tags,
        })
    return found, warnings


def inspect(root: Path) -> dict[str, Any]:
    files = project_files(root)
    gradle_entries: list[dict[str, Any]] = []
    maven_entries: list[dict[str, Any]] = []
    warnings: list[str] = []
    wrapper_versions: set[str] = set()
    catalog_plugins: list[dict[str, Any]] = []
    all_steps: set[str] = set()
    gradle_steps: set[str] = set()
    all_formats: set[str] = set()
    all_ratchets: set[str] = set()
    suppressions: set[str] = set()

    plugin_pattern = re.compile(r"com\.diffplug(?:\.gradle)?\.spotless")
    version_pattern = re.compile(r"(?:id\s*\(?\s*[\"']com\.diffplug(?:\.gradle)?\.spotless[\"']\s*\)?\s*version\s*)[\"']([^\"']+)[\"']")
    block_pattern = re.compile(r"\b(" + "|".join(sorted(LANGUAGES)) + r")\s*(?:\([^)]*\))?\s*\{")
    generic_format_pattern = re.compile(r"\bformat\s*(?:\(\s*)?[\"']([^\"']+)[\"']")
    step_pattern = re.compile(r"\b(" + "|".join(sorted(FORMATTER_STEPS)) + r")\s*(?:\(|[\"'])")
    ratchet_pattern = re.compile(r"ratchetFrom\s*(?:\(\s*)?[\"']([^\"']+)[\"']")
    target_pattern = re.compile(r"\b(target|targetExclude)\s*(?:\(|[\"'])")
    policy_pattern = re.compile(r"\b(lineEndings|encoding)\b")
    suppression_pattern = re.compile(r"\b(ignoreErrorForStep|ignoreErrorForPath|suppressLintsFor)\b")

    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.name == "gradle-wrapper.properties":
            wrapper_versions.update(re.findall(r"gradle-([0-9][0-9A-Za-z.-]*)-(?:bin|all)\.zip", text))
            continue
        if path.name == "libs.versions.toml":
            entries = inspect_version_catalog(path)
            for entry in entries:
                entry["file"] = rel(path, root)
            catalog_plugins.extend(entries)
            continue
        if path.name == "pom.xml":
            entries, parse_warnings = inspect_maven(path, root)
            maven_entries.extend(entries)
            warnings.extend(parse_warnings)
            for entry in entries:
                all_steps.update(entry["formatter_steps"])
                all_formats.update(entry["formats"])
                all_ratchets.update(entry["ratchet_refs"])
                if entry["has_lint_suppressions"]:
                    suppressions.add(f"{entry['file']}:lintSuppressions")
            continue
        if not plugin_pattern.search(text) and "spotless" not in text:
            continue
        versions = sorted(set(version_pattern.findall(text)))
        steps = sorted(set(step_pattern.findall(text)))
        formats = sorted(set(block_pattern.findall(text)) | set(generic_format_pattern.findall(text)))
        ratchets = sorted(set(ratchet_pattern.findall(text)))
        suppress = sorted(set(suppression_pattern.findall(text)))
        all_steps.update(steps)
        gradle_steps.update(steps)
        all_formats.update(formats)
        all_ratchets.update(ratchets)
        suppressions.update(f"{rel(path, root)}:{item}" for item in suppress)
        gradle_entries.append({
            "file": rel(path, root),
            "plugin_lines": line_numbers(text, plugin_pattern),
            "versions": versions,
            "formats": formats,
            "formatter_steps": steps,
            "ratchet_refs": ratchets,
            "target_lines": line_numbers(text, target_pattern),
            "line_policy_lines": line_numbers(text, policy_pattern),
            "suppressions": suppress,
            "enforce_check_disabled": bool(re.search(r"enforceCheck\s*(?:\(\s*false\s*\)|\s+false)", text)),
            "custom_steps": len(re.findall(r"\bcustom(?:Lazy)?\s*(?:\(|[\"'])", text)),
            "custom_version_bumps": len(re.findall(r"bumpThisNumberIfACustomStepChanges", text)),
        })

    explicit_versions = {version for entry in gradle_entries for version in entry["versions"]}
    explicit_versions.update(entry["version"] for entry in catalog_plugins if entry["version"] != "unresolved")
    maven_versions = {entry["version"] for entry in maven_entries}
    if not gradle_entries and not catalog_plugins and not maven_entries:
        warnings.append("No Spotless Gradle or Maven plugin declaration found.")
    if len(explicit_versions) > 1:
        warnings.append("Multiple Spotless Gradle plugin versions found; verify intentional build boundaries.")
    if len(maven_versions) > 1:
        warnings.append("Multiple Spotless Maven plugin versions found; verify parent/property resolution.")
    if any(not entry["version_resolved"] for entry in maven_entries):
        warnings.append("At least one Maven Spotless version property is unresolved.")
    if any(entry["in_plugin_management"] for entry in maven_entries):
        warnings.append("Spotless is declared in pluginManagement; confirm an active plugin declaration inherits it.")
    if any(entry["enforce_check_disabled"] for entry in gradle_entries):
        warnings.append("Gradle enforceCheck is disabled; confirm CI invokes spotlessCheck explicitly.")
    if any(setting.endswith("=true") for entry in maven_entries for setting in entry["skip_settings"]):
        warnings.append("A Maven Spotless skip setting is true; enforcement may be disabled.")
    if suppressions:
        warnings.append("Spotless error/lint suppressions exist; verify each exception is narrow and documented.")
    if any(ref.upper() == "HEAD" for ref in all_ratchets):
        warnings.append("ratchetFrom uses HEAD; prefer a stable remote ref or tag.")
    for entry in gradle_entries:
        if entry["custom_steps"] > entry["custom_version_bumps"]:
            warnings.append(f"{entry['file']} has custom steps without matching cache-version bumps.")

    gradle_unpinned = {
        step
        for step in gradle_steps & VERSIONED_STEPS
        if not any(
            re.search(rf"\b{re.escape(step)}\s*(?:\(\s*)?[\"']", path.read_text(encoding="utf-8", errors="replace"))
            for path in files
            if path.name.endswith((".gradle", ".gradle.kts"))
        )
    }
    maven_unpinned = {step for entry in maven_entries for step in entry["possibly_unpinned_steps"]}
    unpinned = sorted(gradle_unpinned | maven_unpinned)

    return {
        "root": str(root),
        "build_files_scanned": len(files),
        "gradle_wrapper_versions": sorted(wrapper_versions),
        "gradle": gradle_entries,
        "version_catalog_plugins": catalog_plugins,
        "maven": maven_entries,
        "summary": {
            "formats": sorted(all_formats),
            "formatter_steps": sorted(all_steps),
            "ratchet_refs": sorted(all_ratchets),
            "suppressions": sorted(suppressions),
            "possibly_unpinned_steps": unpinned,
        },
        "warnings": sorted(set(warnings)),
    }


def print_human(data: dict[str, Any]) -> None:
    summary = data["summary"]
    print(f"Root: {data['root']}")
    print(f"Build files scanned: {data['build_files_scanned']}")
    print(f"Gradle wrapper: {', '.join(data['gradle_wrapper_versions']) or 'not found'}")
    print(f"Gradle entries: {len(data['gradle'])}; Maven entries: {len(data['maven'])}")
    print(f"Formats: {', '.join(summary['formats']) or 'none detected'}")
    print(f"Formatter steps: {', '.join(summary['formatter_steps']) or 'none detected'}")
    print(f"Ratchet refs: {', '.join(summary['ratchet_refs']) or 'none'}")
    print(f"Possibly unpinned: {', '.join(summary['possibly_unpinned_steps']) or 'none'}")
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
    print(json.dumps(data, indent=2, sort_keys=True) if args.json else "", end="" if args.json else "")
    if args.json:
        print()
    else:
        print_human(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
