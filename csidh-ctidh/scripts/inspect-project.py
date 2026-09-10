#!/usr/bin/env python3
"""Inspect CSIDH-family projects for provenance, validation, protocol, timing, and fault-risk signals."""

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
    "build",
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
    ".h",
    ".hpp",
    ".rs",
    ".go",
    ".py",
    ".java",
    ".kt",
    ".swift",
    ".toml",
    ".json",
    ".yml",
    ".yaml",
    ".md",
    ".txt",
    ".mk",
}
TEXT_NAMES = {"Makefile", "CMakeLists.txt", "Cargo.toml", "Cargo.lock", "meson.build"}
MAX_FILE_BYTES = 2_000_000


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    files: tuple[str, ...] = ()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect CSIDH/CTIDH/dCTIDH provenance, parameters, validation, KDF, CT, and fault signals."
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
    code_files = tuple(
        path
        for path in files
        if path.suffix.lower() in {".c", ".cc", ".cpp", ".h", ".hpp", ".rs", ".go", ".py", ".java", ".kt", ".swift"}
    )

    isogeny_files = matching(
        files,
        texts,
        r"\b(?:CSIDH|CTIDH|dCSIDH|dCTIDH)\b|\b(?:csidh|ctidh|dcsidh|dctidh)[_-](?:private|public|action|validate|derive|keygen)|class[-_ ]group action",
    )
    isogeny_code = tuple(path for path in code_files if path in isogeny_files)
    csidh_files = matching(isogeny_files, texts, r"\b(?:d?CSIDH)\b|\bd?csidh_")
    ctidh_files = matching(isogeny_files, texts, r"\b(?:d?CTIDH)\b|\bd?ctidh_")
    dummy_free_files = matching(isogeny_files, texts, r"\bd(?:CSIDH|CTIDH)\b|\bd(?:csidh|ctidh)_|dummy[-_ ]free")
    sidh_sike_files = matching(files, texts, r"\bSIDH\b|\bSIKE\b|sidh_|sike_")
    signature_files = matching(files, texts, r"SQISign|SeaSign|isogeny[^\n]{0,40}signature")

    source_pin_files = matching(
        isogeny_files,
        texts,
        r"(?:csidh|ctidh|dcsidh|dctidh)(?:[-_A-Za-z0-9/.]+)?@[0-9a-f]{7,40}|source(?:[-_ ]commit)?\s*[@=:]\s*[0-9a-f]{7,40}|commit\s*[=:]\s*[0-9a-f]{7,40}|sha256\s*[=:]\s*[0-9a-f]{64}|2021[-_]?05[-_]?23",
    )
    parameter_files = matching(
        isogeny_files,
        texts,
        r"(?:CSIDH|CTIDH|dCSIDH|dCTIDH)[-_ ]?(?:511|512|1024|2047|2048|4096|5120|6144|8192|9216)|\bp(?:bits|_bits)?\s*[=:]\s*(?:511|512|1024|2047|2048|4096|5120|6144|8192|9216)|\bprimes?\s*\[",
    )
    custom_parameter_files = matching(
        code_files,
        texts,
        r"generate[_-]?(?:csidh|ctidh)?[_-]?parameters?|custom[_-]?(?:prime|parameters?)|random[_-]?prime|nextPrime|next_prime|probablePrime",
    )
    volatile_parameter_files = matching(
        custom_parameter_files,
        texts,
        r"time\s*\(|currentTimeMillis|Instant\.now|UUID\.randomUUID|random\.random|Math\.random|\brand\s*\(",
    )

    keygen_files = matching(
        isogeny_code,
        texts,
        r"(?:csidh|ctidh|dcsidh|dctidh)[_-](?:private|keygen|secret)|generate[_-]?(?:private|secret)[_-]?key",
    )
    action_files = matching(
        isogeny_code,
        texts,
        r"(?:csidh|ctidh|dcsidh|dctidh)[_-](?:action|derive|shared)|class[_-]?group[_-]?action|group_action",
    )
    validation_files = matching(
        isogeny_files,
        texts,
        r"(?:csidh|ctidh|dcsidh|dctidh)[_-]?(?:validate|validation)|validate[_-]?(?:public|curve)|supersingular|supersingularity|is_supersingular|class[_-]?membership",
    )
    canonical_decode_files = matching(
        isogeny_files,
        texts,
        r"canonical|decode[_-]?(?:public|curve)|field[_-]?(?:decode|from_bytes)|reject[^\n]{0,60}(?:noncanonical|out.of.range|singular)",
    )
    range_only_validation = matching(
        isogeny_code,
        texts,
        r"validate[^\n{]{0,100}\{[^}]{0,400}(?:<\s*p|>=\s*p|field[_-]?range)[^}]{0,200}\}",
    )

    kdf_files = matching(
        isogeny_files,
        texts,
        r"\bHKDF\b|\bKDF\b|derive[_-]?(?:session|key)|extract[_-]?and[_-]?expand|shake256[^\n]{0,80}(?:shared|transcript)",
    )
    transcript_files = matching(
        isogeny_files,
        texts,
        r"transcript|protocol[_-]?version|ciphersuite|role[_-]?(?:a|b|client|server)|public[_-]?key[_-]?a|public[_-]?key[_-]?b",
    )
    direct_shared_key_files = matching(
        isogeny_code,
        texts,
        r"(?:AES|ChaCha|Poly1305|SecretKeySpec|cipher[_-]?key)[^\n]{0,100}(?:shared[_-]?(?:curve|coefficient|secret)|curve[_-]?coefficient)|(?:shared[_-]?(?:curve|coefficient)|curve[_-]?coefficient)[^\n]{0,100}(?:AES|ChaCha|SecretKeySpec|cipher)",
    )

    rng_files = matching(
        isogeny_code,
        texts,
        r"getrandom|arc4random|randombytes|RAND_bytes|OsRng|SecureRandom|crypto\.rand|/dev/urandom|CSPRNG|DRBG",
    )
    weak_rng_files = matching(
        isogeny_code,
        texts,
        r"\b(?:s?rand|rand)\s*\(|Math\.random|random\.random|java\.util\.Random|kotlin\.random\.Random",
    )
    secret_branch_files = matching(
        isogeny_code,
        texts,
        r"\bif\s*\(\s*!?\s*(?:secret|private|exponent|e\s*\[)|\b(?:switch|while)\s*\(\s*(?:secret|private|exponent|e\s*\[)",
    )
    secret_index_files = matching(
        isogeny_code,
        texts,
        r"[A-Za-z_][A-Za-z0-9_]*\s*\[\s*(?:secret|private|exponent|e\s*\[)",
    )
    dummy_files = matching(
        isogeny_code,
        texts,
        r"dummy[_-]?(?:isogeny|action|step|point)|(?:real|dummy)[-_ ]operation|is_dummy",
    )
    ct_test_files = matching(
        files,
        texts,
        r"\btimecop\b|ctgrind|dudect|valgrind[^\n]{0,80}(?:secret|constant)|constant[-_ ]time[^\n]{0,80}(?:test|check)",
    )
    fault_test_files = matching(
        files,
        texts,
        r"fault[_-]?(?:inject|test|campaign)|glitch|voltage[-_ ]fault|clock[-_ ]fault|skip[-_ ]instruction|power[_-]?analysis|electromagnetic|\bEM trace",
    )
    cpu_feature_files = matching(
        files,
        texts,
        r"\bADX\b|\bAVX2\b|\bBMI2\b|Broadwell|Zen\+?|target_feature|march=|mcpu=",
    )
    velusqrt_files = matching(isogeny_files, texts, r"velu[_-]?sqrt|VeluSqrt|velusqrt|sqrt[_-]?velu")
    vectors_files = matching(
        files,
        texts,
        r"test[_-]?vectors?|known[_-]?answer|\bKATs?\b|commutativ(?:e|ity)[^\n]{0,80}(?:test|check)|agreement[_-]?test",
    )
    invalid_key_test_files = matching(
        files,
        texts,
        r"invalid[_-]?(?:public|curve|key)|noncanonical|singular|ordinary[_-]?curve|non[-_]?supersingular|wrong[-_]?(?:parameter|variant)|cross[-_]?(?:parameter|variant)",
    )

    findings: list[Finding] = []
    if not isogeny_files:
        findings.append(Finding("info", "NO_CSIDH_FAMILY_SIGNALS", "No CSIDH/CTIDH/dCSIDH/dCTIDH signals were found."))
    if isogeny_files and not source_pin_files:
        findings.append(
            Finding(
                "warning",
                "SOURCE_REVISION_UNPINNED",
                "CSIDH-family code/configuration was found without a recognizable commit/archive date/digest. Pin the exact paper/source/parameter tuple.",
                names(root, isogeny_files),
            )
        )
    if isogeny_files and not parameter_files:
        findings.append(
            Finding(
                "warning",
                "PARAMETER_SET_NOT_IDENTIFIED",
                "No recognized CSIDH-family parameter label/prime-size definition was found. Do not infer parameters from key length.",
                names(root, isogeny_files),
            )
        )
    if sidh_sike_files and isogeny_files:
        findings.append(
            Finding(
                "warning",
                "SIDH_SIKE_CONSTRUCTION_CONFUSION",
                "SIDH/SIKE and CSIDH-family identifiers coexist. Keep their constructions, status, keys, and security claims separate; SIDH/SIKE is broken.",
                names(root, sidh_sike_files + isogeny_files),
            )
        )
    if signature_files and isogeny_files:
        findings.append(
            Finding(
                "warning",
                "ISOGENY_SIGNATURE_SCOPE_MIXED",
                "Isogeny-signature and CSIDH-family group-action signals coexist. Verify separate protocols, parameters, and implementations.",
                names(root, signature_files + isogeny_files),
            )
        )
    if action_files and not validation_files:
        findings.append(
            Finding(
                "warning",
                "PUBLIC_KEY_VALIDATION_NOT_FOUND",
                "A secret class-group action is present without recognizable full public-key validation. Validate canonical, nonsingular, expected supersingular/class membership before action.",
                names(root, action_files),
            )
        )
    if validation_files and not canonical_decode_files:
        findings.append(
            Finding(
                "warning",
                "CANONICAL_DECODE_NOT_FOUND",
                "Public-key validation exists without recognizable canonical decode/range/singularity handling.",
                names(root, validation_files),
            )
        )
    if range_only_validation and not matching(validation_files, texts, r"supersingular|class[_-]?membership|order[_-]?check"):
        findings.append(
            Finding(
                "warning",
                "RANGE_ONLY_VALIDATION_SIGNAL",
                "Validation appears limited to field range. Use the exact supersingularity/class validation required by the selected construction.",
                names(root, range_only_validation),
            )
        )
    if action_files and not kdf_files:
        findings.append(
            Finding(
                "warning",
                "TRANSCRIPT_KDF_NOT_FOUND",
                "Shared-action code exists without a recognized KDF. Never use a curve coefficient directly as a session key.",
                names(root, action_files),
            )
        )
    if kdf_files and not transcript_files:
        findings.append(
            Finding(
                "warning",
                "TRANSCRIPT_BINDING_NOT_FOUND",
                "A KDF exists without recognizable protocol/version/ciphersuite/roles/both-public-key transcript binding.",
                names(root, kdf_files),
            )
        )
    if direct_shared_key_files:
        findings.append(
            Finding(
                "warning",
                "DIRECT_SHARED_CURVE_KEY_USE",
                "Shared curve/coefficient appears to feed an application cipher directly. Insert a canonical transcript-bound KDF.",
                names(root, direct_shared_key_files),
            )
        )
    if keygen_files and not rng_files:
        findings.append(
            Finding(
                "warning",
                "CSPRNG_NOT_FOUND",
                "Secret-exponent generation was found without a recognized CSPRNG/DRBG integration.",
                names(root, keygen_files),
            )
        )
    if weak_rng_files:
        findings.append(
            Finding(
                "warning",
                "POSSIBLE_NON_CSPRNG",
                "A general-purpose random API appears in CSIDH-family code. Replace it with a failure-reporting CSPRNG/approved DRBG or prove it is unrelated.",
                names(root, weak_rng_files),
            )
        )
    if secret_branch_files or secret_index_files:
        findings.append(
            Finding(
                "warning",
                "SECRET_DEPENDENT_CONTROL_OR_INDEX",
                "Secret/private/exponent values appear in branch/loop/index expressions. Prove the selected algorithm and target path are constant-time or remove the dependency.",
                names(root, secret_branch_files + secret_index_files),
            )
        )
    if dummy_files and not fault_test_files:
        findings.append(
            Finding(
                "warning",
                "DUMMY_ACTION_WITHOUT_FAULT_EVIDENCE",
                "Dummy operations were found without recognizable fault-injection/power/EM tests. Real-versus-dummy distinction can enable key recovery.",
                names(root, dummy_files),
            )
        )
    if isogeny_code and not ct_test_files:
        findings.append(
            Finding(
                "info",
                "CONSTANT_TIME_TEST_NOT_FOUND",
                "No recognized timecop/ctgrind/dudect/constant-time test was found for CSIDH-family implementation code.",
                names(root, isogeny_code),
            )
        )
    if isogeny_code and not fault_test_files:
        findings.append(
            Finding(
                "info",
                "FAULT_TEST_NOT_FOUND",
                "No recognized fault/power/EM test was found. Confirm whether physical/fault attackers are excluded from the threat model.",
                names(root, isogeny_code),
            )
        )
    if custom_parameter_files:
        findings.append(
            Finding(
                "warning",
                "CUSTOM_PARAMETER_GENERATION",
                "Custom CSIDH-family parameter generation was found. Require reproducible constants, independent checks, attack estimates, and a new parameter identity.",
                names(root, custom_parameter_files),
            )
        )
    if volatile_parameter_files:
        findings.append(
            Finding(
                "warning",
                "VOLATILE_PARAMETER_GENERATION",
                "Custom parameter generation depends on time or general-purpose randomness without recorded deterministic provenance.",
                names(root, volatile_parameter_files),
            )
        )
    if velusqrt_files and not vectors_files:
        findings.append(
            Finding(
                "warning",
                "VELUSQRT_BASELINE_TEST_NOT_FOUND",
                "VeluSqrt integration exists without recognizable baseline/vector comparison. Verify formulas/preconditions and output equality before optimization claims.",
                names(root, velusqrt_files),
            )
        )
    if validation_files and not invalid_key_test_files:
        findings.append(
            Finding(
                "info",
                "INVALID_KEY_TESTS_NOT_FOUND",
                "Public-key validation exists without recognizable noncanonical/singular/wrong-class/cross-parameter tests.",
                names(root, validation_files),
            )
        )
    if isogeny_code and not cpu_feature_files:
        findings.append(
            Finding(
                "info",
                "TARGET_DISPATCH_NOT_FOUND",
                "No recognizable CPU-feature/compiler-target declaration was found. Confirm the exact implementation path used in timing/performance evidence.",
            )
        )

    signals = {
        "isogeny_files": names(root, isogeny_files),
        "csidh_files": names(root, csidh_files),
        "ctidh_files": names(root, ctidh_files),
        "dummy_free_variant_files": names(root, dummy_free_files),
        "sidh_sike_files": names(root, sidh_sike_files),
        "signature_scheme_files": names(root, signature_files),
        "source_pin_files": names(root, source_pin_files),
        "parameter_files": names(root, parameter_files),
        "keygen_files": names(root, keygen_files),
        "action_files": names(root, action_files),
        "validation_files": names(root, validation_files),
        "canonical_decode_files": names(root, canonical_decode_files),
        "kdf_files": names(root, kdf_files),
        "transcript_files": names(root, transcript_files),
        "rng_files": names(root, rng_files),
        "dummy_operation_files": names(root, dummy_files),
        "constant_time_test_files": names(root, ct_test_files),
        "fault_test_files": names(root, fault_test_files),
        "cpu_feature_files": names(root, cpu_feature_files),
        "velusqrt_files": names(root, velusqrt_files),
        "vector_or_agreement_test_files": names(root, vectors_files),
        "invalid_key_test_files": names(root, invalid_key_test_files),
        "custom_parameter_files": names(root, custom_parameter_files),
    }
    return {
        "root": str(root),
        "summary": {
            "files_scanned": len(files),
            "isogeny_files": len(isogeny_files),
            "warnings": sum(item.severity == "warning" for item in findings),
            "info": sum(item.severity == "info" for item in findings),
        },
        "signals": signals,
        "findings": [asdict(item) for item in findings],
    }


def print_human(report: dict[str, object]) -> None:
    summary = report["summary"]
    assert isinstance(summary, dict)
    print(f"CSIDH/CTIDH inspection: {report['root']}")
    print(
        f"Scanned {summary['files_scanned']} files; "
        f"{summary['isogeny_files']} CSIDH-family files."
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
