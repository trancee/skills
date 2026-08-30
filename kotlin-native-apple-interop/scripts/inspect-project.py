#!/usr/bin/env python3
"""Inspect Kotlin/Native Apple framework, cinterop, and exported-API configuration."""

from __future__ import annotations

import argparse
import json
import platform
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

IGNORED = {".cache", ".git", ".gradle", ".idea", "build", "target", "node_modules", "vendor"}
BUILD_NAMES = {
    "build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts",
    "gradle.properties", "Podfile", "Package.swift",
}
APPLE_TARGETS = {
    "iosArm64", "iosSimulatorArm64", "iosX64", "macosArm64", "macosX64", "tvosArm64",
    "tvosSimulatorArm64", "watchosArm32", "watchosArm64", "watchosDeviceArm64", "watchosSimulatorArm64",
}
EXPORT_ANNOTATIONS = {"HiddenFromObjC", "ObjCName", "ShouldRefineInSwift", "Throws", "OverrideInit", "ObjCSignatureOverride"}
DEF_KEYS = {
    "headers", "modules", "language", "package", "headerFilter", "excludeFilter", "compilerOpts",
    "linkerOpts", "excludedFunctions", "staticLibraries", "libraryPaths", "strictEnums", "nonStrictEnums",
    "noStringConversion", "disableDesignatedInitializerChecks", "foreignExceptionMode", "userSetupHint",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="project root (default: cwd)")
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    return parser.parse_args()


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def line_numbers(text: str, pattern: re.Pattern[str]) -> list[int]:
    return [number for number, line in enumerate(text.splitlines(), 1) if pattern.search(line)]


def project_files(root: Path) -> tuple[list[Path], list[Path], list[Path]]:
    builds: list[Path] = []
    definitions: list[Path] = []
    sources: list[Path] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in IGNORED for part in relative.parts) or not path.is_file():
            continue
        if path.name in BUILD_NAMES or path.name.endswith(".gradle.kts") or path.name.endswith(".podspec"):
            builds.append(path)
        elif path.suffix == ".def":
            definitions.append(path)
        elif path.suffix == ".kt":
            sources.append(path)
    key = lambda item: item.as_posix()
    return sorted(builds, key=key), sorted(definitions, key=key), sorted(sources, key=key)


def parse_def(path: Path, root: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    values: dict[str, list[str]] = {}
    for line in text.splitlines():
        if line.strip() == "---":
            break
        match = re.match(r"\s*([\w.]+)\s*=\s*(.*)$", line)
        if not match:
            continue
        key, value = match.group(1), match.group(2).strip()
        base_key = key.split(".", 1)[0]
        if base_key in DEF_KEYS:
            values.setdefault(key, []).append(value)
    return {
        "file": rel(path, root),
        "package": next(iter(values.get("package", [])), None),
        "headers": values.get("headers", []),
        "modules": values.get("modules", []),
        "header_filters": values.get("headerFilter", []),
        "exclude_filters": values.get("excludeFilter", []),
        "compiler_option_keys": sorted(key for key in values if key.startswith("compilerOpts")),
        "linker_option_keys": sorted(key for key in values if key.startswith("linkerOpts")),
        "absolute_path_options": sorted({
            value for key, items in values.items() if key.startswith(("compilerOpts", "linkerOpts", "libraryPaths"))
            for value in items if re.search(r"(?:^|\s)-(?:I|L)?/|(?:^|\s)/", value)
        }),
        "static_libraries": values.get("staticLibraries", []),
        "disable_designated_initializer_checks": any(value.lower() == "true" for value in values.get("disableDesignatedInitializerChecks", [])),
        "foreign_exception_mode": values.get("foreignExceptionMode", []),
        "user_setup_hint": bool(values.get("userSetupHint")),
    }


def inspect(root: Path) -> dict[str, Any]:
    build_files, def_files, source_files = project_files(root)
    build_entries: list[dict[str, Any]] = []
    definitions = [parse_def(path, root) for path in def_files]
    warnings: list[str] = []
    kotlin_versions: set[str] = set()
    targets: set[str] = set()
    base_names: set[str] = set()
    binary_properties: dict[str, str] = {}
    framework_count = 0
    xcframework = False
    transitive_export = False
    direct_integration = False
    cocoapods = False
    cinterops = False
    exports = 0
    api_dependencies = 0
    deployment_settings: set[str] = set()
    duplicate_gradle_packages = False

    kotlin_patterns = (
        re.compile(r"kotlin\s*\(\s*[\"']multiplatform[\"']\s*\)\s*version\s*[\"']([^\"']+)[\"']"),
        re.compile(r"id\s*\(?\s*[\"']org\.jetbrains\.kotlin\.multiplatform[\"']\s*\)?\s*version\s*[\"']([^\"']+)[\"']"),
    )
    for path in build_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.name == "gradle.properties":
            for match in re.finditer(r"^\s*(kotlin\.native\.binary\.[^=]+)=(.*)$", text, re.MULTILINE):
                binary_properties[match.group(1).strip()] = match.group(2).strip()
            continue
        if path.name in {"Podfile", "Package.swift"} or path.name.endswith(".podspec"):
            build_entries.append({"file": rel(path, root), "integration_file": path.name})
            continue
        if path.name in {"settings.gradle", "settings.gradle.kts"}:
            continue
        found_versions = {value for pattern in kotlin_patterns for value in pattern.findall(text)}
        found_targets = {name for name in APPLE_TARGETS if re.search(rf"\b{re.escape(name)}\s*(?:\(|\{{)", text)}
        found_bases = set(re.findall(r"\bbaseName\s*=\s*[\"']([^\"']+)[\"']", text))
        found_packages = re.findall(r"\bpackageName\s*(?:=\s*|\(\s*)[\"']([^\"']+)[\"']", text)
        found_frameworks = len(re.findall(r"\bframework\s*(?:\([^)]*\))?\s*\{", text))
        found_exports = len(re.findall(r"\bexport\s*\(", text))
        found_api = len(re.findall(r"\bapi\s*\(", text))
        found_deployments = set(re.findall(r"\b(?:ios|macos|tvos|watchos)\.deploymentTarget\s*=\s*[\"']([^\"']+)[\"']", text))
        kotlin_versions.update(found_versions)
        targets.update(found_targets)
        base_names.update(found_bases)
        framework_count += found_frameworks
        exports += found_exports
        api_dependencies += found_api
        duplicate_gradle_packages = duplicate_gradle_packages or any(count > 1 for count in Counter(found_packages).values())
        deployment_settings.update(found_deployments)
        xcframework = xcframework or "XCFramework" in text
        transitive_export = transitive_export or bool(re.search(r"\btransitiveExport\s*=\s*true", text))
        direct_integration = direct_integration or "embedAndSignAppleFrameworkForXcode" in text
        cocoapods = cocoapods or bool(re.search(r"\bcocoapods\s*\{", text))
        cinterops = cinterops or bool(re.search(r"\bcinterops\b", text))
        if found_versions or found_targets or found_frameworks or xcframework or cocoapods or cinterops:
            build_entries.append({
                "file": rel(path, root), "kotlin_versions": sorted(found_versions),
                "apple_targets": sorted(found_targets), "framework_blocks": found_frameworks,
                "base_names": sorted(found_bases),
                "static_values": sorted(set(re.findall(r"\bisStatic\s*=\s*(true|false)", text))),
                "exports": found_exports, "api_dependencies": found_api,
                "transitive_export": bool(re.search(r"\btransitiveExport\s*=\s*true", text)),
                "xcframework": "XCFramework" in text, "cocoapods": bool(re.search(r"\bcocoapods\s*\{", text)),
                "cinterops": bool(re.search(r"\bcinterops\b", text)),
                "package_names": sorted(set(found_packages)),
                "binary_options": sorted(set(re.findall(r"\bbinaryOption\s*\(\s*[\"']([^\"']+)[\"']", text))),
                "task_mentions": sorted(set(re.findall(r"\b(?:link(?:Debug|Release)Framework\w+|assemble\w*XCFramework|embedAndSignAppleFrameworkForXcode)\b", text))),
            })

    source_entries: list[dict[str, Any]] = []
    totals = {name: 0 for name in EXPORT_ANNOTATIONS}
    stable_create = stable_dispose = native_alloc = native_free = 0
    public_suspend = 0
    public_value_classes = 0
    native_public_candidates: list[dict[str, Any]] = []
    simple_classes: list[tuple[str, str, str]] = []
    platform_usage_files = 0

    for path in source_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if not any(token in text for token in ("platform.", "kotlinx.cinterop", "ObjCName", "HiddenFromObjC", "ShouldRefineInSwift", "StableRef")):
            continue
        annotations: dict[str, list[int]] = {}
        for name in EXPORT_ANNOTATIONS:
            pattern = re.compile(rf"@(?:kotlin\.native\.)?{re.escape(name)}\b")
            lines = line_numbers(text, pattern)
            if lines:
                annotations[name] = lines
                totals[name] += sum(1 for _ in pattern.finditer(text))
        creates = len(re.findall(r"\bStableRef\.create\s*\(", text))
        disposes = len(re.findall(r"\.dispose\s*\(", text))
        allocs = len(re.findall(r"\bnativeHeap\.(?:alloc|allocArray)\b", text))
        frees = len(re.findall(r"\bnativeHeap\.free\s*\(", text))
        stable_create += creates
        stable_dispose += disposes
        native_alloc += allocs
        native_free += frees
        suspend_lines = line_numbers(text, re.compile(r"\bpublic\s+suspend\s+fun\b|^\s*suspend\s+fun\b"))
        value_lines = line_numbers(text, re.compile(r"\bpublic\s+(?:value|inline)\s+class\b|^\s*(?:value|inline)\s+class\b"))
        public_suspend += len(suspend_lines)
        public_value_classes += len(value_lines)
        platform_imports = re.findall(r"^import\s+platform\.[\w.]+\.([A-Z][A-Za-z0-9_]*)", text, re.MULTILINE)
        platform_usage_files += int(bool(platform_imports))
        candidate_lines = []
        for number, line in enumerate(text.splitlines(), 1):
            if re.search(r"\b(public\s+)?(?:fun|val|var|class|interface)\b", line) and any(re.search(rf"\b{re.escape(name)}\b", line) for name in platform_imports):
                candidate_lines.append(number)
        if candidate_lines:
            native_public_candidates.append({"file": rel(path, root), "lines": candidate_lines})
        package_match = re.search(r"^\s*package\s+([\w.]+)", text, re.MULTILINE)
        package_name = package_match.group(1) if package_match else ""
        for class_name in re.findall(r"^\s*(?:public\s+)?(?:data\s+|sealed\s+|open\s+)?(?:class|interface|object)\s+(\w+)", text, re.MULTILINE):
            simple_classes.append((class_name, package_name, rel(path, root)))
        source_entries.append({
            "file": rel(path, root), "annotations": dict(sorted(annotations.items())),
            "platform_imports": sorted(set(platform_imports)), "native_public_candidate_lines": candidate_lines,
            "stable_ref_create": creates, "stable_ref_dispose": disposes,
            "native_heap_alloc": allocs, "native_heap_free": frees,
            "mem_scoped": len(re.findall(r"\bmemScoped\s*\{", text)),
            "autoreleasepool": len(re.findall(r"\bautoreleasepool\s*\{", text)),
            "public_suspend_lines": suspend_lines, "public_value_class_lines": value_lines,
        })

    if not targets:
        warnings.append("No Apple Kotlin/Native targets found.")
    if targets and framework_count == 0:
        warnings.append("Apple targets found without binaries.framework configuration.")
    if framework_count and platform.system() != "Darwin":
        warnings.append("Current host is not macOS; Apple framework linking, cinterop, and Swift consumer verification are unavailable.")
    if xcframework and len(targets) < 2:
        warnings.append("XCFramework configured with fewer than two detected Apple target slices.")
    if framework_count and len(base_names) != 1:
        warnings.append("Framework slices need one consistent explicit baseName.")
    if exports and api_dependencies == 0:
        warnings.append("Framework exports found without visible api dependencies; only api dependencies can be exported.")
    if transitive_export:
        warnings.append("transitiveExport=true expands API/binary size and disables dead-code elimination for transitive exports.")
    for definition in definitions:
        if definition["headers"] and not definition["header_filters"]:
            warnings.append(f"{definition['file']} imports headers without headerFilter; generated bindings may include transitive headers.")
        if not definition["package"]:
            warnings.append(f"{definition['file']} has no explicit unique package.")
        if definition["absolute_path_options"]:
            warnings.append(f"{definition['file']} contains absolute compiler/linker/library paths; published interop may be machine-specific.")
        if definition["static_libraries"]:
            warnings.append(f"{definition['file']} embeds static libraries; consumers cannot replace or deduplicate them.")
        if definition["disable_designated_initializer_checks"]:
            warnings.append(f"{definition['file']} disables designated initializer checks.")
    package_counts = Counter(item["package"] for item in definitions if item["package"])
    if any(count > 1 for count in package_counts.values()):
        warnings.append("Multiple definition files use the same generated Kotlin package.")
    if duplicate_gradle_packages:
        warnings.append("Multiple cinterop/CocoaPods declarations use the same configured package name.")
    if stable_create > stable_dispose:
        warnings.append("StableRef.create calls outnumber visible dispose calls; inspect callback lifetime ownership.")
    if native_alloc > native_free:
        warnings.append("nativeHeap allocations outnumber visible frees; inspect allocation ownership.")
    if native_public_candidates:
        warnings.append("Platform/native types appear in public declaration candidates; review published-library compatibility.")
    collisions = {name for name, count in Counter(name for name, _, _ in simple_classes).items() if count > 1}
    if framework_count and collisions:
        warnings.append("Same simple exported type names appear across files/packages; Objective-C namespace collisions can be renamed unstably.")
    if platform_usage_files and not deployment_settings:
        warnings.append("Apple platform APIs are used but no deployment target setting was detected; review strong-link availability.")
    if public_suspend:
        warnings.append("Public suspend functions found; compiler-native Swift async export is highly experimental and completion threads require testing.")
    if public_value_classes:
        warnings.append("Public value/inline classes found; Objective-C framework export is not properly supported.")

    return {
        "root": str(root), "host": {"system": platform.system(), "machine": platform.machine()},
        "build_files_scanned": len(build_files), "definition_files_scanned": len(def_files), "source_files_scanned": len(source_files),
        "kotlin_versions": sorted(kotlin_versions), "apple_targets": sorted(targets),
        "framework_count": framework_count, "framework_base_names": sorted(base_names),
        "xcframework": xcframework, "cocoapods": cocoapods, "cinterops": cinterops,
        "direct_integration_task_mentioned": direct_integration, "deployment_settings": sorted(deployment_settings),
        "binary_properties": dict(sorted(binary_properties.items())),
        "gradle": build_entries, "definitions": definitions, "interop_sources": source_entries,
        "totals": {
            "exports": exports, "api_dependencies": api_dependencies, "stable_ref_create": stable_create,
            "stable_ref_dispose": stable_dispose, "native_heap_alloc": native_alloc, "native_heap_free": native_free,
            "public_suspend": public_suspend, "public_value_classes": public_value_classes,
            **{name: count for name, count in sorted(totals.items()) if count},
        },
        "warnings": sorted(set(warnings)),
    }


def print_human(data: dict[str, Any]) -> None:
    print(f"Root: {data['root']}")
    print(f"Host: {data['host']['system']} {data['host']['machine']}")
    print(f"Kotlin: {', '.join(data['kotlin_versions']) or 'unresolved'}")
    print(f"Apple targets: {', '.join(data['apple_targets']) or 'none'}")
    print(f"Frameworks/XCFramework: {data['framework_count']} / {data['xcframework']}")
    print(f"Definition files: {data['definition_files_scanned']}")
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
