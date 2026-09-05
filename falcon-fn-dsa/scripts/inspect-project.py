#!/usr/bin/env python3
"""Inspect a repository for Falcon/FN-DSA integration and implementation risks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Pattern

SKIP_DIRS = {
    ".git",
    ".gradle",
    ".idea",
    ".cache",
    ".tox",
    ".venv",
    "build",
    "coverage",
    "dist",
    "generated",
    "node_modules",
    "out",
    "target",
    "vendor",
}
TEXT_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".go",
    ".gradle",
    ".h",
    ".hpp",
    ".java",
    ".js",
    ".json",
    ".kt",
    ".kts",
    ".md",
    ".py",
    ".rs",
    ".sh",
    ".swift",
    ".toml",
    ".ts",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
TEXT_NAMES = {
    "CMakeLists.txt",
    "Cargo.lock",
    "Cargo.toml",
    "Makefile",
    "go.mod",
    "go.sum",
    "meson.build",
    "package-lock.json",
    "package.json",
    "pom.xml",
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
        description="Inspect Falcon/FN-DSA provenance, formats, randomness, internals, and verification signals."
    )
    parser.add_argument("--root", default=".", help="Repository root (default: current directory)")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when warnings are present; inspection errors always exit 2",
    )
    return parser.parse_args()


def iter_text_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in SKIP_DIRS for part in relative.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in TEXT_NAMES:
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


def compile_pattern(pattern: str) -> Pattern[str]:
    return re.compile(pattern, re.IGNORECASE | re.MULTILINE | re.DOTALL)


def matching(
    files: Iterable[Path], texts: dict[Path, str], pattern: str
) -> tuple[Path, ...]:
    regex = compile_pattern(pattern)
    return tuple(path for path in files if regex.search(texts[path]))


def relative_names(root: Path, paths: Iterable[Path], limit: int = 16) -> tuple[str, ...]:
    unique = dict.fromkeys(path.relative_to(root).as_posix() for path in paths)
    return tuple(list(unique)[:limit])


def inspect(root: Path) -> dict[str, object]:
    files = list(iter_text_files(root))
    texts = {path: read_text(path) for path in files}

    falcon_files = matching(
        files,
        texts,
        r"\bfalcon(?:[-_ ]?(?:512|1024|padded))?\b|\bFN[-_ ]?DSA\b|OQS_SIG_alg_falcon|PQCLEAN_FALCON",
    )
    code_files = tuple(
        path
        for path in falcon_files
        if path.suffix.lower()
        in {".c", ".cc", ".cpp", ".cs", ".go", ".h", ".hpp", ".java", ".js", ".kt", ".kts", ".py", ".rs", ".swift", ".ts"}
    )
    falcon_text = {path: texts[path] for path in falcon_files}

    dependencies = matching(
        falcon_files,
        falcon_text,
        r"liboqs|open[-_ ]quantum[-_ ]safe|pqclean|falcon[-_ ](?:512|1024)|PQCLEAN_FALCON|OQS_SIG_alg_falcon",
    )
    fn_dsa_files = matching(falcon_files, falcon_text, r"\bFN[-_ ]?DSA\b|\bFIPS\s*206\b")
    fips_pin_files = matching(
        fn_dsa_files,
        falcon_text,
        r"FIPS\s*206[^\n]{0,80}(?:final|published|\d{4}[-/]\d{2}[-/]\d{2}|revision|rev\.)",
    )
    parameter_512 = matching(falcon_files, falcon_text, r"Falcon[-_ ]?512|logn\s*[=:]\s*9\b")
    parameter_1024 = matching(falcon_files, falcon_text, r"Falcon[-_ ]?1024|logn\s*[=:]\s*10\b")
    reduced_degree = matching(
        code_files,
        falcon_text,
        r"Falcon[-_ ]?(?:2|4|8|16|32|64|128|256)\b|logn\s*[=:]\s*[1-8]\b",
    )

    sign_calls = matching(
        code_files,
        falcon_text,
        r"falcon_sign_(?:dyn|tree|start)|OQS_SIG_(?:falcon[^\s(]*_)?sign\s*\(|crypto_sign_signature\s*\(|\bFN[-_ ]?DSA[^\n]{0,40}\bsign\b",
    )
    verify_calls = matching(
        code_files,
        falcon_text,
        r"falcon_verify(?:_start|_finish)?\s*\(|OQS_SIG_(?:falcon[^\s(]*_)?verify\s*\(|crypto_sign_verify\s*\(|\bFN[-_ ]?DSA[^\n]{0,40}\bverify\b",
    )
    explicit_formats = matching(
        falcon_files,
        falcon_text,
        r"FALCON_SIG_(?:COMPRESSED|PADDED|CT)|falcon[-_ ]padded",
    )
    inferred_format = matching(
        code_files,
        falcon_text,
        r"falcon_verify(?:_finish)?\s*\([^;]{0,500}?,\s*0\s*,",
    )

    rng_files = matching(
        code_files,
        falcon_text,
        r"shake256_init_prng_from_(?:system|seed)|getrandom|arc4random|RAND_bytes|randombytes|OsRng|SecureRandom|crypto\.rand|/dev/urandom",
    )
    weak_rng = matching(
        code_files,
        falcon_text,
        r"\b(?:s?rand|rand)\s*\(|Math\.random\s*\(|\brandom\.random\s*\(|\bjava\.util\.Random\s*\(|\bkotlin\.random\.Random\b",
    )
    deterministic_signing = matching(
        code_files,
        falcon_text,
        r"deterministic[^\n]{0,80}(?:falcon|sign)|(?:falcon|sign)[^\n]{0,80}deterministic|sign[^\n]{0,100}(?:fixed|static|constant)[-_ ]seed",
    )

    stream_sign_start = matching(code_files, falcon_text, r"falcon_sign_start\s*\(")
    stream_sign_finish = matching(
        code_files, falcon_text, r"falcon_sign_(?:dyn|tree)_finish\s*\("
    )
    stream_verify_start = matching(code_files, falcon_text, r"falcon_verify_start\s*\(")
    stream_verify_finish = matching(code_files, falcon_text, r"falcon_verify_finish\s*\(")

    custom_internals = matching(
        code_files,
        falcon_text,
        r"\b(?:SamplerZ|samplerz|ffSampling|ffLDL|BerExp|hash_to_point|hash_to_point_ct|solve_NTRU|solve_ntru)\b",
    )
    floating_flags = matching(
        files,
        texts,
        r"(?:-ffast-math|-Ofast|fast[-_ ]math|fp-contract\s*=\s*fast|ffp-contract=fast)",
    )
    prng_reference_api = matching(
        code_files,
        falcon_text,
        r"shake256_init_prng_from_(?:seed|system)\s*\(",
    )
    corrected_reference_marker = matching(
        falcon_files,
        falcon_text,
        r"2021[-_]?11[-_]?01|Falcon-impl-20211101|FALCON(?:_|-)?20211101",
    )

    secret_logging = matching(
        code_files,
        falcon_text,
        r"(?:printf|fprintf|console\.log|println!|log\.(?:debug|info|warn|error)|print\s*\()[^\n]{0,160}(?:priv(?:ate)?[-_ ]?key|secret[-_ ]?key|expanded[-_ ]?key|ldl[-_ ]?tree|fft[-_ ]?basis|rng[-_ ]?state)",
    )
    seed_export = matching(
        falcon_files,
        falcon_text,
        r"(?:export|serialize|persist|store|write)[^\n]{0,100}(?:private[-_ ]?key[-_ ]?seed|falcon[-_ ]?seed)|seed[-_ ]only[-_ ]private[-_ ]key",
    )
    zeroization = matching(
        code_files,
        falcon_text,
        r"explicit_bzero|memset_s|OPENSSL_cleanse|sodium_memzero|zeroize|Zeroizing|SecureZeroMemory",
    )
    vector_files = matching(
        files,
        texts,
        r"Known Answer Test|\bKATs?\b|PQCsignKAT|test-vector-sampler-falcon|SamplerZ[^\n]{0,40}vector",
    )
    negative_tests = matching(
        files,
        texts,
        r"(?:reject|invalid|malformed|noncanonical|tamper|truncat|wrong[-_ ](?:key|message|parameter)|padding)[^\n]{0,100}(?:falcon|signature|verify)|(?:falcon|signature|verify)[^\n]{0,100}(?:reject|invalid|malformed|noncanonical|tamper|truncat|padding)",
    )

    findings: list[Finding] = []
    if not falcon_files:
        findings.append(
            Finding(
                "info",
                "NO_FALCON_SIGNALS",
                "No Falcon or FN-DSA identifiers were found in scanned text files.",
            )
        )
    if fn_dsa_files and not fips_pin_files:
        findings.append(
            Finding(
                "warning",
                "FN_DSA_WITHOUT_NORMATIVE_PIN",
                "FN-DSA/FIPS 206 identifiers were found without a nearby final publication or revision marker. Confirm that code does not implement provisional behavior or claim unpublished conformance.",
                relative_names(root, fn_dsa_files),
            )
        )
    if reduced_degree:
        findings.append(
            Finding(
                "warning",
                "REDUCED_RESEARCH_DEGREE",
                "A Falcon degree below logn=9 appears in code. Reduced variants are research-only and must not be exposed as deployed Falcon parameter sets.",
                relative_names(root, reduced_degree),
            )
        )
    if sign_calls and not rng_files:
        findings.append(
            Finding(
                "warning",
                "SIGNING_RNG_NOT_FOUND",
                "Falcon signing calls were found without a recognized CSPRNG/DRBG integration in the same Falcon-related files. Trace the actual randomness owner and failure path.",
                relative_names(root, sign_calls),
            )
        )
    if weak_rng:
        findings.append(
            Finding(
                "warning",
                "POSSIBLE_NON_CSPRNG",
                "A general-purpose random API appears in Falcon-related code. Replace it with a failure-reporting CSPRNG/approved DRBG or prove the call is unrelated.",
                relative_names(root, weak_rng),
            )
        )
    if deterministic_signing:
        findings.append(
            Finding(
                "warning",
                "DETERMINISTIC_SIGNING_SIGNAL",
                "Deterministic Falcon signing or a fixed signing seed appears in code. Confine deterministic seeds to vector tests and keep production signing randomized.",
                relative_names(root, deterministic_signing),
            )
        )
    if inferred_format:
        findings.append(
            Finding(
                "warning",
                "SIGNATURE_FORMAT_INFERENCE",
                "A Falcon verification call appears to pass sig_type=0. Bind one explicit expected format to prevent representation malleability/transcoding.",
                relative_names(root, inferred_format),
            )
        )
    if sign_calls and not explicit_formats:
        findings.append(
            Finding(
                "info",
                "EXPLICIT_FORMAT_NOT_FOUND",
                "Signing code was found without a recognized explicit Falcon format marker. Confirm that the library/protocol fixes compressed, padded, or CT encoding.",
                relative_names(root, sign_calls),
            )
        )
    if stream_sign_start and not stream_sign_finish:
        findings.append(
            Finding(
                "warning",
                "INCOMPLETE_STREAM_SIGN_FLOW",
                "falcon_sign_start appears without a matching dynamic/tree finish call in the scanned project.",
                relative_names(root, stream_sign_start),
            )
        )
    if stream_verify_start and not stream_verify_finish:
        findings.append(
            Finding(
                "warning",
                "INCOMPLETE_STREAM_VERIFY_FLOW",
                "falcon_verify_start appears without falcon_verify_finish in the scanned project.",
                relative_names(root, stream_verify_start),
            )
        )
    if custom_internals:
        findings.append(
            Finding(
                "warning",
                "CUSTOM_FALCON_INTERNALS",
                "Falcon sampler/FFT/NTRU internals were found. Require official low-level vectors, numerical review, target side-channel evidence, and a maintenance owner.",
                relative_names(root, custom_internals),
            )
        )
    if custom_internals and floating_flags:
        findings.append(
            Finding(
                "warning",
                "UNSAFE_FLOAT_OPTIMIZATION_SIGNAL",
                "Falcon internals coexist with fast-math/FMA-contraction signals. Verify exact operation order and generated target code; disable unsafe optimization where required.",
                relative_names(root, floating_flags),
            )
        )
    if prng_reference_api and not corrected_reference_marker:
        findings.append(
            Finding(
                "warning",
                "REFERENCE_PRNG_FIX_PROVENANCE_MISSING",
                "The Falcon reference PRNG API appears without a 2021-11-01 corrected-source marker. Prove provenance or the equivalent PRNG initialization fix.",
                relative_names(root, prng_reference_api),
            )
        )
    if secret_logging:
        findings.append(
            Finding(
                "warning",
                "SECRET_LOGGING_SIGNAL",
                "A logging/printing call appears to include Falcon private or expanded signing material. Remove it or prove no secret value reaches the sink.",
                relative_names(root, secret_logging),
            )
        )
    if seed_export:
        findings.append(
            Finding(
                "warning",
                "PRIVATE_SEED_EXPORT_SIGNAL",
                "Falcon/FN-DSA seed export or seed-only private-key storage appears in the project. Match the exact scheme contract and keep provisional FN-DSA plans out of persistent formats.",
                relative_names(root, seed_export),
            )
        )
    if sign_calls and not zeroization:
        findings.append(
            Finding(
                "info",
                "ZEROIZATION_NOT_FOUND",
                "No recognized zeroization primitive was found in Falcon signing code. Confirm whether the library/runtime owns secret cleanup for the deployment threat model.",
                relative_names(root, sign_calls),
            )
        )
    if (sign_calls or verify_calls) and not vector_files:
        findings.append(
            Finding(
                "info",
                "OFFICIAL_VECTOR_SIGNAL_NOT_FOUND",
                "Falcon operations were found without an official KAT/SamplerZ vector reference in scanned files. Confirm vector coverage outside the repository if applicable.",
            )
        )
    if verify_calls and not negative_tests:
        findings.append(
            Finding(
                "info",
                "NEGATIVE_TEST_SIGNAL_NOT_FOUND",
                "Falcon verification was found without recognizable malformed/tampered/canonical-encoding tests.",
                relative_names(root, verify_calls),
            )
        )

    signals = {
        "falcon_files": relative_names(root, falcon_files),
        "dependencies_or_implementations": relative_names(root, dependencies),
        "fn_dsa_files": relative_names(root, fn_dsa_files),
        "falcon_512_files": relative_names(root, parameter_512),
        "falcon_1024_files": relative_names(root, parameter_1024),
        "sign_files": relative_names(root, sign_calls),
        "verify_files": relative_names(root, verify_calls),
        "explicit_format_files": relative_names(root, explicit_formats),
        "randomness_files": relative_names(root, rng_files),
        "streaming_files": relative_names(
            root,
            stream_sign_start + stream_sign_finish + stream_verify_start + stream_verify_finish,
        ),
        "custom_internal_files": relative_names(root, custom_internals),
        "vector_files": relative_names(root, vector_files),
        "negative_test_files": relative_names(root, negative_tests),
    }
    return {
        "root": str(root),
        "summary": {
            "files_scanned": len(files),
            "falcon_files": len(falcon_files),
            "warnings": sum(item.severity == "warning" for item in findings),
            "info": sum(item.severity == "info" for item in findings),
        },
        "signals": signals,
        "findings": [asdict(item) for item in findings],
    }


def print_human(report: dict[str, object]) -> None:
    summary = report["summary"]
    assert isinstance(summary, dict)
    print(f"Falcon/FN-DSA inspection: {report['root']}")
    print(
        f"Scanned {summary['files_scanned']} files; "
        f"{summary['falcon_files']} Falcon-related files."
    )
    findings = report["findings"]
    assert isinstance(findings, list)
    if not findings:
        print("No heuristic findings.")
        return
    for finding in findings:
        assert isinstance(finding, dict)
        print(f"{str(finding['severity']).upper()} [{finding['code']}]: {finding['message']}")
        files = finding.get("files", ())
        assert isinstance(files, (list, tuple))
        for path in files:
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
