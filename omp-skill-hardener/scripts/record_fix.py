#!/usr/bin/env python3
"""Append an approved hardening change to the private recurrence ledger."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def load_ledger(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 1, "fixes": []}
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict) or value.get("version") != 1 or not isinstance(value.get("fixes"), list):
        raise ValueError("ledger must be a version 1 object containing a fixes array")
    return value


def atomic_private_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> int:
    parser = argparse.ArgumentParser(description="Record one approved OMP skill hardening fix.")
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--target", required=True, help="attributed target, for example skill:foo")
    parser.add_argument("--signature", required=True)
    parser.add_argument("--guardrail", required=True, help="exact approved instruction or concise change summary")
    parser.add_argument("--changed-file", action="append", default=[])
    parser.add_argument("--source-report")
    parser.add_argument("--fixed-at", help="ISO-8601 timestamp; defaults to current UTC time")
    args = parser.parse_args()

    fixed_at = args.fixed_at or datetime.now(timezone.utc).isoformat()
    try:
        parsed_time = datetime.fromisoformat(fixed_at.replace("Z", "+00:00"))
    except ValueError:
        parser.error("--fixed-at must be ISO-8601")
    if parsed_time.tzinfo is None:
        parser.error("--fixed-at must include a UTC offset or Z suffix")
    if not args.target.strip() or not args.signature.strip() or not args.guardrail.strip():
        parser.error("target, signature, and guardrail must not be blank")

    identity = hashlib.sha256(
        f"{args.target}\0{args.signature}\0{fixed_at}\0{args.guardrail}".encode()
    ).hexdigest()[:16]
    entry = {
        "id": identity,
        "target": args.target,
        "signature": args.signature,
        "fixedAt": fixed_at,
        "guardrail": args.guardrail,
        "changedFiles": args.changed_file,
        "sourceReport": args.source_report,
    }

    path = args.ledger.expanduser()
    lock_path = path.with_suffix(path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "a+", encoding="utf-8") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            ledger = load_ledger(path)
            if any(fix.get("id") == identity for fix in ledger["fixes"] if isinstance(fix, dict)):
                raise ValueError(f"fix already recorded: {identity}")
            ledger["fixes"].append(entry)
            atomic_private_write(path, ledger)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    print(f"Recorded fix {identity} in {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
