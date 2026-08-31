#!/usr/bin/env python3
"""Inspect Apple projects for Core Bluetooth lifecycle, flow-control, and restoration hazards."""

from __future__ import annotations

import argparse
import json
import platform
import plistlib
import re
import sys
from pathlib import Path
from typing import Any

IGNORED = {".build", ".cache", ".git", ".swiftpm", "Build", "DerivedData", "Pods", "SourcePackages", "build", "node_modules", "vendor"}
CONFIG_SUFFIXES = {".plist", ".entitlements", ".pbxproj", ".xcconfig"}

SIGNALS = {
    "corebluetooth_import": r"\bimport\s+CoreBluetooth\b",
    "central_manager": r"\bCBCentralManager\s*\(",
    "peripheral_manager": r"\bCBPeripheralManager\s*\(",
    "central_state_callback": r"\bcentralManagerDidUpdateState\s*\(",
    "peripheral_state_callback": r"\bperipheralManagerDidUpdateState\s*\(",
    "powered_on": r"\.poweredOn\b",
    "authorization": r"\bCBManager\.authorization\b|\.authorization\b",
    "scan": r"\.scanForPeripherals\s*\(",
    "scan_nil_services": r"scanForPeripherals\s*\(\s*withServices\s*:\s*nil\b",
    "scan_duplicates": r"CBCentralManagerScanOptionAllowDuplicatesKey\s*:\s*true\b",
    "stop_scan": r"\.stopScan\s*\(",
    "discovery_callback": r"centralManager\s*\([^\n]*didDiscover\s+peripheral",
    "retained_peripheral": r"\b(?:var|let)\s+\w+\s*:\s*(?:CBPeripheral\??|\[CBPeripheral\]|\[[^]]*:\s*CBPeripheral\])",
    "connect": r"\.connect\s*\(",
    "cancel_connection": r"\.cancelPeripheralConnection\s*\(",
    "did_connect": r"centralManager\s*\([^\n]*didConnect\s+peripheral",
    "did_fail_connect": r"centralManager\s*\([^\n]*didFailToConnect",
    "did_disconnect": r"centralManager\s*\([^\n]*didDisconnectPeripheral",
    "peripheral_delegate": r"\.delegate\s*=",
    "discover_services": r"\.discoverServices\s*\(",
    "discover_characteristics": r"\.discoverCharacteristics\s*\(",
    "discover_descriptors": r"\.discoverDescriptors\s*\(",
    "did_discover_services": r"peripheral\s*\([^\n]*didDiscoverServices",
    "did_discover_characteristics": r"peripheral\s*\([^\n]*didDiscoverCharacteristicsFor",
    "did_discover_descriptors": r"peripheral\s*\([^\n]*didDiscoverDescriptorsFor",
    "read_value": r"\.readValue\s*\(",
    "write_with_response": r"\.writeValue\s*\([^\n]*\.withResponse\b",
    "write_without_response": r"\.writeValue\s*\([^\n]*\.withoutResponse\b",
    "did_update_value": r"peripheral\s*\([^\n]*didUpdateValueFor",
    "did_write_value": r"peripheral\s*\([^\n]*didWriteValueFor",
    "maximum_write": r"\.maximumWriteValueLength\s*\(",
    "can_send_without_response": r"\.canSendWriteWithoutResponse\b",
    "ready_without_response": r"peripheralIsReady\s*\(\s*toSendWriteWithoutResponse",
    "set_notify": r"\.setNotifyValue\s*\(",
    "notification_state": r"peripheral\s*\([^\n]*didUpdateNotificationStateFor",
    "modified_services": r"peripheral\s*\([^\n]*didModifyServices",
    "mutable_service": r"\bCBMutableService\s*\(",
    "mutable_characteristic": r"\bCBMutableCharacteristic\s*\(",
    "add_service": r"\.add\s*\([^\n]*(?:service|Service)",
    "did_add_service": r"peripheralManager\s*\([^\n]*didAdd\s+service",
    "start_advertising": r"\.startAdvertising\s*\(",
    "stop_advertising": r"\.stopAdvertising\s*\(",
    "did_start_advertising": r"peripheralManagerDidStartAdvertising\s*\(",
    "unsupported_ad_key": r"CBAdvertisementData(?:ManufacturerData|TxPowerLevel|ServiceData|SolicitedServiceUUIDs|OverflowServiceUUIDs)Key",
    "update_value": r"\.updateValue\s*\(",
    "ready_subscribers": r"peripheralManagerIsReady\s*\(\s*toUpdateSubscribers",
    "subscribe_callback": r"peripheralManager\s*\([^\n]*didSubscribeTo",
    "unsubscribe_callback": r"peripheralManager\s*\([^\n]*didUnsubscribeFrom",
    "att_read": r"peripheralManager\s*\([^\n]*didReceiveRead",
    "att_write": r"peripheralManager\s*\([^\n]*didReceiveWrite",
    "att_respond": r"\.respond\s*\(\s*to\s*:",
    "att_offset": r"\.offset\b",
    "central_restore_key": r"CBCentralManagerOptionRestoreIdentifierKey",
    "peripheral_restore_key": r"CBPeripheralManagerOptionRestoreIdentifierKey",
    "central_restore_callback": r"centralManager\s*\([^\n]*willRestoreState",
    "peripheral_restore_callback": r"peripheralManager\s*\([^\n]*willRestoreState",
    "unstable_restore_id": r"(?:RestoreIdentifierKey[^\n]*UUID\s*\(\s*\)\.uuidString|UUID\s*\(\s*\)\.uuidString[^\n]*RestoreIdentifierKey)",
    "l2cap": r"\b(?:openL2CAPChannel|publishL2CAPChannel|CBL2CAPChannel)\b",
    "delay_sequencing": r"\b(?:Thread\.sleep|usleep)\s*\(|asyncAfter\s*\(",
}
COMPILED_SIGNALS = {name: re.compile(pattern) for name, pattern in SIGNALS.items()}
SUBCLASS = re.compile(r"\bclass\s+\w+(?:\s*<[^>]+>)?\s*:\s*(?:CBCentralManager|CBPeripheralManager|CBPeripheral|CBCentral|CBService|CBCharacteristic|CBDescriptor|CBATTRequest)\b")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Apple project root (default: cwd)")
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    return parser.parse_args()


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def project_files(root: Path) -> tuple[list[Path], list[Path]]:
    swift: list[Path] = []
    configs: list[Path] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in IGNORED for part in relative.parts) or not path.is_file():
            continue
        if path.suffix == ".swift":
            swift.append(path)
        elif path.suffix in CONFIG_SUFFIXES or path.name == "project.pbxproj":
            configs.append(path)
    key = lambda item: item.as_posix()
    return sorted(swift, key=key), sorted(configs, key=key)


def line_numbers(text: str, pattern: re.Pattern[str]) -> list[int]:
    return [number for number, line in enumerate(text.splitlines(), 1) if pattern.search(line)]


def inspect_source(path: Path, root: Path) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    signals = {name: lines for name, pattern in COMPILED_SIGNALS.items() if (lines := line_numbers(text, pattern))}
    subclass_lines = line_numbers(text, SUBCLASS)
    if not signals and not subclass_lines:
        return None
    return {"file": rel(path, root), "signals": signals, "unsupported_subclass_lines": subclass_lines}


def flatten_plist(value: Any, prefix: str = "") -> list[tuple[str, Any]]:
    result: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key in sorted(value):
            name = f"{prefix}.{key}" if prefix else str(key)
            result.append((name, value[key]))
            result.extend(flatten_plist(value[key], name))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            result.extend(flatten_plist(item, f"{prefix}[{index}]"))
    return result


def inspect_config(path: Path, root: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    parsed: dict[str, Any] | None = None
    parse_error: str | None = None
    if path.suffix in {".plist", ".entitlements"}:
        try:
            loaded = plistlib.loads(raw)
            parsed = loaded if isinstance(loaded, dict) else None
        except Exception as error:  # malformed/generated plist remains searchable as text
            parse_error = str(error)
    keys = []
    background_modes: set[str] = set()
    if parsed is not None:
        keys = sorted(key for key, _ in flatten_plist(parsed))
        value = parsed.get("UIBackgroundModes", [])
        if isinstance(value, list):
            background_modes.update(str(item) for item in value)
    for mode in ("bluetooth-central", "bluetooth-peripheral"):
        if mode in text:
            background_modes.add(mode)
    usage_keys = sorted(key for key in ("NSBluetoothAlwaysUsageDescription", "NSBluetoothPeripheralUsageDescription") if key in text or (parsed and key in parsed))
    platforms = sorted(set(re.findall(r"\b(?:SDKROOT|SUPPORTED_PLATFORMS)\s*=\s*([^;\n]+)", text)))
    return {
        "file": rel(path, root), "usage_keys": usage_keys, "background_modes": sorted(background_modes),
        "platform_settings": platforms, "plist_keys": keys, "parse_error": parse_error,
    }


def inspect(root: Path) -> dict[str, Any]:
    swift_files, config_files = project_files(root)
    sources = [entry for path in swift_files if (entry := inspect_source(path, root))]
    configs = [inspect_config(path, root) for path in config_files]
    signals = {name for entry in sources for name in entry["signals"]}
    usage_keys = sorted({key for config in configs for key in config["usage_keys"]})
    background_modes = sorted({mode for config in configs for mode in config["background_modes"]})
    warnings: list[str] = []
    uses_corebluetooth = "corebluetooth_import" in signals or "central_manager" in signals or "peripheral_manager" in signals
    if uses_corebluetooth and "NSBluetoothAlwaysUsageDescription" not in usage_keys:
        warnings.append("Core Bluetooth use found without NSBluetoothAlwaysUsageDescription in detected plist/build settings.")
    if "central_manager" in signals and "central_state_callback" not in signals:
        warnings.append("CBCentralManager found without centralManagerDidUpdateState callback.")
    if "peripheral_manager" in signals and "peripheral_state_callback" not in signals:
        warnings.append("CBPeripheralManager found without peripheralManagerDidUpdateState callback.")
    role_calls = {"scan", "connect", "discover_services", "add_service", "start_advertising", "update_value"}
    if signals.intersection(role_calls) and "powered_on" not in signals:
        warnings.append("Core Bluetooth role calls found without a detected .poweredOn gate.")
    if "scan_nil_services" in signals:
        warnings.append("Unfiltered scan found; prefer explicit service UUIDs, which are required for iOS background scanning.")
    if "scan" in signals and "stop_scan" not in signals:
        warnings.append("Scan found without stopScan lifecycle candidate.")
    if "scan_duplicates" in signals and "bluetooth-central" in background_modes:
        warnings.append("Duplicate scan option found with bluetooth-central background mode; scan options have no effect in background.")
    if "connect" in signals and "retained_peripheral" not in signals:
        warnings.append("Connection found without a retained CBPeripheral property/collection candidate; deallocation cancels a pending connection.")
    if "connect" in signals and "cancel_connection" not in signals:
        warnings.append("Connection found without cancelPeripheralConnection timeout/teardown candidate; connect attempts do not time out.")
    if "connect" in signals and not ({"did_connect", "did_fail_connect", "did_disconnect"} <= signals):
        warnings.append("Connection lifecycle lacks one or more didConnect, didFailToConnect, or didDisconnect callbacks.")
    discovery_pairs = (("discover_services", "did_discover_services"), ("discover_characteristics", "did_discover_characteristics"), ("discover_descriptors", "did_discover_descriptors"))
    for call, callback in discovery_pairs:
        if call in signals and callback not in signals:
            warnings.append(f"{call} call found without matching {callback} callback candidate.")
    if "read_value" in signals and "did_update_value" not in signals:
        warnings.append("readValue found without didUpdateValueFor callback candidate.")
    if "write_with_response" in signals and "did_write_value" not in signals:
        warnings.append("With-response write found without didWriteValueFor callback candidate.")
    if "write_without_response" in signals and not ({"can_send_without_response", "ready_without_response"} <= signals):
        warnings.append("Without-response write lacks canSendWriteWithoutResponse and readiness-callback flow control.")
    if ("write_with_response" in signals or "write_without_response" in signals) and "maximum_write" not in signals:
        warnings.append("Characteristic write found without maximumWriteValueLength(for:) sizing candidate.")
    if "set_notify" in signals and "notification_state" not in signals:
        warnings.append("setNotifyValue found without didUpdateNotificationStateFor result callback.")
    if "discover_services" in signals and "modified_services" not in signals:
        warnings.append("Discovered services found without didModifyServices invalidation handling.")
    if "add_service" in signals and "did_add_service" not in signals:
        warnings.append("Local service publication found without didAdd service callback.")
    if "start_advertising" in signals and "did_start_advertising" not in signals:
        warnings.append("startAdvertising found without peripheralManagerDidStartAdvertising callback.")
    if "unsupported_ad_key" in signals:
        warnings.append("Unsupported CBPeripheralManager advertising-data key candidate found; only local name and service UUIDs are accepted.")
    if "update_value" in signals and "ready_subscribers" not in signals:
        warnings.append("updateValue found without peripheralManagerIsReady(toUpdateSubscribers:) backpressure callback.")
    if ("att_read" in signals or "att_write" in signals) and "att_respond" not in signals:
        warnings.append("Peripheral ATT request callback found without respond(to:withResult:) candidate.")
    if "att_read" in signals and "att_offset" not in signals:
        warnings.append("Peripheral ATT read callback found without CBATTRequest.offset handling candidate.")
    restore_pairs = (("central_restore_key", "central_restore_callback"), ("peripheral_restore_key", "peripheral_restore_callback"))
    for key, callback in restore_pairs:
        if (key in signals) != (callback in signals):
            warnings.append(f"State restoration requires both {key} and {callback} candidates.")
    if "unstable_restore_id" in signals:
        warnings.append("Fresh UUID restoration identifier candidate found; restoration identifiers must remain stable across launches.")
    if any(entry["unsupported_subclass_lines"] for entry in sources):
        warnings.append("Core Bluetooth framework class subclass candidate found; use composition because subclassing is unsupported.")
    if "delay_sequencing" in signals:
        warnings.append("Sleep/delay-based Core Bluetooth sequencing found; advance from the matching delegate callback/state instead.")
    if "bluetooth-central" in background_modes and "central_manager" not in signals:
        warnings.append("bluetooth-central background mode found without a CBCentralManager candidate.")
    if "bluetooth-peripheral" in background_modes and "peripheral_manager" not in signals:
        warnings.append("bluetooth-peripheral background mode found without a CBPeripheralManager candidate.")
    return {
        "root": str(root), "host": {"system": platform.system(), "machine": platform.machine()},
        "swift_files_scanned": len(swift_files), "config_files_scanned": len(config_files),
        "usage_description_keys": usage_keys, "background_modes": background_modes,
        "platform_settings": sorted({item for config in configs for item in config["platform_settings"]}),
        "configs": configs, "sources": sources, "warnings": sorted(set(warnings)),
    }


def print_human(data: dict[str, Any]) -> None:
    print(f"Root: {data['root']}")
    print(f"Host: {data['host']['system']} {data['host']['machine']}")
    print(f"Swift/config files: {data['swift_files_scanned']} / {data['config_files_scanned']}")
    print(f"Usage keys: {', '.join(data['usage_description_keys']) or 'none detected'}")
    print(f"Background modes: {', '.join(data['background_modes']) or 'none detected'}")
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
