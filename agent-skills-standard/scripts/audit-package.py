#!/usr/bin/env python3
"""Audit an existing Agent Skills package against shared format rules."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

try:
    import yaml
except ImportError:
    yaml = None

NAME_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
SHARED_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}


def issue(code: str, path: Path, message: str) -> dict[str, str]:
    return {"code": code, "path": path.as_posix(), "message": message}


def within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def frontmatter(text: str, skill_file: Path) -> tuple[dict[str, Any] | None, str, list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        errors.append(issue("frontmatter-opening", skill_file, "SKILL.md must start with an exact '---' line."))
        return None, "", errors
    try:
        end = lines.index("---", 1)
    except ValueError:
        errors.append(issue("frontmatter-closing", skill_file, "SKILL.md is missing the closing '---' frontmatter line."))
        return None, "", errors
    source = "\n".join(lines[1:end])
    try:
        parsed = yaml.safe_load(source) if yaml is not None else None
    except yaml.YAMLError as error:
        errors.append(issue("yaml", skill_file, f"YAML frontmatter cannot be parsed: {error}"))
        return None, "", errors
    if not isinstance(parsed, dict):
        errors.append(issue("frontmatter-type", skill_file, "YAML frontmatter must be a mapping."))
        return None, "", errors
    return parsed, "\n".join(lines[end + 1 :]).strip(), errors


def validate_frontmatter(
    data: dict[str, Any], package: Path, skill_file: Path
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    name = data.get("name")
    if not isinstance(name, str) or not name:
        errors.append(issue("name-required", skill_file, "Frontmatter field 'name' must be a non-empty string."))
    else:
        if len(name) > 64 or NAME_RE.fullmatch(name) is None:
            errors.append(
                issue(
                    "name-format",
                    skill_file,
                    "Field 'name' must contain 1 to 64 lowercase letters, digits, or single hyphens without leading or trailing hyphens.",
                )
            )
        if name != package.name:
            errors.append(
                issue(
                    "name-directory",
                    skill_file,
                    f"Field 'name' is {name!r}, but the package directory is {package.name!r}.",
                )
            )

    description = data.get("description")
    if not isinstance(description, str) or not description:
        errors.append(issue("description-required", skill_file, "Frontmatter field 'description' must be a non-empty string."))
    elif len(description) > 1024:
        errors.append(
            issue(
                "description-length",
                skill_file,
                f"Field 'description' has {len(description)} characters; the maximum is 1024.",
            )
        )

    compatibility = data.get("compatibility")
    if compatibility is not None:
        if not isinstance(compatibility, str) or not compatibility:
            errors.append(issue("compatibility-type", skill_file, "Field 'compatibility' must be a non-empty string when present."))
        elif len(compatibility) > 500:
            errors.append(
                issue(
                    "compatibility-length",
                    skill_file,
                    f"Field 'compatibility' has {len(compatibility)} characters; the maximum is 500.",
                )
            )

    for field in ("license", "allowed-tools"):
        value = data.get(field)
        if value is not None and (not isinstance(value, str) or not value):
            errors.append(issue(f"{field}-type", skill_file, f"Field {field!r} must be a non-empty string when present."))

    metadata = data.get("metadata")
    if metadata is not None:
        if not isinstance(metadata, dict):
            errors.append(issue("metadata-type", skill_file, "Field 'metadata' must be a mapping from strings to strings."))
        else:
            for key, value in metadata.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    errors.append(
                        issue(
                            "metadata-value",
                            skill_file,
                            f"Metadata entry {key!r} must use a string key and string value.",
                        )
                    )

    for field in sorted(set(data) - SHARED_FIELDS):
        warnings.append(
            issue(
                "extension-field",
                skill_file,
                f"Top-level field {field!r} is a client extension, not a field defined by the shared specification.",
            )
        )
    return errors, warnings


def validate_links(package: Path) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    root = package.resolve()
    for markdown in sorted(package.rglob("*.md")):
        try:
            text = markdown.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            errors.append(issue("markdown-read", markdown, f"Markdown file cannot be read as UTF-8: {error}"))
            continue
        for raw_target in LINK_RE.findall(text):
            target = raw_target.strip()
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            path_text = unquote(parsed.path)
            destination = (markdown.parent / path_text).resolve()
            if not within(destination, root):
                errors.append(issue("link-escape", markdown, f"Local link {target!r} resolves outside the package."))
            elif not destination.exists():
                errors.append(issue("link-missing", markdown, f"Local link {target!r} does not exist."))
    return errors


def validate_symlinks(package: Path) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    root = package.resolve()
    for path in sorted(package.rglob("*")):
        if path.is_symlink() and not within(path.resolve(), root):
            errors.append(issue("symlink-escape", path, f"Symlink resolves outside the package: {path.resolve()}"))
    return errors


def audit(package: Path, max_lines: int) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    skill_file = package / "SKILL.md"
    if not skill_file.is_file():
        errors.append(issue("skill-file", skill_file, "Package must contain a file named exactly SKILL.md."))
        return {"schemaVersion": 1, "package": str(package), "valid": False, "errors": errors, "warnings": warnings}

    try:
        text = skill_file.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        errors.append(issue("skill-read", skill_file, f"SKILL.md cannot be read as UTF-8: {error}"))
        return {"schemaVersion": 1, "package": str(package), "valid": False, "errors": errors, "warnings": warnings}

    data, body, parse_errors = frontmatter(text, skill_file)
    errors.extend(parse_errors)
    if data is not None:
        field_errors, field_warnings = validate_frontmatter(data, package, skill_file)
        errors.extend(field_errors)
        warnings.extend(field_warnings)
    if data is not None and not body:
        warnings.append(issue("body-empty", skill_file, "SKILL.md has no Markdown instructions after frontmatter."))
    line_count = len(text.splitlines())
    if line_count > max_lines:
        warnings.append(
            issue(
                "body-lines",
                skill_file,
                f"SKILL.md has {line_count} lines; the progressive-disclosure recommendation is at most {max_lines}.",
            )
        )

    errors.extend(validate_links(package))
    errors.extend(validate_symlinks(package))
    return {
        "schemaVersion": 1,
        "package": str(package),
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
    }


def print_human(report: dict[str, Any]) -> None:
    for item in report["errors"]:
        print(f"ERROR [{item['code']}] {item['path']}: {item['message']}", file=sys.stderr)
    for item in report["warnings"]:
        print(f"WARNING [{item['code']}] {item['path']}: {item['message']}", file=sys.stderr)
    if report["valid"]:
        print(f"PASS: {report['package']} satisfies the checked Agent Skills package rules")
    else:
        print(f"FAIL: {report['package']} has {len(report['errors'])} error(s)", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit an existing Agent Skills package against shared format rules.")
    parser.add_argument("package", type=Path, help="skill package directory containing SKILL.md")
    parser.add_argument("--json", action="store_true", help="write a structured audit report")
    parser.add_argument("--strict", action="store_true", help="return failure when warnings are present")
    parser.add_argument("--max-lines", type=int, default=500, help="recommended SKILL.md line limit; default: 500")
    args = parser.parse_args()

    if yaml is None:
        print("ERROR: PyYAML is required. Install it in a disposable environment or run skills-ref validate instead.", file=sys.stderr)
        return 2
    if args.max_lines < 1:
        parser.error("--max-lines must be positive")
    package = args.package.expanduser().resolve()
    if not package.is_dir():
        print(f"ERROR: package is not a directory: {package}", file=sys.stderr)
        return 2

    report = audit(package, args.max_lines)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_human(report)
    if not report["valid"] or (args.strict and report["warnings"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
