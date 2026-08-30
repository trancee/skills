#!/usr/bin/env python3
"""Map resolved-looking Kotlin ecosystem coordinates to official API references."""

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
    "libs.versions.toml", "pom.xml", "gradle.lockfile",
}
FAMILIES = [
    ("coroutines", lambda g, a: g == "org.jetbrains.kotlinx" and a.startswith("kotlinx-coroutines-"), "https://kotlinlang.org/api/kotlinx.coroutines/", "https://github.com/Kotlin/kotlinx.coroutines"),
    ("serialization", lambda g, a: g == "org.jetbrains.kotlinx" and a.startswith("kotlinx-serialization-"), "https://kotlinlang.org/api/kotlinx.serialization/", "https://github.com/Kotlin/kotlinx.serialization"),
    ("kotlinx-io", lambda g, a: g == "org.jetbrains.kotlinx" and a.startswith("kotlinx-io-"), "https://kotlinlang.org/api/kotlinx-io/", "https://github.com/Kotlin/kotlinx-io"),
    ("datetime", lambda g, a: g == "org.jetbrains.kotlinx" and a.startswith("kotlinx-datetime"), "https://kotlinlang.org/api/kotlinx-datetime/", "https://github.com/Kotlin/kotlinx-datetime"),
    ("immutable-collections", lambda g, a: g == "org.jetbrains.kotlinx" and a.startswith("kotlinx-collections-immutable"), "https://kotlinlang.org/api/kotlinx.collections.immutable/", "https://github.com/Kotlin/kotlinx.collections.immutable"),
    ("kotlin-test", lambda g, a: g == "org.jetbrains.kotlin" and a.startswith("kotlin-test"), "https://kotlinlang.org/api/core/kotlin-test/", "https://github.com/JetBrains/kotlin"),
    ("kotlin-stdlib", lambda g, a: g == "org.jetbrains.kotlin" and a.startswith("kotlin-stdlib"), "https://kotlinlang.org/api/core/kotlin-stdlib/", "https://github.com/JetBrains/kotlin"),
    ("kotlin-gradle-plugin", lambda g, a: g == "org.jetbrains.kotlin" and a.startswith("kotlin-gradle-plugin"), "https://kotlinlang.org/api/kotlin-gradle-plugin/", "https://github.com/JetBrains/kotlin"),
    ("kotlin-metadata", lambda g, a: g == "org.jetbrains.kotlin" and a == "kotlin-metadata-jvm", "https://kotlinlang.org/api/kotlinx-metadata-jvm/", "https://github.com/JetBrains/kotlin"),
    ("ktor", lambda g, a: g == "io.ktor", "https://api.ktor.io/", "https://github.com/ktorio/ktor"),
    ("compose-material3", lambda g, a: "compose" in g and "material3" in a, "https://kotlinlang.org/api/compose-multiplatform/material3/", "https://github.com/JetBrains/compose-multiplatform-core"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="project root (default: cwd)")
    parser.add_argument("--coordinate", action="append", default=[], help="extra group:artifact:version coordinate")
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    return parser.parse_args()


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def project_files(root: Path) -> list[Path]:
    result: list[Path] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in IGNORED for part in relative.parts) or not path.is_file():
            continue
        if path.name in BUILD_NAMES or path.name.endswith(".gradle.kts"):
            result.append(path)
    return sorted(result, key=lambda item: item.as_posix())


def family_for(group: str, artifact: str) -> tuple[str, str, str] | None:
    for name, predicate, docs, repository in FAMILIES:
        if predicate(group, artifact):
            return name, docs, repository
    return None


def parse_coordinate(value: str) -> tuple[str, str, str] | None:
    parts = value.strip().split(":")
    if len(parts) < 3 or not all(parts[:2]):
        return None
    return parts[0], parts[1], ":".join(parts[2:])


def resolve_version(value: Any, versions: dict[str, Any]) -> tuple[str, bool]:
    if isinstance(value, dict):
        reference = value.get("ref")
        return (str(versions[reference]), True) if reference in versions else (f"version.ref:{reference}", False)
    if value is None:
        return "unresolved", False
    return str(value), True


def catalog_coordinates(path: Path, root: Path) -> tuple[list[tuple[str, str, str, str, bool]], list[str]]:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        return [], [f"Cannot parse {rel(path, root)}: {error}"]
    versions = data.get("versions", {})
    result: list[tuple[str, str, str, str, bool]] = []
    for alias, entry in data.get("libraries", {}).items():
        if not isinstance(entry, dict):
            continue
        module = entry.get("module")
        if not module and entry.get("group") and entry.get("name"):
            module = f"{entry['group']}:{entry['name']}"
        if not module or ":" not in module:
            continue
        group, artifact = str(module).split(":", 1)
        version, resolved = resolve_version(entry.get("version"), versions)
        result.append((group, artifact, version, f"{rel(path, root)}:libraries.{alias}", resolved))
    for alias, entry in data.get("plugins", {}).items():
        if not isinstance(entry, dict) or not str(entry.get("id", "")).startswith("org.jetbrains.kotlin"):
            continue
        version, resolved = resolve_version(entry.get("version"), versions)
        result.append(("org.jetbrains.kotlin", "kotlin-gradle-plugin", version, f"{rel(path, root)}:plugins.{alias}", resolved))
    return result, []


def maven_coordinates(path: Path, root: Path) -> tuple[list[tuple[str, str, str, str, bool]], list[str]]:
    try:
        tree = ET.parse(path)
    except (OSError, ET.ParseError) as error:
        return [], [f"Cannot parse {rel(path, root)}: {error}"]
    project = tree.getroot()
    properties: dict[str, str] = {}
    for child in project:
        if local_name(child.tag) == "properties":
            properties.update({local_name(item.tag): (item.text or "").strip() for item in child})
    result: list[tuple[str, str, str, str, bool]] = []
    for element in project.iter():
        if local_name(element.tag) not in {"dependency", "plugin"}:
            continue
        parts = {local_name(child.tag): (child.text or "").strip() for child in element}
        group, artifact = parts.get("groupId"), parts.get("artifactId")
        if not group or not artifact:
            continue
        version = parts.get("version", "unresolved")
        match = re.fullmatch(r"\$\{([^}]+)}", version)
        resolved = True
        if match:
            key = match.group(1)
            if key in properties:
                version = properties[key]
            else:
                resolved = False
        elif version == "unresolved":
            resolved = False
        result.append((group, artifact, version, rel(path, root), resolved))
    return result, []


def inspect(root: Path, extras: list[str]) -> dict[str, Any]:
    files = project_files(root)
    raw: list[tuple[str, str, str, str, bool]] = []
    warnings: list[str] = []
    kgp_versions: set[str] = set()

    literal_pattern = re.compile(r"([\w.-]+):([\w.-]+):([^\"'\s)]+)")
    kotlin_plugin_patterns = (
        re.compile(r"kotlin\s*\(\s*[\"'][^\"']+[\"']\s*\)\s*version\s*[\"']([^\"']+)[\"']"),
        re.compile(r"id\s*\(?\s*[\"']org\.jetbrains\.kotlin\.[^\"']+[\"']\s*\)?\s*version\s*[\"']([^\"']+)[\"']"),
    )

    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.name == "libs.versions.toml":
            found, problems = catalog_coordinates(path, root)
            raw.extend(found)
            warnings.extend(problems)
            continue
        if path.name == "pom.xml":
            found, problems = maven_coordinates(path, root)
            raw.extend(found)
            warnings.extend(problems)
            continue
        if path.name == "gradle.lockfile":
            for line in text.splitlines():
                coordinate = line.split("=", 1)[0]
                parsed = parse_coordinate(coordinate)
                if parsed:
                    raw.append((*parsed, rel(path, root), True))
            continue
        for group, artifact, version in literal_pattern.findall(text):
            raw.append((group, artifact, version, rel(path, root), not version.startswith("$")))
        for pattern in kotlin_plugin_patterns:
            for version in pattern.findall(text):
                kgp_versions.add(version)
                raw.append(("org.jetbrains.kotlin", "kotlin-gradle-plugin", version, rel(path, root), True))
        for shorthand in re.findall(r"kotlin\s*\(\s*[\"'](stdlib[^\"']*|test[^\"']*)[\"']\s*\)", text):
            artifact = f"kotlin-{shorthand.replace('_', '-')}"
            version = next(iter(kgp_versions)) if len(kgp_versions) == 1 else "kgp-managed"
            raw.append(("org.jetbrains.kotlin", artifact, version, rel(path, root), len(kgp_versions) == 1))

    for value in extras:
        parsed = parse_coordinate(value)
        if not parsed:
            warnings.append(f"Invalid coordinate '{value}'; expected group:artifact:version.")
        else:
            raw.append((*parsed, "--coordinate", True))
    kgp_versions.update(
        version
        for group, artifact, version, _, resolved in raw
        if group == "org.jetbrains.kotlin" and artifact == "kotlin-gradle-plugin" and resolved
    )
    if len(kgp_versions) == 1:
        kgp_version = next(iter(kgp_versions))
        raw = [
            (group, artifact, kgp_version, source, True)
            if group == "org.jetbrains.kotlin" and artifact.startswith(("kotlin-stdlib", "kotlin-test")) and version == "kgp-managed"
            else (group, artifact, version, source, resolved)
            for group, artifact, version, source, resolved in raw
        ]

    records: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for group, artifact, version, source, resolved in raw:
        family = family_for(group, artifact)
        if not family:
            continue
        key = group, artifact, version, source
        if key in seen:
            continue
        seen.add(key)
        name, docs, repository = family
        records.append({
            "coordinate": f"{group}:{artifact}:{version}",
            "group": group,
            "artifact": artifact,
            "version": version,
            "version_resolved": resolved,
            "family": name,
            "api_root": docs,
            "source_repository": repository,
            "declared_at": source,
        })
    records.sort(key=lambda item: (item["family"], item["coordinate"], item["declared_at"]))

    if not records:
        warnings.append("No mapped official Kotlin ecosystem coordinates found.")
    if any(not record["version_resolved"] for record in records):
        warnings.append("At least one mapped dependency version is unresolved; query the effective dependency graph.")
    family_versions: dict[str, set[str]] = {}
    for record in records:
        family_versions.setdefault(record["family"], set()).add(record["version"])
    for family, versions in family_versions.items():
        resolved = {version for version in versions if version not in {"unresolved", "kgp-managed"} and not version.startswith("version.ref:")}
        if len(resolved) > 1:
            warnings.append(f"Multiple declared versions found for {family}: {', '.join(sorted(resolved))}.")
    stdlib = family_versions.get("kotlin-stdlib", set())
    if len(kgp_versions) == 1 and stdlib:
        kgp = next(iter(kgp_versions))
        if any(version not in {kgp, "kgp-managed"} for version in stdlib):
            warnings.append("Explicit Kotlin stdlib version differs from the detected Kotlin Gradle plugin version.")
    if records:
        warnings.append("Official API portals may show current docs or moving source links; verify each dependency at its exact release ref.")

    return {
        "root": str(root),
        "build_files_scanned": len(files),
        "extra_coordinates": extras,
        "detected_kgp_versions": sorted(kgp_versions),
        "references": records,
        "families": sorted(family_versions),
        "warnings": sorted(set(warnings)),
    }


def print_human(data: dict[str, Any]) -> None:
    print(f"Root: {data['root']}")
    print(f"Build files scanned: {data['build_files_scanned']}")
    for record in data["references"]:
        state = "resolved" if record["version_resolved"] else "unresolved"
        print(f"- {record['coordinate']} [{state}] -> {record['api_root']}")
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
    data = inspect(root, args.coordinate)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print_human(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
