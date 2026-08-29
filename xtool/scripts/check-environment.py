#!/usr/bin/env python3
"""Check xtool host prerequisites and optional setup boundaries."""

from __future__ import annotations

import argparse
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(f"cannot run {' '.join(command)!r}: {error}") from error


def executable(name: str, failures: list[str]) -> str | None:
    path = shutil.which(name)
    if path is None:
        failures.append(f"required executable not found on PATH: {name}")
        return None
    print(f"PASS: {name}={path}")
    return path


def version_tuple(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.split("."))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check xtool, Swift, host tools, authentication, and Darwin SDK setup without printing credentials."
    )
    parser.add_argument("--min-swift", help="minimum Swift version, for example 6.3")
    parser.add_argument("--require-auth", action="store_true", help="require xtool Apple authentication")
    parser.add_argument("--require-sdk", action="store_true", help="require xtool and Swift to report the Darwin SDK")
    parser.add_argument(
        "--require-device-tools",
        action="store_true",
        help="require Linux usbmuxd or the macOS iOS SDK toolchain",
    )
    parser.add_argument("--xcode-xip", type=Path, help="verify a Linux/WSL Xcode.xip input path")
    args = parser.parse_args()

    failures: list[str] = []
    warnings: list[str] = []
    system = platform.system()
    architecture = platform.machine()
    osrelease = platform.release().lower()
    is_wsl = system == "Linux" and ("microsoft" in osrelease or "wsl" in osrelease)
    host = "WSL" if is_wsl else system
    print(f"INFO: host={host} architecture={architecture}")

    xtool_path = executable("xtool", failures)
    swift_path = executable("swift", failures)

    if xtool_path is not None:
        result = run([xtool_path, "--version"])
        if result.returncode != 0:
            failures.append(f"xtool --version failed with exit {result.returncode}")
        else:
            print(f"PASS: {result.stdout.strip()}")

    if swift_path is not None:
        result = run([swift_path, "--version"])
        if result.returncode != 0:
            failures.append(f"swift --version failed with exit {result.returncode}")
        else:
            first_line = result.stdout.splitlines()[0] if result.stdout.splitlines() else ""
            print(f"PASS: {first_line}")
            match = re.search(r"Swift version (\d+(?:\.\d+)+)", result.stdout)
            if args.min_swift:
                if match is None:
                    failures.append("could not parse Swift version for --min-swift")
                else:
                    actual = version_tuple(match.group(1))
                    minimum = version_tuple(args.min_swift)
                    width = max(len(actual), len(minimum))
                    if actual + (0,) * (width - len(actual)) < minimum + (0,) * (width - len(minimum)):
                        failures.append(f"Swift {match.group(1)} is older than required {args.min_swift}")
        if system == "Linux" and Path(swift_path).resolve().is_relative_to("/usr"):
            warnings.append(
                "Swift resolves under /usr; distribution builds can omit Apple cross-target support. "
                "Prefer an official Swift.org/Swiftly toolchain and prove it with xtool dev build."
            )

    if system == "Linux":
        usbmuxd_path = shutil.which("usbmuxd")
        if usbmuxd_path:
            print(f"PASS: usbmuxd={usbmuxd_path}")
        elif args.require_device_tools:
            failures.append("usbmuxd is required for Linux/WSL device access but was not found")
        else:
            warnings.append("usbmuxd not found; physical iOS device deployment will not work")
        if is_wsl:
            warnings.append("verify USBIPD binding and attachment from Windows; this checker cannot inspect the Windows host")
    elif system == "Darwin":
        xcrun_path = shutil.which("xcrun")
        if xcrun_path:
            result = run([xcrun_path, "-sdk", "iphoneos", "-show-sdk-path"])
            if result.returncode == 0 and result.stdout.strip():
                print("PASS: macOS iPhoneOS SDK is available")
            elif args.require_device_tools:
                failures.append("xcrun could not locate the iPhoneOS SDK")
            else:
                warnings.append("xcrun could not locate the iPhoneOS SDK")
        elif args.require_device_tools:
            failures.append("xcrun is required on macOS but was not found")
    else:
        failures.append(f"unsupported host operating system: {system}")

    if args.xcode_xip is not None:
        if system != "Linux":
            warnings.append("--xcode-xip is only used by Linux/WSL setup")
        elif not args.xcode_xip.is_file() or args.xcode_xip.suffix.lower() != ".xip":
            failures.append(f"Xcode archive is not a readable .xip file: {args.xcode_xip}")
        else:
            print(f"PASS: Xcode archive={args.xcode_xip}")

    if args.require_auth and xtool_path is not None:
        result = run([xtool_path, "auth", "status"])
        if result.returncode != 0 or "logged in" not in result.stdout.lower():
            failures.append("xtool authentication is not logged in")
        else:
            print("PASS: xtool authentication is logged in (account details redacted)")

    if args.require_sdk:
        if xtool_path is not None:
            result = run([xtool_path, "sdk", "status"])
            if result.returncode != 0 or "not installed" in result.stdout.lower():
                failures.append("xtool reports that the Darwin SDK is not installed")
            else:
                print("PASS: xtool reports an installed Darwin SDK")
        if swift_path is not None:
            result = run([swift_path, "sdk", "list"])
            sdks = {line.strip() for line in result.stdout.splitlines()}
            if result.returncode != 0 or "darwin" not in sdks:
                failures.append("swift sdk list does not contain darwin")
            else:
                print("PASS: swift sdk list contains darwin")

    for warning in warnings:
        print(f"WARN: {warning}")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        print(f"FAIL: {len(failures)} environment check(s) failed", file=sys.stderr)
        return 1

    print(f"PASS: xtool environment checks completed with {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
