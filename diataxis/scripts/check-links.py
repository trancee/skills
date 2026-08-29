#!/usr/bin/env python3
"""Check local links and Markdown heading fragments in documentation files."""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote, urlsplit

INLINE_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
REFERENCE_LINK = re.compile(r"^\s*\[[^\]]+\]:\s*(\S+)", re.MULTILINE)
FENCED_BLOCK = re.compile(r"^\s*(```|~~~).*?^\s*\1\s*$", re.MULTILINE | re.DOTALL)
HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$", re.MULTILINE)
HTML_ID = re.compile(r"\bid=[\"']([^\"']+)[\"']", re.IGNORECASE)
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def markdown_files(paths: list[Path]) -> list[Path]:
    files: set[Path] = set()
    for path in paths:
        if not path.exists():
            raise ValueError(f"path does not exist: {path}")
        if path.is_file():
            if path.suffix.lower() not in {".md", ".mdx"}:
                raise ValueError(f"expected a Markdown file or directory: {path}")
            files.add(path.resolve())
            continue
        files.update(
            candidate.resolve()
            for candidate in path.rglob("*")
            if candidate.is_file() and candidate.suffix.lower() in {".md", ".mdx"}
        )
    return sorted(files)


def visible_text(text: str) -> str:
    return FENCED_BLOCK.sub("", text)


def slugify(heading: str) -> str:
    heading = re.sub(r"<[^>]+>", "", heading)
    heading = re.sub(r"[`*_~]", "", heading)
    heading = heading.strip().lower()
    heading = re.sub(r"[^\w\- ]", "", heading, flags=re.UNICODE)
    return re.sub(r"\s+", "-", heading)


def anchors(text: str) -> set[str]:
    cleaned = visible_text(text)
    result = set(HTML_ID.findall(cleaned))
    occurrences: dict[str, int] = defaultdict(int)
    for match in HEADING.finditer(cleaned):
        base = slugify(match.group(2))
        if not base:
            continue
        count = occurrences[base]
        occurrences[base] += 1
        result.add(base if count == 0 else f"{base}-{count}")
    return result


def link_targets(text: str) -> list[str]:
    cleaned = visible_text(text)
    targets = [match.group(1).strip() for match in INLINE_LINK.finditer(cleaned)]
    targets.extend(match.group(1).strip() for match in REFERENCE_LINK.finditer(cleaned))
    return targets


def normalize_target(raw: str) -> str:
    target = raw
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    if " " in target:
        target = target.split(None, 1)[0]
    return target


def check(files: list[Path]) -> list[str]:
    errors: list[str] = []
    text_cache: dict[Path, str] = {}
    anchor_cache: dict[Path, set[str]] = {}

    for source in files:
        try:
            text = source.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            errors.append(f"{source}: cannot read UTF-8 Markdown: {error}")
            continue
        text_cache[source] = text

        for raw in link_targets(text):
            target = normalize_target(raw)
            if not target:
                continue
            if target.startswith(("/", "//")):
                continue
            if SCHEME.match(target):
                continue

            parsed = urlsplit(target)
            path_text = unquote(parsed.path)
            fragment = unquote(parsed.fragment)
            destination = source if not path_text else (source.parent / path_text).resolve()

            if path_text and not destination.exists():
                errors.append(f"{source}: missing local target {raw!r} -> {destination}")
                continue
            if destination.is_dir():
                if not fragment:
                    continue
                index = next(
                    (candidate for name in ("README.md", "index.md", "_index.md") if (candidate := destination / name).exists()),
                    None,
                )
                if index is None:
                    errors.append(f"{source}: directory link {raw!r} has no Markdown index")
                    continue
                destination = index
            if fragment and destination.suffix.lower() in {".md", ".mdx"}:
                if destination not in anchor_cache:
                    try:
                        destination_text = text_cache.get(destination) or destination.read_text(encoding="utf-8")
                    except (OSError, UnicodeError) as error:
                        errors.append(f"{source}: cannot inspect fragment target {destination}: {error}")
                        continue
                    anchor_cache[destination] = anchors(destination_text)
                if fragment not in anchor_cache[destination]:
                    errors.append(f"{source}: missing fragment #{fragment} in {destination}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check local Markdown links and local heading fragments; external URLs are skipped."
    )
    parser.add_argument("paths", nargs="+", type=Path, help="Markdown files or directories")
    args = parser.parse_args()

    try:
        files = markdown_files(args.paths)
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    errors = check(files)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"FAIL: {len(errors)} local link error(s) in {len(files)} Markdown file(s)", file=sys.stderr)
        return 1

    print(f"PASS: checked local links in {len(files)} Markdown file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
