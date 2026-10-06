#!/usr/bin/env python3
"""Inventory Tamarin .spthy theories and flag review hazards."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    files: tuple[str, ...] = ()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inventory Tamarin .spthy theories and flag review hazards."
    )
    parser.add_argument(
        "--root",
        required=True,
        help="A .spthy file or directory containing .spthy files.",
    )
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when warning or error findings exist.",
    )
    return parser.parse_args()


def discover(root: Path) -> tuple[Path, ...]:
    if root.is_file():
        return (root,) if root.suffix == ".spthy" else ()
    return tuple(sorted(path for path in root.rglob("*.spthy") if path.is_file()))


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.DOTALL)
    return re.sub(r"//[^\n]*", " ", text)


def matches(pattern: str, text: str, flags: int = re.MULTILINE) -> tuple[str, ...]:
    return tuple(match.group(1) for match in re.finditer(pattern, text, flags))


def relative(root: Path, path: Path) -> str:
    base = root if root.is_dir() else root.parent
    return path.relative_to(base).as_posix()


def inspect(root: Path, files: Iterable[Path]) -> dict[str, object]:
    findings: list[Finding] = []
    file_reports: list[dict[str, object]] = []

    for path in files:
        try:
            raw = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            findings.append(
                Finding("error", "UNREADABLE_THEORY", f"Cannot read UTF-8 theory: {error}", (relative(root, path),))
            )
            continue

        text = strip_comments(raw)
        file_name = relative(root, path)
        theories = matches(r"^\s*theory\s+([A-Za-z][A-Za-z0-9_]*)\b", text)
        builtins = tuple(
            item.strip()
            for declaration in matches(r"^\s*builtins\s*:\s*([^\n]+)", text)
            for item in declaration.split(",")
            if item.strip()
        )
        rules = matches(r"^\s*(?:diff_)?rule\s+([A-Za-z][A-Za-z0-9_]*)\b", text)
        lemmas = matches(
            r"^\s*(?:diffLemma|equivLemma|diffEquivLemma|accountability\s+lemma|lemma)\s+([A-Za-z][A-Za-z0-9_]*)\b",
            text,
        )
        restrictions = matches(r"^\s*(?:restriction|axiom)\s+([A-Za-z][A-Za-z0-9_]*)\b", text)
        has_process = bool(re.search(r"^\s*process(?:\s|:|=)", text, re.MULTILINE))
        has_custom_equations = bool(re.search(r"^\s*equations(?:\s*\[[^]]+\])?\s*:", text, re.MULTILINE))
        has_exists_trace = bool(re.search(r"\bexists-trace\b", text))
        has_sources = bool(re.search(r"\[\s*sources(?:\s*,|\s*\])", text))
        sorry_count = len(re.findall(r"\bsorry\b", text))
        has_diff = bool(re.search(r"\b(?:diff|diff_rule|diffLemma|equivLemma|diffEquivLemma)\b", text))

        if len(theories) != 1 or len(re.findall(r"^\s*begin\s*$", text, re.MULTILINE)) != 1 or len(re.findall(r"^\s*end\s*$", text, re.MULTILINE)) != 1:
            findings.append(Finding("error", "THEORY_BOUNDARY", "Expected exactly one theory declaration, begin, and end.", (file_name,)))
        if not rules and not has_process:
            findings.append(Finding("warning", "NO_PROTOCOL_BEHAVIOR", "No rule or SAPIC+ process declaration was found.", (file_name,)))
        if rules and has_process:
            findings.append(Finding("warning", "MIXED_MODELING_STYLES", "Handwritten rules and a SAPIC+ process coexist; review translation interactions.", (file_name,)))
        if not lemmas:
            findings.append(Finding("warning", "NO_LEMMAS", "No lemma declaration was found.", (file_name,)))
        if lemmas and not has_exists_trace:
            findings.append(Finding("warning", "NO_EXECUTABILITY_LEMMA", "No exists-trace lemma was found; all-traces claims may be vacuous.", (file_name,)))
        if has_custom_equations:
            findings.append(Finding("warning", "CUSTOM_EQUATIONS", "Custom equations require external convergence and finite-variant-property evidence.", (file_name,)))
        if sorry_count:
            findings.append(Finding("warning", "UNFINISHED_PROOFS", f"Found {sorry_count} unfinished 'sorry' proof marker(s).", (file_name,)))
        if has_diff:
            findings.append(Finding("info", "EQUIVALENCE_MODE", "Diff/equivalence syntax was found; record the approximation and restriction limits.", (file_name,)))
        if has_sources:
            findings.append(Finding("info", "SOURCES_LEMMA", "A sources lemma was found; prove it against raw sources and inspect refined sources.", (file_name,)))

        file_reports.append(
            {
                "file": file_name,
                "theories": theories,
                "builtins": builtins,
                "rules": rules,
                "has_process": has_process,
                "lemmas": lemmas,
                "restrictions": restrictions,
                "custom_equations": has_custom_equations,
                "exists_trace": has_exists_trace,
                "sources_lemma": has_sources,
                "unfinished_proofs": sorry_count,
                "equivalence_mode": has_diff,
            }
        )

    severity_order = {"error": 0, "warning": 1, "info": 2}
    findings.sort(key=lambda item: (severity_order[item.severity], item.code, item.files))
    summary = {
        "files_scanned": len(file_reports),
        "errors": sum(item.severity == "error" for item in findings),
        "warnings": sum(item.severity == "warning" for item in findings),
        "info": sum(item.severity == "info" for item in findings),
    }
    return {
        "root": str(root),
        "summary": summary,
        "files": file_reports,
        "findings": [asdict(item) for item in findings],
    }


def print_human(report: dict[str, object]) -> None:
    summary = report["summary"]
    assert isinstance(summary, dict)
    print(f"Tamarin model inspection: {report['root']}")
    print(
        f"Scanned {summary['files_scanned']} file(s); "
        f"{summary['errors']} error(s), {summary['warnings']} warning(s), {summary['info']} info notice(s)."
    )
    findings = report["findings"]
    assert isinstance(findings, list)
    if not findings:
        print("No heuristic findings.")
        return
    for finding in findings:
        assert isinstance(finding, dict)
        print(f"{str(finding['severity']).upper()} [{finding['code']}]: {finding['message']}")
        for path in finding.get("files", ()):
            print(f"  - {path}")


def main() -> int:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()
    if not root.exists():
        print(f"error: inspection root does not exist: {root}", file=sys.stderr)
        return 2
    if not root.is_file() and not root.is_dir():
        print(f"error: inspection root is not a regular file or directory: {root}", file=sys.stderr)
        return 2

    files = discover(root)
    if not files:
        print(f"error: no .spthy theories found under: {root}", file=sys.stderr)
        return 2

    report = inspect(root, files)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)

    summary = report["summary"]
    assert isinstance(summary, dict)
    return 1 if args.strict and (summary["errors"] or summary["warnings"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
