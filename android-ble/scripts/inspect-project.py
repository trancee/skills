#!/usr/bin/env python3
"""Inspect Android BLE SDK, manifest, scan, GATT, background, and Android 17 migration signals."""

from __future__ import annotations

import argparse
import json
import platform
import re
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

ANDROID_NS = "{http://schemas.android.com/apk/res/android}"
IGNORED = {".cache", ".git", ".gradle", ".idea", "build", "node_modules", "target", "vendor"}
BUILD_NAMES = {"build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts", "gradle.properties", "libs.versions.toml"}
BLE_PERMISSIONS = {"android.permission.BLUETOOTH_SCAN", "android.permission.BLUETOOTH_CONNECT", "android.permission.BLUETOOTH_ADVERTISE"}
SIGNALS = {
    "scan_start": re.compile(r"\bstartScan\s*\("),
    "scan_stop": re.compile(r"\bstopScan\s*\("),
    "scan_filter": re.compile(r"\bScanFilter\b"),
    "scan_failure": re.compile(r"\bonScanFailed\s*\(|EXTRA_ERROR_CODE"),
    "pending_intent_scan": re.compile(r"\bstartScan\s*\([^;\n]*PendingIntent|EXTRA_LIST_SCAN_RESULT", re.IGNORECASE),
    "advertising": re.compile(r"\b(?:BluetoothLeAdvertiser|startAdvertising|startAdvertisingSet)\b"),
    "gatt_connect": re.compile(r"\bconnectGatt\s*\("),
    "gatt_connection_settings": re.compile(r"\bBluetoothGattConnectionSettings\b"),
    "gatt_executor": re.compile(r"\bExecutor\b|Executors\."),
    "discover_services": re.compile(r"\bdiscoverServices\s*\("),
    "read_characteristic": re.compile(r"\breadCharacteristic\s*\("),
    "write_characteristic": re.compile(r"\bwriteCharacteristic\s*\("),
    "read_descriptor": re.compile(r"\breadDescriptor\s*\("),
    "write_descriptor": re.compile(r"\bwriteDescriptor\s*\("),
    "local_notification": re.compile(r"\bsetCharacteristicNotification\s*\("),
    "cccd": re.compile(r"00002902-0000-1000-8000-00805f9b34fb|ENABLE_(?:NOTIFICATION|INDICATION)_VALUE", re.IGNORECASE),
    "request_mtu": re.compile(r"\brequestMtu\s*\("),
    "service_changed": re.compile(r"\bonServiceChanged\s*\("),
    "gatt_close": re.compile(r"\b(?:gatt|bluetoothGatt)\s*\.\s*close\s*\("),
    "gatt_disconnect": re.compile(r"\b(?:gatt|bluetoothGatt)\s*\.\s*disconnect\s*\("),
    "operation_queue": re.compile(r"\b(?:ArrayDeque|Channel|Mutex|operationQueue|gattQueue)\b"),
    "companion_device": re.compile(r"\b(?:CompanionDeviceManager|CompanionDeviceService|startObservingDevicePresence)\b"),
    "foreground_service": re.compile(r"\b(?:startForegroundService|startForeground)\s*\("),
    "pairing_request": re.compile(r"\bACTION_PAIRING_REQUEST\b"),
    "pairing_context": re.compile(r"\bEXTRA_PAIRING_CONTEXT\b"),
    "repairing_context": re.compile(r"\bPAIRING_CONTEXT_REPAIRING\b"),
    "wrong_pairing_constant": re.compile(r"\bPAIRING_CONTEXT_AUTONOMOUS\b"),
    "set_pin": re.compile(r"\.setPin\s*\("),
    "rfcomm": re.compile(r"\b(?:createRfcommSocket|listenUsingRfcomm|RFCOMM)\b", re.IGNORECASE),
    "socket_read": re.compile(r"\.read\s*\("),
    "socket_eof_check": re.compile(r"(?:==|<=)\s*-1|<\s*0"),
    "background_activity_mode": re.compile(r"\bMODE_BACKGROUND_ACTIVITY_START_ALLOWED\b"),
    "background_activity_start": re.compile(r"\bstartActivity\s*\("),
    "audio": re.compile(r"\b(?:AudioTrack|AudioManager|requestAudioFocus|setStreamVolume|adjustStreamVolume|MediaPlayer)\b"),
    "loopback": re.compile(r"127\.0\.0\.1|localhost"),
    "cross_profile": re.compile(r"\b(?:CrossProfile|INTERACT_ACROSS_PROFILES|DevicePolicyManager|work profile)\b", re.IGNORECASE),
    "device_address": re.compile(r"\b(?:device\.)?address\b|\.getAddress\s*\("),
    "deprecated_value_state": re.compile(r"\.(?:setValue\s*\(|value\s*=)"),
    "value_callback": re.compile(r"onCharacteristic(?:Read|Changed)\s*\([^)]*(?:ByteArray|byte\s*\[\])", re.DOTALL),
}


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


def sdk_values(text: str, name: str) -> set[int]:
    patterns = (
        rf"\b{name}(?:Version)?\s*(?:=|\()?\s*(\d+)",
        rf"\b{name}\s*\{{[^}}]*\brelease\s*\(\s*(\d+)",
    )
    return {int(value) for pattern in patterns for value in re.findall(pattern, text, re.DOTALL)}


def inspect_catalog(path: Path, root: Path) -> tuple[dict[str, Any], list[str]]:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        return {}, [f"Cannot parse {rel(path, root)}: {error}"]
    versions = {key: str(value) for key, value in data.get("versions", {}).items()}
    android_versions = {key: value for key, value in versions.items() if any(token in key.lower() for token in ("compile", "target", "min", "agp"))}
    return {"file": rel(path, root), "android_related_versions": dict(sorted(android_versions.items()))}, []


def inspect_build(path: Path, root: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return {
        "file": rel(path, root),
        "compile_sdk": sorted(sdk_values(text, "compileSdk")),
        "target_sdk": sorted(sdk_values(text, "targetSdk")),
        "min_sdk": sorted(sdk_values(text, "minSdk")),
        "android_plugins": sorted(set(re.findall(r"[\"'](com\.android\.(?:application|library))[\"']", text))),
    }


def inspect_manifest(path: Path, root: Path) -> tuple[dict[str, Any], list[str]]:
    try:
        tree = ET.parse(path)
    except (OSError, ET.ParseError) as error:
        return {}, [f"Cannot parse {rel(path, root)}: {error}"]
    root_element = tree.getroot()
    permissions = []
    for element in root_element.findall("uses-permission"):
        name = element.get(ANDROID_NS + "name")
        if name:
            permissions.append({
                "name": name,
                "max_sdk": element.get(ANDROID_NS + "maxSdkVersion"),
                "flags": element.get(ANDROID_NS + "usesPermissionFlags"),
            })
    features = []
    for element in root_element.findall("uses-feature"):
        name = element.get(ANDROID_NS + "name")
        if name:
            features.append({"name": name, "required": element.get(ANDROID_NS + "required")})
    services = []
    for element in root_element.findall(".//service"):
        services.append({
            "name": element.get(ANDROID_NS + "name"),
            "exported": element.get(ANDROID_NS + "exported"),
            "foreground_service_types": sorted(filter(None, (element.get(ANDROID_NS + "foregroundServiceType") or "").split("|"))),
        })
    actions = sorted({element.get(ANDROID_NS + "name") for element in root_element.findall(".//receiver/intent-filter/action") if element.get(ANDROID_NS + "name")})
    return {
        "file": rel(path, root), "permissions": sorted(permissions, key=lambda item: item["name"]),
        "features": sorted(features, key=lambda item: item["name"]), "services": services, "receiver_actions": actions,
    }, []


def signal_lines(text: str, pattern: re.Pattern[str]) -> list[int]:
    return [number for number, line in enumerate(text.splitlines(), 1) if pattern.search(line)]


def inspect_source(path: Path, root: Path) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    signals = {name: signal_lines(text, pattern) for name, pattern in SIGNALS.items()}
    signals = {name: lines for name, lines in signals.items() if lines}
    legacy_connect = []
    for match in re.finditer(r"\bconnectGatt\s*\(\s*([^,\n]+)", text):
        first_arg = match.group(1).strip()
        if not re.search(r"(?:settings|ConnectionSettings)", first_arg, re.IGNORECASE):
            legacy_connect.append(text[:match.start()].count("\n") + 1)
    unfiltered_scans = []
    for match in re.finditer(r"\bstartScan\s*\(\s*([A-Za-z_][\w.]*)\s*\)", text):
        unfiltered_scans.append(text[:match.start()].count("\n") + 1)
    if not (signals or legacy_connect or unfiltered_scans):
        return None
    return {
        "file": rel(path, root), "signals": signals,
        "legacy_connect_gatt_candidate_lines": sorted(set(legacy_connect)),
        "unfiltered_scan_candidate_lines": sorted(set(unfiltered_scans)),
    }


def inspect(root: Path) -> dict[str, Any]:
    build_files, manifest_files, source_files = project_files(root)
    warnings: list[str] = []
    builds: list[dict[str, Any]] = []
    manifests: list[dict[str, Any]] = []
    catalogs: list[dict[str, Any]] = []
    for path in build_files:
        if path.name == "libs.versions.toml":
            catalog, problems = inspect_catalog(path, root)
            if catalog:
                catalogs.append(catalog)
            warnings.extend(problems)
        elif path.name.endswith((".gradle", ".gradle.kts")):
            builds.append(inspect_build(path, root))
    for path in manifest_files:
        manifest, problems = inspect_manifest(path, root)
        if manifest:
            manifests.append(manifest)
        warnings.extend(problems)
    sources = [entry for path in source_files if (entry := inspect_source(path, root))]
    compile_sdks = {value for entry in builds for value in entry["compile_sdk"]}
    target_sdks = {value for entry in builds for value in entry["target_sdk"]}
    min_sdks = {value for entry in builds for value in entry["min_sdk"]}
    permissions = {item["name"] for manifest in manifests for item in manifest["permissions"]}
    signals = {name for entry in sources for name in entry["signals"]}
    target = max(target_sdks) if target_sdks else None
    compile_sdk = max(compile_sdks) if compile_sdks else None
    if compile_sdk is not None and compile_sdk < 37 and ({"gatt_connection_settings", "pairing_context", "repairing_context"} & signals):
        warnings.append("Android 17/API 37 Bluetooth APIs found while compileSdk is below 37.")
    if target is not None and target >= 37 and any(entry["legacy_connect_gatt_candidate_lines"] for entry in sources):
        warnings.append("Legacy connectGatt overload candidate found for target 37; migrate to BluetoothGattConnectionSettings plus Executor callback API.")
    if "scan_start" in signals and "android.permission.BLUETOOTH_SCAN" not in permissions and (target or 0) >= 31:
        warnings.append("BLE scan APIs found without BLUETOOTH_SCAN manifest permission for target 31+.")
    if "advertising" in signals and "android.permission.BLUETOOTH_ADVERTISE" not in permissions and (target or 0) >= 31:
        warnings.append("BLE advertising APIs found without BLUETOOTH_ADVERTISE manifest permission for target 31+.")
    gatt_signals = {"gatt_connect", "discover_services", "read_characteristic", "write_characteristic", "read_descriptor", "write_descriptor", "request_mtu"}
    if signals & gatt_signals and "android.permission.BLUETOOTH_CONNECT" not in permissions and (target or 0) >= 31:
        warnings.append("GATT/connect APIs found without BLUETOOTH_CONNECT manifest permission for target 31+.")
    permission_entries = [item for manifest in manifests for item in manifest["permissions"]]
    for name in ("android.permission.BLUETOOTH", "android.permission.BLUETOOTH_ADMIN"):
        if any(item["name"] == name and item["max_sdk"] != "30" for item in permission_entries) and (target or 0) >= 31:
            warnings.append(f"Legacy {name.rsplit('.', 1)[-1]} permission lacks android:maxSdkVersion=30.")
    if any(item["name"] == "android.permission.BLUETOOTH_SCAN" and item["flags"] == "neverForLocation" for item in permission_entries) and "android.permission.ACCESS_FINE_LOCATION" in permissions:
        warnings.append("BLUETOOTH_SCAN neverForLocation and unrestricted ACCESS_FINE_LOCATION coexist; verify the product's location assertion/legacy maxSdkVersion.")
    service_types = {value for manifest in manifests for service in manifest["services"] for value in service["foreground_service_types"]}
    if "foreground_service" in signals and (target or 0) >= 34:
        if "connectedDevice" not in service_types and (signals & ({"gatt_connect", "scan_start", "advertising"})):
            warnings.append("BLE foreground-service use found without connectedDevice service type for target 34+.")
        if "android.permission.FOREGROUND_SERVICE_CONNECTED_DEVICE" not in permissions:
            warnings.append("Connected-device foreground-service candidate lacks FOREGROUND_SERVICE_CONNECTED_DEVICE permission.")
    if "local_notification" in signals and not {"write_descriptor", "cccd"}.issubset(signals):
        warnings.append("setCharacteristicNotification found without detected CCCD descriptor write/configuration.")
    if len([line for entry in sources for line in entry["signals"].get("request_mtu", [])]) > 1 and (target or 0) >= 34:
        warnings.append("Multiple requestMtu call sites found; Android 14+ first-client 517 request behavior requires one MTU owner.")
    if "deprecated_value_state" in signals and ({"write_characteristic", "write_descriptor"} & signals) and (target or 0) >= 33:
        warnings.append("Mutable characteristic/descriptor value API candidate found; use API 33+ value-taking methods and callbacks.")
    operation_count = sum(len(entry["signals"].get(name, [])) for entry in sources for name in ("read_characteristic", "write_characteristic", "read_descriptor", "write_descriptor", "request_mtu"))
    if operation_count > 1 and "operation_queue" not in signals:
        warnings.append("Multiple asynchronous GATT operation sites found without a detected queue/serialization primitive.")
    if "scan_start" in signals and "scan_failure" not in signals:
        warnings.append("BLE scanning found without a detected onScanFailed/PendingIntent error handler.")
    if any(entry["unfiltered_scan_candidate_lines"] for entry in sources):
        warnings.append("Unfiltered one-argument callback scan candidate found; Android stops unfiltered scans on screen-off.")
    if "pairing_request" in signals and "pairing_context" not in signals and (compile_sdk or 0) >= 37:
        warnings.append("Pairing-request handling lacks EXTRA_PAIRING_CONTEXT for Android 17 autonomous repair.")
    if "wrong_pairing_constant" in signals:
        warnings.append("PAIRING_CONTEXT_AUTONOMOUS is not the API 37 constant; use PAIRING_CONTEXT_REPAIRING.")
    if "set_pin" in signals and (compile_sdk or 0) >= 37:
        warnings.append("setPin usage found; API 37 deprecates byte-array PIN setting and ordinary apps should preserve system pairing UI.")
    rfcomm_files = [entry for entry in sources if "rfcomm" in entry["signals"] and "socket_read" in entry["signals"]]
    if target is not None and target >= 37 and any("socket_eof_check" not in entry["signals"] for entry in rfcomm_files):
        warnings.append("RFCOMM InputStream read loop candidate lacks explicit -1 EOF handling required by target-37 behavior.")
    if "background_activity_mode" in signals and (target or 0) >= 37:
        warnings.append("MODE_BACKGROUND_ACTIVITY_START_ALLOWED is deprecated for target 37; use granular visibility mode or user notification flow.")
    if "audio" in signals and (target or 0) >= 37 and "mediaPlayback" not in service_types:
        warnings.append("Audio API use found for target 37 without mediaPlayback service type; verify Android 17 visibility/FGS/WIU lifecycle.")
    if "loopback" in signals and "cross_profile" in signals:
        warnings.append("Cross-profile loopback candidate found; Android 17 blocks it by default while same-profile loopback remains unaffected.")
    if "android.permission.USE_LOOPBACK_INTERFACE" in permissions:
        warnings.append("USE_LOOPBACK_INTERFACE manifest permission found; verify against official public Android 17 guidance instead of secondary-source advice.")
    if "device_address" in signals:
        warnings.append("Bluetooth device-address usage found; inspect whether transient/private address is incorrectly used as persistent identity.")
    if "gatt_connect" in signals and not {"gatt_disconnect", "gatt_close"}.issubset(signals):
        warnings.append("GATT connection found without detected disconnect and close lifecycle calls.")
    return {
        "root": str(root), "host": {"system": platform.system(), "machine": platform.machine()},
        "build_files_scanned": len(build_files), "manifest_files_scanned": len(manifest_files), "source_files_scanned": len(source_files),
        "compile_sdk": sorted(compile_sdks), "target_sdk": sorted(target_sdks), "min_sdk": sorted(min_sdks),
        "manifests": manifests, "builds": builds, "version_catalogs": catalogs, "sources": sources,
        "warnings": sorted(set(warnings)),
    }


def print_human(data: dict[str, Any]) -> None:
    print(f"Root: {data['root']}")
    print(f"Host: {data['host']['system']} {data['host']['machine']}")
    print(f"SDK compile/target/min: {data['compile_sdk'] or 'unresolved'} / {data['target_sdk'] or 'unresolved'} / {data['min_sdk'] or 'unresolved'}")
    print(f"Manifests/relevant sources: {len(data['manifests'])} / {len(data['sources'])}")
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
