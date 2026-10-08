#!/usr/bin/env python3
"""Inspect one Cargo library for Gobley without building code or downloading dependencies."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def inspect(args: argparse.Namespace) -> dict[str, object]:
    manifest = args.manifest.expanduser().resolve()
    if not manifest.is_file():
        raise ValueError(f"manifest not found: {manifest}; pass the owning Cargo.toml")
    command = [
        "cargo", "metadata", "--format-version", "1", "--no-deps", "--offline",
        "--manifest-path", str(manifest),
    ]
    result = subprocess.run(command, cwd=manifest.parent, text=True, capture_output=True, timeout=60)
    if result.returncode:
        raise ValueError(f"cargo metadata failed; correct the manifest/workspace/toolchain:\n{result.stderr.strip()}")
    metadata = json.loads(result.stdout)
    members = set(metadata["workspace_members"])
    packages = [package for package in metadata["packages"] if package["id"] in members]
    if args.package:
        packages = [package for package in packages if package["name"] == args.package]
    else:
        owners = [package for package in packages if Path(package["manifest_path"]).resolve() == manifest]
        if owners:
            packages = owners
    if len(packages) != 1:
        names = ", ".join(package["name"] for package in packages) or "none"
        raise ValueError(f"select exactly one workspace member with --package NAME; candidates: {names}")
    package = packages[0]
    libraries = [target for target in package["targets"] if set(target["crate_types"]) & {"lib", "rlib", "dylib", "cdylib", "staticlib"}]
    if len(libraries) != 1:
        raise ValueError(f"package {package['name']} needs one library target; inspect [lib] and crate-type")
    library = libraries[0]
    errors: list[str] = []
    warnings: list[str] = []
    for kind in sorted(set(args.require_kind) - set(library["crate_types"])):
        errors.append(f"missing crate-type {kind}; add it to [lib].crate-type for the requested Kotlin targets")
    uniffi = [dependency for dependency in package["dependencies"] if dependency["name"] == "uniffi" and dependency["kind"] is None]
    requirements = sorted({dependency["req"] for dependency in uniffi})
    if args.uniffi_version:
        if not requirements:
            errors.append("no normal uniffi dependency; add the selected generator-compatible runtime dependency")
        elif any(requirement != f"={args.uniffi_version}" for requirement in requirements):
            warnings.append(f"UniFFI requirements {requirements} are not an exact ={args.uniffi_version} pin; inspect Cargo.lock and generator compatibility")
    if any(dependency.get("optional") for dependency in uniffi):
        warnings.append("uniffi is optional; confirm the selected Cargo features enable it for generation and runtime builds")
    return {
        "valid": not errors,
        "package": package["name"],
        "manifest": package["manifest_path"],
        "library": library["name"],
        "source": library["src_path"],
        "crate_types": library["crate_types"],
        "edition": library["edition"],
        "uniffi_requirements": requirements,
        "errors": errors,
        "warnings": warnings,
        "limits": "Cargo metadata only: no resolved dependency graph, Gradle, scaffolding, build, linking, packaging, or runtime proof.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True, help="owning Cargo.toml or virtual workspace manifest")
    parser.add_argument("--package", help="workspace member package name, not the library crate name")
    parser.add_argument("--require-kind", action="append", choices=("cdylib", "staticlib"), default=[], help="required artifact kind; repeat for mixed targets")
    parser.add_argument("--uniffi-version", help="expected exact runtime pin matching the selected Gobley bindgen")
    parser.add_argument("--strict", action="store_true", help="exit 1 for warnings as well as missing requirements")
    parser.add_argument("--json", action="store_true", help="emit the metadata report as JSON")
    args = parser.parse_args()
    try:
        report = inspect(args)
    except FileNotFoundError:
        print("error: cargo is unavailable; install/select the Rust toolchain and expose cargo on PATH", file=sys.stderr)
        return 2
    except subprocess.TimeoutExpired:
        print("error: cargo metadata exceeded 60s; inspect the selected toolchain/workspace before retrying", file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"{report['package']} -> {report['library']}: {', '.join(report['crate_types'])}")
        for message in report["errors"]:
            print(f"error: {message}", file=sys.stderr)
        for message in report["warnings"]:
            print(f"warning: {message}", file=sys.stderr)
        print(report["limits"])
    return 1 if report["errors"] or (args.strict and report["warnings"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
