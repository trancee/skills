#!/usr/bin/env python3
"""Count skill context with the GPT-5 tokenizer and compare a git baseline."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import tiktoken
except ImportError:
    tiktoken = None

LEGAL_FILES = {"license", "license.md", "license.txt", "upstream-license.txt"}


def included(relative: Path) -> bool:
    parts = relative.parts
    if parts == ("SKILL.md",):
        return True
    return len(parts) == 2 and parts[0] in {"assets", "references"} and parts[1].lower() not in LEGAL_FILES


def current_files(package: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(package.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(package)
        if not included(relative):
            continue
        try:
            result[relative.as_posix()] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
    return result


def git_output(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, check=False)


def baseline_files(root: Path, package: Path, revision: str) -> dict[str, str]:
    try:
        package_relative = package.relative_to(root).as_posix()
    except ValueError as error:
        raise ValueError(f"package is outside --root and cannot use --baseline: {package}") from error

    listing = git_output(root, "ls-tree", "-r", "--name-only", revision, "--", package_relative)
    if listing.returncode != 0:
        detail = listing.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"git cannot read baseline {revision!r}: {detail}")

    result: dict[str, str] = {}
    for repository_path in listing.stdout.decode("utf-8").splitlines():
        relative = Path(repository_path).relative_to(package_relative)
        if not included(relative):
            continue
        content = git_output(root, "show", f"{revision}:{repository_path}")
        if content.returncode != 0:
            detail = content.stderr.decode("utf-8", errors="replace").strip()
            raise ValueError(f"git cannot read {revision}:{repository_path}: {detail}")
        try:
            result[relative.as_posix()] = content.stdout.decode("utf-8")
        except UnicodeDecodeError:
            continue
    return result


def count_files(files: dict[str, str], encoding: Any) -> tuple[dict[str, int], int, int]:
    counts = {path: len(encoding.encode_ordinary(text)) for path, text in files.items()}
    core = counts.get("SKILL.md", 0)
    resources = sum(value for path, value in counts.items() if path != "SKILL.md")
    return counts, core, resources


def resolve_packages(root: Path, values: list[Path]) -> list[Path]:
    if values:
        packages = [(root / value).resolve() if not value.is_absolute() else value.resolve() for value in values]
    else:
        packages = sorted(path for path in root.iterdir() if path.is_dir() and (path / "SKILL.md").is_file())
    for package in packages:
        if not package.is_dir() or not (package / "SKILL.md").is_file():
            raise ValueError(f"not a skill package: {package}")
    return packages


def main() -> int:
    parser = argparse.ArgumentParser(description="Count SKILL.md and direct assets/references with GPT-5-compatible tokenization.")
    parser.add_argument("packages", nargs="*", type=Path, help="package paths relative to --root; default: every root package")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root; default: current directory")
    parser.add_argument("--baseline", help="git revision for token delta, usually HEAD")
    parser.add_argument("--model", default="gpt-5.6-sol", help="tiktoken model name; default: gpt-5.6-sol")
    parser.add_argument("--encoding", help="explicit tiktoken encoding; overrides --model")
    parser.add_argument("--json", action="store_true", help="write JSON")
    args = parser.parse_args()

    if tiktoken is None:
        print("ERROR: tiktoken is required. Install tiktoken>=0.14 in a disposable environment.", file=sys.stderr)
        return 2

    root = args.root.expanduser().resolve()
    if not root.is_dir():
        print(f"ERROR: --root is not a directory: {root}", file=sys.stderr)
        return 2
    try:
        packages = resolve_packages(root, args.packages)
        encoding = tiktoken.get_encoding(args.encoding) if args.encoding else tiktoken.encoding_for_model(args.model)
        reports: list[dict[str, Any]] = []
        for package in packages:
            files = current_files(package)
            file_counts, core, resources = count_files(files, encoding)
            baseline_total: int | None = None
            if args.baseline:
                old_files = baseline_files(root, package, args.baseline)
                _, old_core, old_resources = count_files(old_files, encoding)
                baseline_total = old_core + old_resources
            total = core + resources
            reports.append(
                {
                    "package": package.relative_to(root).as_posix() if package.is_relative_to(root) else str(package),
                    "coreTokens": core,
                    "resourceTokens": resources,
                    "totalTokens": total,
                    "baselineTokens": baseline_total,
                    "deltaTokens": None if baseline_total is None else total - baseline_total,
                    "files": file_counts,
                }
            )
    except (KeyError, OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    output = {
        "schemaVersion": 1,
        "model": args.model,
        "encoding": encoding.name,
        "ordinaryTextOnly": True,
        "baseline": args.baseline,
        "packages": reports,
        "totals": {
            "coreTokens": sum(item["coreTokens"] for item in reports),
            "resourceTokens": sum(item["resourceTokens"] for item in reports),
            "totalTokens": sum(item["totalTokens"] for item in reports),
            "baselineTokens": None if not args.baseline else sum(item["baselineTokens"] for item in reports),
            "deltaTokens": None if not args.baseline else sum(item["deltaTokens"] for item in reports),
        },
    }
    if args.json:
        print(json.dumps(output, indent=2))
        return 0

    print(f"encoding={encoding.name} model={args.model} baseline={args.baseline or '-'}")
    for item in reports:
        baseline = "-" if item["baselineTokens"] is None else str(item["baselineTokens"])
        delta = "-" if item["deltaTokens"] is None else f"{item['deltaTokens']:+d}"
        print(
            f"{item['package']}: core={item['coreTokens']} resources={item['resourceTokens']} "
            f"total={item['totalTokens']} baseline={baseline} delta={delta}"
        )
    totals = output["totals"]
    total_baseline = "-" if totals["baselineTokens"] is None else str(totals["baselineTokens"])
    total_delta = "-" if totals["deltaTokens"] is None else f"{totals['deltaTokens']:+d}"
    print(
        f"TOTAL: core={totals['coreTokens']} resources={totals['resourceTokens']} "
        f"total={totals['totalTokens']} baseline={total_baseline} delta={total_delta}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
