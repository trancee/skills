#!/usr/bin/env python3
"""Mine recurring friction signals from persisted OMP session JSONL files."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

DEFAULT_SESSIONS = Path.home() / ".omp" / "agent" / "sessions"

FRUSTRATION_PATTERNS = (
    r"\bthat'?s (?:wrong|not (?:right|what|it))\b",
    r"\bnot what i (?:asked|wanted|said)\b",
    r"\bundo (?:that|this)\b",
    r"\bstill (?:broken|failing|wrong|not working)\b",
    r"\byou (?:didn'?t|keep|always|never|still)\b",
    r"\bwhy did you\b",
    r"\bi (?:already )?(?:said|told you|asked)\b",
    r"\bdon'?t (?:do|keep|change|touch)\b",
    r"\bquit (?:doing|trying)\b",
    r"\bthis is (?:wrong|broken)\b",
    r"\bendless loop\b",
    r"\bgaslight",
)
FRUSTRATION_RE = re.compile("|".join(FRUSTRATION_PATTERNS), re.IGNORECASE)
REVERSAL_RE = re.compile(
    r"\bthat'?s not the plan\b|\bdon'?t (?:do|build|implement) (?:that|this)\b|"
    r"\bnot what (?:we|i) (?:planned|agreed)\b|\bscrap (?:that|the plan)\b|"
    r"\b(?:go back|start over)\b|\bnot (?:like )?that\b",
    re.IGNORECASE,
)
DONE_RE = re.compile(
    r"\b(?:all set|done|fixed|works now|resolved|complete|completed|implemented)\b",
    re.IGNORECASE,
)
VERIFY_RE = re.compile(
    r"\b(?:test|pytest|cargo test|go test|npm test|pnpm test|bun test|build|lint|"
    r"typecheck|check|verify|smoke|compile|diagnostic)\b",
    re.IGNORECASE,
)
BLOCK_RE = re.compile(r"\b(?:blocked|denied|approval rejected|prevented continuation|hook)\b", re.IGNORECASE)
AUTO_TEXT_RE = re.compile(
    r"^\s*(?:<system-reminder|<system-notice|\[IMPORTANT: User invoked|"
    r"\[Request interrupted|This session is being continued|<task-notification)",
    re.IGNORECASE,
)
SKILL_NAME_RE = re.compile(r'User invoked the "([^"]+)" skill')
SKILL_DIR_RE = re.compile(r"\[Skill directory:\s*([^\]\n]+)\]")
SKILL_URL_RE = re.compile(r"^skill://([^/:]+)")
EDIT_PATH_RE = re.compile(r"^\[([^\]#]+)(?:#[0-9A-Fa-f]+)?\]", re.MULTILINE)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
SECRET_RES = (
    re.compile(r"\b(?:sk|pk|ghp|github_pat)_[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"),
    re.compile(r"(?i)\b(?:api[_-]?key|token|password|secret)\s*[:=]\s*\S+"),
)



def flatten_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    chunks: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text" and isinstance(block.get("text"), str):
            chunks.append(block["text"])
    return "\n".join(chunks)


def redact(text: str, limit: int = 280) -> str:
    text = EMAIL_RE.sub("<REDACTED_EMAIL>", text)
    text = re.sub(r"/home/[^/\s]+", "~", text)
    for pattern in SECRET_RES:
        text = pattern.sub("<REDACTED_SECRET>", text)
    return " ".join(text.split())[:limit]


def caps_ratio(text: str) -> float:
    letters = [char for char in text if char.isalpha()]
    if len(letters) < 8:
        return 0.0
    return sum(char.isupper() for char in letters) / len(letters)


def human_text(record: dict[str, Any]) -> str | None:
    if record.get("type") != "message":
        return None
    message = record.get("message")
    if not isinstance(message, dict) or message.get("role") != "user":
        return None
    if message.get("attribution") not in (None, "user"):
        return None
    text = flatten_text(message.get("content")).strip()
    if not text or AUTO_TEXT_RE.match(text):
        return None
    return text


def tool_calls(message: dict[str, Any]) -> Iterable[tuple[str | None, str, dict[str, Any]]]:
    content = message.get("content")
    if not isinstance(content, list):
        return
    for block in content:
        if not isinstance(block, dict) or block.get("type") != "toolCall":
            continue
        name = block.get("name")
        arguments = block.get("arguments")
        if isinstance(name, str):
            identifier = block.get("id") if isinstance(block.get("id"), str) else None
            yield identifier, name, arguments if isinstance(arguments, dict) else {}


def edit_paths(name: str, arguments: dict[str, Any]) -> list[str]:
    if name == "write" and isinstance(arguments.get("path"), str):
        path = arguments["path"]
        return [] if path.startswith("xd://") else [path]
    if name == "edit" and isinstance(arguments.get("input"), str):
        return EDIT_PATH_RE.findall(arguments["input"])
    return []


def is_verification_call(name: str, arguments: dict[str, Any]) -> bool:
    if name == "bash":
        return bool(VERIFY_RE.search(str(arguments.get("command", ""))))
    if name == "eval":
        return bool(VERIFY_RE.search(f"{arguments.get('title', '')} {arguments.get('code', '')}"))
    if name != "write" or not isinstance(arguments.get("path"), str):
        return False
    device = arguments["path"]
    try:
        payload = json.loads(str(arguments.get("content", "{}")))
    except json.JSONDecodeError:
        return False
    if device == "xd://browser":
        return payload.get("action") == "run"
    if device == "xd://debug":
        return payload.get("action") in {"launch", "continue", "evaluate", "stack_trace"}
    if device == "xd://lsp":
        return payload.get("action") == "diagnostics"
    return False


def read_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                value["_line"] = line_number
                records.append(value)
    return records

def active_branch(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep the ancestry of the latest persisted conversation node."""
    nodes = {
        record["id"]: record
        for record in records
        if isinstance(record.get("id"), str) and "parentId" in record
    }
    leaf = next(
        (
            record
            for record in reversed(records)
            if isinstance(record.get("id"), str) and "parentId" in record
        ),
        None,
    )
    if leaf is None:
        return records
    ancestry: set[str] = set()
    current: dict[str, Any] | None = leaf
    while current is not None:
        identifier = current.get("id")
        if not isinstance(identifier, str) or identifier in ancestry:
            break
        ancestry.add(identifier)
        parent = current.get("parentId")
        current = nodes.get(parent) if isinstance(parent, str) else None
    return [
        record
        for record in records
        if record.get("type") in {"title", "session"} or record.get("id") in ancestry
    ]


def analyze_session(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    records = read_records(path)
    records = active_branch(records)
    header = next((record for record in records if record.get("type") == "session"), None)
    if header is None:
        raise ValueError("missing session header")

    session_id = str(header.get("id", path.stem))
    project = str(header.get("cwd", ""))
    events: list[dict[str, Any]] = []
    active_skills: list[str] = []
    skill_paths: dict[str, str] = {}
    edit_counts: Counter[str] = Counter()
    error_streak = 0
    error_tool: str | None = None
    verified_since_user = False
    current_mode = "none"
    plan_exit_turn: int | None = None
    human_turn = 0
    tool_by_id: dict[str, str] = {}

    def activate_skill(name: str) -> None:
        if name in active_skills:
            active_skills.remove(name)
        active_skills.append(name)


    def emit(signature: str, record: dict[str, Any], snippet: str, **extra: Any) -> None:
        target = f"skill:{active_skills[-1]}" if active_skills else "base:AGENTS.md"
        event = {
            "session": session_id,
            "sessionFile": str(path),
            "project": project,
            "signature": signature,
            "timestamp": str(record.get("timestamp", "")),
            "line": record.get("_line"),
            "target": target,
            "targetPath": skill_paths.get(active_skills[-1]) if active_skills else None,
            "activeSkills": list(active_skills),
            "snippet": redact(snippet),
        }
        event.update(extra)
        events.append(event)

    for record in records:
        record_type = record.get("type")

        if record_type == "reset_boundary":
            active_skills.clear()
            edit_counts.clear()
            error_streak = 0
            error_tool = None
            tool_by_id.clear()
            verified_since_user = False
            current_mode = "none"
            plan_exit_turn = None
            continue

        if record_type == "mode_change":
            new_mode = str(record.get("mode", "none"))
            if current_mode == "plan" and new_mode != "plan":
                plan_exit_turn = human_turn
            current_mode = new_mode
            continue

        if record_type == "custom_message" and record.get("customType") == "skill-prompt":
            content = flatten_text(record.get("content")) if not isinstance(record.get("content"), str) else record["content"]
            match = SKILL_NAME_RE.search(content)
            if match:
                name = match.group(1)
                activate_skill(name)
                directory = SKILL_DIR_RE.search(content)
                if directory:
                    skill_paths[name] = str(Path(directory.group(1).strip()) / "SKILL.md")
            continue

        text = human_text(record)
        if text is not None:
            human_turn += 1
            ratio = caps_ratio(text)
            if plan_exit_turn is not None and human_turn - plan_exit_turn <= 2 and REVERSAL_RE.search(text):
                emit("plan_reversal", record, text, capsRatio=round(ratio, 2))
                plan_exit_turn = None
            elif FRUSTRATION_RE.search(text) or ratio > 0.6:
                emit("user_frustration", record, text, capsRatio=round(ratio, 2))
            verified_since_user = False
            continue

        if record_type != "message":
            continue
        message = record.get("message")
        if not isinstance(message, dict):
            continue
        role = message.get("role")

        if role == "assistant":
            if message.get("stopReason") == "aborted":
                emit("user_interrupt", record, "assistant turn aborted")
            for tool_id, name, arguments in tool_calls(message):
                if tool_id is not None:
                    tool_by_id[tool_id] = name
                if name == "read" and isinstance(arguments.get("path"), str):
                    match = SKILL_URL_RE.match(arguments["path"])
                    if match:
                        activate_skill(match.group(1))
                for edited_path in edit_paths(name, arguments):
                    edit_counts[edited_path] += 1
                    if edit_counts[edited_path] in {3, 5, 8}:
                        emit(
                            "repeated_edit",
                            record,
                            f"{edited_path} edited {edit_counts[edited_path]} times in one session",
                            filePath=edited_path,
                            editCount=edit_counts[edited_path],
                        )
                if is_verification_call(name, arguments):
                    verified_since_user = True
            assistant_text = flatten_text(message.get("content"))
            if assistant_text and DONE_RE.search(assistant_text) and not verified_since_user:
                emit("claimed_done_no_verify", record, assistant_text)
            continue

        if role == "toolResult":
            is_error = message.get("isError") is True
            result_text = flatten_text(message.get("content"))
            tool_name = str(message.get("toolName") or tool_by_id.get(str(message.get("toolCallId")), "tool"))
            if is_error:
                if tool_name == error_tool:
                    error_streak += 1
                else:
                    error_tool = tool_name
                    error_streak = 1
                if error_streak in {3, 5, 8}:
                    emit(
                        "repeated_tool_error",
                        record,
                        result_text,
                        toolName=tool_name,
                        errorStreak=error_streak,
                    )
                if BLOCK_RE.search(result_text):
                    emit("hook_block", record, result_text, toolName=tool_name)
            else:
                error_streak = 0
                error_tool = None

    return header, events


def session_age_days(path: Path) -> float:
    return (time.time() - path.stat().st_mtime) / 86400.0


def discover_sessions(root: Path) -> list[Path]:
    if not root.is_dir():
        raise ValueError(f"sessions directory does not exist: {root}")
    return sorted(path for path in root.glob("*/*.jsonl") if path.is_file())


def collect(
    paths: Iterable[Path],
    days: int,
    project_filter: str | None,
) -> tuple[list[dict[str, Any]], int, int]:
    events: list[dict[str, Any]] = []
    scanned = 0
    skipped = 0
    for path in paths:
        if days and session_age_days(path) > days:
            continue
        try:
            header, session_events = analyze_session(path)
        except (OSError, ValueError) as error:
            print(f"WARN: skipped {path}: {error}", file=sys.stderr)
            skipped += 1
            continue
        cwd = str(header.get("cwd", ""))
        if project_filter and project_filter.casefold() not in f"{path} {cwd}".casefold():
            continue
        scanned += 1
        events.extend(session_events)
    return events, scanned, skipped


def write_private_json(path: Path, events: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(descriptor, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(events, handle, indent=2)
        handle.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Mine redacted friction signals from OMP v3 session JSONL files."
    )
    parser.add_argument("--sessions-dir", type=Path, default=DEFAULT_SESSIONS)
    parser.add_argument("--session", type=Path, help="analyze one session JSONL file")
    parser.add_argument("--days", type=int, default=30, help="mtime window; 0 scans all")
    parser.add_argument("--project", help="substring filter for session path or recorded cwd")
    parser.add_argument("--min-cluster", type=int, default=3)
    parser.add_argument("--json", type=Path, help="write redacted event records with mode 0600")
    args = parser.parse_args()

    if args.days < 0 or args.min_cluster < 1:
        parser.error("--days must be nonnegative and --min-cluster must be positive")
    try:
        paths = [args.session] if args.session else discover_sessions(args.sessions_dir.expanduser())
        if args.session and not args.session.is_file():
            raise ValueError(f"session file does not exist: {args.session}")
        events, scanned, skipped = collect(paths, args.days, args.project)
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    by_signature: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_target: Counter[tuple[str, str]] = Counter()
    for event in events:
        by_signature[event["signature"]].append(event)
        by_target[(event["signature"], event["target"])] += 1

    print(f"OMP friction scan: scanned={scanned} skipped={skipped} events={len(events)} window={args.days or 'all'}d")
    print("Signature clusters:")
    shown = False
    for signature, cluster in sorted(by_signature.items(), key=lambda item: (-len(item[1]), item[0])):
        sessions = {event["session"] for event in cluster}
        if len(cluster) < args.min_cluster or len(sessions) < 2:
            continue
        print(f"- {signature}: {len(cluster)} events across {len(sessions)} sessions")
        shown = True
    if not shown:
        print("- none above recurrence gate")

    print("Attribution:")
    shown = False
    for (signature, target), count in by_target.most_common(25):
        if count < args.min_cluster:
            continue
        print(f"- {signature} -> {target}: {count}")
        shown = True
    if not shown:
        print("- none above display threshold")

    if args.json:
        write_private_json(args.json.expanduser(), events)
        print(f"Wrote {len(events)} redacted events to {args.json} with mode 0600")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
