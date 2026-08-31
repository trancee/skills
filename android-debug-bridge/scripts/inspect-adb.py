#!/usr/bin/env python3
"""Inspect adb executable, host server, and attached transports without mutating devices."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adb", default="adb", help="adb executable name or path (default: adb on PATH)")
    parser.add_argument("--timeout", type=float, default=5.0, help="per-command timeout seconds (default: 5)")
    parser.add_argument("--mdns", action="store_true", help="also inspect mDNS availability and discovered services")
    parser.add_argument("--show-serials", action="store_true", help="include raw device serials instead of stable hashes")
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    return parser.parse_args()


def resolve_adb(value: str) -> Path | None:
    candidate = Path(value).expanduser()
    if candidate.parent != Path(".") or candidate.is_absolute():
        return candidate.resolve() if candidate.is_file() else None
    found = shutil.which(value)
    return Path(found).resolve() if found else None


def run(adb: Path, args: list[str], timeout: float) -> dict[str, Any]:
    command = [str(adb), *args]
    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout)
        return {"args": args, "returncode": completed.returncode, "stdout": completed.stdout.strip(), "stderr": completed.stderr.strip(), "timed_out": False}
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout.decode(errors="replace") if isinstance(error.stdout, bytes) else (error.stdout or "")
        stderr = error.stderr.decode(errors="replace") if isinstance(error.stderr, bytes) else (error.stderr or "")
        return {"args": args, "returncode": None, "stdout": stdout.strip(), "stderr": stderr.strip(), "timed_out": True}


def parse_version(text: str) -> dict[str, Any]:
    protocol = re.search(r"Android Debug Bridge version\s+([^\s]+)", text)
    package = re.search(r"^Version\s+([^\s]+)", text, re.MULTILINE)
    installed = re.search(r"^Installed as\s+(.+)$", text, re.MULTILINE)
    package_value = package.group(1) if package else None
    numeric = re.match(r"(\d+)\.(\d+)\.(\d+)", package_value or "")
    return {
        "protocol": protocol.group(1) if protocol else None,
        "package": package_value,
        "numeric": [int(numeric.group(index)) for index in range(1, 4)] if numeric else None,
        "reported_executable": installed.group(1).strip() if installed else None,
    }


def parse_server_status(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not re.fullmatch(r"[a-z_]+", key):
            continue
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        elif value in {"true", "false"}:
            value = value == "true"
        result[key] = value
    return result


def serial_label(serial: str, show: bool) -> str:
    if show:
        return serial
    return "sha256:" + hashlib.sha256(serial.encode()).hexdigest()[:12]


def parse_devices(text: str, show_serials: bool) -> list[dict[str, Any]]:
    devices: list[dict[str, Any]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("List of devices attached") or stripped.startswith("*"):
            continue
        parts = stripped.split()
        if len(parts) < 2:
            continue
        serial, state = parts[0], parts[1]
        properties: dict[str, str] = {}
        notes: list[str] = []
        for item in parts[2:]:
            if ":" in item:
                key, value = item.split(":", 1)
                properties[key] = value
            else:
                notes.append(item)
        if serial.startswith("emulator-"):
            transport = "emulator"
        elif re.search(r":\d+$", serial) or serial.endswith(".local"):
            transport = "network"
        else:
            transport = "usb-or-other"
        devices.append({"serial": serial_label(serial, show_serials), "state": state, "transport": transport, "properties": properties, "notes": notes})
    return sorted(devices, key=lambda item: (item["serial"], item["state"]))


def inspect(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    adb = resolve_adb(args.adb)
    if adb is None:
        message = f"adb executable not found: {args.adb!r}; install Android SDK Platform-Tools or pass --adb /path/to/adb"
        return {"error": message, "requested_adb": args.adb}, 2
    version_command = run(adb, ["version"], args.timeout)
    if version_command["returncode"] != 0 or version_command["timed_out"]:
        message = "adb version failed" + (" (timed out)" if version_command["timed_out"] else f" with exit {version_command['returncode']}")
        return {"error": message, "adb": str(adb), "version_command": version_command}, 3
    version = parse_version(version_command["stdout"])
    server_command = run(adb, ["server-status"], args.timeout)
    device_command = run(adb, ["devices", "-l"], args.timeout)
    devices = parse_devices(device_command["stdout"], args.show_serials) if device_command["returncode"] == 0 else []
    server_status = parse_server_status(server_command["stdout"]) if server_command["returncode"] == 0 else {}
    mdns_commands: list[dict[str, Any]] = []
    if args.mdns:
        mdns_commands = [run(adb, ["mdns", "check"], args.timeout), run(adb, ["mdns", "services"], args.timeout)]
    warnings: list[str] = []
    numeric = version["numeric"]
    if numeric is not None and tuple(numeric) < (37, 0, 1):
        warnings.append("adb is older than current Platform-Tools 37.0.1; update before diagnosing current USB/mDNS/Wi-Fi behavior.")
    if server_command["returncode"] != 0 or server_command["timed_out"]:
        warnings.append("adb server-status is unavailable or failed; inspect server version/path/backend with the installed adb help and logs.")
    chosen = str(adb)
    server_executable = server_status.get("executable_absolute_path")
    if server_executable and os.path.realpath(str(server_executable)) != os.path.realpath(chosen):
        warnings.append("Running adb server executable differs from the selected adb client; restart deliberately after resolving PATH/version ownership.")
    if server_status.get("mdns_enabled") is False:
        warnings.append("adb server reports mDNS disabled; secure wireless auto-discovery will not work.")
    backend = str(server_status.get("mdns_backend", ""))
    if backend and backend != "LIBADBMDNS" and numeric is not None and tuple(numeric) >= (37, 0, 1):
        warnings.append("adb 37.0.1+ should use LIBADBMDNS; openscreen was removed from current Platform-Tools.")
    if device_command["returncode"] != 0 or device_command["timed_out"]:
        warnings.append("adb devices -l failed or timed out; resolve host server/transport before device commands.")
    elif not devices:
        warnings.append("No adb devices are attached.")
    if len(devices) > 1:
        warnings.append("Multiple adb devices are attached; bind every command with -s SERIAL or -t TRANSPORT_ID.")
    states = {device["state"] for device in devices}
    if "unauthorized" in states:
        warnings.append("At least one device is unauthorized; unlock it and approve the workstation RSA fingerprint.")
    if "offline" in states:
        warnings.append("At least one device is offline; distinguish boot, USB, and wireless transport before reconnecting.")
    if args.mdns:
        for command in mdns_commands:
            if command["returncode"] != 0 or command["timed_out"]:
                warnings.append("An adb mDNS inspection command failed or timed out; inspect server-status, network multicast/firewall, and Wireless debugging.")
                break
    data = {
        "host": {"system": platform.system(), "release": platform.release(), "machine": platform.machine()},
        "adb": str(adb), "version": version, "server_status": server_status, "devices": devices,
        "commands": {"version": version_command, "server_status": server_command, "devices": device_command, "mdns": mdns_commands},
        "serials_redacted": not args.show_serials, "warnings": sorted(set(warnings)),
    }
    return data, 0


def print_human(data: dict[str, Any]) -> None:
    if "error" in data:
        print(f"Error: {data['error']}")
        return
    print(f"ADB: {data['adb']}")
    print(f"Version: {data['version']['package'] or 'unparsed'}")
    print(f"Devices: {len(data['devices'])}")
    for device in data["devices"]:
        print(f"- {device['serial']} {device['state']} {device['transport']}")
    if data["warnings"]:
        print("Warnings:")
        for warning in data["warnings"]:
            print(f"- {warning}")


def main() -> int:
    args = parse_args()
    if args.timeout <= 0:
        print("error: --timeout must be greater than zero", file=sys.stderr)
        return 2
    data, code = inspect(args)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print_human(data)
    if code and "error" in data:
        print(data["error"], file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
