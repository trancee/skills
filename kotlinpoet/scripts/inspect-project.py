#!/usr/bin/env python3
"""Inspect KotlinPoet setup and generator source for determinism and interop risks."""

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
    ".kotlin",
    "build",
    "dist",
    "generated",
    "node_modules",
    "out",
    "target",
}
TEXT_SUFFIXES = {".gradle", ".kts", ".kt", ".toml", ".xml", ".properties"}
TEXT_NAMES = {"pom.xml", "settings.gradle", "settings.gradle.kts", "gradle.properties", "libs.versions.toml"}
MAX_FILE_BYTES = 2_000_000


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    files: tuple[str, ...] = ()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect KotlinPoet dependencies, structured builders, KSP writes, determinism, and compile-test signals."
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


def inspect(root: Path) -> dict[str, object]:
    files = list(iter_files(root))
    texts = {path: read_text(path) for path in files}
    kotlin_files = tuple(path for path in files if path.suffix == ".kt")
    build_files = tuple(path for path in files if path not in kotlin_files)

    dependency_files = matching(
        build_files,
        texts,
        r"com\.squareup:kotlinpoet(?:-jvm|-ksp|-metadata(?:-specs)?)?|com\.squareup\.kotlinpoet|kotlinpoet[-_.](?:version|core|jvm|ksp|metadata)",
    )
    core_dependency = matching(
        dependency_files,
        texts,
        r"com\.squareup:kotlinpoet(?::|[\"'])|com\.squareup:kotlinpoet-jvm",
    )
    ksp_dependency = matching(dependency_files, texts, r"kotlinpoet-ksp")
    metadata_dependency = matching(dependency_files, texts, r"kotlinpoet-metadata")
    explicit_versions: set[str] = set()
    version_pattern = re.compile(
        r"com\.squareup:kotlinpoet(?:-jvm|-ksp|-metadata(?:-specs)?)?:([0-9][0-9A-Za-z.+-]*)",
        re.IGNORECASE,
    )
    for path in dependency_files:
        explicit_versions.update(version_pattern.findall(texts[path]))

    kotlinpoet_sources = matching(
        kotlin_files,
        texts,
        r"import\s+com\.squareup\.kotlinpoet|\b(?:FileSpec|TypeSpec|FunSpec|PropertySpec|ParameterSpec|AnnotationSpec|TypeAliasSpec|CodeBlock)\.(?:builder|of)",
    )
    spec_files = matching(
        kotlinpoet_sources,
        texts,
        r"\b(?:FileSpec|TypeSpec|FunSpec|PropertySpec|ParameterSpec|AnnotationSpec|TypeAliasSpec)\.",
    )
    code_block_files = matching(
        kotlinpoet_sources,
        texts,
        r"\bCodeBlock\.|\.add(?:Code|Statement|Kdoc)\s*\(|\.initializer\s*\(",
    )
    placeholder_files = {
        placeholder: matching(code_block_files, texts, rf"%{placeholder}")
        for placeholder in ("L", "N", "S", "P", "T", "M")
    }
    wrap_marker_files = matching(code_block_files, texts, r"♢")
    raw_format_variable = matching(
        code_block_files,
        texts,
        r"\.(?:add|addCode|addStatement|addKdoc|initializer)\s*\(\s*[A-Za-z_][A-Za-z0-9_.]*\s*(?:,|\))",
    )
    interpolated_format = matching(
        code_block_files,
        texts,
        r"\.(?:add|addCode|addStatement|addKdoc|initializer)\s*\(\s*\"[^\"\n]*\$[A-Za-z_{]",
    )
    literal_string_via_percent_l = matching(
        code_block_files,
        texts,
        r"[\"'][^\"'\n]*%L[^\"'\n]*[\"']\s*,\s*[\"']",
    )
    mixed_placeholder_style = matching(
        code_block_files,
        texts,
        r"[\"'][^\"'\n]*(?:%\d+[A-Z][^\"'\n]*%(?!\d|[a-z][A-Za-z0-9_]*:)[A-Z]|%[a-z][A-Za-z0-9_]*:[A-Z][^\"'\n]*%(?:\d+)?[A-Z])",
    )

    type_model_files = matching(
        kotlinpoet_sources,
        texts,
        r"\b(?:ClassName|TypeName|ParameterizedTypeName|TypeVariableName|WildcardTypeName|LambdaTypeName|MemberName)\b",
    )
    name_allocator_files = matching(kotlinpoet_sources, texts, r"\bNameAllocator\b|addAliasedImport\s*\(")
    string_type_guessing = matching(
        kotlinpoet_sources,
        texts,
        r"ClassName\.bestGuess\s*\(|(?:ClassName|MemberName)\s*\([^\n]{0,120}\.toString\s*\(",
    )

    ksp_sources = matching(
        kotlinpoet_sources,
        texts,
        r"com\.google\.devtools\.ksp|CodeGenerator|SymbolProcessor|KSFile|toTypeParameterResolver|addOriginatingKSFile",
    )
    type_resolver_files = matching(ksp_sources, texts, r"TypeParameterResolver|toTypeParameterResolver\s*\(")
    originating_files = matching(ksp_sources, texts, r"addOriginatingKSFile\s*\(|Dependencies\s*\(")
    code_generator_write = matching(
        ksp_sources,
        texts,
        r"(?:FileSpec|fileSpec|file)\.writeTo\s*\(\s*(?:codeGenerator|codeGenerator\s*=)|writeTo\s*\(\s*codeGenerator\s*=",  # CodeGenerator target
    )
    aggregating_files = matching(ksp_sources, texts, r"aggregating\s*=")
    direct_filesystem_write = matching(
        ksp_sources,
        texts,
        r"\.writeTo\s*\(\s*(?:File|Path|Paths\.|outputDirectory)|Files\.write|FileOutputStream|\.writeText\s*\(",
    )

    discovery_order_files = matching(
        kotlinpoet_sources,
        texts,
        r"getSymbolsWithAnnotation|getAllFiles\s*\(|\.values\b|\.entries\b|HashMap|HashSet|mutableMapOf|mutableSetOf",
    )
    sorting_files = matching(kotlinpoet_sources, texts, r"sorted(?:By|With)?\s*(?:\(|\{)|toSortedMap\s*\(|compareBy\s*\(")
    volatile_output_files = matching(
        kotlinpoet_sources,
        texts,
        r"currentTimeMillis|Instant\.now|LocalDateTime\.now|UUID\.randomUUID|System\.getProperty\s*\(\s*[\"']user\.(?:dir|home)|absolutePath|canonicalPath",
    )
    writer_files = matching(
        kotlinpoet_sources,
        texts,
        r"\.writeTo\s*\(|\.toString\s*\(\)|\.build\s*\(\)",
    )
    compile_test_files = matching(
        files,
        texts,
        r"kotlin-compile-testing|KotlinCompilation|compileTesting|kotlinc|compileKotlin|compileTestKotlin|assertCompiles|CompilationResult",
    )
    golden_test_files = matching(
        files,
        texts,
        r"golden|expected(?:Source|Code|File)|assertEquals\s*\([^\n]{0,120}(?:toString|writeTo)|verifyFile|snapshot",
    )
    determinism_test_files = matching(
        files,
        texts,
        r"determin(?:ism|istic)|byte[-_ ]?identical|sha256|digest|permut(?:e|ed)|incremental[^\n]{0,80}(?:remove|rename)",
    )

    findings: list[Finding] = []
    if not dependency_files and not kotlinpoet_sources:
        findings.append(Finding("info", "NO_KOTLINPOET_SIGNALS", "No KotlinPoet dependency or source usage was found."))
    if len(explicit_versions) > 1:
        findings.append(
            Finding(
                "warning",
                "KOTLINPOET_VERSION_SKEW",
                "Multiple explicit KotlinPoet versions were found: " + ", ".join(sorted(explicit_versions)) + ". Align all modules.",
                names(root, dependency_files),
            )
        )
    if (ksp_dependency or metadata_dependency) and not core_dependency:
        findings.append(
            Finding(
                "info",
                "CORE_ARTIFACT_NOT_VISIBLE",
                "Interop artifact exists without a recognizable direct core dependency; confirm transitive or catalog-managed KotlinPoet core resolution.",
                names(root, ksp_dependency + metadata_dependency),
            )
        )
    if raw_format_variable:
        findings.append(
            Finding(
                "warning",
                "DYNAMIC_FORMAT_STRING",
                "A KotlinPoet formatting method appears to receive a variable format string. Keep format strings generator-owned and pass data as placeholder arguments.",
                names(root, raw_format_variable),
            )
        )
    if interpolated_format:
        findings.append(
            Finding(
                "warning",
                "KOTLIN_INTERPOLATED_FORMAT_STRING",
                "A Kotlin string interpolation appears inside a KotlinPoet format string. Use placeholders so KotlinPoet owns escaping/import/name rendering.",
                names(root, interpolated_format),
            )
        )
    if literal_string_via_percent_l:
        findings.append(
            Finding(
                "warning",
                "STRING_INSERTED_WITH_PERCENT_L",
                "A string literal appears to be inserted with %L. Use %S for a literal or %P for an intentional Kotlin template.",
                names(root, literal_string_via_percent_l),
            )
        )
    if mixed_placeholder_style:
        findings.append(
            Finding(
                "warning",
                "MIXED_PLACEHOLDER_ADDRESSING",
                "A format string appears to mix relative, positional, or named placeholder styles.",
                names(root, mixed_placeholder_style),
            )
        )
    if string_type_guessing:
        findings.append(
            Finding(
                "warning",
                "STRING_GUESSED_SYMBOL",
                "A type/member name appears inferred from text. Carry structured package/nesting identity and use KotlinPoet/KSP type conversions.",
                names(root, string_type_guessing),
            )
        )
    if direct_filesystem_write:
        findings.append(
            Finding(
                "warning",
                "KSP_DIRECT_FILESYSTEM_WRITE",
                "KSP-related generator code appears to write directly to the filesystem. Write FileSpec through CodeGenerator with correct dependencies.",
                names(root, direct_filesystem_write),
            )
        )
    if ksp_sources and not type_resolver_files:
        findings.append(
            Finding(
                "warning",
                "KSP_TYPE_PARAMETER_RESOLVER_NOT_FOUND",
                "KSP/KotlinPoet interop exists without a recognized TypeParameterResolver. Verify generic and enclosing type-variable conversion.",
                names(root, ksp_sources),
            )
        )
    if ksp_sources and not originating_files:
        findings.append(
            Finding(
                "warning",
                "KSP_ORIGINATING_FILES_NOT_FOUND",
                "KSP generator output has no recognized originating KSFile/dependency declaration.",
                names(root, ksp_sources),
            )
        )
    if ksp_sources and not code_generator_write:
        findings.append(
            Finding(
                "warning",
                "KSP_CODEGENERATOR_WRITE_NOT_FOUND",
                "KSP/KotlinPoet source exists without a recognized FileSpec.writeTo(CodeGenerator) path.",
                names(root, ksp_sources),
            )
        )
    if ksp_sources and not aggregating_files:
        findings.append(
            Finding(
                "warning",
                "KSP_AGGREGATING_DECISION_NOT_FOUND",
                "KotlinPoet KSP output does not visibly declare aggregating true/false. Classify it from the real dependency set.",
                names(root, ksp_sources),
            )
        )
    if discovery_order_files and not sorting_files:
        findings.append(
            Finding(
                "warning",
                "STABLE_SORT_NOT_FOUND",
                "Generator input comes from symbols/maps/sets without a recognized stable sort before emission.",
                names(root, discovery_order_files),
            )
        )
    if volatile_output_files:
        findings.append(
            Finding(
                "warning",
                "VOLATILE_OUTPUT_SIGNAL",
                "Generator source references time, random UUIDs, or machine paths that can make output nondeterministic.",
                names(root, volatile_output_files),
            )
        )
    if writer_files and not compile_test_files:
        findings.append(
            Finding(
                "info",
                "GENERATED_SOURCE_COMPILE_TEST_NOT_FOUND",
                "Generated-source writes were found without a recognized compile-testing or compile task signal.",
                names(root, writer_files),
            )
        )
    if writer_files and not golden_test_files:
        findings.append(
            Finding(
                "info",
                "GOLDEN_SOURCE_TEST_NOT_FOUND",
                "Generated-source writes were found without a recognizable exact golden/snapshot source test.",
                names(root, writer_files),
            )
        )
    if writer_files and not determinism_test_files:
        findings.append(
            Finding(
                "info",
                "DETERMINISM_TEST_NOT_FOUND",
                "Generated-source writes were found without recognizable repeated/permuted/incremental byte checks.",
                names(root, writer_files),
            )
        )

    signals = {
        "dependency_files": names(root, dependency_files),
        "explicit_versions": sorted(explicit_versions),
        "core_dependency_files": names(root, core_dependency),
        "ksp_dependency_files": names(root, ksp_dependency),
        "metadata_dependency_files": names(root, metadata_dependency),
        "kotlinpoet_source_files": names(root, kotlinpoet_sources),
        "spec_files": names(root, spec_files),
        "code_block_files": names(root, code_block_files),
        "placeholder_files": {key: names(root, value) for key, value in sorted(placeholder_files.items())},
        "wrap_marker_files": names(root, wrap_marker_files),
        "type_model_files": names(root, type_model_files),
        "name_allocator_or_alias_files": names(root, name_allocator_files),
        "ksp_source_files": names(root, ksp_sources),
        "type_parameter_resolver_files": names(root, type_resolver_files),
        "originating_file_signal_files": names(root, originating_files),
        "code_generator_write_files": names(root, code_generator_write),
        "aggregating_decision_files": names(root, aggregating_files),
        "sorting_files": names(root, sorting_files),
        "compile_test_files": names(root, compile_test_files),
        "golden_test_files": names(root, golden_test_files),
        "determinism_test_files": names(root, determinism_test_files),
    }
    return {
        "root": str(root),
        "summary": {
            "files_scanned": len(files),
            "kotlinpoet_files": len(kotlinpoet_sources),
            "warnings": sum(item.severity == "warning" for item in findings),
            "info": sum(item.severity == "info" for item in findings),
        },
        "signals": signals,
        "findings": [asdict(item) for item in findings],
    }


def print_human(report: dict[str, object]) -> None:
    summary = report["summary"]
    assert isinstance(summary, dict)
    print(f"KotlinPoet inspection: {report['root']}")
    print(
        f"Scanned {summary['files_scanned']} files; "
        f"{summary['kotlinpoet_files']} KotlinPoet source files."
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
