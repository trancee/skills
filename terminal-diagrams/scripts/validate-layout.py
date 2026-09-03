#!/usr/bin/env python3
"""Validate visible-cell widths, ANSI policy, and rectangular terminal-diagram components."""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ESC = "\x1b"
RESET = "\x1b[0m"
REGIONAL_START = 0x1F1E6
REGIONAL_END = 0x1F1FF
EMOJI_MODIFIER_START = 0x1F3FB
EMOJI_MODIFIER_END = 0x1F3FF
VARIATION_RANGES = ((0xFE00, 0xFE0F), (0xE0100, 0xE01EF))
BOX_PAIRS = (("┌", "┐"), ("└", "┘"), ("╔", "╗"), ("╚", "╝"))


@dataclass(frozen=True)
class Issue:
    level: str
    message: str
    line: int | None = None

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"level": self.level, "message": self.message}
        if self.line is not None:
            result["line"] = self.line
        return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="UTF-8 unfenced diagram file, or - for stdin")
    parser.add_argument("--target", choices=("markdown_code_block", "ansi_terminal"), required=True)
    parser.add_argument("--canvas-width", type=int, help="maximum visible columns")
    parser.add_argument("--ambiguous-width", type=int, choices=(1, 2), default=1)
    parser.add_argument("--component", action="append", default=[], metavar="START:END", help="inclusive 1-based rectangular row range; repeatable")
    parser.add_argument("--equal-width", action="store_true", help="require every diagram row to have the same visible width")
    parser.add_argument("--json", action="store_true", help="emit structured JSON")
    return parser.parse_args()


def parse_component(value: str) -> tuple[int, int]:
    try:
        left, right = value.split(":", 1)
        start, end = int(left), int(right)
    except (ValueError, TypeError) as error:
        raise ValueError(f"invalid component {value!r}; expected START:END") from error
    if start < 1 or end < start:
        raise ValueError(f"invalid component {value!r}; require 1 <= START <= END")
    return start, end


def read_text(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    try:
        return Path(path).read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"diagram is not valid UTF-8: {error}") from error
    except OSError as error:
        raise ValueError(f"cannot read diagram {path!r}: {error}") from error


def strip_sgr(line: str, line_number: int) -> tuple[str, bool, list[Issue]]:
    output: list[str] = []
    issues: list[Issue] = []
    sequences: list[str] = []
    index = 0
    while index < len(line):
        char = line[index]
        if char != ESC:
            output.append(char)
            index += 1
            continue
        if index + 1 >= len(line):
            issues.append(Issue("error", "unterminated ESC byte", line_number))
            break
        if line[index + 1] != "[":
            issues.append(Issue("error", "only ANSI CSI SGR color/style sequences are allowed", line_number))
            index += 2
            continue
        end = index + 2
        while end < len(line) and not ("@" <= line[end] <= "~"):
            end += 1
        if end >= len(line):
            issues.append(Issue("error", "unterminated ANSI CSI sequence", line_number))
            break
        sequence = line[index : end + 1]
        final = line[end]
        if final != "m":
            issues.append(Issue("error", f"non-SGR ANSI CSI sequence is not allowed: {sequence!r}", line_number))
        else:
            params = line[index + 2 : end]
            if params and any(part and not part.isdigit() for part in params.split(";")):
                issues.append(Issue("error", f"unsupported SGR parameter sequence: {sequence!r}", line_number))
            sequences.append(sequence)
        index = end + 1
    if sequences and sequences[-1] != RESET:
        issues.append(Issue("error", "ANSI-styled row must end its styling with ESC[0m", line_number))
    return "".join(output), bool(sequences), issues


def in_ranges(value: int, ranges: tuple[tuple[int, int], ...]) -> bool:
    return any(start <= value <= end for start, end in ranges)


def visible_cells(text: str, line_number: int, ambiguous_width: int) -> tuple[int, list[Issue]]:
    width = 0
    issues: list[Issue] = []
    has_base = False
    regional_count = 0
    for char in text:
        code = ord(char)
        category = unicodedata.category(char)
        if char == "\t":
            issues.append(Issue("error", "tab width is renderer-dependent; replace tabs with spaces", line_number))
            continue
        if code == 0x200D:
            issues.append(Issue("error", "ZWJ grapheme sequence has terminal-dependent width", line_number))
            continue
        if in_ranges(code, VARIATION_RANGES):
            issues.append(Issue("error", "variation-selector presentation has terminal-dependent width", line_number))
            continue
        if REGIONAL_START <= code <= REGIONAL_END:
            regional_count += 1
            issues.append(Issue("error", "regional-indicator flag sequence has terminal-dependent width", line_number))
            continue
        if EMOJI_MODIFIER_START <= code <= EMOJI_MODIFIER_END or code == 0x20E3:
            issues.append(Issue("error", "emoji modifier/keycap sequence has terminal-dependent width", line_number))
            continue
        if category == "Co":
            issues.append(Issue("error", "private-use character has no portable terminal width", line_number))
            continue
        if category == "Cs":
            issues.append(Issue("error", "surrogate code point is invalid Unicode text", line_number))
            continue
        if unicodedata.combining(char) or category in {"Mn", "Me"}:
            if not has_base:
                issues.append(Issue("error", "combining mark has no preceding base character", line_number))
            continue
        if category.startswith("C"):
            issues.append(Issue("error", f"control/format character U+{code:04X} is not allowed", line_number))
            continue
        has_base = True
        east_asian = unicodedata.east_asian_width(char)
        if east_asian in {"W", "F"}:
            width += 2
        elif east_asian == "A":
            width += ambiguous_width
        else:
            width += 1
    if regional_count:
        # Count is retained only to avoid silently treating these code points as zero-width.
        width += regional_count * 2
    return width, issues


def validate_box_pairs(plain: str, line_number: int) -> list[Issue]:
    issues: list[Issue] = []
    for left, right in BOX_PAIRS:
        if plain.count(left) != plain.count(right):
            issues.append(Issue("error", f"unpaired box corners {left}{right}", line_number))
    single = any(char in plain for char in "┌┐└┘─│┬┴├┤┼")
    double = any(char in plain for char in "╔╗╚╝═║╦╩╠╣╬")
    if single and double and any(char in plain for char in "┌┐└┘╔╗╚╝"):
        issues.append(Issue("warning", "single and double border families share a boundary row; verify the mixed junction is intentional", line_number))
    return issues


def validate(text: str, args: argparse.Namespace, components: list[tuple[int, int]]) -> dict[str, Any]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    issues: list[Issue] = []
    widths: list[int] = []
    has_ansi = False
    if not lines:
        issues.append(Issue("error", "diagram is empty"))
    for number, line in enumerate(lines, 1):
        plain, line_has_ansi, ansi_issues = strip_sgr(line, number)
        has_ansi = has_ansi or line_has_ansi or ESC in line
        issues.extend(ansi_issues)
        if args.target == "markdown_code_block" and ESC in line:
            issues.append(Issue("error", "raw ANSI escape sequence is forbidden for Markdown output", number))
        width, width_issues = visible_cells(plain, number, args.ambiguous_width)
        widths.append(width)
        issues.extend(width_issues)
        issues.extend(validate_box_pairs(plain, number))
        if args.canvas_width is not None and width > args.canvas_width:
            issues.append(Issue("error", f"visible width {width} exceeds canvas width {args.canvas_width}", number))
        if plain.lstrip().startswith(("```", "~~~")):
            issues.append(Issue("warning", "validator expects unfenced diagram input; component line numbers include this fence", number))
    component_results: list[dict[str, Any]] = []
    for start, end in components:
        if end > len(lines):
            issues.append(Issue("error", f"component {start}:{end} exceeds diagram line count {len(lines)}"))
            component_results.append({"range": f"{start}:{end}", "valid": False, "widths": []})
            continue
        selected = widths[start - 1 : end]
        valid = len(set(selected)) <= 1
        component_results.append({"range": f"{start}:{end}", "valid": valid, "widths": selected})
        if not valid:
            issues.append(Issue("error", f"component {start}:{end} rows have unequal visible widths: {selected}"))
    if args.equal_width and widths and len(set(widths)) > 1:
        issues.append(Issue("error", f"diagram rows have unequal visible widths: {widths}"))
    errors = [issue for issue in issues if issue.level == "error"]
    warnings = [issue for issue in issues if issue.level == "warning"]
    return {
        "valid": not errors,
        "target": args.target,
        "ambiguous_width": args.ambiguous_width,
        "canvas_width": args.canvas_width,
        "line_count": len(lines),
        "line_widths": [{"line": index, "visible_width": width} for index, width in enumerate(widths, 1)],
        "components": component_results,
        "has_ansi": has_ansi,
        "errors": [issue.as_dict() for issue in errors],
        "warnings": [issue.as_dict() for issue in warnings],
    }


def print_human(report: dict[str, Any]) -> None:
    status = "VALID" if report["valid"] else "INVALID"
    print(f"{status}: {report['line_count']} rows; target={report['target']}; ambiguous_width={report['ambiguous_width']}")
    print("Widths: " + ", ".join(f"{item['line']}={item['visible_width']}" for item in report["line_widths"]))
    for issue in report["errors"] + report["warnings"]:
        location = f"line {issue['line']}: " if "line" in issue else ""
        print(f"{issue['level'].upper()}: {location}{issue['message']}")


def main() -> int:
    args = parse_args()
    if args.canvas_width is not None and args.canvas_width <= 0:
        print("error: --canvas-width must be greater than zero", file=sys.stderr)
        return 2
    try:
        components = [parse_component(value) for value in args.component]
        text = read_text(args.path)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    report = validate(text, args, components)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print_human(report)
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
