#!/usr/bin/env python3
"""Find legacy iOS support candidates in two GitHub inventories; never install.

With no identity arguments, query one USB device using libimobiledevice.
No automatic pairing, mounting, archive execution, or Xcode modification.
Exit 0: exact-label candidates; 3: manual review/no match/modern iOS;
2: invalid input, device query failure, or incomplete repository inventory.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import plistlib
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from xml.parsers.expat import ExpatError


SOURCES = {"filsv": ("filsv/iOSDeviceSupport", ""),
           "ighibli": ("iGhibli/iOS-DeviceSupport", "DeviceSupport/")}
VERSION = re.compile(r"[0-9]{1,2}\.[0-9]{1,2}(?:\.[0-9]{1,2})?")
BUILD = re.compile(r"[0-9]{1,3}[A-Z][0-9]+[a-z]?")
LABEL = re.compile(r"(?P<version>[0-9]{1,2}\.[0-9]{1,2}(?:\.[0-9]{1,2})?)(?P<suffix>.*)")
SHA = re.compile(r"[0-9a-f]{40}")


def version_key(value: str) -> tuple[int, int, int]:
    parts = [int(part) for part in value.split(".")]
    return tuple((parts + [0, 0, 0])[:3])


def get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "ios-device-support-lookup",
                                                 "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read(4 * 1024 * 1024 + 1)
    if len(data) > 4 * 1024 * 1024:
        raise ValueError("GitHub response exceeds the inventory limit")
    result = json.loads(data)
    if not isinstance(result, dict):
        raise ValueError("GitHub returned an unexpected response")
    return result


def inventory(source: str, ref: str) -> tuple[str, list[dict]]:
    repo, _ = SOURCES[source]
    revision = ref if SHA.fullmatch(ref) else get_json(
        f"https://api.github.com/repos/{repo}/commits/{urllib.parse.quote(ref, safe='')}"
    ).get("sha", "")
    if not SHA.fullmatch(revision):
        raise ValueError(f"{source}: unable to resolve an immutable commit")
    tree = get_json(f"https://api.github.com/repos/{repo}/git/trees/{revision}?recursive=1")
    if tree.get("truncated") is not False or not isinstance(tree.get("tree"), list):
        raise ValueError(f"{source}: incomplete GitHub tree; no selection inferred")
    entries = tree["tree"]
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise ValueError(f"{source}: invalid inventory entry")
        if entry.get("type") == "blob" and (
            not SHA.fullmatch(entry.get("sha", ""))
            or not isinstance(entry.get("size"), int) or entry["size"] < 0
        ):
            raise ValueError(f"{source}: invalid blob metadata")
    return revision, entries


def candidates(source: str, revision: str, entries: list[dict]) -> list[dict]:
    repo, prefix = SOURCES[source]
    blobs = {entry["path"]: entry for entry in entries
             if entry.get("type") == "blob" and entry.get("mode") in {"100644", "100755"}}
    packages: dict[str, list[str]] = {}
    for path in sorted(blobs):
        relative = path.removeprefix(prefix) if path.startswith(prefix) else ""
        if relative.endswith(".zip") and "/" not in relative:
            packages[relative[:-4]] = [path]
    if not prefix:
        for path in sorted(blobs):
            if path.count("/") == 1 and path.endswith("/DeveloperDiskImage.dmg"):
                label = path.split("/")[0]
                signature = path + ".signature"
                if signature in blobs and blobs[path]["size"] and blobs[signature]["size"]:
                    packages.setdefault(label, [path, signature])
    result = []
    for label, paths in packages.items():
        match = LABEL.fullmatch(label)
        if not match:
            continue
        suffix = match["suffix"].strip()
        build = suffix[1:-1] if suffix.startswith("(") and suffix.endswith(")") else ""
        label_build = build if BUILD.fullmatch(build) else None
        result.append({"source": source, "repository": repo, "revision": revision,
                       "label": label, "iosVersion": match["version"], "labelBuild": label_build,
                       "annotation": suffix if suffix and not label_build else None,
                       "artifacts": [{"path": path, "size": blobs[path]["size"],
                                      "gitBlobSHA1": blobs[path]["sha"],
                                      "url": f"https://raw.githubusercontent.com/{repo}/{revision}/"
                                             + urllib.parse.quote(path, safe="/")}
                                     for path in paths]})
    return result


def choose(items: list[dict], version: str, build: str) -> tuple[str, list[dict], list[dict]]:
    exact, review = [], []
    beta_build = build[-1].islower()
    for item in items:
        same = version_key(item["iosVersion"]) == version_key(version)
        same_minor = version_key(item["iosVersion"])[:2] == version_key(version)[:2]
        if same and item["labelBuild"] == build:
            exact.append({**item, "match": "exact-version-and-build-label", "rank": 0})
        elif same and not item["labelBuild"] and not item["annotation"] and not beta_build:
            exact.append({**item, "match": "exact-version-label-build-unverified", "rank": 1})
        elif same and item["annotation"]:
            review.append({**item, "reason": "Xcode/provenance annotation is not an iOS build match"})
        elif same and not item["labelBuild"] and beta_build:
            review.append({**item, "reason": "prerelease-looking device build needs explicit build evidence"})
        elif same_minor and not same and not item["labelBuild"] and not item["annotation"]:
            review.append({**item, "reason": "different patch version; compatibility unverified"})
    if exact:
        best = min(item["rank"] for item in exact)
        return "candidates-found", [item for item in exact if item["rank"] == best], review
    return ("review-required" if review else "no-match"), [], review


def query_device(udid: str | None) -> dict:
    if not udid:
        result = subprocess.run(["idevice_id", "-l"], capture_output=True, text=True, timeout=15)
        if result.returncode:
            raise ValueError("USB enumeration failed; check usbmuxd/connection or use --device-plist")
        devices = list(dict.fromkeys(result.stdout.split()))
        if len(devices) != 1:
            raise ValueError(f"found {len(devices)} USB devices; connect one or supply --udid explicitly")
        udid = devices[0]
    if not re.fullmatch(r"[A-Za-z0-9-]{8,80}", udid):
        raise ValueError("invalid UDID format")
    result = subprocess.run(["ideviceinfo", "-s", "-u", udid, "-x"], capture_output=True, timeout=15)
    if result.returncode:
        raise ValueError("device query failed; check unlock/trust/pairing manually; no pairing attempted")
    return plistlib.loads(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    identity = parser.add_mutually_exclusive_group()
    identity.add_argument("--udid", help="USB device to query; omitted means require exactly one")
    identity.add_argument("--device-plist", type=Path, help="saved ideviceinfo -x plist; no device query")
    identity.add_argument("--ios-version", help="explicit numeric ProductVersion, with --build-version")
    parser.add_argument("--build-version", help="exact iOS BuildVersion; not an Xcode build")
    parser.add_argument("--source", choices=["all", *SOURCES], default="all")
    parser.add_argument("--filsv-ref", default="master", help="commit or ref to resolve for filsv")
    parser.add_argument("--ighibli-ref", default="master", help="commit or ref to resolve for iGhibli")
    args = parser.parse_args()
    if bool(args.ios_version) != bool(args.build_version):
        parser.error("--ios-version and --build-version must be supplied together")
    try:
        if args.ios_version:
            version, build = args.ios_version, args.build_version
        else:
            data = plistlib.loads(args.device_plist.read_bytes()) if args.device_plist else query_device(args.udid)
            if not isinstance(data, dict):
                raise ValueError("device plist must contain an information dictionary")
            version, build = data.get("ProductVersion"), data.get("BuildVersion")
            product = data.get("ProductType", "iPhone")
            if not isinstance(product, str) or not product.startswith(("iPhone", "iPad", "iPod")):
                raise ValueError("device is not an iOS/iPadOS device")
        if not isinstance(version, str) or not VERSION.fullmatch(version):
            raise ValueError("ProductVersion must be numeric major.minor[.patch]")
        if not isinstance(build, str) or not BUILD.fullmatch(build):
            raise ValueError("BuildVersion missing/invalid; read the actual device build, not a marketing version")
        report = {"iosVersion": version, "buildVersion": build, "sources": {},
                  "status": "modern-personalized-route", "candidates": [], "reviewCandidates": [],
                  "limits": ["Filename/inventory matches are not verified payload or Xcode compatibility.",
                             "No install, pairing, image mount, Xcode or device mutation performed."]}
        if version_key(version)[0] >= 17:
            report["limits"].append("iOS 17+ requires the supported Xcode/CoreDevice personalized-image route; no legacy zip selected.")
        else:
            items = []
            for source in SOURCES if args.source == "all" else [args.source]:
                revision, entries = inventory(source, getattr(args, source + "_ref"))
                report["sources"][source] = revision
                items.extend(candidates(source, revision, entries))
            report["status"], report["candidates"], report["reviewCandidates"] = choose(items, version, build)
            report["limits"].append("Both sources must be fully inventoried when --source all; no silent partial lookup.")
        print(json.dumps(report, indent=2))
        return 0 if report["status"] == "candidates-found" else 3
    except (OSError, ValueError, TypeError, plistlib.InvalidFileException, ExpatError,
            subprocess.TimeoutExpired, urllib.error.URLError) as error:
        print(f"ERROR: support lookup unavailable: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
