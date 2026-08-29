#!/usr/bin/env python3
"""Rank OMP friction clusters and render reviewable hardening proposals."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SEVERITY = {
    "plan_reversal": 7,
    "user_frustration": 6,
    "hook_block": 5,
    "repeated_tool_error": 5,
    "user_interrupt": 4,
    "repeated_edit": 3,
    "claimed_done_no_verify": 3,
}
GUARDRAIL_SEEDS = {
    "plan_reversal": "Before leaving plan mode, restate the chosen scope and preserve every explicit constraint.",
    "user_frustration": "Treat the user's correction as authoritative; change the stated behavior instead of rechecking it.",
    "hook_block": "When a policy or approval blocks an action, preserve completed work and ask only for the missing authorization.",
    "repeated_tool_error": "After two failures with the same tool approach, stop retrying unchanged and diagnose the shared cause.",
    "user_interrupt": "Keep long-running or destructive steps interruptible and report durable progress before retrying.",
    "repeated_edit": "Before a third edit to one file, reread the whole affected construct and fix the root cause in one coherent change.",
    "claimed_done_no_verify": "Do not claim completion until the changed behavior has been exercised on the actual surface.",
}


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def parse_time(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


def recurrence_after(events: list[dict[str, Any]], fixed_at: str) -> int:
    boundary = parse_time(fixed_at)
    if boundary is None:
        return 0
    count = 0
    for event in events:
        observed = parse_time(str(event.get("timestamp", "")))
        if observed is not None and observed > boundary:
            count += 1
    return count


def cluster_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        signature = event.get("signature")
        target = event.get("target")
        if isinstance(signature, str) and isinstance(target, str):
            grouped[(signature, target)].append(event)

    clusters: list[dict[str, Any]] = []
    for (signature, target), members in grouped.items():
        sessions = sorted({str(event.get("session", "")) for event in members})
        snippets = list(dict.fromkeys(str(event.get("snippet", "")) for event in members if event.get("snippet")))[:3]
        timestamps = sorted(str(event.get("timestamp", "")) for event in members if event.get("timestamp"))
        score = SEVERITY.get(signature, 1) * len(sessions) + len(members)
        paths = [event.get("targetPath") for event in members if event.get("targetPath")]
        clusters.append(
            {
                "signature": signature,
                "target": target,
                "targetPath": paths[-1] if paths else None,
                "events": len(members),
                "sessions": sessions,
                "sessionCount": len(sessions),
                "firstSeen": timestamps[0] if timestamps else "",
                "lastSeen": timestamps[-1] if timestamps else "",
                "score": score,
                "snippets": snippets,
                "guardrailSeed": GUARDRAIL_SEEDS.get(signature, "Add a narrow instruction that prevents this observed failure mode."),
                "_members": members,
            }
        )
    return sorted(clusters, key=lambda cluster: (-cluster["score"], cluster["signature"], cluster["target"]))


def load_fixes(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    value = load_json(path)
    if not isinstance(value, dict) or value.get("version") != 1 or not isinstance(value.get("fixes"), list):
        raise ValueError("ledger must be a version 1 object containing a fixes array")
    return [entry for entry in value["fixes"] if isinstance(entry, dict)]


def annotate_fixes(clusters: list[dict[str, Any]], fixes: list[dict[str, Any]]) -> None:
    for cluster in clusters:
        matches = [
            fix
            for fix in fixes
            if fix.get("signature") == cluster["signature"] and fix.get("target") == cluster["target"]
        ]
        if not matches:
            cluster["fix"] = None
            cluster["postFixRecurrence"] = 0
            continue
        fix = max(matches, key=lambda item: str(item.get("fixedAt", "")))
        cluster["fix"] = fix
        cluster["postFixRecurrence"] = recurrence_after(cluster["_members"], str(fix.get("fixedAt", "")))


def markdown(clusters: list[dict[str, Any]], min_events: int, min_sessions: int) -> str:
    eligible = [
        cluster
        for cluster in clusters
        if cluster["events"] >= min_events and cluster["sessionCount"] >= min_sessions
    ]
    lines = [
        "# OMP Skill Hardening Report",
        "",
        f"Recurrence gate: at least {min_events} events across {min_sessions} sessions.",
        "Event excerpts are redacted by the miner; still review the report before sharing it.",
        "",
    ]
    if not eligible:
        lines.extend(["No cluster met the recurrence gate.", ""])
        return "\n".join(lines)

    for index, cluster in enumerate(eligible, 1):
        lines.extend(
            [
                f"## {index}. `{cluster['signature']}` -> `{cluster['target']}`",
                "",
                f"- Evidence: {cluster['events']} events across {cluster['sessionCount']} sessions",
                f"- Window: {cluster['firstSeen'] or 'unknown'} to {cluster['lastSeen'] or 'unknown'}",
                f"- Rank score: {cluster['score']}",
                f"- Resolved path: `{cluster['targetPath']}`" if cluster["targetPath"] else "- Resolved path: unresolved; verify provider precedence manually",
            ]
        )
        if cluster["fix"]:
            lines.append(
                f"- Recorded fix: `{cluster['fix'].get('id', 'unknown')}` at {cluster['fix'].get('fixedAt', 'unknown')}"
            )
            lines.append(f"- Post-fix recurrence: {cluster['postFixRecurrence']}")
        lines.extend(["", "Observed excerpts:"])
        for snippet in cluster["snippets"]:
            lines.append(f"- {snippet}")
        lines.extend(
            [
                "",
                "Candidate guardrail seed (rewrite against the attributed skill and surrounding rules):",
                "",
                f"> {cluster['guardrailSeed']}",
                "",
                "Required review: confirm attribution, reject a one-off/environmental cause, preserve user intent, and cap the applied change at three narrow edits.",
                "",
            ]
        )
    return "\n".join(lines)


def write_private(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(descriptor, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(content)
        if not content.endswith("\n"):
            handle.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a ranked report from mine_friction.py JSON output.")
    parser.add_argument("events", type=Path)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--min-events", type=int, default=3)
    parser.add_argument("--min-sessions", type=int, default=2)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.min_events < 1 or args.min_sessions < 1:
        parser.error("recurrence thresholds must be positive")
    try:
        value = load_json(args.events)
        if not isinstance(value, list):
            raise ValueError("events input must be a JSON array")
        events = [event for event in value if isinstance(event, dict)]
        clusters = cluster_events(events)
        annotate_fixes(clusters, load_fixes(args.ledger))
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    if args.format == "json":
        serializable = [{key: value for key, value in cluster.items() if key != "_members"} for cluster in clusters]
        content = json.dumps(serializable, indent=2)
    else:
        content = markdown(clusters, args.min_events, args.min_sessions)

    if args.output:
        write_private(args.output, content)
        print(f"Wrote report to {args.output} with mode 0600")
    else:
        print(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
