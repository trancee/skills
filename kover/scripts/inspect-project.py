#!/usr/bin/env python3
"""Inspect Kover configuration without executing a build."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

IGNORED = {".git", ".gradle", ".idea", "build", "target", "node_modules"}
BUILD_NAMES = {
    "build.gradle",
    "build.gradle.kts",
    "settings.gradle",
    "settings.gradle.kts",
    "gradle.properties",
    "libs.versions.toml",
    "pom.xml",
}

PATTERNS = {
    "plugin_ids": re.compile(r"org\.jetbrains\.kotlinx\.kover(?:\.aggregation)?"),
    "versions": re.compile(
        r"(?:org\.jetbrains\.kotlinx(?::kover-[\w.-]+:|\.kover(?:\.aggregation)?[^\n]{0,100}?version\s*[=( ]?)|kover(?:Version)?\s*=\s*)[\"']?([0-9]+\.[0-9]+\.[0-9]+(?:[-\w.]*)?)",
        re.IGNORECASE,
    ),
    "kover_projects": re.compile(r"kover\s*\(\s*project\s*\(\s*[\"']([^\"']+)[\"']\s*\)\s*\)"),
    "jacoco": re.compile(r"useJacoco\s*\(([^)]*)\)"),
    "variants": re.compile(r"(?:variant|createVariant)\s*\(\s*[\"']([^\"']+)[\"']"),
    "rules": re.compile(r"rule\s*\(\s*[\"']([^\"']+)[\"']"),
    "bounds": re.compile(r"\b(minBound|maxBound|minValue|maxValue)\s*(?:=|\()\s*([^\n),}]+)"),
    "class_filters": re.compile(r"\b(classes|annotatedBy|inheritedFrom)\s*\(([^\n)]*)\)"),
    "source_sets": re.compile(r"\b(includedSourceSets|excludedSourceSets)\b[^\n]*"),
    "disabled_tests": re.compile(r"\bdisableForTestTasks\b[^\n]*"),
    "report_tasks": re.compile(r"\bkover(?:(?:Html|Xml|Binary)Report|Log|Verify)\w*\b"),
    "maven_goals": re.compile(r"<goal>(instrumentation|report-(?:xml|html|ic)|verify|log)</goal>"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="project root (default: cwd)")
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    return parser.parse_args()


def build_files(root: Path) -> list[Path]:
    result: list[Path] = []
    for path in root.rglob("*"):
        if any(part in IGNORED for part in path.relative_to(root).parts):
            continue
        if path.is_file() and (path.name in BUILD_NAMES or path.name.endswith(".gradle.kts")):
            result.append(path)
    return sorted(result, key=lambda item: item.as_posix())


def matches(pattern: re.Pattern[str], text: str) -> list[str]:
    values: list[str] = []
    for match in pattern.finditer(text):
        value = match.group(0).strip()
        if match.lastindex == 1:
            value = match.group(1).strip()
        elif match.lastindex and match.lastindex > 1:
            value = "=".join(group.strip() for group in match.groups())
        values.append(value)
    return sorted(set(values))


def lines_with(pattern: re.Pattern[str], text: str) -> list[int]:
    return [index for index, line in enumerate(text.splitlines(), 1) if pattern.search(line)]


def relative(path: Path, root: Path) -> str:
    value = path.relative_to(root).as_posix()
    return value or "."


def inspect(root: Path) -> dict[str, Any]:
    files = build_files(root)
    evidence: list[dict[str, Any]] = []
    combined: list[str] = []
    systems: set[str] = set()
    versions: set[str] = set()
    plugin_ids: set[str] = set()
    projects: set[str] = set()
    engines: set[str] = set()
    variants: set[str] = set()
    rules: set[str] = set()
    bounds: set[str] = set()
    filters: set[str] = set()
    source_sets: set[str] = set()
    disabled_tests: set[str] = set()
    report_tasks: set[str] = set()
    maven_goals: set[str] = set()

    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        combined.append(text)
        if path.name == "pom.xml":
            systems.add("maven")
        elif "gradle" in path.name or path.name == "libs.versions.toml":
            systems.add("gradle")

        file_plugins = matches(PATTERNS["plugin_ids"], text)
        file_versions = matches(PATTERNS["versions"], text)
        plugin_ids.update(file_plugins)
        versions.update(file_versions)
        projects.update(matches(PATTERNS["kover_projects"], text))
        variants.update(matches(PATTERNS["variants"], text))
        rules.update(matches(PATTERNS["rules"], text))
        bounds.update(matches(PATTERNS["bounds"], text))
        filters.update(matches(PATTERNS["class_filters"], text))
        source_sets.update(matches(PATTERNS["source_sets"], text))
        disabled_tests.update(matches(PATTERNS["disabled_tests"], text))
        report_tasks.update(matches(PATTERNS["report_tasks"], text))
        maven_goals.update(matches(PATTERNS["maven_goals"], text))
        if file_plugins or "kover-maven-plugin" in text:
            evidence.append(
                {
                    "file": relative(path, root),
                    "kover_lines": lines_with(PATTERNS["plugin_ids"], text)
                    or lines_with(re.compile(r"kover-maven-plugin"), text),
                    "plugin_ids": file_plugins,
                    "versions": file_versions,
                }
            )

    all_text = "\n".join(combined)
    if plugin_ids or "kover-maven-plugin" in all_text:
        engines.add("jacoco" if PATTERNS["jacoco"].search(all_text) else "embedded-kover")
    warnings: list[str] = []
    if not plugin_ids and "kover-maven-plugin" not in all_text:
        warnings.append("No Kover Gradle or Maven plugin declaration found.")
    if len(versions) > 1:
        warnings.append("Multiple explicit Kover versions found; align all Kover components.")
    if "org.jetbrains.kotlinx.kover.aggregation" in plugin_ids:
        warnings.append("Aggregated Settings plugin is prototype/preliminary.")
    if "org.jetbrains.kotlinx.kover" in plugin_ids and "org.jetbrains.kotlinx.kover.aggregation" in plugin_ids:
        warnings.append("Regular and prototype aggregation plugins both appear; verify intentional ownership.")
    if re.search(r"warningInsteadOfFailure\s*=\s*true", all_text):
        warnings.append("Verification is configured as warningInsteadOfFailure=true.")
    if re.search(r"kotlin\s*\(\s*[\"']multiplatform", all_text) or "kotlin-multiplatform" in all_text:
        warnings.append("KMP JS/Native targets are not covered; only common/JVM bytecode through JVM tests is measured.")
    if re.search(r"com\.android\.|kotlin\s*\(\s*[\"']android", all_text):
        warnings.append("Android device instrumentation tests are not covered; local JVM unit tests are.")
    if systems == {"gradle"} and plugin_ids and "mavenCentral()" not in all_text:
        warnings.append("No literal mavenCentral() found; confirm Kover artifacts resolve through a mirror/repository policy.")

    return {
        "root": str(root),
        "build_systems": sorted(systems),
        "build_files_scanned": len(files),
        "evidence": evidence,
        "kover": {
            "plugin_ids": sorted(plugin_ids),
            "versions": sorted(versions),
            "engines": sorted(engines),
            "merged_projects": sorted(projects),
            "variants": sorted(variants),
            "verification_rules": sorted(rules),
            "bounds": sorted(bounds),
            "filters": sorted(filters),
            "source_set_controls": sorted(source_sets),
            "disabled_test_controls": sorted(disabled_tests),
            "report_task_mentions": sorted(report_tasks),
            "maven_goals": sorted(maven_goals),
        },
        "warnings": warnings,
    }


def print_human(data: dict[str, Any]) -> None:
    kover = data["kover"]
    print(f"Root: {data['root']}")
    print(f"Build systems: {', '.join(data['build_systems']) or 'none'}")
    print(f"Build files scanned: {data['build_files_scanned']}")
    for key, label in (
        ("plugin_ids", "Plugins"),
        ("versions", "Versions"),
        ("engines", "Engines"),
        ("merged_projects", "Merged projects"),
        ("variants", "Variants"),
        ("verification_rules", "Rules"),
        ("bounds", "Bounds"),
        ("filters", "Filters"),
        ("report_task_mentions", "Task mentions"),
        ("maven_goals", "Maven goals"),
    ):
        print(f"{label}: {', '.join(kover[key]) or 'none'}")
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
