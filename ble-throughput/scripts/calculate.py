#!/usr/bin/env python3
"""Calculate an explicit upper-bound model for one-direction ATT traffic on LE 1M/2M."""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any

PHY = {
    "1m": {"bits_per_us": 1.0, "preamble_bytes": 1},
    "2m": {"bits_per_us": 2.0, "preamble_bytes": 2},
}
OPERATIONS = ("notification", "write-command", "indication", "write-request")
ATT_OVERHEAD_BYTES = 3
L2CAP_HEADER_BYTES = 4
MAX_ATTRIBUTE_VALUE_BYTES = 512
LEGACY_MIN_INTERVAL_MS = 7.5
SCI_MIN_INTERVAL_MS = 0.375


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phy", choices=sorted(PHY), required=True, help="effective uncoded PHY")
    parser.add_argument("--att-mtu", type=int, required=True, help="effective ATT MTU, 23..517")
    parser.add_argument("--ll-payload-octets", type=int, required=True, help="effective LL data payload, 27..251")
    parser.add_argument("--connection-interval-ms", type=float, required=True, help="effective connection interval/rate")
    parser.add_argument("--event-duration-ms", type=float, required=True, help="observed usable duration of one connection event")
    parser.add_argument("--packets-per-event", type=int, required=True, help="observed outgoing data LL packet cap")
    parser.add_argument("--operation", choices=OPERATIONS, required=True)
    parser.add_argument("--value-bytes", type=int, help="ATT attribute value bytes; default: largest LL-aligned value")
    parser.add_argument("--ifs-us", type=float, default=150.0, help="effective inter-frame space; default: 150")
    parser.add_argument("--controller-overhead-us", type=float, default=0.0, help="extra scheduling time per data/empty pair")
    parser.add_argument("--encrypted", action="store_true", help="include a 4-byte MIC on each LL packet")
    parser.add_argument("--shorter-connection-intervals", action="store_true", help="allow Core 6.2 SCI intervals below 7.5 ms")
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    return parser.parse_args()


def fail(message: str) -> None:
    raise ValueError(message)


def validate(args: argparse.Namespace) -> None:
    if not 23 <= args.att_mtu <= 517:
        fail("--att-mtu must be between 23 and 517 bytes")
    if not 27 <= args.ll_payload_octets <= 251:
        fail("--ll-payload-octets must be between 27 and 251 bytes")
    minimum = SCI_MIN_INTERVAL_MS if args.shorter_connection_intervals else LEGACY_MIN_INTERVAL_MS
    if not minimum <= args.connection_interval_ms <= 4000:
        suffix = " with negotiated Core 6.2 SCI" if args.shorter_connection_intervals else " unless --shorter-connection-intervals is justified by negotiated Core 6.2 SCI"
        fail(f"--connection-interval-ms must be between {minimum:g} and 4000 ms{suffix}")
    if not 0 < args.event_duration_ms <= args.connection_interval_ms:
        fail("--event-duration-ms must be positive and no greater than --connection-interval-ms")
    if args.packets_per_event < 1:
        fail("--packets-per-event must be at least 1")
    if args.ifs_us < 0:
        fail("--ifs-us cannot be negative")
    if args.controller_overhead_us < 0:
        fail("--controller-overhead-us cannot be negative")


def aligned_values(att_mtu: int, ll_payload: int) -> list[int]:
    maximum = min(att_mtu - ATT_OVERHEAD_BYTES, MAX_ATTRIBUTE_VALUE_BYTES)
    values = []
    for fragments in range(1, math.ceil((maximum + ATT_OVERHEAD_BYTES + L2CAP_HEADER_BYTES) / ll_payload) + 1):
        value = fragments * ll_payload - ATT_OVERHEAD_BYTES - L2CAP_HEADER_BYTES
        if 1 <= value <= maximum:
            values.append(value)
    return values


def fragment_lengths(total: int, capacity: int) -> list[int]:
    lengths = []
    remaining = total
    while remaining:
        length = min(remaining, capacity)
        lengths.append(length)
        remaining -= length
    return lengths


def packet_airtime_us(payload_bytes: int, phy: dict[str, float | int], encrypted: bool) -> float:
    mic = 4 if encrypted else 0
    packet_bytes = int(phy["preamble_bytes"]) + 4 + 2 + payload_bytes + mic + 3
    return packet_bytes * 8 / float(phy["bits_per_us"])


def calculate(args: argparse.Namespace) -> dict[str, Any]:
    validate(args)
    phy = PHY[args.phy]
    maximum_value = min(args.att_mtu - ATT_OVERHEAD_BYTES, MAX_ATTRIBUTE_VALUE_BYTES)
    aligned = aligned_values(args.att_mtu, args.ll_payload_octets)
    recommended = max(aligned) if aligned else maximum_value
    value_bytes = args.value_bytes if args.value_bytes is not None else recommended
    if not 1 <= value_bytes <= maximum_value:
        fail(f"--value-bytes must be between 1 and {maximum_value} for ATT MTU {args.att_mtu}")
    l2cap_pdu_bytes = value_bytes + ATT_OVERHEAD_BYTES + L2CAP_HEADER_BYTES
    fragments = fragment_lengths(l2cap_pdu_bytes, args.ll_payload_octets)
    empty_airtime = packet_airtime_us(0, phy, args.encrypted)
    pair_times = [
        packet_airtime_us(fragment, phy, args.encrypted) + empty_airtime + 2 * args.ifs_us + args.controller_overhead_us
        for fragment in fragments
    ]
    operation_airtime = sum(pair_times)
    event_us = args.event_duration_ms * 1000
    airtime_operations = math.floor(event_us / operation_airtime)
    packet_cap_operations = args.packets_per_event // len(fragments)
    operation_limit = 1 if args.operation in {"indication", "write-request"} else min(airtime_operations, packet_cap_operations)
    operations_per_event = min(airtime_operations, packet_cap_operations, operation_limit)
    modeled_bps = operations_per_event * value_bytes * 8 * 1000 / args.connection_interval_ms
    continuous_bps = value_bytes * 8_000_000 / operation_airtime
    event_utilization = operations_per_event * operation_airtime / event_us
    warnings = [
        "Upper bound only: excludes retransmissions, host latency, queue starvation, application headers, security framing, and receiver work.",
        "Packets per event means outgoing data LL packets; the airtime model separately includes an empty reverse LL packet.",
    ]
    if args.att_mtu == 23:
        warnings.append("Default ATT MTU limits notification/write-command values to 20 bytes.")
    if args.ll_payload_octets == 27:
        warnings.append("A 27-octet LL payload indicates DLE is absent or not effectively negotiated.")
    if aligned and value_bytes not in aligned:
        warnings.append("Selected value does not end on an LL fragment boundary; compare the recommended aligned value empirically.")
    if args.operation in {"indication", "write-request"}:
        warnings.append("Request/confirmation operation is conservatively capped at one value per event; callback round trips may be slower.")
    if args.connection_interval_ms < LEGACY_MIN_INTERVAL_MS:
        warnings.append("Sub-7.5 ms interval assumes negotiated Core 6.2 Shorter Connection Intervals support across both peers, hosts, and controllers.")
    if args.ifs_us != 150:
        warnings.append("Non-150 us frame spacing must come from effective controller/trace evidence; the calculator does not model negotiation.")
    if args.event_duration_ms == args.connection_interval_ms:
        warnings.append("Event duration equals the full connection interval; this is optimistic unless a trace proves the event remains open that long.")
    return {
        "inputs": {
            "phy": args.phy, "att_mtu": args.att_mtu, "ll_payload_octets": args.ll_payload_octets,
            "connection_interval_ms": args.connection_interval_ms, "event_duration_ms": args.event_duration_ms,
            "packets_per_event": args.packets_per_event, "operation": args.operation,
            "value_bytes": value_bytes, "encrypted": args.encrypted, "ifs_us": args.ifs_us,
            "controller_overhead_us": args.controller_overhead_us,
            "shorter_connection_intervals": args.shorter_connection_intervals,
        },
        "sizing": {
            "maximum_att_value_bytes": maximum_value, "aligned_value_bytes": aligned,
            "recommended_aligned_value_bytes": recommended, "att_overhead_bytes": ATT_OVERHEAD_BYTES,
            "l2cap_header_bytes": L2CAP_HEADER_BYTES, "l2cap_pdu_bytes": l2cap_pdu_bytes,
            "ll_fragment_payload_bytes": fragments, "ll_fragments_per_value": len(fragments),
        },
        "airtime": {
            "fragment_exchange_us": [round(value, 3) for value in pair_times],
            "value_exchange_us": round(operation_airtime, 3),
            "airtime_operations_per_event": airtime_operations,
            "packet_cap_operations_per_event": packet_cap_operations,
            "modeled_operations_per_event": operations_per_event,
            "modeled_event_utilization": round(event_utilization, 6),
        },
        "bounds": {
            "continuous_radio_useful_bits_per_second": round(continuous_bps, 3),
            "modeled_event_useful_bits_per_second": round(modeled_bps, 3),
            "modeled_event_useful_bytes_per_second": round(modeled_bps / 8, 3),
        },
        "warnings": warnings,
    }


def print_human(data: dict[str, Any]) -> None:
    sizing = data["sizing"]
    airtime = data["airtime"]
    bounds = data["bounds"]
    print(f"ATT value: {data['inputs']['value_bytes']} bytes; aligned recommendation: {sizing['recommended_aligned_value_bytes']} bytes")
    print(f"LL fragments/value: {sizing['ll_fragments_per_value']} {sizing['ll_fragment_payload_bytes']}")
    print(f"Exchange airtime/value: {airtime['value_exchange_us']:.3f} us")
    print(f"Operations/event (airtime / packet cap / modeled): {airtime['airtime_operations_per_event']} / {airtime['packet_cap_operations_per_event']} / {airtime['modeled_operations_per_event']}")
    print(f"Modeled useful throughput: {bounds['modeled_event_useful_bytes_per_second']:.3f} B/s ({bounds['modeled_event_useful_bits_per_second']:.3f} bit/s)")
    print("Warnings:")
    for warning in data["warnings"]:
        print(f"- {warning}")


def main() -> int:
    args = parse_args()
    try:
        data = calculate(args)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print_human(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
