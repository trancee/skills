#!/usr/bin/env python3
"""Run structural assertions and fresh OMP headless replays for a hardened skill."""

from __future__ import annotations

import argparse
import json
import re
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


def load_spec(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict) or value.get("version") != 1:
        raise ValueError("regression spec must be a version 1 JSON object")
    if not isinstance(value.get("skill"), str) or not value["skill"]:
        raise ValueError("regression spec requires a nonblank skill name")
    for key in ("structural", "replays"):
        if key in value and not isinstance(value[key], list):
            raise ValueError(f"{key} must be an array")
    return value


def recursive_dicts(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from recursive_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from recursive_dicts(child)


def content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    chunks: list[str] = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str):
            chunks.append(block["text"])
    return "\n".join(chunks)


def parse_event_stream(stdout: str) -> list[Any]:
    events: list[Any] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def skill_was_read(events: list[Any], skill: str) -> bool:
    expected = f"skill://{skill}"
    for event in events:
        for item in recursive_dicts(event):
            name = item.get("name") or item.get("toolName")
            arguments = item.get("arguments") or item.get("args")
            if name == "read" and isinstance(arguments, dict):
                path = arguments.get("path")
                if isinstance(path, str) and (path == expected or path.startswith(expected + "/")):
                    return True
    return False


def assistant_text(events: list[Any]) -> str:
    candidates: list[str] = []
    for event in events:
        for item in recursive_dicts(event):
            if item.get("role") != "assistant":
                continue
            text = content_text(item.get("content"))
            if text:
                candidates.append(text)
    return candidates[-1] if candidates else ""


def check_text(expect: dict[str, Any], text: str) -> list[str]:
    failures: list[str] = []
    for needle in expect.get("contains", []):
        if needle not in text:
            failures.append(f"missing expected text: {needle!r}")
    for needle in expect.get("notContains", []):
        if needle in text:
            failures.append(f"found forbidden text: {needle!r}")
    for pattern in expect.get("regex", []):
        if not re.search(pattern, text, re.MULTILINE):
            failures.append(f"regex did not match: {pattern!r}")
    for pattern in expect.get("notRegex", []):
        if re.search(pattern, text, re.MULTILINE):
            failures.append(f"forbidden regex matched: {pattern!r}")
    return failures


def run_structural(root: Path, checks: list[Any]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for index, check in enumerate(checks, 1):
        if not isinstance(check, dict):
            results.append({"name": f"structural-{index}", "ok": False, "failures": ["check is not an object"]})
            continue
        name = str(check.get("name") or f"structural-{index}")
        relative = check.get("path")
        failures: list[str] = []
        if not isinstance(relative, str) or not relative:
            failures.append("path is required")
            text = ""
        else:
            path = root / relative
            try:
                text = path.read_text(encoding="utf-8")
            except OSError as error:
                failures.append(f"cannot read {relative}: {error}")
                text = ""
        if text:
            failures.extend(check_text(check, text))
            for rule in check.get("maxOccurrences", []):
                if not isinstance(rule, dict) or not isinstance(rule.get("text"), str) or not isinstance(rule.get("max"), int):
                    failures.append("maxOccurrences entries require text and integer max")
                    continue
                actual = text.count(rule["text"])
                if actual > rule["max"]:
                    failures.append(f"{rule['text']!r} occurs {actual} times; maximum is {rule['max']}")
        results.append({"name": name, "ok": not failures, "failures": failures})
    return results


def run_replay(
    omp: str,
    model: str | None,
    skill: str,
    replay: dict[str, Any],
    root: Path,
    timeout: int,
) -> dict[str, Any]:
    name = str(replay.get("name") or "unnamed replay")
    prompt = replay.get("prompt")
    if not isinstance(prompt, str) or not prompt:
        return {"name": name, "ok": False, "failures": ["prompt is required"]}
    expectation = replay.get("expect", {})
    if not isinstance(expectation, dict):
        return {"name": name, "ok": False, "failures": ["expect must be an object"]}

    command = [
        omp,
        "-p",
        "--mode",
        "json",
        "--no-session",
        "--no-title",
        "--skills",
        skill,
        "--append-system-prompt",
        f"For this regression replay, first read skill://{skill} and follow it. Do not modify files.",
    ]
    if model:
        command.extend(["--model", model])
    command.append(prompt)
    try:
        process = subprocess.run(
            command,
            cwd=root,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"name": name, "ok": False, "failures": [f"replay could not complete: {error}"], "command": command}

    events = parse_event_stream(process.stdout)
    text = assistant_text(events)
    failures: list[str] = []
    expected_exit = expectation.get("exitCode", 0)
    if process.returncode != expected_exit:
        failures.append(f"exit code {process.returncode}; expected {expected_exit}")
    if not events:
        failures.append("stdout did not contain an OMP JSON event stream")
    if replay.get("requireSkillRead", True) and not skill_was_read(events, skill):
        failures.append(f"no read tool call for skill://{skill} was observed")
    if not text:
        failures.append("no final assistant text was found in the event stream")
    else:
        failures.extend(check_text(expectation, text))
    return {
        "name": name,
        "ok": not failures,
        "failures": failures,
        "exitCode": process.returncode,
        "assistantText": text,
        "stderr": process.stderr[-1000:],
        "command": command,
    }


def write_private(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(descriptor, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(content)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run OMP skill hardening regression checks.")
    parser.add_argument("spec", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--omp", default="omp", help="OMP executable path")
    parser.add_argument("--model")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--skip-replay", action="store_true")
    parser.add_argument("--replay", action="append", help="run only replays whose names contain this text")
    parser.add_argument("--json-report", type=Path)
    args = parser.parse_args()

    if args.timeout < 1:
        parser.error("--timeout must be positive")
    try:
        spec = load_spec(args.spec)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    root = args.root.resolve()
    results = run_structural(root, spec.get("structural", []))
    if not args.skip_replay:
        selected = [replay for replay in spec.get("replays", []) if isinstance(replay, dict)]
        if args.replay:
            filters = [value.casefold() for value in args.replay]
            selected = [
                replay
                for replay in selected
                if any(value in str(replay.get("name", "")).casefold() for value in filters)
            ]
        results.extend(
            run_replay(args.omp, args.model, spec["skill"], replay, root, args.timeout)
            for replay in selected
        )

    for result in results:
        marker = "PASS" if result["ok"] else "FAIL"
        print(f"{marker}: {result['name']}")
        for failure in result.get("failures", []):
            print(f"  - {failure}")
    report = {"version": 1, "skill": spec["skill"], "ok": all(result["ok"] for result in results), "results": results}
    if args.json_report:
        write_private(args.json_report, json.dumps(report, indent=2) + "\n")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
