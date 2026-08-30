#!/usr/bin/env python3
"""Validate the logical BLE GAP/GATT/L2CAP schema used by the ble-protocol-stack skill."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")
UUID16_RE = re.compile(r"^(?:0x)?[0-9A-Fa-f]{4}$")
UUID128_RE = re.compile(r"^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$")
GAP_ROLES = {"broadcaster", "observer", "peripheral", "central"}
GATT_ROLES = {"client", "server"}
PROPERTIES = {"broadcast", "read", "write-without-response", "write", "notify", "indicate", "authenticated-signed-writes", "extended-properties"}
SECURITY = {"denied", "open", "encrypted", "authenticated", "authorized"}


class DuplicateKeyError(ValueError):
    pass


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("schema", type=Path, help="logical GATT schema JSON")
    parser.add_argument("--json", action="store_true", help="emit structured JSON")
    return parser.parse_args()


def check_keys(value: dict[str, Any], allowed: set[str], path: str, errors: list[str]) -> None:
    for key in sorted(set(value) - allowed):
        errors.append(f"{path}: unknown field {key!r}")


def require_dict(value: Any, path: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{path}: expected object")
        return {}
    return value


def require_list(value: Any, path: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{path}: expected array")
        return []
    return value


def integer(value: Any, path: str, errors: list[str], minimum: int, maximum: int) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        errors.append(f"{path}: expected integer")
        return None
    if not minimum <= value <= maximum:
        errors.append(f"{path}: expected {minimum}..{maximum}, got {value}")
    return value

def one_of(value: Any, allowed: set[str], path: str, errors: list[str]) -> str | None:
    if not isinstance(value, str) or value not in allowed:
        errors.append(f"{path}: expected one of {sorted(allowed)}")
        return None
    return value



def logical_id(value: Any, path: str, errors: list[str]) -> str | None:
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        errors.append(f"{path}: expected lowercase logical ID matching {ID_RE.pattern}")
        return None
    return value


def normalize_uuid(value: Any, namespace: Any, path: str, errors: list[str]) -> str | None:
    if not isinstance(value, str) or not (UUID16_RE.fullmatch(value) or UUID128_RE.fullmatch(value)):
        errors.append(f"{path}: expected 16-bit hex or canonical 128-bit UUID")
        return None
    normalized = value.lower().removeprefix("0x")
    if not isinstance(namespace, str) or namespace not in {"sig", "vendor"}:
        errors.append(f"{path.rsplit('.', 1)[0]}.namespace: expected 'sig' or 'vendor'")
    elif namespace == "sig" and not UUID16_RE.fullmatch(value):
        errors.append(f"{path}: SIG definitions must use their assigned 16-bit UUID in this schema")
    elif namespace == "vendor" and not UUID128_RE.fullmatch(value):
        errors.append(f"{path}: vendor definitions require a 128-bit UUID")
    return normalized


def validate_descriptor(raw: Any, path: str, errors: list[str]) -> tuple[str | None, str | None]:
    descriptor = require_dict(raw, path, errors)
    check_keys(descriptor, {"id", "uuid", "namespace", "permissions"}, path, errors)
    descriptor_id = logical_id(descriptor.get("id"), f"{path}.id", errors)
    uuid = normalize_uuid(descriptor.get("uuid"), descriptor.get("namespace"), f"{path}.uuid", errors)
    permissions = require_dict(descriptor.get("permissions"), f"{path}.permissions", errors)
    check_keys(permissions, {"read", "write"}, f"{path}.permissions", errors)
    for operation in ("read", "write"):
        one_of(permissions.get(operation), SECURITY, f"{path}.permissions.{operation}", errors)
    return descriptor_id, uuid


def validate_value(raw: Any, path: str, errors: list[str]) -> None:
    value = require_dict(raw, path, errors)
    check_keys(value, {"minBytes", "maxBytes", "encoding", "byteOrder", "unit", "version"}, path, errors)
    minimum = integer(value.get("minBytes"), f"{path}.minBytes", errors, 0, 512)
    maximum = integer(value.get("maxBytes"), f"{path}.maxBytes", errors, 0, 512)
    if minimum is not None and maximum is not None and minimum > maximum:
        errors.append(f"{path}: minBytes cannot exceed maxBytes")
    if not isinstance(value.get("encoding"), str) or not value["encoding"].strip():
        errors.append(f"{path}.encoding: expected non-empty string")
    one_of(value.get("byteOrder"), {"little", "big", "opaque"}, f"{path}.byteOrder", errors)
    if not isinstance(value.get("unit"), str) or not value["unit"].strip():
        errors.append(f"{path}.unit: expected non-empty string")
    integer(value.get("version"), f"{path}.version", errors, 1, 2**31 - 1)


def validate_characteristic(raw: Any, path: str, errors: list[str], warnings: list[str]) -> tuple[str | None, str | None]:
    characteristic = require_dict(raw, path, errors)
    check_keys(characteristic, {"id", "uuid", "namespace", "properties", "permissions", "value", "subscription", "descriptors"}, path, errors)
    char_id = logical_id(characteristic.get("id"), f"{path}.id", errors)
    uuid = normalize_uuid(characteristic.get("uuid"), characteristic.get("namespace"), f"{path}.uuid", errors)
    properties_raw = require_list(characteristic.get("properties"), f"{path}.properties", errors)
    properties = set()
    for index, item in enumerate(properties_raw):
        selected = one_of(item, PROPERTIES, f"{path}.properties[{index}]", errors)
        if selected:
            properties.add(selected)
    if len(properties_raw) != len({item for item in properties_raw if isinstance(item, str)}):
        errors.append(f"{path}.properties: duplicates are not allowed")
    permissions = require_dict(characteristic.get("permissions"), f"{path}.permissions", errors)
    check_keys(permissions, {"read", "write"}, f"{path}.permissions", errors)
    for operation in ("read", "write"):
        one_of(permissions.get(operation), SECURITY, f"{path}.permissions.{operation}", errors)
    if "read" in properties and permissions.get("read") == "denied":
        errors.append(f"{path}: read property conflicts with denied read permission")
    if "read" not in properties and permissions.get("read") not in {None, "denied"}:
        errors.append(f"{path}: readable permission requires read property")
    write_properties = properties & {"write", "write-without-response", "authenticated-signed-writes"}
    if write_properties and permissions.get("write") == "denied":
        errors.append(f"{path}: write property conflicts with denied write permission")
    if not write_properties and permissions.get("write") not in {None, "denied"}:
        errors.append(f"{path}: writable permission requires a write property")
    validate_value(characteristic.get("value"), f"{path}.value", errors)
    descriptor_items = require_list(characteristic.get("descriptors", []), f"{path}.descriptors", errors)
    descriptor_records = [validate_descriptor(item, f"{path}.descriptors[{index}]", errors) for index, item in enumerate(descriptor_items)]
    descriptor_ids = [item[0] for item in descriptor_records if item[0]]
    descriptor_uuids = [item[1] for item in descriptor_records if item[1]]
    if len(descriptor_ids) != len(set(descriptor_ids)):
        errors.append(f"{path}: duplicate descriptor logical id")
    if descriptor_uuids.count("2902") > 1:
        errors.append(f"{path}: only one CCCD (0x2902) is allowed")
    if descriptor_uuids.count("2900") > 1:
        errors.append(f"{path}: only one Extended Properties descriptor (0x2900) is allowed")
    subscription = characteristic.get("subscription")
    subscribable = bool(properties & {"notify", "indicate"})
    if subscribable:
        subscription_obj = require_dict(subscription, f"{path}.subscription", errors)
        check_keys(subscription_obj, {"cccd", "security", "persistForBonded"}, f"{path}.subscription", errors)
        cccd = one_of(subscription_obj.get("cccd"), {"explicit", "stack-managed"}, f"{path}.subscription.cccd", errors)
        one_of(subscription_obj.get("security"), SECURITY - {"denied"}, f"{path}.subscription.security", errors)
        if subscription_obj.get("persistForBonded") is not True:
            errors.append(f"{path}.subscription.persistForBonded: expected true because CCCD state persists for bonded clients")
        if cccd == "explicit" and "2902" not in descriptor_uuids:
            errors.append(f"{path}: explicit subscription requires descriptor 0x2902")
        if cccd == "stack-managed" and "2902" in descriptor_uuids:
            errors.append(f"{path}: stack-managed CCCD must not also be declared explicitly")
    elif subscription is not None:
        errors.append(f"{path}: subscription requires notify or indicate property")
    if "extended-properties" in properties and "2900" not in descriptor_uuids:
        errors.append(f"{path}: extended-properties requires descriptor 0x2900")
    if "2902" in descriptor_uuids and not subscribable:
        errors.append(f"{path}: CCCD requires notify or indicate property")
    if properties == {"notify"} and permissions.get("read") == "denied":
        warnings.append(f"{path}: notify-only value cannot be read for initial state; verify this is intentional")
    return char_id, uuid


def validate_service(raw: Any, path: str, errors: list[str], warnings: list[str]) -> tuple[str | None, str | None, list[str]]:
    service = require_dict(raw, path, errors)
    check_keys(service, {"id", "uuid", "namespace", "kind", "includedServices", "characteristics"}, path, errors)
    service_id = logical_id(service.get("id"), f"{path}.id", errors)
    uuid = normalize_uuid(service.get("uuid"), service.get("namespace"), f"{path}.uuid", errors)
    one_of(service.get("kind"), {"primary", "secondary"}, f"{path}.kind", errors)
    includes = require_list(service.get("includedServices", []), f"{path}.includedServices", errors)
    include_ids = []
    for index, value in enumerate(includes):
        include_id = logical_id(value, f"{path}.includedServices[{index}]", errors)
        if include_id:
            include_ids.append(include_id)
    characteristics = require_list(service.get("characteristics"), f"{path}.characteristics", errors)
    char_ids: set[str] = set()
    char_uuids: list[str] = []
    for index, raw_char in enumerate(characteristics):
        char_id, char_uuid = validate_characteristic(raw_char, f"{path}.characteristics[{index}]", errors, warnings)
        if char_id:
            if char_id in char_ids:
                errors.append(f"{path}: duplicate characteristic logical id {char_id!r}")
            char_ids.add(char_id)
        if char_uuid:
            char_uuids.append(char_uuid)
    duplicate_uuids = sorted(value for value in set(char_uuids) if char_uuids.count(value) > 1)
    if duplicate_uuids:
        warnings.append(f"{path}: repeated characteristic UUID instances {duplicate_uuids}; clients must disambiguate by logical instance/handle context")
    return service_id, uuid, include_ids


def parse_spsm(value: Any, path: str, errors: list[str]) -> int | None:
    if isinstance(value, str) and re.fullmatch(r"0x[0-9A-Fa-f]{1,4}", value):
        value = int(value, 16)
    return integer(value, path, errors, 1, 0xFF)


def validate_l2cap(raw: Any, path: str, errors: list[str], warnings: list[str]) -> tuple[str | None, int | None]:
    channel = require_dict(raw, path, errors)
    check_keys(channel, {"id", "mode", "spsm", "mtu", "mps", "initialCredits", "security", "framing"}, path, errors)
    channel_id = logical_id(channel.get("id"), f"{path}.id", errors)
    mode = one_of(channel.get("mode"), {"le-credit", "enhanced-credit"}, f"{path}.mode", errors)
    spsm = parse_spsm(channel.get("spsm"), f"{path}.spsm", errors)
    minimum = 64 if mode == "enhanced-credit" else 23
    integer(channel.get("mtu"), f"{path}.mtu", errors, minimum, 65535)
    integer(channel.get("mps"), f"{path}.mps", errors, minimum, 65533)
    credit_minimum = 1 if mode == "enhanced-credit" else 0
    integer(channel.get("initialCredits"), f"{path}.initialCredits", errors, credit_minimum, 65535)
    one_of(channel.get("security"), SECURITY - {"denied"}, f"{path}.security", errors)
    if not isinstance(channel.get("framing"), str) or not channel["framing"].strip():
        errors.append(f"{path}.framing: expected non-empty application SDU framing/version description")
    if spsm is not None and 0x80 <= spsm <= 0xFF:
        warnings.append(f"{path}: dynamic SPSM must be rediscovered/negotiated as required on reconnection")
    return channel_id, spsm


def validate(data: Any) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    root = require_dict(data, "$", errors)
    check_keys(root, {"schemaVersion", "device", "database", "l2capChannels"}, "$", errors)
    if root.get("schemaVersion") != 1:
        errors.append("$.schemaVersion: expected 1")

    device = require_dict(root.get("device"), "$.device", errors)
    check_keys(device, {"gapRoles", "gattRoles", "advertising"}, "$.device", errors)
    gap_roles = require_list(device.get("gapRoles"), "$.device.gapRoles", errors)
    gatt_roles = require_list(device.get("gattRoles"), "$.device.gattRoles", errors)
    valid_gap_roles = set()
    valid_gatt_roles = set()
    for index, role in enumerate(gap_roles):
        selected = one_of(role, GAP_ROLES, f"$.device.gapRoles[{index}]", errors)
        if selected:
            valid_gap_roles.add(selected)
    for index, role in enumerate(gatt_roles):
        selected = one_of(role, GATT_ROLES, f"$.device.gattRoles[{index}]", errors)
        if selected:
            valid_gatt_roles.add(selected)
    if len(valid_gap_roles) != len(gap_roles):
        errors.append("$.device.gapRoles: duplicates or invalid values are not allowed")
    if len(valid_gatt_roles) != len(gatt_roles):
        errors.append("$.device.gattRoles: duplicates or invalid values are not allowed")

    advertising = require_dict(device.get("advertising"), "$.device.advertising", errors)
    check_keys(advertising, {"mode", "dataBytes", "scanResponseBytes", "controllerMaxDataBytes", "serviceUuids"}, "$.device.advertising", errors)
    mode = one_of(advertising.get("mode"), {"none", "legacy", "extended"}, "$.device.advertising.mode", errors)
    data_bytes = integer(advertising.get("dataBytes"), "$.device.advertising.dataBytes", errors, 0, 65535)
    scan_bytes = integer(advertising.get("scanResponseBytes"), "$.device.advertising.scanResponseBytes", errors, 0, 65535)
    if mode != "none" and mode is not None and not ({"broadcaster", "peripheral"} & valid_gap_roles):
        errors.append("$.device.advertising: advertising requires broadcaster or peripheral GAP role")
    if mode == "none" and (data_bytes or scan_bytes or advertising.get("serviceUuids")):
        errors.append("$.device.advertising: mode 'none' requires zero data/scan-response bytes and no service UUIDs")
    if mode == "legacy":
        if data_bytes is not None and data_bytes > 31:
            errors.append("$.device.advertising.dataBytes: legacy advertising permits at most 31 encoded bytes")
        if scan_bytes is not None and scan_bytes > 31:
            errors.append("$.device.advertising.scanResponseBytes: legacy scan response permits at most 31 encoded bytes")
    elif mode == "extended":
        controller_max = integer(advertising.get("controllerMaxDataBytes"), "$.device.advertising.controllerMaxDataBytes", errors, 1, 65535)
        if data_bytes is not None and controller_max is not None and data_bytes > controller_max:
            errors.append("$.device.advertising.dataBytes: exceeds controllerMaxDataBytes")
        if scan_bytes is not None and controller_max is not None and scan_bytes > controller_max:
            errors.append("$.device.advertising.scanResponseBytes: exceeds controllerMaxDataBytes")
    advertised_raw = require_list(advertising.get("serviceUuids"), "$.device.advertising.serviceUuids", errors)
    advertised = []
    for index, value in enumerate(advertised_raw):
        namespace = "sig" if isinstance(value, str) and UUID16_RE.fullmatch(value) else "vendor"
        advertised.append(normalize_uuid(value, namespace, f"$.device.advertising.serviceUuids[{index}]", errors))

    database = require_dict(root.get("database"), "$.database", errors)
    check_keys(database, {"mutable", "serviceChanged", "databaseHash", "robustCaching", "services"}, "$.database", errors)
    for field in ("mutable", "serviceChanged", "databaseHash", "robustCaching"):
        if not isinstance(database.get(field), bool):
            errors.append(f"$.database.{field}: expected boolean")
    if database.get("mutable") and not database.get("serviceChanged"):
        errors.append("$.database: mutable database requires Service Changed")
    if database.get("robustCaching") and not (database.get("serviceChanged") and database.get("databaseHash")):
        errors.append("$.database: robustCaching requires both Service Changed and Database Hash")
    if database.get("mutable") and not database.get("databaseHash"):
        warnings.append("$.database: mutable database without Database Hash requires Service Changed/rediscovery cache handling")
    services_raw = require_list(database.get("services"), "$.database.services", errors)
    if not services_raw and "server" in valid_gatt_roles:
        warnings.append("$.database.services: GATT server declares no application services; verify stack-managed mandatory services are sufficient")
    service_ids: set[str] = set()
    service_uuids: list[str] = []
    includes: list[tuple[str | None, str]] = []
    for index, raw_service in enumerate(services_raw):
        service_id, service_uuid, include_ids = validate_service(raw_service, f"$.database.services[{index}]", errors, warnings)
        if service_id:
            if service_id in service_ids:
                errors.append(f"$.database.services: duplicate service logical id {service_id!r}")
            service_ids.add(service_id)
        if service_uuid:
            service_uuids.append(service_uuid)
        includes.extend((service_id, include_id) for include_id in include_ids)
    include_map: dict[str, list[str]] = {service_id: [] for service_id in service_ids}
    for owner, include_id in includes:
        if include_id not in service_ids:
            errors.append(f"$.database: service {owner!r} includes unknown service {include_id!r}")
        elif owner:
            include_map[owner].append(include_id)
        if owner == include_id:
            errors.append(f"$.database: service {owner!r} cannot include itself")

    def reaches(start: str, current: str, seen: set[str]) -> bool:
        if current in seen:
            return False
        seen.add(current)
        return any(child == start or reaches(start, child, seen) for child in include_map.get(current, []))

    for service_id in sorted(service_ids):
        if reaches(service_id, service_id, set()):
            errors.append(f"$.database: included-service cycle contains {service_id!r}")
    duplicate_services = sorted(value for value in set(service_uuids) if service_uuids.count(value) > 1)
    if duplicate_services:
        warnings.append(f"$.database: repeated service UUID instances {duplicate_services}; clients must preserve instance/handle context")
    for index, uuid in enumerate(advertised):
        if uuid and uuid not in service_uuids:
            warnings.append(f"$.device.advertising.serviceUuids[{index}]: UUID is not present in the declared GATT database")

    channels_raw = require_list(root.get("l2capChannels"), "$.l2capChannels", errors)
    channel_ids: set[str] = set()
    spsms: set[int] = set()
    for index, raw_channel in enumerate(channels_raw):
        channel_id, spsm = validate_l2cap(raw_channel, f"$.l2capChannels[{index}]", errors, warnings)
        if channel_id:
            if channel_id in channel_ids:
                errors.append(f"$.l2capChannels: duplicate channel logical id {channel_id!r}")
            channel_ids.add(channel_id)
        if spsm is not None:
            if spsm in spsms:
                warnings.append(f"$.l2capChannels: repeated SPSM 0x{spsm:04x}; verify multiplexing/direction contract")
            spsms.add(spsm)

    return {
        "schemaVersion": 1,
        "valid": not errors,
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
        "summary": {
            "gapRoles": sorted(valid_gap_roles),
            "gattRoles": sorted(valid_gatt_roles),
            "services": len(services_raw),
            "characteristics": sum(len(service.get("characteristics", [])) for service in services_raw if isinstance(service, dict) and isinstance(service.get("characteristics"), list)),
            "l2capChannels": len(channels_raw),
        },
    }


def main() -> int:
    args = parse_args()
    try:
        data = json.loads(args.schema.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    except FileNotFoundError:
        print(f"error: schema file not found: {args.schema}", file=sys.stderr)
        return 2
    except (OSError, UnicodeError, json.JSONDecodeError, DuplicateKeyError) as error:
        print(f"error: cannot parse schema {args.schema}: {error}", file=sys.stderr)
        return 2
    report = validate(data)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Schema: {args.schema}")
        print(f"Valid: {report['valid']}")
        print(f"Services/characteristics/L2CAP channels: {report['summary']['services']} / {report['summary']['characteristics']} / {report['summary']['l2capChannels']}")
        for warning in report["warnings"]:
            print(f"warning: {warning}")
        for error in report["errors"]:
            print(f"error: {error}", file=sys.stderr)
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
