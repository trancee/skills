#!/usr/bin/env python3
"""Review captured xcodebuild -showBuildSettings -json without executing commands."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

MAX_BYTES = 8 * 1024 * 1024
UNRESOLVED = re.compile(r"\$\([^)]*\)|\$\{[^}]*\}")
BUNDLE_TYPES = {
    "com.apple.product-type.application",
    "com.apple.product-type.app-extension",
    "com.apple.product-type.application.on-demand-install-capable",
    "com.apple.product-type.application.watchapp2",
    "com.apple.product-type.watchkit2-extension",
}


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key; regenerate an unambiguous settings capture")
        result[key] = value
    return result


def load(path: str) -> list[dict[str, object]]:
    if path == "-":
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
    else:
        with Path(path).open("rb") as source:
            raw = source.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("settings capture exceeds 8 MiB; select a narrower scheme/target")
    data = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    if not isinstance(data, list) or not data:
        raise ValueError("expected a nonempty xcodebuild settings array, not a project-list or export plist")
    if len(data) > 1000:
        raise ValueError("more than 1000 target rows; narrow the settings capture")
    for row in data:
        if not isinstance(row, dict) or not isinstance(row.get("target"), str) or not row["target"]:
            raise ValueError("every row requires a nonempty target string")
        settings = row.get("buildSettings")
        if not isinstance(settings, dict):
            raise ValueError("every target requires a buildSettings object")
        if any(not isinstance(value, str) for value in settings.values()):
            raise ValueError("buildSettings values must be strings; capture actual -showBuildSettings -json output")
    return data


def inspect(rows: list[dict[str, object]], selected: list[str], expected_team: str | None) -> dict[str, object]:
    reports: list[dict[str, object]] = []
    issues: list[dict[str, str]] = []
    bundles: dict[str, str] = {}
    teams: set[str] = set()

    def issue(level: str, code: str, target: str, message: str) -> None:
        issues.append({"severity": level, "code": code, "target": target, "message": message})

    known = {str(row["target"]) for row in rows}
    for target in sorted(set(selected) - known):
        issue("error", "TARGET_NOT_FOUND", target, "requested target absent; capture its owning shared scheme")

    for row in rows:
        target = str(row["target"])
        if selected and target not in selected:
            continue
        settings = row["buildSettings"]
        assert isinstance(settings, dict)
        wrapper = str(settings.get("WRAPPER_EXTENSION", ""))
        product = str(settings.get("PRODUCT_TYPE", ""))
        is_bundle = wrapper in {"app", "appex"} or product in BUNDLE_TYPES
        if not is_bundle:
            continue
        platform = str(settings.get("PLATFORM_NAME", ""))
        sdk = str(settings.get("SDK_NAME", settings.get("SDKROOT", "")))
        device_platform = platform in {"iphoneos", "watchos"}
        if not platform:
            device_platform = bool(re.search(r"(?:^|/)(?:iphoneos|watchos)(?:[0-9.]|$)", sdk.lower()))
        team = str(settings.get("DEVELOPMENT_TEAM", ""))
        bundle = str(settings.get("PRODUCT_BUNDLE_IDENTIFIER", ""))
        style = str(settings.get("CODE_SIGN_STYLE", ""))
        profile = str(settings.get("PROVISIONING_PROFILE_SPECIFIER", "") or settings.get("PROVISIONING_PROFILE", ""))
        allowed = str(settings.get("CODE_SIGNING_ALLOWED", ""))
        required = str(settings.get("CODE_SIGNING_REQUIRED", ""))
        identity = str(settings.get("CODE_SIGN_IDENTITY", ""))
        reports.append({
            "target": target, "wrapper": wrapper, "platform": platform,
            "bundle_id": bundle, "team_id": team, "signing_style": style,
            "signing_allowed": allowed, "profile_selected": bool(profile),
            "identity_selected": bool(identity),
        })
        if not device_platform:
            issue("error", "NOT_DEVICE_PLATFORM", target, "device archive expected; simulator/macOS settings do not prove physical-device signing")
        if allowed == "NO" or required == "NO":
            issue("error", "SIGNING_DISABLED", target, "signing disabled for an app/extension; fix the owning target, not the verification gate")
        elif allowed != "YES":
            issue("warning", "SIGNING_FLAG_UNRESOLVED", target, "signing flag is not resolved YES/NO")
        if not team or UNRESOLVED.search(team):
            issue("error", "TEAM_UNRESOLVED", target, "device signing requires an explicit resolved team")
        else:
            teams.add(team)
            if expected_team and team != expected_team:
                issue("error", "TEAM_MISMATCH", target, "target does not use the requested team")
        if not bundle or UNRESOLVED.search(bundle):
            issue("error", "BUNDLE_ID_UNRESOLVED", target, "bundle ID missing/unresolved; provisioning cannot be matched")
        elif bundle in bundles:
            issue("error", "DUPLICATE_BUNDLE_ID", target, "multiple executable targets share a bundle ID; review app/extension mapping")
        else:
            bundles[bundle] = target
        if style == "Manual":
            if not profile or UNRESOLVED.search(profile):
                issue("error", "MANUAL_PROFILE_UNRESOLVED", target, "manual signing requires a target-specific resolved profile")
            if not identity or UNRESOLVED.search(identity):
                issue("error", "MANUAL_IDENTITY_UNRESOLVED", target, "manual signing identity missing/unresolved; inspect effective target settings")
        elif style == "Automatic":
            if profile:
                issue("warning", "AUTOMATIC_PROFILE_OVERRIDE", target, "automatic style has an explicit profile; inspect conflicting target overrides")
        else:
            issue("warning", "SIGNING_STYLE_UNKNOWN", target, "signing style missing/unknown; inspect effective target configuration")
    if not reports:
        issue("error", "NO_EXECUTABLE_BUNDLES", "", "no selected app/appex rows; capture the intended device scheme and wrapper settings")
    if len(teams) > 1:
        issue("warning", "MULTIPLE_TEAMS", "", "multiple teams across executable bundles; verify the distribution contract")
    issues.sort(key=lambda item: (item["severity"], item["target"], item["code"]))
    reports.sort(key=lambda item: str(item["target"]))
    return {
        "valid": not any(item["severity"] == "error" for item in issues),
        "targets": reports, "issues": issues,
        "limits": ["Captured settings only: no keychain/private-key/trust/profile-content/signature/build verification."],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="captured settings JSON file, or - for stdin")
    parser.add_argument("--target", action="append", default=[], help="target name to inspect; repeatable")
    parser.add_argument("--team-id", help="expected team for all selected executable bundles")
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON with allowlisted fields only")
    parser.add_argument("--strict", action="store_true", help="exit 1 for warnings as well as errors")
    args = parser.parse_args()
    try:
        report = inspect(load(args.path), args.target, args.team_id)
    except (OSError, UnicodeError, ValueError, RecursionError):
        print("error: cannot read a valid bounded UTF-8 xcodebuild settings array; verify path, JSON shape/types, duplicate keys, and input size", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Signing settings: {len(report['targets'])} executable bundle target(s); valid={report['valid']}")
        for item in report["issues"]:
            print(f"{item['severity'].upper()} [{item['code']}] {json.dumps(item['target'])}: {item['message']}")
        print(report["limits"][0])
    return 1 if not report["valid"] or (args.strict and report["issues"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
