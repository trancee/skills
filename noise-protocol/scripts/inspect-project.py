#!/usr/bin/env python3
"""Inspect Noise protocol names, dependencies, state APIs, and risky configuration candidates."""

from __future__ import annotations

import argparse
import json
import platform
import re
import sys
from pathlib import Path
from typing import Any

IGNORED_DIRS = {".cache", ".git", ".gradle", ".idea", "build", "dist", "node_modules", "target", "vendor"}
SOURCE_SUFFIXES = {".c", ".cc", ".cpp", ".cs", ".go", ".h", ".hpp", ".java", ".js", ".kt", ".kts", ".py", ".rs", ".swift", ".ts"}
CONFIG_SUFFIXES = {".gradle", ".json", ".mod", ".toml", ".xml", ".yaml", ".yml"}
CONFIG_NAMES = {"Cargo.toml", "Package.swift", "build.gradle", "build.gradle.kts", "go.mod", "package.json", "pom.xml", "pyproject.toml", "requirements.txt"}
MAX_FILE_SIZE = 2 * 1024 * 1024
PROTOCOL_RE = re.compile(r"\bNoise_[A-Za-z0-9+/_-]+\b")
KNOWN_PATTERNS = {
    "N", "K", "X", "NN", "NK", "NX", "XN", "XK", "XX", "KN", "KK", "KX", "IN", "IK", "IX",
    "NK1", "NX1", "X1N", "X1K", "XK1", "X1K1", "X1X", "XX1", "X1X1",
    "K1N", "K1K", "KK1", "K1K1", "K1X", "KX1", "K1X1",
    "I1N", "I1K", "IK1", "I1K1", "I1X", "IX1", "I1X1",
}
DEFERRED_PATTERNS = KNOWN_PATTERNS - {"N", "K", "X", "NN", "NK", "NX", "XN", "XK", "XX", "KN", "KK", "KX", "IN", "IK", "IX"}
OFFICIAL_ALGORITHMS = {
    "dh": {"25519", "448"},
    "cipher": {"ChaChaPoly", "AESGCM"},
    "hash": {"SHA256", "SHA512", "BLAKE2s", "BLAKE2b"},
}
DEPENDENCY_PATTERNS = {
    "flynn/noise": re.compile(r"github\.com/flynn/noise"),
    "nyquist": re.compile(r"github\.com/yawning/nyquist"),
    "snow": re.compile(r"(?:\buse\s+snow::|\bsnow\s*=|[\"']snow[\"'])"),
    "noiseprotocol": re.compile(r"(?:\bfrom\s+noise(?:\.|\s)|\bimport\s+noise\b|\bnoiseprotocol\b)"),
    "dissononce": re.compile(r"\bdissononce\b"),
    "cacophony": re.compile(r"\bcacophony\b"),
    "noise-c": re.compile(r"(?:\bnoise-c\b|#\s*include\s*[<\"]noise/)"),
    "noise-java": re.compile(r"(?:\bnoise-java\b|com\.southernstorm\.noise)"),
}
SIGNALS = {
    "write_handshake": re.compile(r"\b(?:write_message|writeMessage|WriteMessage)\b"),
    "read_handshake": re.compile(r"\b(?:read_message|readMessage|ReadMessage)\b"),
    "transport_transition": re.compile(r"\b(?:into_transport_mode|Split|split)\b"),
    "handshake_hash": re.compile(r"\b(?:get_handshake_hash|GetHandshakeHash|handshake_hash|handshakeHash)\b"),
    "prologue": re.compile(r"\bprologue\b", re.IGNORECASE),
    "psk": re.compile(r"\b(?:psk|pre_shared_key|preSharedKey)\b", re.IGNORECASE),
    "remote_static": re.compile(r"\b(?:remote_static|remoteStatic|rs)\b"),
    "static_key": re.compile(r"\b(?:static_key|staticKey|StaticKeypair)\b"),
    "ephemeral": re.compile(r"\b(?:ephemeral|Ephemeral|generate_keypair|GenerateKeypair)\b"),
    "rekey": re.compile(r"\b(?:rekey|Rekey)\b"),
    "set_nonce": re.compile(r"\b(?:set_nonce|setNonce|SetNonce)\b"),
    "encrypt_transport": re.compile(r"\b(?:encrypt|EncryptWithAd|write_transport_message)\b"),
    "decrypt_transport": re.compile(r"\b(?:decrypt|DecryptWithAd|read_transport_message)\b"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="project root (default: cwd)")
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    return parser.parse_args()


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def candidate_files(root: Path) -> tuple[list[Path], list[str]]:
    files: list[Path] = []
    skipped_large: list[str] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in IGNORED_DIRS for part in relative.parts) or not path.is_file():
            continue
        if path.name.endswith((".lock", ".min.js")):
            continue
        if path.name not in CONFIG_NAMES and path.suffix not in SOURCE_SUFFIXES | CONFIG_SUFFIXES:
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size > MAX_FILE_SIZE:
            skipped_large.append(relative.as_posix())
            continue
        files.append(path)
    return sorted(files, key=lambda item: item.as_posix()), sorted(skipped_large)


def parse_pattern_section(section: str) -> tuple[str | None, list[str], list[str]]:
    errors: list[str] = []
    match = re.fullmatch(r"([A-Z][A-Z0-9]*)(.*)", section)
    if not match:
        return None, [], ["invalid handshake pattern section"]
    base = match.group(1)
    remainder = match.group(2)
    modifiers: list[str] = []
    if remainder:
        modifiers = remainder.split("+")
        if any(not re.fullmatch(r"[a-z][a-z0-9]*", modifier) for modifier in modifiers):
            errors.append("invalid pattern modifier syntax/order")
    if len(modifiers) != len(set(modifiers)):
        errors.append("duplicate pattern modifier")
    return base, modifiers, errors


def validate_protocol_name(name: str) -> dict[str, Any]:
    errors: list[str] = []
    try:
        encoded = name.encode("ascii")
    except UnicodeEncodeError:
        encoded = b""
        errors.append("protocol name is not ASCII")
    if len(encoded) > 255:
        errors.append("protocol name exceeds 255 bytes")
    parts = name.split("_")
    if len(parts) != 5 or parts[0] != "Noise":
        return {"name": name, "valid": False, "errors": sorted(set(errors + ["expected Noise_<pattern>_<DH>_<cipher>_<hash>"]))}
    pattern_section, dh, cipher, hash_name = parts[1:]
    base, modifiers, pattern_errors = parse_pattern_section(pattern_section)
    errors.extend(pattern_errors)
    for label, section in (("DH", dh), ("cipher", cipher), ("hash", hash_name)):
        if any(not re.fullmatch(r"[A-Za-z0-9/]+", algorithm) for algorithm in section.split("+")):
            errors.append(f"invalid {label} algorithm section")
    return {
        "name": name, "valid": not errors, "errors": sorted(set(errors)),
        "base_pattern": base, "modifiers": modifiers,
        "known_revision_34_pattern": base in KNOWN_PATTERNS if base else False,
        "deferred_revision_34_pattern": base in DEFERRED_PATTERNS if base else False,
        "dh": dh, "cipher": cipher, "hash": hash_name,
        "official_revision_34_algorithms": {
            "dh": all(item in OFFICIAL_ALGORITHMS["dh"] for item in dh.split("+")),
            "cipher": all(item in OFFICIAL_ALGORITHMS["cipher"] for item in cipher.split("+")),
            "hash": all(item in OFFICIAL_ALGORITHMS["hash"] for item in hash_name.split("+")),
        },
    }


def line_numbers(text: str, pattern: re.Pattern[str]) -> list[int]:
    return [number for number, line in enumerate(text.splitlines(), 1) if pattern.search(line)]


def inspect_file(path: Path, root: Path) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[dict[str, Any]]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    protocols = [{**validate_protocol_name(name), "file": rel(path, root), "line": text[:match.start()].count("\n") + 1}
                 for match in PROTOCOL_RE.finditer(text) for name in [match.group(0)]]
    signal_lines = {name: line_numbers(text, pattern) for name, pattern in SIGNALS.items()}
    signal_lines = {name: lines for name, lines in signal_lines.items() if lines}
    dependency_markers = sorted(name for name, pattern in DEPENDENCY_PATTERNS.items() if pattern.search(text))
    custom_patterns = []
    pattern_line = re.compile(r"(?:->|<-)\s*(?:e|s|ee|es|se|ss|psk)(?:\s*,\s*(?:e|s|ee|es|se|ss|psk))*")
    for number, line in enumerate(text.splitlines(), 1):
        if pattern_line.search(line):
            custom_patterns.append({"file": rel(path, root), "line": number})
    secret_candidates: list[dict[str, Any]] = []
    secret_pattern = re.compile(
        r"(?i)\b(psk|pre[_-]?shared[_-]?key|static[_-]?private|private[_-]?key)\b[^\n=]{0,40}=\s*[\"'](?:[0-9a-f]{64}|[A-Za-z0-9+/]{43,}={0,2})[\"']"
    )
    for match in secret_pattern.finditer(text):
        secret_candidates.append({"file": rel(path, root), "line": text[:match.start()].count("\n") + 1, "kind": match.group(1).lower()})
    insecure_rng = line_numbers(text, re.compile(r"\b(?:Math\.random|random\.random|rand\s*\()"))
    secret_logging = line_numbers(text, re.compile(r"(?i)(?:print|log|debug|trace)[^\n]*(?:psk|private[_ ]?key|keypair)"))
    raw_primitives = sorted(name for name in ("X25519", "HKDF", "ChaCha20Poly1305", "AESGCM") if name.lower() in text.lower())
    relevant = bool(protocols or signal_lines or dependency_markers or custom_patterns or secret_candidates or insecure_rng or secret_logging)
    entry = None
    if relevant:
        entry = {
            "file": rel(path, root), "protocol_names": sorted({item["name"] for item in protocols}),
            "dependency_markers": dependency_markers, "signals": signal_lines,
            "hardcoded_secret_candidates": secret_candidates,
            "insecure_rng_candidate_lines": insecure_rng, "secret_logging_candidate_lines": secret_logging,
            "raw_primitive_markers": raw_primitives,
        }
    return entry, protocols, custom_patterns


def inspect(root: Path) -> dict[str, Any]:
    files, skipped_large = candidate_files(root)
    entries: list[dict[str, Any]] = []
    protocols: list[dict[str, Any]] = []
    custom_patterns: list[dict[str, Any]] = []
    for path in files:
        entry, found_protocols, found_patterns = inspect_file(path, root)
        if entry:
            entries.append(entry)
        protocols.extend(found_protocols)
        custom_patterns.extend(found_patterns)
    unique_protocols = {item["name"]: item for item in protocols}
    ordered_protocols = [unique_protocols[name] for name in sorted(unique_protocols)]
    dependency_found = any(entry["dependency_markers"] for entry in entries)
    signals = {name for entry in entries for name in entry["signals"]}
    warnings: list[str] = []
    if protocols and not dependency_found:
        warnings.append("Noise protocol names found but no known Noise library dependency marker was detected.")
    if any(not item["valid"] for item in ordered_protocols):
        warnings.append("Invalid Noise protocol name syntax found.")
    if any(not item.get("known_revision_34_pattern", False) for item in ordered_protocols if item["valid"]):
        warnings.append("Unknown/custom handshake pattern found; require its governing specification and expert review.")
    if any(item.get("deferred_revision_34_pattern", False) for item in ordered_protocols):
        warnings.append("Revision-34 deferred handshake pattern found; deferred patterns are marked unstable.")
    if any(not all(item.get("official_revision_34_algorithms", {}).values()) for item in ordered_protocols if item["valid"]):
        warnings.append("Non-core revision-34 algorithm name found; verify extension specification and library support.")
    if any(any(modifier.startswith("psk") for modifier in item.get("modifiers", [])) for item in ordered_protocols) and "psk" not in signals:
        warnings.append("PSK protocol modifier found without a detected PSK configuration/use site.")
    if any(item.get("base_pattern", "").endswith("K") for item in ordered_protocols) and "remote_static" not in signals:
        warnings.append("Pattern requiring pre-known responder static key found without a detected remote-static input site.")
    if custom_patterns:
        warnings.append("Custom handshake token notation found; use only vetted named patterns or require expert review.")
    if any(entry["hardcoded_secret_candidates"] for entry in entries):
        warnings.append("Hard-coded PSK/private-key candidate found; provision secrets outside source and logs.")
    if any(entry["insecure_rng_candidate_lines"] for entry in entries) and (protocols or dependency_found):
        warnings.append("Non-cryptographic RNG candidate found near a Noise integration; production key generation must use a CSPRNG.")
    if any(entry["secret_logging_candidate_lines"] for entry in entries):
        warnings.append("Potential PSK/private-key logging site found.")
    if "set_nonce" in signals:
        warnings.append("Explicit nonce-setting API found; verify bounded replay tracking and successful-decrypt nonce consumption.")
    if "rekey" in signals and not ({"encrypt_transport", "decrypt_transport"} & signals):
        warnings.append("Rekey use found without detected transport operation; verify synchronized per-direction trigger ownership.")
    raw_files = [entry for entry in entries if len(entry["raw_primitive_markers"]) >= 3]
    if raw_files and not dependency_found:
        warnings.append("Custom Noise primitive/state-machine candidate found; prefer a maintained Noise library and require expert review.")
    if ({"write_handshake", "read_handshake"} & signals) and "transport_transition" not in signals:
        warnings.append("Handshake read/write APIs found without a detected split/transport transition.")
    if "transport_transition" in signals and "handshake_hash" not in signals:
        warnings.append("Transport transition found without detected handshake-hash/channel-binding handling; verify application authentication needs.")
    return {
        "root": str(root), "host": {"system": platform.system(), "machine": platform.machine()},
        "files_scanned": len(files), "skipped_large_files": skipped_large,
        "protocols": ordered_protocols, "integration_files": entries,
        "custom_pattern_candidates": sorted(custom_patterns, key=lambda item: (item["file"], item["line"])),
        "warnings": sorted(set(warnings)),
    }


def print_human(data: dict[str, Any]) -> None:
    print(f"Root: {data['root']}")
    print(f"Host: {data['host']['system']} {data['host']['machine']}")
    print(f"Files scanned: {data['files_scanned']}")
    print(f"Protocol names: {', '.join(item['name'] for item in data['protocols']) or 'none'}")
    print(f"Integration files: {len(data['integration_files'])}")
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
