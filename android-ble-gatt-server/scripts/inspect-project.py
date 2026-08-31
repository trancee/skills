#!/usr/bin/env python3
"""Inspect Android BluetoothGattServer projects for request, subscription, and lifecycle hazards."""

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
    "open_server": r"\.openGattServer\s*\(",
    "server_type": r"\bBluetoothGattServer\b",
    "server_callback": r"\bBluetoothGattServerCallback\s*\(",
    "retained_server": r"\b(?:val|var|final\s+BluetoothGattServer|BluetoothGattServer)\s+\w*[Ss]erver\w*\s*(?::\s*BluetoothGattServer\??)?\s*[=;]",
    "server_close": r"(?:gattServer|server)\??\.close\s*\(",
    "clear_services": r"\.clearServices\s*\(",
    "add_service": r"\.addService\s*\(",
    "service_added": r"\bonServiceAdded\s*\(",
    "publication_queue": r"\b(?:serviceQueue|publicationQueue|pendingServices|ArrayDeque<\s*BluetoothGattService|Channel<\s*BluetoothGattService)\b",
    "service": r"\bBluetoothGattService\s*\(",
    "characteristic": r"\bBluetoothGattCharacteristic\s*\(",
    "descriptor": r"\bBluetoothGattDescriptor\s*\(",
    "cccd": r"00002902-0000-1000-8000-00805f9b34fb|ENABLE_(?:NOTIFICATION|INDICATION)_VALUE|DISABLE_NOTIFICATION_VALUE",
    "notify_property": r"PROPERTY_(?:NOTIFY|INDICATE)",
    "read_characteristic": r"\bonCharacteristicReadRequest\s*\(",
    "write_characteristic": r"\bonCharacteristicWriteRequest\s*\(",
    "read_descriptor": r"\bonDescriptorReadRequest\s*\(",
    "write_descriptor": r"\bonDescriptorWriteRequest\s*\(",
    "execute_write": r"\bonExecuteWrite\s*\(",
    "send_response": r"\.sendResponse\s*\(",
    "offset_check": r"\boffset\s*(?:<=|<|>=|>)|(?:size|length)\s*(?:<=|<|>=|>)\s*offset|copyOfRange\s*\(\s*offset|drop\s*\(\s*offset",
    "response_needed": r"\bresponseNeeded\b",
    "prepared_write": r"\bpreparedWrite\b",
    "prepared_store": r"\b(?:preparedWrites|pendingWrites|writeTransaction|fragment|stagedWrites)\b",
    "execute_flag": r"\bexecute\b",
    "per_device_state": r"\b(?:Map|MutableMap|ConcurrentHashMap)\s*<\s*BluetoothDevice|\b(?:deviceStates|subscriptions|cccdByDevice|mtuByDevice)\b",
    "connection_state": r"\bonConnectionStateChange\s*\(",
    "mtu_changed": r"\bonMtuChanged\s*\(",
    "notify": r"\.notifyCharacteristicChanged\s*\(",
    "notification_sent": r"\bonNotificationSent\s*\(",
    "notification_queue": r"\b(?:notificationQueue|outboundQueue|pendingNotifications|Channel<[^>]*(?:Notification|Update)|inFlightNotification)\b",
    "submission_status": r"BluetoothStatusCodes\.SUCCESS|\bnotificationStatus\b|\bsubmitStatus\b",
    "deprecated_value": r"\.(?:setValue\s*\(|value\s*=)",
    "unsupported_server_query": r"(?:gattServer|server)\??\.(?:getConnectedDevices|getConnectionState|getDevicesMatchingConnectionStates)\s*\(",
    "manager_server_query": r"\.getConnectedDevices\s*\(\s*BluetoothProfile\.GATT_SERVER",
    "cancel_connection": r"\.cancelConnection\s*\(",
    "server_connect": r"(?:gattServer|server)\??\.connect\s*\(",
    "callback_confinement": r"\b(?:Handler|Executor|Channel|Mutex|synchronized|ReentrantLock|callbackScope|serverActor)\b",
    "global_scope": r"\bGlobalScope\b",
    "value_limit": r"\b512\b|MAX_ATTRIBUTE_(?:LENGTH|SIZE)|maxAttribute(?:Length|Size)",
    "device_address": r"\.address\b|\.getAddress\s*\(",
    "connection_updated": r"\bonConnectionUpdated\s*\(",
    "sdk_guard_372": r"SDK_INT_FULL|VERSION_CODES_FULL|37\.2|API_FULL",
}
COMPILED = {name: re.compile(pattern) for name, pattern in SIGNALS.items()}
CALLBACK_NAMES = ("onCharacteristicReadRequest", "onCharacteristicWriteRequest", "onDescriptorReadRequest", "onDescriptorWriteRequest", "onExecuteWrite")


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


def function_blocks(text: str, names: tuple[str, ...]) -> list[dict[str, Any]]:
    pattern = re.compile(rf"\b(?:fun|void)\s+({'|'.join(map(re.escape, names))})\s*\([^)]*\)[^{{;]*\{{")
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
                    result.append({
                        "name": match.group(1), "line": text[:match.start()].count("\n") + 1,
                        "send_response": ".sendResponse" in body, "checks_offset": bool(COMPILED["offset_check"].search(body)),
                        "uses_response_needed": "responseNeeded" in body,
                        "handles_prepared_write": "preparedWrite" in body and bool(COMPILED["prepared_store"].search(body)),
                        "uses_execute_flag": bool(re.search(r"\bexecute\b", body)),
                    })
                    break
    return result


def call_argument_counts(text: str, name: str) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    for match in re.finditer(rf"\b{re.escape(name)}\s*\(", text):
        opening = text.find("(", match.start())
        depth = 0
        commas = 0
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
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    content = text[opening + 1:index].strip()
                    result.append((text[:match.start()].count("\n") + 1, 0 if not content else commas + 1))
                    break
            elif char == "," and depth == 1:
                commas += 1
    return result


def inspect_build(path: Path, root: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    values = lambda pattern: sorted({int(item) for item in re.findall(pattern, text)})
    full = sorted(set(re.findall(r"\b(?:compileSdkExtension|compileSdkFull|compileSdkMinor)\s*(?:=|\()?\s*([^\s;)]+)", text)))
    return {"file": rel(path, root), "min_sdk": values(r"\bminSdk(?:Version)?\s*(?:=|\()?\s*(\d+)"), "compile_sdk": values(r"\bcompileSdk(?:Version)?\s*(?:=|\()?\s*(\d+)"), "target_sdk": values(r"\btargetSdk(?:Version)?\s*(?:=|\()?\s*(\d+)"), "full_sdk_markers": full}


def inspect_manifest(path: Path, root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"file": rel(path, root), "permissions": [], "features": [], "parse_error": None}
    try:
        root_node = ET.parse(path).getroot()
        result["permissions"] = sorted({node.attrib.get(ANDROID_NS + "name", "") for node in root_node.findall("uses-permission") if node.attrib.get(ANDROID_NS + "name")})
        result["features"] = sorted({node.attrib.get(ANDROID_NS + "name", "") for node in root_node.findall("uses-feature") if node.attrib.get(ANDROID_NS + "name")})
    except ET.ParseError as error:
        result["parse_error"] = str(error)
    return result


def inspect_source(path: Path, root: Path) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    signals = {name: lines for name, pattern in COMPILED.items() if (lines := line_numbers(text, pattern))}
    callbacks = function_blocks(text, CALLBACK_NAMES)
    notify_calls = [{"line": line, "arguments": count} for line, count in call_argument_counts(text, "notifyCharacteristicChanged")]
    if not signals and not callbacks and not notify_calls:
        return None
    return {"file": rel(path, root), "signals": signals, "request_callbacks": callbacks, "notify_calls": notify_calls}


def max_or_none(values: list[int]) -> int | None:
    return max(values) if values else None


def inspect(root: Path) -> dict[str, Any]:
    build_files, manifest_files, source_files = project_files(root)
    builds = [inspect_build(path, root) for path in build_files]
    manifests = [inspect_manifest(path, root) for path in manifest_files]
    sources = [entry for path in source_files if (entry := inspect_source(path, root))]
    signals = {name for entry in sources for name in entry["signals"]}
    permissions = {permission for manifest in manifests for permission in manifest["permissions"]}
    compile_sdk = max_or_none([value for build in builds for value in build["compile_sdk"]])
    target_sdk = max_or_none([value for build in builds for value in build["target_sdk"]])
    min_sdk_values = [value for build in builds for value in build["min_sdk"]]
    min_sdk = min(min_sdk_values) if min_sdk_values else None
    callbacks = [callback for entry in sources for callback in entry["request_callbacks"]]
    notify_calls = [call for entry in sources for call in entry["notify_calls"]]
    warnings: list[str] = []
    server_use = bool({"open_server", "server_type", "server_callback"} & signals)
    if server_use and (target_sdk or 0) >= 31 and "android.permission.BLUETOOTH_CONNECT" not in permissions:
        warnings.append("BluetoothGattServer targets API 31+ without BLUETOOTH_CONNECT in detected manifests.")
    if "open_server" in signals and "retained_server" not in signals:
        warnings.append("openGattServer result lacks a retained server-owner field candidate.")
    if "open_server" in signals and "server_close" not in signals:
        warnings.append("openGattServer found without BluetoothGattServer.close lifecycle candidate.")
    if server_use and "connection_state" not in signals:
        warnings.append("GATT server found without onConnectionStateChange per-device lifecycle handling.")
    if server_use and "callback_confinement" not in signals:
        warnings.append("GATT server callback state has no detected serial handler/executor/actor confinement.")
    if "add_service" in signals and "service_added" not in signals:
        warnings.append("addService found without onServiceAdded completion callback.")
    add_count = sum(len(entry["signals"].get("add_service", [])) for entry in sources)
    if add_count > 1 and "publication_queue" not in signals:
        warnings.append("Multiple addService sites found without a service publication queue; Android requires waiting for each onServiceAdded callback.")
    if "notify_property" in signals and "cccd" not in signals:
        warnings.append("Notify/indicate characteristic property found without a CCCD candidate.")
    read_callbacks = [item for item in callbacks if item["name"] in {"onCharacteristicReadRequest", "onDescriptorReadRequest"}]
    if read_callbacks and any(not item["send_response"] for item in read_callbacks):
        warnings.append("Read request callback lacks sendResponse.")
    if read_callbacks and any(not item["checks_offset"] for item in read_callbacks):
        warnings.append("Read request callback lacks explicit offset bounds/slicing.")
    write_callbacks = [item for item in callbacks if item["name"] in {"onCharacteristicWriteRequest", "onDescriptorWriteRequest"}]
    if write_callbacks and any(not item["uses_response_needed"] for item in write_callbacks):
        warnings.append("Write request callback ignores responseNeeded request-versus-command semantics.")
    if write_callbacks and any(not item["send_response"] for item in write_callbacks):
        warnings.append("Write request callback lacks conditional sendResponse handling.")
    if write_callbacks and any(not item["handles_prepared_write"] for item in write_callbacks):
        warnings.append("Write callback lacks prepared-write staging/bounds candidate.")
    execute_callbacks = [item for item in callbacks if item["name"] == "onExecuteWrite"]
    if "prepared_write" in signals and not execute_callbacks:
        warnings.append("preparedWrite callback parameter found without onExecuteWrite transaction completion.")
    if execute_callbacks and any(not item["send_response"] or not item["uses_execute_flag"] for item in execute_callbacks):
        warnings.append("onExecuteWrite lacks execute/cancel handling and one sendResponse completion.")
    if ({"write_descriptor", "read_descriptor"} & signals) and "cccd" in signals and "per_device_state" not in signals:
        warnings.append("CCCD callback handling lacks per-device subscription state candidate.")
    if "notify" in signals:
        if "notification_sent" not in signals:
            warnings.append("notifyCharacteristicChanged found without onNotificationSent completion callback.")
        if "notification_queue" not in signals:
            warnings.append("Notifications found without queue/in-flight serialization; Android requires waiting for onNotificationSent.")
        if "value_limit" not in signals:
            warnings.append("Notification path lacks a detected 512-byte/effective-payload bound.")
        if compile_sdk is not None and compile_sdk >= 33 and any(call["arguments"] == 3 for call in notify_calls):
            warnings.append("Deprecated mutable-value notifyCharacteristicChanged overload found; use API 33+ explicit value bytes.")
        if any(call["arguments"] >= 4 for call in notify_calls) and "submission_status" not in signals:
            warnings.append("API 33+ notifyCharacteristicChanged submission status appears unchecked.")
    if "deprecated_value" in signals and (compile_sdk or 0) >= 33:
        warnings.append("Deprecated mutable characteristic/descriptor value API found for API 33+ server path.")
    if "unsupported_server_query" in signals:
        warnings.append("Unsupported BluetoothGattServer connection query found; use BluetoothManager GATT_SERVER snapshot plus app-owned callback state.")
    if "server_connect" in signals and "cancel_connection" not in signals:
        warnings.append("Server-initiated connect found without cancelConnection teardown candidate.")
    if ({"connection_state", "mtu_changed", "write_descriptor", "notify"} & signals) and "per_device_state" not in signals:
        warnings.append("Per-central callbacks found without a detected BluetoothDevice-keyed state model.")
    if "global_scope" in signals:
        warnings.append("GlobalScope found in GATT server ownership; use a lifecycle-owned scope and close/drain on cancellation.")
    if "device_address" in signals:
        warnings.append("BluetoothDevice address access/log candidate found; avoid address-only identity and redact identifiers.")
    if "connection_updated" in signals and not any(build["full_sdk_markers"] for build in builds) and "sdk_guard_372" not in signals:
        warnings.append("onConnectionUpdated is documented for API 37.2 but no full/minor SDK guard marker was detected.")
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
