#!/usr/bin/env python3
"""Inspect Android BluetoothSocket projects for API, lifecycle, and stream hazards."""

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
SOCKET_CREATORS = (
    "listenUsingRfcommWithServiceRecord", "listenUsingInsecureRfcommWithServiceRecord",
    "createRfcommSocketToServiceRecord", "createInsecureRfcommSocketToServiceRecord",
    "listenUsingL2capChannel", "listenUsingInsecureL2capChannel",
    "createL2capChannel", "createInsecureL2capChannel",
    "listenUsingSocketSettings", "createUsingSocketSettings",
)
SIGNALS = {
    "socket_type": r"\bBluetoothSocket\b",
    "server_socket_type": r"\bBluetoothServerSocket\b",
    "settings": r"\bBluetoothSocketSettings(?:\.Builder)?\b",
    "settings_type": r"\.setSocketType\s*\(",
    "settings_rfcomm": r"\.setSocketType\s*\(\s*BluetoothSocket\.TYPE_RFCOMM",
    "settings_le": r"\.setSocketType\s*\(\s*BluetoothSocket\.TYPE_LE",
    "settings_uuid": r"\.setRfcommUuid\s*\(",
    "settings_name": r"\.setRfcommServiceName\s*\(",
    "settings_psm": r"\.setL2capPsm\s*\(",
    "settings_auth": r"\.setAuthenticationRequired\s*\(",
    "settings_encryption": r"\.setEncryptionRequired\s*\(",
    "secure_rfcomm_server": r"(?<!Insecure)listenUsingRfcommWithServiceRecord\s*\(",
    "secure_rfcomm_client": r"(?<!Insecure)createRfcommSocketToServiceRecord\s*\(",
    "insecure_rfcomm": r"(?:listenUsing|create)InsecureRfcomm",
    "secure_l2cap_server": r"(?<!Insecure)listenUsingL2capChannel\s*\(",
    "secure_l2cap_client": r"(?<!Insecure)createL2capChannel\s*\(",
    "insecure_l2cap": r"(?:listenUsing|create)InsecureL2capChannel",
    "settings_server": r"\.listenUsingSocketSettings\s*\(",
    "settings_client": r"\.createUsingSocketSettings\s*\(",
    "accept": r"\.accept\s*\(",
    "accept_timeout": r"\.accept\s*\(\s*[^)]",
    "connect": r"\.connect\s*\(\s*\)",
    "cancel_discovery": r"\.cancelDiscovery\s*\(",
    "get_psm": r"\.getPsm\s*\(\)|\.psm\b",
    "input_stream": r"\.(?:getInputStream\s*\(\)|inputStream\b)",
    "output_stream": r"\.(?:getOutputStream\s*\(\)|outputStream\b)",
    "read": r"\.read\s*\(",
    "read_assignment": r"(?:\b(?:val|var|int)\s+\w+\s*=|\b\w+\s*=)\s*[^\n]*\.read\s*\(",
    "eof": r"(?:==|<=)\s*-1\b|<\s*0\b",
    "read_copy": r"\.copyOf(?:Range)?\s*\(|Arrays\.copyOf\s*\(|ByteArray\s*\(\s*(?:count|length|numBytes|bytesRead)",
    "whole_buffer_handoff": r"(?:send|emit|offer|post|obtainMessage|onBytes|onData)\s*\([^\n]*(?:buffer|mmBuffer)\b",
    "write": r"\.write\s*\(",
    "write_serializer": r"\b(?:Mutex|ReentrantLock|synchronized|writeMutex|writerChannel|writeChannel|writerActor)\b",
    "framing": r"\b(?:DataInputStream|ByteBuffer|frameLength|lengthPrefix|FrameDecoder|delimiter|messageLength|readInt)\b",
    "close": r"\.close\s*\(",
    "socket_close": r"\b(?:socket|clientSocket|connectedSocket|mmSocket)\??\.close\s*\(",
    "server_close": r"(?:serverSocket|ServerSocket|mmServerSocket)\??\.close\s*\(",
    "io_execution": r"Dispatchers\.IO|\bThread\s*\(|:\s*Thread\s*\(|\bExecutor(?:Service)?\b|newSingleThreadExecutor|newFixedThreadPool",
    "coroutine": r"\b(?:suspend\s+fun|CoroutineScope|launch\s*\{|async\s*\{|withContext)\b",
    "timeout": r"\bwithTimeout(?:OrNull)?\s*\(",
    "cancel_close": r"invokeOnCancellation[^\n]*(?:close|cancel)|(?:close|cancel)[^\n]*Cancellation",
    "global_scope": r"\bGlobalScope\b",
    "unbounded_channel": r"Channel\.UNLIMITED|LinkedBlockingQueue\s*<[^>]+>\s*\(\s*\)",
    "bounded_channel": r"Channel\s*<[^>]+>\s*\(\s*(?:[1-9]\d*|Channel\.RENDEZVOUS|Channel\.BUFFERED)|ArrayBlockingQueue",
    "io_exception": r"\bIOException\b",
    "socket_exception": r"\bBluetoothSocketException\b",
    "socket_error_code": r"\.errorCode\b|\.getErrorCode\s*\(",
    "packet_size": r"\.getMax(?:Receive|Transmit)PacketSize\s*\(\)|\.max(?:Receive|Transmit)PacketSize\b",
    "is_connected": r"\.isConnected\b|\.isConnected\s*\(",
    "foreground_service": r"\b(?:startForeground|startForegroundService)\s*\(",
    "sdk_guard_36": r"SDK_INT\s*>=\s*(?:36|Build\.VERSION_CODES\.BAKLAVA)|VERSION_CODES\.BAKLAVA",
}
COMPILED = {name: re.compile(pattern) for name, pattern in SIGNALS.items()}


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


def inspect_build(path: Path, root: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    values = lambda pattern: sorted({int(item) for item in re.findall(pattern, text)})
    return {
        "file": rel(path, root),
        "min_sdk": values(r"\bminSdk(?:Version)?\s*(?:=|\()?\s*(\d+)"),
        "compile_sdk": values(r"\bcompileSdk(?:Version)?\s*(?:=|\()?\s*(\d+)"),
        "target_sdk": values(r"\btargetSdk(?:Version)?\s*(?:=|\()?\s*(\d+)"),
    }


def inspect_manifest(path: Path, root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"file": rel(path, root), "permissions": [], "features": [], "service_types": [], "parse_error": None}
    try:
        tree = ET.parse(path)
        root_node = tree.getroot()
        result["permissions"] = sorted({node.attrib.get(ANDROID_NS + "name", "") for node in root_node.findall("uses-permission") if node.attrib.get(ANDROID_NS + "name")})
        result["features"] = sorted({node.attrib.get(ANDROID_NS + "name", "") for node in root_node.findall("uses-feature") if node.attrib.get(ANDROID_NS + "name")})
        result["service_types"] = sorted({part for node in root_node.findall(".//service") for part in node.attrib.get(ANDROID_NS + "foregroundServiceType", "").split("|") if part})
    except ET.ParseError as error:
        result["parse_error"] = str(error)
    return result


def inspect_source(path: Path, root: Path) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    creators = {name: line_numbers(text, re.compile(rf"\b{name}\s*\(")) for name in SOCKET_CREATORS}
    creators = {name: lines for name, lines in creators.items() if lines}
    signals = {name: lines for name, pattern in COMPILED.items() if (lines := line_numbers(text, pattern))}
    accepted_names = set(re.findall(r"(?:\b(?:val|var)\s+(\w+)(?:\s*:\s*BluetoothSocket\??)?|\bBluetoothSocket\s+(\w+))\s*=\s*[^\n;]*\.accept\s*\(", text))
    accepted_connect_lines = sorted({line for pair in accepted_names for name in pair if name for line in line_numbers(text, re.compile(rf"\b{re.escape(name)}\.connect\s*\(\s*\)"))})
    if not creators and not signals and not accepted_connect_lines:
        return None
    return {"file": rel(path, root), "creators": creators, "signals": signals, "accepted_socket_connect_lines": accepted_connect_lines}


def maximum(values: list[int]) -> int | None:
    return max(values) if values else None


def minimum(values: list[int]) -> int | None:
    return min(values) if values else None


def inspect(root: Path) -> dict[str, Any]:
    build_files, manifest_files, source_files = project_files(root)
    builds = [inspect_build(path, root) for path in build_files]
    manifests = [inspect_manifest(path, root) for path in manifest_files]
    sources = [entry for path in source_files if (entry := inspect_source(path, root))]
    signals = {name for entry in sources for name in entry["signals"]}
    creators = {name for entry in sources for name in entry["creators"]}
    permissions = {permission for manifest in manifests for permission in manifest["permissions"]}
    service_types = {item for manifest in manifests for item in manifest["service_types"]}
    compile_sdk = maximum([value for build in builds for value in build["compile_sdk"]])
    target_sdk = maximum([value for build in builds for value in build["target_sdk"]])
    min_sdk = minimum([value for build in builds for value in build["min_sdk"]])
    warnings: list[str] = []
    socket_use = bool(creators or {"socket_type", "server_socket_type"}.intersection(signals))
    if socket_use and (target_sdk or 0) >= 31 and "android.permission.BLUETOOTH_CONNECT" not in permissions:
        warnings.append("Bluetooth socket use targets API 31+ without BLUETOOTH_CONNECT in detected manifests.")
    if "cancel_discovery" in signals and (target_sdk or 0) >= 31 and "android.permission.BLUETOOTH_SCAN" not in permissions:
        warnings.append("cancelDiscovery targets API 31+ without BLUETOOTH_SCAN in detected manifests.")
    if "connect" in signals and "cancel_discovery" not in signals:
        warnings.append("BluetoothSocket.connect found without cancelDiscovery candidate; adapter discovery substantially slows connections.")
    if any(entry["accepted_socket_connect_lines"] for entry in sources):
        warnings.append("connect() called on a socket returned by accept(); accepted BluetoothSocket instances are already connected.")
    if {"accept", "connect", "read", "write"}.intersection(signals) and "io_execution" not in signals:
        warnings.append("Blocking Bluetooth socket call found without dedicated I/O thread/dispatcher/executor candidate.")
    if "accept" in signals and "server_close" not in signals:
        warnings.append("BluetoothServerSocket.accept found without listening-socket close cancellation candidate.")
    if socket_use and {"connect", "accept", "read", "write"}.intersection(signals) and "socket_close" not in signals:
        warnings.append("Connected Bluetooth socket work found without connected-socket close candidate.")
    if "read" in signals and "read_assignment" not in signals:
        warnings.append("InputStream.read result appears unused; retain the count for EOF and partial-byte handling.")
    if "read" in signals and "eof" not in signals:
        warnings.append("Socket read found without explicit -1 EOF handling.")
    if "whole_buffer_handoff" in signals and "read_copy" not in signals:
        warnings.append("Reusable read buffer appears handed off without copying the valid byte range.")
    if "read" in signals and "framing" not in signals:
        warnings.append("Socket byte reads found without a framing/decoder candidate; read boundaries are not message boundaries.")
    if "write" in signals and "write_serializer" not in signals:
        warnings.append("Socket writes found without a single writer/lock/channel candidate; concurrent frame bytes can interleave.")
    if "unbounded_channel" in signals:
        warnings.append("Unbounded socket queue candidate found; bound frames/bytes and define overflow/backpressure.")
    if "global_scope" in signals:
        warnings.append("GlobalScope found in socket ownership; use a lifecycle-owned parent and close sockets on cancellation.")
    if "timeout" in signals and "cancel_close" not in signals:
        warnings.append("Coroutine timeout found without detected cancellation-close wiring; timeout alone does not interrupt blocking Bluetooth I/O.")
    if "settings" in signals:
        if compile_sdk is not None and compile_sdk < 36:
            warnings.append("BluetoothSocketSettings requires compile SDK 36+.")
        if min_sdk is not None and min_sdk < 36 and "sdk_guard_36" not in signals:
            warnings.append("BluetoothSocketSettings is used with min SDK below 36 without a detected SDK guard.")
        if "settings_type" not in signals:
            warnings.append("BluetoothSocketSettings relies on default socket type; set TYPE_RFCOMM or TYPE_LE explicitly.")
        if not ({"settings_auth", "settings_encryption"} <= signals):
            warnings.append("BluetoothSocketSettings lacks explicit authentication and encryption requirements; both default to false.")
        if "settings_rfcomm" in signals and "settings_uuid" not in signals:
            warnings.append("RFCOMM BluetoothSocketSettings lacks setRfcommUuid.")
        if "settings_client" in signals and "settings_le" in signals and "settings_psm" not in signals:
            warnings.append("TYPE_LE settings client lacks the server's valid setL2capPsm value.")
    if ({"insecure_rfcomm", "insecure_l2cap"} & signals):
        warnings.append("Insecure Bluetooth socket API found; document unauthenticated-link threat acceptance and application authentication.")
    if ({"listenUsingL2capChannel", "listenUsingInsecureL2capChannel"} & creators) and "get_psm" not in signals:
        warnings.append("LE CoC server found without getPsm/disclosure candidate.")
    if "socket_exception" in signals and "socket_error_code" not in signals:
        warnings.append("BluetoothSocketException caught/referenced without errorCode-based classification candidate.")
    if {"read", "write", "connect", "accept"}.intersection(signals) and "io_exception" not in signals:
        warnings.append("Blocking socket operations found without IOException handling candidate.")
    if "foreground_service" in signals and "connectedDevice" not in service_types:
        warnings.append("Foreground service socket lifecycle found without connectedDevice service type in detected manifests.")
    if target_sdk is not None and target_sdk >= 37 and "read" in signals and "eof" not in signals:
        warnings.append("Target-37 socket read loop lacks explicit RFCOMM -1 EOF migration handling.")
    return {
        "root": str(root), "host": {"system": platform.system(), "machine": platform.machine()},
        "build_files_scanned": len(build_files), "manifest_files_scanned": len(manifest_files), "source_files_scanned": len(source_files),
        "min_sdk": min_sdk, "compile_sdk": compile_sdk, "target_sdk": target_sdk,
        "permissions": sorted(permissions), "service_types": sorted(service_types),
        "builds": builds, "manifests": manifests, "sources": sources, "warnings": sorted(set(warnings)),
    }


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
