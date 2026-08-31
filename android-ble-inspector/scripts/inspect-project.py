#!/usr/bin/env python3
"""Inspect Android Compose BLE diagnostic apps for lifecycle, UI-state, and decoder hazards."""

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
    "compose": r"@Composable\b|\bandroidx\.compose\b",
    "view_model": r"\bViewModel\b|\bviewModel\s*\(",
    "state_flow": r"\b(?:Mutable)?StateFlow\b",
    "lifecycle_collect": r"\bcollectAsStateWithLifecycle\s*\(",
    "plain_collect": r"\bcollectAsState\s*\(",
    "platform_in_composable": r"remember\s*\{[^\n]*(?:BluetoothGatt|BluetoothLeScanner|BluetoothLeAdvertiser|BluetoothGattServer)",
    "lazy_list": r"\bLazyColumn\s*\{|\bLazyRow\s*\{",
    "stable_key": r"\bkey\s*=|items\s*\([^\n]*key\s*=",
    "scan_start": r"\.startScan\s*\(",
    "scan_stop": r"\.stopScan\s*\(",
    "callback_flow": r"\bcallbackFlow\s*\{",
    "await_close": r"\bawaitClose\s*\{",
    "scan_failure": r"\bonScanFailed\s*\(",
    "scan_timeout": r"SCAN_PERIOD|scanTimeout|withTimeout[^\n]*scan|delay\s*\([^\n]*stopScan",
    "scan_filter": r"\bScanFilter\b|filterServiceUuid",
    "low_latency": r"SCAN_MODE_LOW_LATENCY",
    "address": r"\.address\b|\.getAddress\s*\(",
    "address_identity": r"(?:associateBy|distinctBy|groupBy|key\s*=|\[[^]]*)[^\n]*\.address\b|\.address[^\n]*(?:associateBy|distinctBy|groupBy)",
    "address_log": r"(?:Log\.|println\s*\(|Timber\.)[^\n]*(?:\.address|getAddress)",
    "name_probe": r"(?:1800|2A00|GENERIC_ACCESS|DEVICE_NAME)[^\n]*(?:connectGatt|readCharacteristic)|(?:connectGatt|readCharacteristic)[^\n]*(?:1800|2A00|GENERIC_ACCESS|DEVICE_NAME)",
    "connect_gatt": r"\.connectGatt\s*\(",
    "discover_services": r"\.discoverServices\s*\(",
    "gatt_tree": r"\b(?:BluetoothGattService|BluetoothGattCharacteristic|BluetoothGattDescriptor|GattTree|services\s*=)\b",
    "instance_id": r"\.instanceId\b|\.getInstanceId\s*\(",
    "read": r"\.readCharacteristic\s*\(",
    "write": r"\.writeCharacteristic\s*\(",
    "notify_local": r"\.setCharacteristicNotification\s*\(",
    "cccd": r"00002902-0000-1000-8000-00805f9b34fb|ENABLE_(?:NOTIFICATION|INDICATION)_VALUE|DISABLE_NOTIFICATION_VALUE",
    "operation_queue": r"\b(?:operationMutex|operationQueue|gattQueue|inFlight|Channel<[^>]*(?:Operation|Gatt)|Mutex)\b",
    "operation_timeout": r"\bwithTimeout(?:OrNull)?\s*\(|operationTimeout",
    "gatt_close": r"(?:gatt|bluetoothGatt)\??\.close\s*\(",
    "progress_state": r"\b(?:Reading|Queued|InFlight|Subscribing|Unsubscribing|ObservationStatus|Starting|Stopping)\b",
    "raw_hex": r"\b(?:toHex|hexString|rawHex|HexFormat|formatHex)\b",
    "raw_ascii": r"\b(?:toAscii|rawAscii|ASCII|printable)\b",
    "decoder": r"\b(?:parseHeartRate|parseBloodPressure|parseSFloat|DecoderRegistry|decodeCharacteristic|BleDataParser)\b",
    "bounds_check": r"(?:bytes|data|value)\.size\s*(?:<|<=|>=|>)|(?:require|check)\s*\([^\n]*(?:size|length)|getOrNull\s*\(",
    "sfloat": r"\b(?:parseSFloat|SFLOAT|SFloat)\b",
    "sfloat_special": r"0x07FF|0x0800|0x07FE|0x0802|0x0801|\bNRes\b|POSITIVE_INFINITY|NEGATIVE_INFINITY",
    "write_confirmation": r"\b(?:ConfirmWrite|WriteConfirmation|confirmWrite|showWriteDialog|AlertDialog)\b",
    "advertise": r"\.startAdvertising\s*\(|\.startAdvertisingSet\s*\(",
    "advertise_failure": r"\bonStartFailure\s*\(|ADVERTISE_FAILED_DATA_TOO_LARGE",
    "advertise_size": r"\b(?:advertisementSize|advertiseSize|encodedSize|payloadBudget|MAX_LEGACY_ADVERTISING_DATA_BYTES)\b",
    "adapter_name_mutation": r"(?:bluetoothAdapter|adapter)\.(?:name\s*=|setName\s*\()",
    "gatt_server": r"\.openGattServer\s*\(|\bBluetoothGattServerCallback\b",
    "permission_profile": r"\b(?:PermissionProfile|BlePermissionProfile|Scanner|Central|Peripheral)\b",
    "raw_log": r"(?:Log\.|Timber\.|println\s*\()[^\n]*(?:toHex|rawHex|bytes\.joinToString)",
    "unbounded_history": r"\bmutableListOf<\s*(?:ByteArray|Data|BleDevice|ScanResult)|Channel\.UNLIMITED",
    "test_annotation": r"@Test\b",
}
COMPILED = {name: re.compile(pattern, re.IGNORECASE if name in {"name_probe"} else 0) for name, pattern in SIGNALS.items()}


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
    kotlin: list[Path] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in IGNORED for part in relative.parts) or not path.is_file():
            continue
        if path.name in BUILD_NAMES or path.name.endswith((".gradle", ".gradle.kts")):
            builds.append(path)
        elif path.name == "AndroidManifest.xml":
            manifests.append(path)
        elif path.suffix in {".kt", ".kts"}:
            kotlin.append(path)
    key = lambda item: item.as_posix()
    return sorted(builds, key=key), sorted(manifests, key=key), sorted(kotlin, key=key)


def line_numbers(text: str, pattern: re.Pattern[str]) -> list[int]:
    return [number for number, line in enumerate(text.splitlines(), 1) if pattern.search(line)]


def inspect_build(path: Path, root: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    values = lambda pattern: sorted({int(item) for item in re.findall(pattern, text)})
    return {"file": rel(path, root), "min_sdk": values(r"\bminSdk(?:Version)?\s*(?:=|\()?\s*(\d+)"), "compile_sdk": values(r"\bcompileSdk(?:Version)?\s*(?:=|\()?\s*(\d+)"), "target_sdk": values(r"\btargetSdk(?:Version)?\s*(?:=|\()?\s*(\d+)"), "compose": bool(re.search(r"compose|androidx\.compose", text, re.IGNORECASE))}


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
    if not signals:
        return None
    return {"file": rel(path, root), "is_test": "/test/" in f"/{rel(path, root)}" or "/androidTest/" in f"/{rel(path, root)}", "signals": signals}


def max_or_none(values: list[int]) -> int | None:
    return max(values) if values else None


def inspect(root: Path) -> dict[str, Any]:
    build_files, manifest_files, source_files = project_files(root)
    builds = [inspect_build(path, root) for path in build_files]
    manifests = [inspect_manifest(path, root) for path in manifest_files]
    sources = [entry for path in source_files if (entry := inspect_source(path, root))]
    production = [entry for entry in sources if not entry["is_test"]]
    tests = [entry for entry in sources if entry["is_test"]]
    signals = {name for entry in production for name in entry["signals"]}
    test_signals = {name for entry in tests for name in entry["signals"]}
    permissions = {permission for manifest in manifests for permission in manifest["permissions"]}
    compile_sdk = max_or_none([value for build in builds for value in build["compile_sdk"]])
    target_sdk = max_or_none([value for build in builds for value in build["target_sdk"]])
    min_values = [value for build in builds for value in build["min_sdk"]]
    min_sdk = min(min_values) if min_values else None
    warnings: list[str] = []
    ble_signals = {"scan_start", "connect_gatt", "read", "write", "notify_local", "advertise", "gatt_server"}
    inspector = bool(signals & ble_signals) and "compose" in signals
    if inspector and not ({"view_model", "state_flow"} <= signals):
        warnings.append("Compose BLE surface lacks both ViewModel and StateFlow state-owner candidates.")
    if "plain_collect" in signals and "lifecycle_collect" not in signals:
        warnings.append("Android Compose Flow uses collectAsState without collectAsStateWithLifecycle.")
    if "platform_in_composable" in signals:
        warnings.append("Composable remember block appears to own a Bluetooth platform object; move it to a lifecycle owner.")
    if "lazy_list" in signals and "stable_key" not in signals:
        warnings.append("Lazy device/GATT list lacks a detected stable key.")
    if "scan_start" in signals:
        missing = {"callback_flow", "await_close", "scan_stop", "scan_failure", "scan_timeout"} - signals
        if missing:
            warnings.append("Scan lifecycle lacks one or more callbackFlow, awaitClose, stopScan, onScanFailed, or bounded-time candidates.")
    if "low_latency" in signals and "scan_timeout" not in signals:
        warnings.append("Low-latency scan lacks a detected bounded interactive timeout.")
    if "address_identity" in signals:
        warnings.append("Bluetooth address appears to be used as durable/stable identity; model transient observations and rotating addresses.")
    if "address_log" in signals:
        warnings.append("Bluetooth address logging candidate found; redact identifiers by default.")
    if "name_probe" in signals:
        warnings.append("Automatic Generic Access Device Name connection/read probe candidate found; require targeted user-selected resolution.")
    if {"connect_gatt", "discover_services"}.intersection(signals) and "progress_state" not in signals:
        warnings.append("Connection/discovery UI lacks explicit progress-state candidate.")
    operation_count = sum(len(entry["signals"].get(name, [])) for entry in production for name in ("discover_services", "read", "write", "notify_local"))
    if operation_count > 1 and "operation_queue" not in signals:
        warnings.append("Multiple GATT operation sites lack a detected queue/mutex/in-flight owner.")
    if "operation_timeout" in signals and "gatt_close" not in signals:
        warnings.append("GATT timeout found without close/reset candidate for the uncertain connection.")
    if "notify_local" in signals and "cccd" not in signals:
        warnings.append("setCharacteristicNotification found without CCCD write constants/path.")
    if {"read", "notify_local"}.intersection(signals) and "progress_state" not in signals:
        warnings.append("Read/subscription actions lack explicit queued/reading/subscribing UI states.")
    if "write" in signals and "write_confirmation" not in signals:
        warnings.append("Inspector characteristic write lacks an explicit confirmation-surface candidate.")
    if "decoder" in signals and not ({"raw_hex", "raw_ascii"} <= signals):
        warnings.append("Structured decoder found without both raw hex and ASCII display candidates.")
    if "decoder" in signals and "bounds_check" not in signals:
        warnings.append("BLE decoder lacks detected byte-length bounds checks.")
    if "sfloat" in signals and "sfloat_special" not in signals:
        warnings.append("IEEE-11073 SFLOAT decoder lacks special-value handling.")
    if "decoder" in signals and not tests:
        warnings.append("BLE decoders found without detected Kotlin test sources.")
    if "adapter_name_mutation" in signals:
        warnings.append("BluetoothAdapter name mutation found; avoid global device-state changes in a transient inspector.")
    if "advertise" in signals and "advertise_failure" not in signals:
        warnings.append("Advertising found without onStartFailure/data-too-large handling.")
    if "advertise" in signals and "advertise_size" not in signals:
        warnings.append("Advertising found without selected-mode payload-size budget candidate.")
    if "unbounded_history" in signals:
        warnings.append("Unbounded BLE observation/value history candidate found; cap items and bytes.")
    if "raw_log" in signals:
        warnings.append("Raw BLE payload logging candidate found; use bounded redacted opt-in evidence export.")
    if bool(signals & ble_signals) and (target_sdk or 0) >= 31:
        if "scan_start" in signals and "android.permission.BLUETOOTH_SCAN" not in permissions:
            warnings.append("BLE scanner targets API 31+ without BLUETOOTH_SCAN in detected manifests.")
        if {"connect_gatt", "read", "write", "notify_local", "gatt_server"}.intersection(signals) and "android.permission.BLUETOOTH_CONNECT" not in permissions:
            warnings.append("BLE connection/GATT work targets API 31+ without BLUETOOTH_CONNECT in detected manifests.")
        if "advertise" in signals and "android.permission.BLUETOOTH_ADVERTISE" not in permissions:
            warnings.append("BLE advertiser targets API 31+ without BLUETOOTH_ADVERTISE in detected manifests.")
    return {"root": str(root), "host": {"system": platform.system(), "machine": platform.machine()}, "build_files_scanned": len(build_files), "manifest_files_scanned": len(manifest_files), "source_files_scanned": len(source_files), "test_files_detected": len(tests), "min_sdk": min_sdk, "compile_sdk": compile_sdk, "target_sdk": target_sdk, "permissions": sorted(permissions), "builds": builds, "manifests": manifests, "sources": sources, "warnings": sorted(set(warnings))}


def print_human(data: dict[str, Any]) -> None:
    print(f"Root: {data['root']}")
    print(f"Host: {data['host']['system']} {data['host']['machine']}")
    print(f"SDK min/compile/target: {data['min_sdk']} / {data['compile_sdk']} / {data['target_sdk']}")
    print(f"Sources/tests: {data['source_files_scanned']} / {data['test_files_detected']}")
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
