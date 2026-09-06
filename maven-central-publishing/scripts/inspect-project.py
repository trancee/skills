#!/usr/bin/env python3
"""Inspect Maven/Gradle projects for Sonatype Central Portal publication readiness and risk signals."""

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
    ".cache",
    ".mvn",
    "build",
    "dist",
    "node_modules",
    "out",
    "target",
}
TEXT_SUFFIXES = {".gradle", ".kts", ".xml", ".toml", ".properties", ".yml", ".yaml", ".json"}
TEXT_NAMES = {"pom.xml", "settings.gradle", "settings.gradle.kts", "gradle.properties", "jreleaser.yml", "jreleaser.yaml"}
MAX_FILE_BYTES = 2_000_000


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    files: tuple[str, ...] = ()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect Maven/Gradle/JReleaser configuration for Central Portal publication signals."
    )
    parser.add_argument("--root", default=".", help="Repository root (default: current directory)")
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when warnings are present; inspection errors always exit 2",
    )
    return parser.parse_args()


def iter_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in SKIP_DIRS for part in relative.parts):
            continue
        if path.name not in TEXT_NAMES and path.suffix.lower() not in TEXT_SUFFIXES:
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


def matching(files: Iterable[Path], texts: dict[Path, str], pattern: str) -> tuple[Path, ...]:
    regex = re.compile(pattern, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    return tuple(path for path in files if regex.search(texts[path]))


def names(root: Path, paths: Iterable[Path], limit: int = 24) -> tuple[str, ...]:
    unique = dict.fromkeys(path.relative_to(root).as_posix() for path in paths)
    return tuple(list(unique)[:limit])


def has_inline_secret(text: str) -> bool:
    assignments = re.compile(
        r"(?im)^\s*(?:central|ossrh|sonatype|signing)?[._-]*(?:username|password|token|tokenUsername|tokenPassword|signingKey|signingPassword|secretKeyRingFile)\s*[=:]\s*([^#\r\n]+)"
    )
    xml_values = re.compile(
        r"(?is)<(?:username|password|token|passphrase|privateKey)>\s*([^<]+)\s*</(?:username|password|token|passphrase|privateKey)>"
    )
    safe_markers = (
        "${",
        "$(",
        "env.",
        "environment",
        "findproperty",
        "providers.",
        "system.getenv",
        "settings.",
        "secret(",
        "<redacted>",
        "changeme",
    )
    for regex in (assignments, xml_values):
        for match in regex.finditer(text):
            candidate = match.group(1).strip().strip('"\'')
            lowered = candidate.lower()
            if candidate and not any(marker in lowered for marker in safe_markers):
                return True
    return False


def inspect(root: Path) -> dict[str, object]:
    files = list(iter_files(root))
    texts = {path: read_text(path) for path in files}
    gradle_files = tuple(path for path in files if path.suffix in {".gradle", ".kts"} or "gradle" in path.name)
    maven_files = tuple(path for path in files if path.name == "pom.xml")
    ci_files = tuple(path for path in files if ".github" in path.parts or path.suffix in {".yml", ".yaml"})
    publication_files = matching(
        files,
        texts,
        r"central-publishing-maven-plugin|maven-publish|maven-deploy-plugin|com\.vanniktech\.maven\.publish|nmcp|gradle-nexus\.publish-plugin|jreleaser|publishing\s*\{",
    )
    central_maven_plugin = matching(files, texts, r"central-publishing-maven-plugin")
    gradle_portal_tools = matching(
        gradle_files + ci_files,
        texts,
        r"com\.vanniktech\.maven\.publish|nmcp|jreleaser|centralPortal|central[-_ ]portal",
    )
    legacy_plugins = matching(
        files,
        texts,
        r"gradle-nexus\.publish-plugin|nexus-staging-maven-plugin|nexusPublishing|closeAndRelease",
    )
    signing_files = matching(
        files,
        texts,
        r"maven-gpg-plugin|\bid\s*\(?[\"']signing[\"']|\bsigning\s*\{|useInMemoryPgpKeys|signing\.keyId|signingKey",
    )
    sources_files = matching(
        files,
        texts,
        r"withSourcesJar\s*\(|sourcesJar|maven-source-plugin|classifier\s*[=:]\s*[\"']sources[\"']",
    )
    javadoc_files = matching(
        files,
        texts,
        r"withJavadocJar\s*\(|javadocJar|maven-javadoc-plugin|dokkaJavadoc|classifier\s*[=:]\s*[\"']javadoc[\"']",
    )
    group_files = matching(
        files,
        texts,
        r"(?m)^\s*group(?:Id)?\s*[=:]|<groupId>|GROUP(?:_ID)?\s*[=:]",
    )
    version_files = matching(
        files,
        texts,
        r"(?m)^\s*version\s*[=:]|<version>|VERSION\s*[=:]",
    )
    snapshot_versions = matching(files, texts, r"(?m)(?:version|<version>)[^\n<]{0,120}-SNAPSHOT")

    pom_fields = {
        "name": matching(publication_files or files, texts, r"<name>|\bname\s*(?:\.set)?\s*[=(]"),
        "description": matching(publication_files or files, texts, r"<description>|\bdescription\s*(?:\.set)?\s*[=(]"),
        "url": matching(publication_files or files, texts, r"<url>|\burl\s*(?:\.set)?\s*[=(]"),
        "licenses": matching(publication_files or files, texts, r"<licenses>|\blicenses\s*\{"),
        "developers": matching(publication_files or files, texts, r"<developers>|\bdevelopers\s*\{"),
        "scm": matching(publication_files or files, texts, r"<scm>|\bscm\s*\{"),
    }

    portal_endpoints = matching(
        files,
        texts,
        r"central\.sonatype\.com/(?:api/v1/publisher|repository)|central\.sonatype\.org/publish",
    )
    snapshot_endpoints = matching(
        files,
        texts,
        r"central\.sonatype\.com/repository/maven-snapshots|maven-snapshots",
    )
    legacy_endpoints = matching(
        files,
        texts,
        r"(?:s01\.)?oss\.sonatype\.org|service/local/staging|nexus2",
    )
    automatic_publish = matching(
        files,
        texts,
        r"autoPublish(?:AfterClose)?\s*[=:]\s*true|publishingType\s*[=:]\s*(?:[\"']?AUTOMATIC|PublishingType\.AUTOMATIC)|<publishingType>\s*AUTOMATIC\s*</publishingType>|automaticPublishing\s*[=:]\s*true",
    )
    user_managed = matching(
        files,
        texts,
        r"USER_MANAGED|PublishingType\.USER_MANAGED|autoPublish(?:AfterClose)?\s*[=:]\s*false",
    )
    secret_indirection = matching(
        files,
        texts,
        r"System\.getenv|providers\.environmentVariable|findProperty|\$\{env\.|\$\{[^}]+\}|secrets\.[A-Za-z0-9_]+",
    )
    inline_secret_files = tuple(path for path in files if has_inline_secret(texts[path]))

    findings: list[Finding] = []
    if not publication_files:
        findings.append(
            Finding("info", "NO_PUBLICATION_CONFIGURATION", "No Maven/Gradle/JReleaser publication configuration was found.")
        )
    if publication_files and not group_files:
        findings.append(
            Finding("warning", "GROUP_ID_NOT_FOUND", "Publication configuration exists, but no group/groupId declaration was found.", names(root, publication_files))
        )
    if publication_files and not version_files:
        findings.append(
            Finding("warning", "VERSION_NOT_FOUND", "Publication configuration exists, but no version declaration was found.", names(root, publication_files))
        )
    missing_pom = tuple(field for field, matches in pom_fields.items() if not matches)
    if publication_files and missing_pom:
        findings.append(
            Finding(
                "warning",
                "POM_METADATA_INCOMPLETE",
                "Required POM metadata signals were not found for: " + ", ".join(missing_pom) + ". Inspect generated POMs before release.",
                names(root, publication_files),
            )
        )
    if publication_files and not sources_files:
        findings.append(
            Finding("warning", "SOURCES_ARTIFACT_NOT_FOUND", "No sources JAR configuration was found for published non-pom components.", names(root, publication_files))
        )
    if publication_files and not javadoc_files:
        findings.append(
            Finding("warning", "JAVADOC_ARTIFACT_NOT_FOUND", "No Javadoc/Dokka JAR configuration was found for published non-pom components.", names(root, publication_files))
        )
    if publication_files and not signing_files:
        findings.append(
            Finding("warning", "SIGNING_NOT_FOUND", "No PGP signing configuration was found for Central publication artifacts and POMs.", names(root, publication_files))
        )
    if gradle_files and publication_files and not gradle_portal_tools and not legacy_plugins:
        findings.append(
            Finding(
                "warning",
                "GRADLE_UPLOAD_ROUTE_NOT_FOUND",
                "Gradle publication exists without a recognized Central Portal/JReleaser/legacy compatibility uploader. Sonatype does not provide an official Gradle plugin.",
                names(root, gradle_files),
            )
        )
    if legacy_endpoints or legacy_plugins:
        findings.append(
            Finding(
                "warning",
                "LEGACY_OSSRH_CONFIGURATION",
                "Legacy OSSRH/Nexus staging configuration was found. Confirm the current compatibility or migration path and avoid conflicting Portal ownership.",
                names(root, legacy_endpoints + legacy_plugins),
            )
        )
    if portal_endpoints and legacy_endpoints:
        findings.append(
            Finding(
                "warning",
                "MIXED_PORTAL_AND_OSSRH_ROUTES",
                "Current Central Portal and legacy OSSRH endpoints coexist; assign one release route before publishing.",
                names(root, portal_endpoints + legacy_endpoints),
            )
        )
    if automatic_publish:
        findings.append(
            Finding(
                "warning",
                "AUTOMATIC_IRREVERSIBLE_PUBLISH",
                "Automatic publication is enabled. A validated deployment can become immutable without a manual publish gate; require explicit policy and point-of-risk approval.",
                names(root, automatic_publish),
            )
        )
    if snapshot_versions and portal_endpoints and not snapshot_endpoints:
        findings.append(
            Finding(
                "warning",
                "SNAPSHOT_RELEASE_ROUTE_RISK",
                "A -SNAPSHOT version and Central release/Publisher endpoint signals coexist without the dedicated snapshot endpoint.",
                names(root, snapshot_versions + portal_endpoints),
            )
        )
    if snapshot_endpoints and not snapshot_versions:
        findings.append(
            Finding(
                "warning",
                "SNAPSHOT_ENDPOINT_WITHOUT_SNAPSHOT_VERSION",
                "A snapshot endpoint was found without a recognizable -SNAPSHOT version guard.",
                names(root, snapshot_endpoints),
            )
        )
    if inline_secret_files:
        findings.append(
            Finding(
                "warning",
                "POSSIBLE_INLINE_PUBLISHING_SECRET",
                "A credential/signing property appears to contain a literal value. Move secrets to approved runtime injection and inspect without printing values.",
                names(root, inline_secret_files),
            )
        )
    if publication_files and not secret_indirection:
        findings.append(
            Finding(
                "info",
                "SECRET_INJECTION_NOT_FOUND",
                "No recognized environment/property/CI-secret indirection was found. Confirm credentials are injected outside versioned files.",
            )
        )
    if publication_files and not (central_maven_plugin or gradle_portal_tools or legacy_plugins or portal_endpoints):
        findings.append(
            Finding(
                "info",
                "CENTRAL_ROUTE_NOT_FOUND",
                "Publication configuration exists without a recognizable Central upload route; it may intentionally target local/private repositories.",
            )
        )

    signals = {
        "publication_files": names(root, publication_files),
        "maven_files": names(root, maven_files),
        "gradle_files": names(root, gradle_files),
        "ci_files": names(root, ci_files),
        "central_maven_plugin_files": names(root, central_maven_plugin),
        "gradle_portal_tool_files": names(root, gradle_portal_tools),
        "legacy_plugin_files": names(root, legacy_plugins),
        "signing_files": names(root, signing_files),
        "sources_files": names(root, sources_files),
        "javadoc_files": names(root, javadoc_files),
        "group_files": names(root, group_files),
        "version_files": names(root, version_files),
        "snapshot_version_files": names(root, snapshot_versions),
        "portal_endpoint_files": names(root, portal_endpoints),
        "snapshot_endpoint_files": names(root, snapshot_endpoints),
        "legacy_endpoint_files": names(root, legacy_endpoints),
        "automatic_publish_files": names(root, automatic_publish),
        "user_managed_files": names(root, user_managed),
        "secret_indirection_files": names(root, secret_indirection),
        "possible_inline_secret_files": names(root, inline_secret_files),
        "pom_metadata_files": {field: names(root, matches) for field, matches in sorted(pom_fields.items())},
    }
    return {
        "root": str(root),
        "summary": {
            "files_scanned": len(files),
            "publication_files": len(publication_files),
            "warnings": sum(finding.severity == "warning" for finding in findings),
            "info": sum(finding.severity == "info" for finding in findings),
        },
        "signals": signals,
        "findings": [asdict(finding) for finding in findings],
    }


def print_human(report: dict[str, object]) -> None:
    summary = report["summary"]
    assert isinstance(summary, dict)
    print(f"Central publication inspection: {report['root']}")
    print(
        f"Scanned {summary['files_scanned']} files; "
        f"{summary['publication_files']} publication files."
    )
    findings = report["findings"]
    assert isinstance(findings, list)
    if not findings:
        print("No heuristic findings.")
        return
    for finding in findings:
        assert isinstance(finding, dict)
        print(f"{str(finding['severity']).upper()} [{finding['code']}]: {finding['message']}")
        paths = finding.get("files", ())
        assert isinstance(paths, (list, tuple))
        for path in paths:
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
