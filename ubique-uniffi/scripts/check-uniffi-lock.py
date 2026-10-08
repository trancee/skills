#!/usr/bin/env python3
"""Check resolved UniFFI versions in selected Cargo lockfiles without executing Cargo."""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

UNIFFI_PACKAGES = {"uniffi", "uniffi_core", "uniffi_meta", "uniffi_macros", "uniffi_internal_macros", "uniffi_build", "uniffi_bindgen", "uniffi_pipeline", "uniffi_udl"}


def check(lock: Path, expected: str) -> dict[str, object]:
    with lock.open("rb") as source:
        data = tomllib.load(source)
    packages = data.get("package")
    if not isinstance(packages, list) or any(not isinstance(package, dict) for package in packages):
        raise ValueError(f"{lock}: expected Cargo.lock [[package]] entries; pass a resolved lockfile, not Cargo.toml")
    found = []
    for package in packages:
        if package.get("name") in UNIFFI_PACKAGES:
            version = package.get("version")
            if not isinstance(version, str):
                raise ValueError(f"{lock}: UniFFI entry lacks a string version; regenerate the Cargo lockfile")
            found.append({"name": package["name"], "version": version, "source": package.get("source", "local")})
    found.sort(key=lambda package: (package["name"], package["version"], package["source"]))
    errors = []
    if not found:
        errors.append("no UniFFI packages found; select the interop crate's resolved lockfile")
    for package in found:
        if package["version"] != expected:
            errors.append(f"{package['name']} resolves {package['version']}, expected {expected}; align the runtime/build/generator dependency graph")
    return {"lockfile": str(lock), "packages": found, "errors": errors, "valid": not errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", action="append", type=Path, required=True, help="Cargo.lock to check; repeat for independent workspaces")
    parser.add_argument("--expected", required=True, help="exact UniFFI version supported by the selected Ubique release")
    parser.add_argument("--json", action="store_true", help="emit a structured report")
    args = parser.parse_args()
    try:
        reports = [check(lock.expanduser().resolve(), args.expected) for lock in args.lock]
    except (OSError, ValueError, TypeError) as error:
        print(f"error: {error}; resolve dependencies and retry with the owning Cargo.lock", file=sys.stderr)
        return 2
    valid = all(report["valid"] for report in reports)
    limits = "Known UniFFI ABI/generation packages in each selected lockfile: no active-feature, allocator, shared-crate ABI, Gradle, binary, or runtime verification. Git patches may share a version."
    if args.json:
        print(json.dumps({"valid": valid, "expected": args.expected, "lockfiles": reports, "limits": limits}, indent=2, sort_keys=True))
    else:
        for report in reports:
            print(f"{report['lockfile']}: {'PASS' if report['valid'] else 'FAIL'}")
            for error in report["errors"]:
                print(f"error: {error}", file=sys.stderr)
        print(limits)
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
