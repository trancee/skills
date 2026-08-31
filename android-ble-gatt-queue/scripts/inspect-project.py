#!/usr/bin/env python3
"""Inspect Android BluetoothGatt coroutine queues for serialization and callback-race hazards."""

from __future__ import annotations

import argparse
import json
import platform
import re
import sys
from pathlib import Path
from typing import Any

IGNORED = {".cache", ".git", ".gradle", ".idea", "build", "node_modules", "target", "vendor"}
GATT_OPERATIONS = ("discoverServices", "readCharacteristic", "writeCharacteristic", "readDescriptor", "writeDescriptor", "requestMtu", "readRemoteRssi", "executeReliableWrite")
CALLBACKS = ("onServicesDiscovered", "onCharacteristicRead", "onCharacteristicWrite", "onDescriptorRead", "onDescriptorWrite", "onMtuChanged", "onReadRemoteRssi", "onReliableWriteCompleted")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Android project root (default: cwd)")
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    return parser.parse_args()


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def project_files(root: Path) -> tuple[list[Path], list[Path]]:
    builds: list[Path] = []
    sources: list[Path] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in IGNORED for part in relative.parts) or not path.is_file():
            continue
        if path.name in {"build.gradle", "build.gradle.kts", "libs.versions.toml"} or path.name.endswith((".gradle", ".gradle.kts")):
            builds.append(path)
        elif path.suffix in {".kt", ".java"}:
            sources.append(path)
    key = lambda item: item.as_posix()
    return sorted(builds, key=key), sorted(sources, key=key)


def line_numbers(text: str, pattern: str, flags: int = 0) -> list[int]:
    compiled = re.compile(pattern, flags)
    return [number for number, line in enumerate(text.splitlines(), 1) if compiled.search(line)]


def function_blocks(text: str, names: tuple[str, ...]) -> list[tuple[str, str]]:
    blocks = []
    pattern = re.compile(rf"\bfun\s+({'|'.join(map(re.escape, names))})\s*\([^)]*\)[^{{]*\{{")
    for match in pattern.finditer(text):
        opening = text.find("{", match.start())
        depth = 0
        quote: str | None = None
        escaped = False
        for index in range(opening, len(text)):
            char = text[index]
            if quote:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = None
            elif char in {'"', "'"}:
                quote = char
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    blocks.append((match.group(1), text[opening + 1:index]))
                    break
    return blocks


def inspect_build(path: Path, root: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    coroutine_versions = sorted(set(re.findall(r"kotlinx-coroutines-(?:core|android|test):([^\"'\s)]+)", text)))
    compile_sdk = sorted({int(value) for value in re.findall(r"\bcompileSdk(?:Version)?\s*(?:=|\()?\s*(\d+)", text)})
    target_sdk = sorted({int(value) for value in re.findall(r"\btargetSdk(?:Version)?\s*(?:=|\()?\s*(\d+)", text)})
    return {"file": rel(path, root), "coroutines_versions": coroutine_versions, "compile_sdk": compile_sdk, "target_sdk": target_sdk}


def inspect_source(path: Path, root: Path) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    operation_lines = {name: line_numbers(text, rf"\b{name}\s*\(") for name in GATT_OPERATIONS}
    operation_lines = {name: lines for name, lines in operation_lines.items() if lines}
    callback_lines = {name: line_numbers(text, rf"\b{name}\s*\(") for name in CALLBACKS}
    callback_lines = {name: lines for name, lines in callback_lines.items() if lines}
    signals = {
        "channel": line_numbers(text, r"\bChannel\s*<"),
        "unlimited_channel": line_numbers(text, r"Channel\.UNLIMITED"),
        "bounded_channel": line_numbers(text, r"Channel\s*<[^>]+>\s*\(\s*(?:[1-9]\d*|Channel\.RENDEZVOUS|Channel\.BUFFERED)"),
        "completable_deferred": line_numbers(text, r"\bCompletableDeferred\s*<"),
        "suspend_cancellable": line_numbers(text, r"\bsuspendCancellableCoroutine\s*[{<(]"),
        "await": line_numbers(text, r"\.await\s*\("),
        "timeout": line_numbers(text, r"\bwithTimeout(?:OrNull)?\s*\("),
        "delay_polling": line_numbers(text, r"\bdelay\s*\("),
        "global_scope": line_numbers(text, r"\bGlobalScope\b"),
        "with_context_io": line_numbers(text, r"withContext\s*\(\s*Dispatchers\.IO"),
        "operation_map": line_numbers(text, r"(?:ConcurrentHashMap|MutableMap)\s*<\s*GattOperation"),
        "operation_id": line_numbers(text, r"\b(?:AtomicLong|operationId|requestId|opId)\b"),
        "epoch": line_numbers(text, r"\b(?:epoch|generation)\b", re.IGNORECASE),
        "in_flight": line_numbers(text, r"\b(?:inFlight|in_flight)\b"),
        "actor_loop": line_numbers(text, r"for\s*\([^)]*\s+in\s+[^)]*(?:Channel|channel|requests)"),
        "notification_callback": line_numbers(text, r"\bonCharacteristicChanged\s*\("),
        "notification_stream": line_numbers(text, r"\b(?:MutableSharedFlow|SharedFlow|tryEmit|trySend)\b"),
        "callback_launch": line_numbers(text, r"\bscope\.launch\s*\{"),
        "set_notification": line_numbers(text, r"\bsetCharacteristicNotification\s*\("),
        "cccd_write": line_numbers(text, r"\bwriteDescriptor\s*\(|ENABLE_(?:NOTIFICATION|INDICATION)_VALUE|00002902", re.IGNORECASE),
        "service_changed": line_numbers(text, r"\bonServiceChanged\s*\("),
        "connection_callback": line_numbers(text, r"\bonConnectionStateChange\s*\("),
        "disconnect": line_numbers(text, r"\.disconnect\s*\("),
        "close": line_numbers(text, r"\.close\s*\("),
        "mutable_value": line_numbers(text, r"\.(?:value\s*=|setValue\s*\()"),
        "caller_cancellation": line_numbers(text, r"invokeOnCancellation|isCancelled|CompletableDeferred\s*\([^)]*(?:Job|coroutineContext)"),
        "reset_on_timeout": line_numbers(text, r"(?:Timeout|timeout)[^\n]*(?:close|reset|disconnect)|(?:close|reset|disconnect)[^\n]*(?:Timeout|timeout)"),
        "byte_array_operation": line_numbers(text, r"data\s+class\s+\w+[^\n]*ByteArray"),
    }
    signals = {name: lines for name, lines in signals.items() if lines}
    invalid_write_callback = []
    invalid_notification_callback = []
    for match in re.finditer(r"onCharacteristicWrite\s*\((.*?)\)", text, re.DOTALL):
        if re.search(r"\b(?:ByteArray|byte\s*\[\])\b", match.group(1)):
            invalid_write_callback.append(text[:match.start()].count("\n") + 1)
    for match in re.finditer(r"onCharacteristicChanged\s*\((.*?)\)", text, re.DOTALL):
        params = match.group(1)
        if re.search(r"\bstatus\s*:", params) or len([part for part in params.split(",") if part.strip()]) > 3:
            invalid_notification_callback.append(text[:match.start()].count("\n") + 1)
    worker_blocks = function_blocks(text, ("processGattOperations", "processOperations", "runQueue", "runWorker", "consumeOperations"))
    workers = []
    for name, block in worker_blocks:
        calls = sorted(operation for operation in GATT_OPERATIONS if re.search(rf"\b{operation}\s*\(", block))
        workers.append({"name": name, "gatt_calls": calls, "awaits_completion": bool(re.search(r"\.await\s*\(|withTimeout|awaitCallback|awaitCompletion", block))})
    if not (operation_lines or callback_lines or signals or invalid_write_callback or invalid_notification_callback or workers):
        return None
    return {
        "file": rel(path, root), "operation_lines": operation_lines, "callback_lines": callback_lines,
        "signals": signals, "worker_functions": workers,
        "invalid_write_callback_lines": invalid_write_callback,
        "invalid_notification_callback_lines": invalid_notification_callback,
    }


def inspect(root: Path) -> dict[str, Any]:
    build_files, source_files = project_files(root)
    builds = [inspect_build(path, root) for path in build_files]
    sources = [entry for path in source_files if (entry := inspect_source(path, root))]
    warnings: list[str] = []
    signals = {name for entry in sources for name in entry["signals"]}
    operation_count = sum(len(lines) for entry in sources for lines in entry["operation_lines"].values())
    callback_count = sum(len(lines) for entry in sources for lines in entry["callback_lines"].values())
    if operation_count > 1 and not ({"channel", "in_flight"} <= signals):
        warnings.append("Multiple GATT operation sites found without both a request channel and single in-flight record candidate.")
    if "unlimited_channel" in signals:
        warnings.append("Channel.UNLIMITED found in a GATT queue; use bounded capacity/backpressure because UNLIMITED is not unbuffered.")
    if "operation_map" in signals:
        warnings.append("GattOperation-keyed completion map found; identical value-equal requests can collide and one in-flight record is sufficient.")
    if "byte_array_operation" in signals and "operation_map" in signals:
        warnings.append("ByteArray-bearing operation is used with value-keyed completion bookkeeping; use immutable copied bytes plus monotonic request ID.")
    if any(not worker["awaits_completion"] and worker["gatt_calls"] for entry in sources for worker in entry["worker_functions"]):
        warnings.append("GATT queue worker submits Android operations without awaiting callback completion before its next receive.")
    if any(entry["invalid_write_callback_lines"] for entry in sources):
        warnings.append("Nonexistent value-bearing onCharacteristicWrite overload candidate found; Android callback provides characteristic and status only.")
    if any(entry["invalid_notification_callback_lines"] for entry in sources):
        warnings.append("Nonexistent status-bearing onCharacteristicChanged overload candidate found; API 33 callback provides characteristic and value only.")
    if "mutable_value" in signals:
        warnings.append("Mutable characteristic/descriptor value API found; use API 33+ value-taking methods and callback value snapshots.")
    if "set_notification" in signals and "cccd_write" not in signals:
        warnings.append("setCharacteristicNotification found without a CCCD descriptor-write composite.")
    if "notification_callback" in signals and "notification_stream" not in signals:
        warnings.append("Characteristic notifications found without a detected separate bounded event stream.")
    if "callback_launch" in signals:
        warnings.append("Callback launches coroutine work directly; verify callback order, ownership, bounded buffering, and cancellation.")
    if "delay_polling" in signals:
        warnings.append("delay()-based GATT readiness/polling found; await the exact callback/state with timeout.")
    if "global_scope" in signals:
        warnings.append("GlobalScope found in GATT ownership; use a lifecycle-owned scope and close/drain on cancellation.")
    if "with_context_io" in signals:
        warnings.append("withContext(Dispatchers.IO) around callback GATT APIs does not serialize completion; use the queue owner context.")
    if "timeout" in signals and "reset_on_timeout" not in signals and not ({"disconnect", "close"} <= signals):
        warnings.append("Operation timeout found without a detected GATT reset/close path; advancing on a timed-out epoch can overlap late callbacks.")
    if "suspend_cancellable" in signals and "caller_cancellation" not in signals:
        warnings.append("suspendCancellableCoroutine found without detected cancellation wiring for queued/in-flight requests.")
    if operation_count and callback_count and "epoch" not in signals:
        warnings.append("GATT operations/callbacks found without a connection epoch/generation candidate for stale callback rejection.")
    if operation_count and "operation_id" not in signals:
        warnings.append("GATT operations found without a monotonic request ID candidate.")
    if operation_count and "in_flight" not in signals:
        warnings.append("GATT operations found without a single in-flight record candidate.")
    if "connection_callback" in signals and not ({"disconnect", "close"} <= signals):
        warnings.append("Connection callback found without both disconnect and close lifecycle candidates.")
    if "service_changed" in signals and "epoch" not in signals:
        warnings.append("onServiceChanged found without queue epoch/reset candidate.")
    return {
        "root": str(root), "host": {"system": platform.system(), "machine": platform.machine()},
        "build_files_scanned": len(build_files), "source_files_scanned": len(source_files),
        "compile_sdk": sorted({value for build in builds for value in build["compile_sdk"]}),
        "target_sdk": sorted({value for build in builds for value in build["target_sdk"]}),
        "coroutines_versions": sorted({value for build in builds for value in build["coroutines_versions"]}),
        "builds": builds, "sources": sources, "operation_calls": operation_count, "callback_methods": callback_count,
        "warnings": sorted(set(warnings)),
    }


def print_human(data: dict[str, Any]) -> None:
    print(f"Root: {data['root']}")
    print(f"Host: {data['host']['system']} {data['host']['machine']}")
    print(f"SDK compile/target: {data['compile_sdk'] or 'unresolved'} / {data['target_sdk'] or 'unresolved'}")
    print(f"GATT operation/callback sites: {data['operation_calls']} / {data['callback_methods']}")
    if data["warnings"]:
        print("Warnings:")
        for warning in data["warnings"]:
            print(f"- {warning}")


def main() -> int:
    args = parse_args()
    root = args.root.expanduser().resolve()
    if not root.is_dir():
        print(f"error: project root is not a directory: {root}", file=sys.stderr)
        return 2
    data = inspect(root)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print_human(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
