#!/usr/bin/env python3
"""Inspect a Kotlin project without invoking its build system."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

SKIP_DIRS = {
    ".git",
    ".gradle",
    ".idea",
    ".kotlin",
    ".mvn",
    "build",
    "dist",
    "node_modules",
    "out",
    "target",
}
BUILD_NAMES = {
    "build.gradle",
    "build.gradle.kts",
    "settings.gradle",
    "settings.gradle.kts",
    "gradle.properties",
    "libs.versions.toml",
    "pom.xml",
}
TARGET_CALLS = {
    "androidTarget",
    "androidNativeArm32",
    "androidNativeArm64",
    "androidNativeX64",
    "androidNativeX86",
    "iosArm64",
    "iosSimulatorArm64",
    "iosX64",
    "js",
    "jvm",
    "linuxArm64",
    "linuxX64",
    "macosArm64",
    "macosX64",
    "mingwX64",
    "tvosArm64",
    "tvosSimulatorArm64",
    "tvosX64",
    "wasmJs",
    "wasmWasi",
    "watchosArm32",
    "watchosArm64",
    "watchosDeviceArm64",
    "watchosSimulatorArm64",
    "watchosX64",
}
PLUGIN_PATTERNS = (
    re.compile(r"\bkotlin\s*\(\s*[\"']([^\"']+)[\"']\s*\)"),
    re.compile(r"\bid\s*\(\s*[\"']((?:org\.jetbrains\.kotlin|com\.android)[^\"']*)[\"']\s*\)"),
    re.compile(r"\balias\s*\(\s*(libs\.plugins\.[A-Za-z0-9_.-]+)\s*\)"),
)
PLUGIN_BLOCK = re.compile(r"(?ms)^\s*plugins\s*\{(.*?)^\s*\}")
DIRECT_KOTLIN_VERSION = re.compile(
    r"(?:\bkotlin\s*\([^)]*\)|\bid\s*\(\s*[\"']org\.jetbrains\.kotlin[^\"']*[\"']\s*\))"
    r"\s*version\s*[\"']([^\"']+)[\"']"
)
CATALOG_KOTLIN_VERSION = re.compile(
    r"(?im)^\s*(?:kotlin|kotlin[-_.]?(?:version|plugin)|kgp)\s*=\s*[\"']([^\"']+)[\"']"
)
MAVEN_KOTLIN_VERSION = re.compile(r"<kotlin\.version>\s*([^<\s]+)\s*</kotlin\.version>")
TARGET_PATTERN = re.compile(r"(?m)^\s*([A-Za-z][A-Za-z0-9]*)\s*\(")


def relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def walk_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for current, directories, names in os.walk(root):
        directories[:] = sorted(name for name in directories if name not in SKIP_DIRS)
        current_path = Path(current)
        files.extend(current_path / name for name in sorted(names))
    return files


def read_config(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ValueError(f"cannot read build file {path}: {error}") from error


def source_set(path: Path, root: Path) -> tuple[str, str] | None:
    parts = path.relative_to(root).parts
    for index, part in enumerate(parts[:-2]):
        if part == "src" and index + 2 < len(parts) and parts[index + 2] in {"kotlin", "java", "resources"}:
            module = "/".join(parts[:index]) or "."
            return module, parts[index + 1]
    return None


def inspect(root: Path) -> dict[str, Any]:
    files = walk_files(root)
    build_files = [path for path in files if path.name in BUILD_NAMES]
    wrappers = [
        path
        for path in files
        if path.name in {"gradlew", "gradlew.bat", "mvnw", "mvnw.cmd"}
    ]
    has_gradle = any(path.name.startswith(("build.gradle", "settings.gradle", "gradle.properties")) for path in build_files) or any(
        path.name.startswith("gradlew") for path in wrappers
    )
    has_maven = any(path.name == "pom.xml" for path in build_files) or any(path.name.startswith("mvnw") for path in wrappers)
    if has_gradle and has_maven:
        build_system = "mixed"
    elif has_gradle:
        build_system = "gradle"
    elif has_maven:
        build_system = "maven"
    else:
        build_system = "standalone" if any(path.suffix in {".kt", ".kts"} for path in files) else "unknown"

    kotlin_sources = [path for path in files if path.suffix == ".kt"]
    kotlin_scripts = [
        path
        for path in files
        if path.suffix == ".kts" and path.name not in {"build.gradle.kts", "settings.gradle.kts"}
    ]
    source_sets = sorted(
        {
            (module, name)
            for path in kotlin_sources
            if (value := source_set(path, root)) is not None
            for module, name in [value]
        }
    )

    plugins: set[str] = set()
    targets: set[str] = set()
    versions: set[str] = set()
    deprecated_kotlin_options: list[str] = []
    for path in build_files:
        text = read_config(path)
        plugin_text = "\n".join(PLUGIN_BLOCK.findall(text))
        for pattern in PLUGIN_PATTERNS:
            plugins.update(pattern.findall(plugin_text))
        if "kotlin-maven-plugin" in text:
            plugins.add("org.jetbrains.kotlin:kotlin-maven-plugin")
        versions.update(DIRECT_KOTLIN_VERSION.findall(plugin_text))
        versions.update(CATALOG_KOTLIN_VERSION.findall(text))
        versions.update(MAVEN_KOTLIN_VERSION.findall(text))
        targets.update(call for call in TARGET_PATTERN.findall(text) if call in TARGET_CALLS)
        if "kotlinOptions" in text:
            deprecated_kotlin_options.append(relative(path, root))

    warnings: list[str] = []
    if build_system == "mixed":
        warnings.append("Both Gradle and Maven build files were found; identify the owning build before running tasks.")
    if build_system == "gradle" and not any(path.name in {"gradlew", "gradlew.bat"} for path in wrappers):
        warnings.append("Gradle files were found without a Gradle wrapper.")
    if build_system == "maven" and not any(path.name in {"mvnw", "mvnw.cmd"} for path in wrappers):
        warnings.append("Maven files were found without a Maven wrapper.")
    if deprecated_kotlin_options:
        warnings.append("Deprecated kotlinOptions blocks were found; use typed compilerOptions when migration is in scope.")

    return {
        "schemaVersion": 1,
        "root": str(root),
        "buildSystem": build_system,
        "wrappers": sorted(relative(path, root) for path in wrappers),
        "buildFiles": sorted(relative(path, root) for path in build_files),
        "plugins": sorted(plugins),
        "kotlinVersionHints": sorted(versions),
        "declaredTargetCalls": sorted(targets),
        "sourceSets": [
            {"module": module, "name": name}
            for module, name in source_sets
        ],
        "kotlinSourceFileCount": len(kotlin_sources),
        "kotlinScriptFileCount": len(kotlin_scripts),
        "deprecatedKotlinOptionsFiles": sorted(deprecated_kotlin_options),
        "warnings": warnings,
    }


def print_human(report: dict[str, Any]) -> None:
    print(f"Root: {report['root']}")
    print(f"Build system: {report['buildSystem']}")
    print(f"Wrappers: {', '.join(report['wrappers']) or 'none'}")
    print(f"Build files: {len(report['buildFiles'])}")
    print(f"Kotlin source files: {report['kotlinSourceFileCount']}")
    print(f"Kotlin script files: {report['kotlinScriptFileCount']}")
    print(f"Plugins: {', '.join(report['plugins']) or 'none detected'}")
    print(f"Kotlin version hints: {', '.join(report['kotlinVersionHints']) or 'none detected'}")
    print(f"Target calls: {', '.join(report['declaredTargetCalls']) or 'none detected'}")
    if report["sourceSets"]:
        print("Source sets:")
        for item in report["sourceSets"]:
            print(f"- {item['module']}: {item['name']}")
    else:
        print("Source sets: none detected")
    for warning in report["warnings"]:
        print(f"WARNING: {warning}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Kotlin build files, targets, and source sets without running the build.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="project root; defaults to the current directory")
    parser.add_argument("--json", action="store_true", help="write the version 1 report as JSON")
    args = parser.parse_args()

    root = args.root.expanduser().resolve()
    if not root.is_dir():
        print(f"ERROR: project root is not a directory: {root}", file=sys.stderr)
        return 2
    try:
        report = inspect(root)
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
