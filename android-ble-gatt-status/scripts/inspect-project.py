#!/usr/bin/env python3
"""Inspect Android BluetoothGatt connection/status handling and retry lifecycles."""

from __future__ import annotations

import argparse
import json
import platform
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

ANDROID_NS = "{http://schemas.android.com/apk/res/android}"
IGNORED = {".cache", ".git", ".gradle", ".idea", "build", "node_modules", "target", "vendor"}
BUILD_NAMES = {"build.gradle", "build.gradle.kts", "gradle.properties", "libs.versions.toml"}
SIGNALS = {
    "connect_gatt": r"\.connectGatt\s*\(",
    "connection_settings": r"\bBluetoothGattConnectionSettings\b",
    "settings_auto": r"\.setAutoConnectEnabled\s*\(",
    "settings_opportunistic": r"\.setOpportunisticEnabled\s*\(",
    "settings_transport": r"\.setTransport\s*\(",
    "settings_mtu": r"\.setAutomaticMtuEnabled\s*\(",
    "executor": r"\bExecutor(?:Service)?\b|Executors\.|newSingleThreadExecutor|connectGatt\s*\([^\n]*executor",
    "sdk_guard_37": r"SDK_INT\s*>=\s*(?:37|Build\.VERSION_CODES\.[A-Z_]+)|VERSION_CODES\.BAKLAVA",
    "connection_callback": r"\bonConnectionStateChange\s*\(",
    "status_133": r"(?:status\s*==\s*133\b|133\s*==\s*status\b|0x85\b)",
    "gatt_error_symbol": r"\b(?:Gatt|BluetoothGatt)\.GATT_ERROR\b",
    "status_success": r"status\s*==\s*BluetoothGatt\.GATT_SUCCESS|BluetoothGatt\.GATT_SUCCESS\s*==\s*status",
    "status_non_success": r"status\s*!=\s*BluetoothGatt\.GATT_SUCCESS|BluetoothGatt\.GATT_SUCCESS\s*!=\s*status",
    "new_state": r"\bnewState\b",
    "epoch": r"\b(?:epoch|generation|attemptId|connectionId)\b",
    "gatt_identity": r"(?:gatt\s*!==?\s*(?:currentGatt|bluetoothGatt)|(?:currentGatt|bluetoothGatt)\s*!==?\s*gatt|===\s*gatt|identityHashCode\s*\(\s*gatt)",
    "disconnect": r"\.disconnect\s*\(",
    "gatt_close": r"\bgatt\??\.close\s*\(",
    "field_close": r"\b(?:bluetoothGatt|currentGatt)\??\.close\s*\(",
    "discover_services": r"\.discoverServices\s*\(",
    "delayed_discovery": r"(?:postDelayed|delay)\s*\([^\n]*(?:discoverServices|500)|discoverServices[^\n]*(?:postDelayed|delay)",
    "retry": r"\b(?:retry|scheduleRetry|RetryWait)\b",
    "max_retries": r"\b(?:maxRetries|maxAttempts|attemptLimit)\b",
    "retry_budget": r"\b(?:retryBudget|maxRetryDuration|retryDeadline|elapsedRetry)\b",
    "backoff": r"\b(?:exponentialBackoff|backoff|pow\s*\(|shl\s+retry)\b",
    "jitter": r"\b(?:jitter|Random\.|nextLong\s*\()",
    "retry_scheduler": r"\b(?:retryScheduler|scheduledExecutor|Handler|ScheduledExecutor|delay\s*\()",
    "scheduler_shutdown": r"\.shutdownNow\s*\(",
    "scheduler_schedule": r"\.schedule\s*\(",
    "retry_cancel": r"\b(?:cancelRetry|retryJob\??\.cancel|removeCallbacks|cancelScheduledRetry)\b",
    "classification": r"GATT_CONNECTION_TIMEOUT|GATT_CONNECTION_CONGESTED|GATT_INSUFFICIENT_AUTHENTICATION|GATT_INSUFFICIENT_ENCRYPTION|FailureClass|classifyStatus|Permanent|Transient|Unknown",
    "null_result": r"connectGatt[^\n]*(?:\?:|==\s*null)|(?:bluetoothGatt|currentGatt)\s*==\s*null",
    "scan_start": r"\.startScan\s*\(",
    "scan_stop": r"\.stopScan\s*\(",
    "adapter_toggle": r"(?:bluetoothAdapter|adapter)\??\.(?:enable|disable)\s*\(",
    "hidden_refresh": r"getDeclaredMethod\s*\(\s*[\"']refresh[\"']|\.refresh\s*\(",
    "raw_address": r"\.getRemoteDevice\s*\([^\n]*(?:address|String)|\.address\b|\.getAddress\s*\(",
    "address_log": r"(?:Log\.|println\s*\(|Timber\.)[^\n]*(?:address|getAddress)",
    "status_log": r"(?:Log\.|println\s*\(|Timber\.)[^\n]*\bstatus\b",
    "state_log": r"(?:Log\.|println\s*\(|Timber\.)[^\n]*\bnewState\b",
    "elapsed_log": r"(?:elapsed|duration|startedAt|monotonic|nanoTime|elapsedRealtime)",
    "attempt_log": r"(?:Log\.|println\s*\(|Timber\.)[^\n]*(?:attempt|epoch|generation)|attemptId|connectionId",
    "global_scope": r"\bGlobalScope\b",
    "callback_blocking": r"onConnectionStateChange[^\n]*(?:Thread\.sleep|runBlocking)|Thread\.sleep[^\n]*onConnectionStateChange",
    "multiple_owner": r"\b(?:MutableMap|Map|ConcurrentHashMap)\s*<[^>]*BluetoothDevice[^>]*BluetoothGatt|\bactiveGatts\b",
    "auto_opportunistic_confusion": r"autoConnect[^\n]*(?:is|=|means)[^\n]*opportunistic|opportunistic[^\n]*(?:is|=|means)[^\n]*autoConnect",
}
COMPILED = {name: re.compile(pattern, re.IGNORECASE if name == "auto_opportunistic_confusion" else 0) for name, pattern in SIGNALS.items()}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Android project root (default: cwd)")
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    return parser.parse_args()


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def project_files(root: Path) -> tuple[list[Path], list[Path], list[Path]]:
    builds: list[Path] = []
    manifests: list[Path] = []
    sources: list[Path] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in IGNORED for part in relative.parts) or not path.is_file():
            continue
        if path.name in BUILD_NAMES or path.name.endswith((".gradle", ".gradle.kts")):
            builds.append(path)
        elif path.name == "AndroidManifest.xml":
            manifests.append(path)
        elif path.suffix in {".kt", ".java"}:
            sources.append(path)
    key = lambda item: item.as_posix()
    return sorted(builds, key=key), sorted(manifests, key=key), sorted(sources, key=key)


def line_numbers(text: str, pattern: re.Pattern[str]) -> list[int]:
    return [number for number, line in enumerate(text.splitlines(), 1) if pattern.search(line)]


def callback_blocks(text: str) -> list[dict[str, Any]]:
    pattern = re.compile(r"\b(?:fun|void)\s+onConnectionStateChange\s*\([^)]*\)[^{;]*\{")
    result: list[dict[str, Any]] = []
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
                    body = text[opening + 1:index]
                    status_positions = [position for token in ("status !=", "status ==", "GATT_SUCCESS") if (position := body.find(token)) >= 0]
                    state_position = body.find("newState")
                    result.append({
                        "line": text[:match.start()].count("\n") + 1,
                        "checks_status": bool(status_positions), "checks_status_before_state": bool(status_positions) and (state_position < 0 or min(status_positions) < state_position),
                        "checks_gatt_identity": bool(COMPILED["gatt_identity"].search(body)),
                        "closes_callback_gatt": bool(COMPILED["gatt_close"].search(body)),
                        "closes_field_gatt": bool(COMPILED["field_close"].search(body)),
                        "handles_all_failure": bool(COMPILED["status_non_success"].search(body)) or "else" in body,
                    })
                    break
    return result


def inspect_build(path: Path, root: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    values = lambda pattern: sorted({int(item) for item in re.findall(pattern, text)})
    return {"file": rel(path, root), "min_sdk": values(r"\bminSdk(?:Version)?\s*(?:=|\()?\s*(\d+)"), "compile_sdk": values(r"\bcompileSdk(?:Version)?\s*(?:=|\()?\s*(\d+)"), "target_sdk": values(r"\btargetSdk(?:Version)?\s*(?:=|\()?\s*(\d+)")}


def inspect_manifest(path: Path, root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"file": rel(path, root), "permissions": [], "parse_error": None}
    try:
        root_node = ET.parse(path).getroot()
        result["permissions"] = sorted({node.attrib.get(ANDROID_NS + "name", "") for node in root_node.findall("uses-permission") if node.attrib.get(ANDROID_NS + "name")})
    except ET.ParseError as error:
        result["parse_error"] = str(error)
    return result


def inspect_source(path: Path, root: Path) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    signals = {name: lines for name, pattern in COMPILED.items() if (lines := line_numbers(text, pattern))}
    callbacks = callback_blocks(text)
    if not signals and not callbacks:
        return None
    return {"file": rel(path, root), "signals": signals, "connection_callbacks": callbacks}


def max_or_none(values: list[int]) -> int | None:
    return max(values) if values else None


def inspect(root: Path) -> dict[str, Any]:
    build_files, manifest_files, source_files = project_files(root)
    builds = [inspect_build(path, root) for path in build_files]
    manifests = [inspect_manifest(path, root) for path in manifest_files]
    sources = [entry for path in source_files if (entry := inspect_source(path, root))]
    signals = {name for entry in sources for name in entry["signals"]}
    callbacks = [callback for entry in sources for callback in entry["connection_callbacks"]]
    permissions = {permission for manifest in manifests for permission in manifest["permissions"]}
    compile_sdk = max_or_none([value for build in builds for value in build["compile_sdk"]])
    target_sdk = max_or_none([value for build in builds for value in build["target_sdk"]])
    min_values = [value for build in builds for value in build["min_sdk"]]
    min_sdk = min(min_values) if min_values else None
    connect_count = sum(len(entry["signals"].get("connect_gatt", [])) for entry in sources)
    warnings: list[str] = []
    if "connect_gatt" in signals and (target_sdk or 0) >= 31 and "android.permission.BLUETOOTH_CONNECT" not in permissions:
        warnings.append("connectGatt targets API 31+ without BLUETOOTH_CONNECT in detected manifests.")
    if callbacks and any(not callback["checks_status"] for callback in callbacks):
        warnings.append("onConnectionStateChange lacks explicit status evaluation.")
    if callbacks and any(not callback["checks_status_before_state"] for callback in callbacks):
        warnings.append("Connection callback appears to inspect newState before status; require status-first transitions.")
    if callbacks and any(not callback["checks_gatt_identity"] for callback in callbacks) and "epoch" not in signals:
        warnings.append("Connection callback lacks GATT identity or attempt/epoch stale-callback guard.")
    if callbacks and any(callback["closes_field_gatt"] and not callback["closes_callback_gatt"] for callback in callbacks):
        warnings.append("Connection callback closes a shared GATT field instead of the callback attempt object.")
    if "status_133" in signals and "status_non_success" not in signals:
        warnings.append("Code special-cases raw status 133 without a general non-success status path.")
    if "gatt_error_symbol" in signals:
        warnings.append("BluetoothGatt.GATT_ERROR/Gatt.GATT_ERROR is not a current public API 37/37.1 constant; preserve raw status numerically.")
    if "delayed_discovery" in signals:
        warnings.append("Fixed-delay service discovery candidate found; submit from verified connected transition unless a device-specific experiment proves the delay.")
    if "discover_services" in signals and not ({"status_success", "status_non_success"} & signals):
        warnings.append("Service discovery appears reachable without a detected GATT_SUCCESS connection gate.")
    if "connect_gatt" in signals and "epoch" not in signals:
        warnings.append("connectGatt found without attempt ID/connection epoch ownership.")
    if "connect_gatt" in signals and "gatt_close" not in signals and "field_close" not in signals:
        warnings.append("connectGatt found without BluetoothGatt.close cleanup candidate.")
    if "retry" in signals:
        required = {"max_retries", "retry_budget", "backoff", "jitter", "retry_scheduler", "retry_cancel", "classification"}
        if missing := sorted(required - signals):
            warnings.append("Retry path lacks one or more classification, cap, elapsed budget, backoff, jitter, scheduler, or cancellation candidates: " + ", ".join(missing) + ".")
        if "gatt_close" not in signals and "field_close" not in signals:
            warnings.append("Retry path lacks prior-attempt GATT close.")
    if "scheduler_shutdown" in signals and "scheduler_schedule" in signals:
        warnings.append("Scheduler is both shut down and scheduled in the same owner; verify retries never reuse a terminated executor.")
    if "adapter_toggle" in signals:
        warnings.append("Programmatic BluetoothAdapter enable/disable found; ordinary target-33+ apps cannot use this as production recovery.")
    if "hidden_refresh" in signals:
        warnings.append("Hidden BluetoothGatt.refresh reflection/call candidate found; use documented cache/service-changed behavior.")
    if "raw_address" in signals:
        warnings.append("Raw Bluetooth address identity candidate found; use scan/association/product identity and handle address rotation.")
    if "address_log" in signals:
        warnings.append("Bluetooth device address logging candidate found; redact with a session-local pseudonym.")
    if "connection_callback" in signals and not ({"status_log", "state_log", "elapsed_log", "attempt_log"} <= signals):
        warnings.append("Connection diagnostics lack one or more status, newState, elapsed-time, or attempt/epoch evidence candidates.")
    if "connection_callback" in signals and "classification" not in signals:
        warnings.append("Connection statuses lack typed transient/permanent/user-action/unknown classification candidate.")
    if "scan_start" in signals and "connect_gatt" in signals and "scan_stop" not in signals:
        warnings.append("Scan and connect coexist without an explicit scan-stop/isolation decision candidate.")
    if "connection_settings" in signals and min_sdk is not None and min_sdk < 37 and "sdk_guard_37" not in signals:
        warnings.append("BluetoothGattConnectionSettings is used below API 37 without a detected SDK guard.")
    if "connection_settings" in signals and not ({"settings_auto", "settings_opportunistic", "settings_transport", "settings_mtu", "executor"} <= signals):
        warnings.append("API 37 GATT settings lack one or more explicit auto-connect, opportunistic, transport, automatic-MTU, or executor decisions.")
    if "auto_opportunistic_confusion" in signals:
        warnings.append("autoConnect and opportunistic mode appear conflated; they are separate API 37 settings.")
    if "global_scope" in signals:
        warnings.append("GlobalScope found in connection/retry ownership; use a lifecycle-owned state machine.")
    if "callback_blocking" in signals:
        warnings.append("Blocking work found in onConnectionStateChange; dispatch bounded work from the callback executor.")
    if connect_count > 1 and "epoch" not in signals:
        warnings.append("Multiple connectGatt sites found without shared attempt/epoch ownership.")
    return {"root": str(root), "host": {"system": platform.system(), "machine": platform.machine()}, "build_files_scanned": len(build_files), "manifest_files_scanned": len(manifest_files), "source_files_scanned": len(source_files), "min_sdk": min_sdk, "compile_sdk": compile_sdk, "target_sdk": target_sdk, "permissions": sorted(permissions), "builds": builds, "manifests": manifests, "sources": sources, "warnings": sorted(set(warnings))}


def print_human(data: dict[str, Any]) -> None:
    print(f"Root: {data['root']}")
    print(f"Host: {data['host']['system']} {data['host']['machine']}")
    print(f"SDK min/compile/target: {data['min_sdk']} / {data['compile_sdk']} / {data['target_sdk']}")
    print(f"Sources/manifests: {data['source_files_scanned']} / {data['manifest_files_scanned']}")
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
