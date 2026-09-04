#!/usr/bin/env python3
"""Inspect an Android project for Jetpack Compose Material 3 setup and migration signals."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

SKIP_DIRS = {
    ".git",
    ".gradle",
    ".idea",
    ".kotlin",
    ".cache",
    "build",
    "generated",
    "node_modules",
    "out",
}
MAX_FILE_BYTES = 2_000_000


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    files: tuple[str, ...] = ()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect Compose Material 3 dependencies, themes, adaptive UI, and test signals."
    )
    parser.add_argument("--root", default=".", help="Android repository root (default: current directory)")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when warnings are present; inspection errors always exit 2",
    )
    return parser.parse_args()


def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        try:
            if path.stat().st_size <= MAX_FILE_BYTES:
                yield path
        except OSError:
            continue


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def matching_files(files: list[Path], texts: dict[Path, str], pattern: str) -> tuple[Path, ...]:
    regex = re.compile(pattern, re.MULTILINE)
    return tuple(path for path in files if regex.search(texts[path]))


def names(root: Path, paths: Iterable[Path]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(rel(root, path) for path in paths))


def inspect(root: Path) -> dict[str, object]:
    all_files = list(iter_files(root))
    build_files = [
        path
        for path in all_files
        if path.name in {"settings.gradle", "settings.gradle.kts", "gradle.properties", "libs.versions.toml"}
        or path.suffix == ".gradle"
        or path.name.endswith(".gradle.kts")
        or (path.suffix == ".toml" and "gradle" in path.parts)
    ]
    kotlin_files = [path for path in all_files if path.suffix == ".kt"]
    manifest_files = [path for path in all_files if path.name == "AndroidManifest.xml"]
    relevant_files = build_files + kotlin_files + manifest_files
    texts = {path: read_text(path) for path in relevant_files}

    material3_dependency = matching_files(
        build_files,
        texts,
        r"androidx\.compose\.material3(?::|\.)|group\s*=\s*[\"']androidx\.compose\.material3",
    )
    material2_dependency = matching_files(
        build_files,
        texts,
        r"androidx\.compose\.material(?::|[\"'])|group\s*=\s*[\"']androidx\.compose\.material[\"']",
    )
    compose_bom = matching_files(build_files, texts, r"androidx\.compose:compose-bom|compose[-_.]bom")
    compose_plugin = matching_files(
        build_files,
        texts,
        r"org\.jetbrains\.kotlin\.plugin\.compose|kotlin[-_.]plugin[-_.]compose",
    )
    compose_enabled = matching_files(
        build_files,
        texts,
        r"buildFeatures\s*\{[^}]*compose\s*=\s*true|buildFeatures\.compose\s*=\s*true",
    )
    stale_compiler_setting = matching_files(
        build_files, texts, r"kotlinCompilerExtensionVersion|composeOptions\s*\{"
    )

    m3_imports = matching_files(kotlin_files, texts, r"^import androidx\.compose\.material3\.")
    m2_imports = matching_files(kotlin_files, texts, r"^import androidx\.compose\.material\.(?!icons\.)")
    theme_files = matching_files(
        kotlin_files,
        texts,
        r"\bMaterialTheme\s*\(|\blightColorScheme\s*\(|\bdarkColorScheme\s*\(",
    )
    dynamic_color_files = matching_files(
        kotlin_files,
        texts,
        r"\bdynamic(?:Light|Dark)ColorScheme\s*\(",
    )
    unguarded_dynamic_color = tuple(
        path
        for path in dynamic_color_files
        if not re.search(r"SDK_INT|VERSION_CODES\.S|API\s*31", texts[path])
    )
    edge_to_edge_files = matching_files(
        kotlin_files,
        texts,
        r"\benableEdgeToEdge\s*\(|WindowInsets|windowInsetsPadding|imePadding\s*\(",
    )
    accompanist_system_ui = matching_files(
        kotlin_files + build_files,
        texts,
        r"accompanist[-.]systemuicontroller|rememberSystemUiController",
    )
    adaptive_files = matching_files(
        relevant_files,
        texts,
        r"material3(?:\.|:)adaptive|currentWindowAdaptiveInfo|NavigationSuiteScaffold|(?:ListDetail|Supporting)PaneScaffold",
    )
    device_assumption_files = matching_files(
        kotlin_files,
        texts,
        r"\bisTablet\b|ORIENTATION_(?:LANDSCAPE|PORTRAIT)",
    )
    preview_files = matching_files(kotlin_files, texts, r"@Preview\b|@DevicePreviews\b")
    compose_test_files = matching_files(
        kotlin_files,
        texts,
        r"create(?:Android)?ComposeRule|runComposeUiTest|onNodeWith|SemanticsMatcher",
    )
    experimental_files = matching_files(
        kotlin_files,
        texts,
        r"ExperimentalMaterial3(?:Api|ExpressiveApi)|ExperimentalMaterial3AdaptiveApi",
    )

    findings: list[Finding] = []
    if not build_files:
        findings.append(
            Finding("warning", "NO_GRADLE_BUILD", "No Gradle build or version catalog was found under the root.")
        )
    if m3_imports and not material3_dependency:
        findings.append(
            Finding(
                "warning",
                "M3_DEPENDENCY_NOT_RESOLVED",
                "Material3 imports exist, but no Material3 coordinate was found. Resolve the version-catalog/plugin indirection manually.",
                names(root, m3_imports[:8]),
            )
        )
    if material3_dependency and not m3_imports:
        findings.append(
            Finding(
                "info",
                "M3_DEPENDENCY_UNUSED_OR_INDIRECT",
                "A Material3 dependency exists, but no direct Material3 Kotlin import was found.",
                names(root, material3_dependency[:8]),
            )
        )
    if m2_imports and m3_imports:
        findings.append(
            Finding(
                "warning",
                "MATERIAL_GENERATIONS_COEXIST",
                "Material 2 and Material 3 imports coexist. Confirm an explicit staged boundary or complete the clean cutover.",
                names(root, (m2_imports + m3_imports)[:12]),
            )
        )
    if material2_dependency and material3_dependency:
        findings.append(
            Finding(
                "warning",
                "MATERIAL_DEPENDENCIES_COEXIST",
                "Material 2 and Material 3 dependency coordinates coexist. Remove Material 2 after the last intentional caller migrates.",
                names(root, (material2_dependency + material3_dependency)[:12]),
            )
        )
    if compose_plugin and stale_compiler_setting:
        findings.append(
            Finding(
                "warning",
                "MIXED_COMPILER_CONFIGURATION",
                "The Kotlin Compose plugin and legacy composeOptions/compiler-extension settings coexist. Verify the selected Kotlin toolchain and remove stale configuration.",
                names(root, (compose_plugin + stale_compiler_setting)[:12]),
            )
        )
    if unguarded_dynamic_color:
        findings.append(
            Finding(
                "warning",
                "DYNAMIC_COLOR_API_GUARD_NOT_FOUND",
                "Dynamic color calls were found without an API 31/Android 12 guard in the same file.",
                names(root, unguarded_dynamic_color[:12]),
            )
        )
    if accompanist_system_ui:
        findings.append(
            Finding(
                "warning",
                "LEGACY_SYSTEM_UI_CONTROLLER",
                "Accompanist System UI Controller usage was found. Prefer current edge-to-edge Activity/system-bar APIs.",
                names(root, accompanist_system_ui[:12]),
            )
        )
    if device_assumption_files:
        findings.append(
            Finding(
                "warning",
                "DEVICE_ORIENTATION_LAYOUT_ASSUMPTION",
                "Tablet/orientation branching was found. Verify that layout decisions use the current window size/posture instead.",
                names(root, device_assumption_files[:12]),
            )
        )
    if m3_imports and not theme_files:
        findings.append(
            Finding(
                "warning",
                "M3_THEME_NOT_FOUND",
                "Material3 UI imports exist, but no MaterialTheme or light/dark ColorScheme definition was found.",
            )
        )
    if m3_imports and not compose_test_files:
        findings.append(
            Finding(
                "info",
                "NO_COMPOSE_UI_TEST_SIGNALS",
                "No Compose semantic UI test API was found. Confirm whether changed observable behavior needs a durable test.",
            )
        )

    signals = {
        "gradle_build_files": names(root, build_files),
        "kotlin_files": len(kotlin_files),
        "manifest_files": names(root, manifest_files),
        "material3_dependencies": names(root, material3_dependency),
        "material2_dependencies": names(root, material2_dependency),
        "compose_bom": names(root, compose_bom),
        "kotlin_compose_plugin": names(root, compose_plugin),
        "compose_enabled": names(root, compose_enabled),
        "material3_import_files": names(root, m3_imports),
        "material2_import_files": names(root, m2_imports),
        "theme_files": names(root, theme_files),
        "dynamic_color_files": names(root, dynamic_color_files),
        "edge_to_edge_or_inset_files": names(root, edge_to_edge_files),
        "adaptive_files": names(root, adaptive_files),
        "preview_files": names(root, preview_files),
        "compose_test_files": names(root, compose_test_files),
        "experimental_material3_files": names(root, experimental_files),
    }
    return {
        "root": str(root),
        "summary": {
            "files_scanned": len(all_files),
            "build_files": len(build_files),
            "kotlin_files": len(kotlin_files),
            "warnings": sum(item.severity == "warning" for item in findings),
            "info": sum(item.severity == "info" for item in findings),
        },
        "signals": signals,
        "findings": [asdict(item) for item in findings],
    }


def print_human(report: dict[str, object]) -> None:
    summary = report["summary"]
    assert isinstance(summary, dict)
    print(f"Material3 Compose inspection: {report['root']}")
    print(
        f"Scanned {summary['files_scanned']} files; "
        f"{summary['build_files']} build files; {summary['kotlin_files']} Kotlin files."
    )
    findings = report["findings"]
    assert isinstance(findings, list)
    if not findings:
        print("No heuristic findings.")
        return
    for finding in findings:
        assert isinstance(finding, dict)
        print(f"{str(finding['severity']).upper()} [{finding['code']}]: {finding['message']}")
        for path in finding.get("files", ()):  # type: ignore[union-attr]
            print(f"  - {path}")


def main() -> int:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()
    if not root.exists():
        print(f"error: inspection root does not exist: {root}", file=sys.stderr)
        return 2
    if not root.is_dir():
        print(f"error: inspection root is not a directory: {root}", file=sys.stderr)
        return 2

    report = inspect(root)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)

    summary = report["summary"]
    assert isinstance(summary, dict)
    return 1 if args.strict and int(summary["warnings"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
