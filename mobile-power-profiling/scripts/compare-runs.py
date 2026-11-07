#!/usr/bin/env python3
"""Summarize paired, homogeneous ROI readings; never parse or attribute traces."""

import argparse
import csv
import json
import math
import statistics
import sys

FIELDS = ("pair", "variant", "device", "scenario", "metric", "unit", "duration_s", "value")
UNITS = {"mW", "J", "mWh", "battery_percent_per_hour", "power_impact"}


def number(text, field, line, *, positive=False):
    try:
        value = float(text)
    except ValueError as error:
        raise ValueError(f"line {line}: {field} must be numeric") from error
    if not math.isfinite(value) or value < 0 or (positive and value == 0):
        bound = "positive" if positive else "nonnegative"
        raise ValueError(f"line {line}: {field} must be finite and {bound}")
    return value


def compare(stream):
    reader = csv.DictReader(stream)
    if tuple(reader.fieldnames or ()) != FIELDS:
        raise ValueError("expected CSV header: " + ",".join(FIELDS))
    context = None
    paired = {}
    for row in reader:
        line = reader.line_num
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"line {line}: incorrect column count")
        row = {key: value.strip() for key, value in row.items()}
        if any(not row[key] for key in FIELDS):
            raise ValueError(f"line {line}: all fields are required")
        if row["variant"] not in {"A", "B"}:
            raise ValueError(f"line {line}: variant must be A (baseline) or B (candidate)")
        if row["unit"] not in UNITS:
            raise ValueError(f"line {line}: unit must be one of {', '.join(sorted(UNITS))}")
        current = {key: row[key] for key in ("device", "scenario", "metric", "unit")}
        current["duration_s"] = number(row["duration_s"], "duration_s", line, positive=True)
        if context is None:
            context = current
        elif current != context:
            raise ValueError(f"line {line}: mixed device, scenario, metric, unit or ROI duration; compare separately")
        value = number(row["value"], "value", line)
        variants = paired.setdefault(row["pair"], {})
        if row["variant"] in variants:
            raise ValueError(f"line {line}: duplicate {row['pair']}/{row['variant']} reading")
        variants[row["variant"]] = value
    for pair, variants in paired.items():
        if set(variants) != {"A", "B"}:
            raise ValueError(f"pair {pair}: requires exactly one A and one B reading")
    if len(paired) < 2:
        raise ValueError("at least two complete A/B pairs are required; collect repeated measurements")
    pairs = [
        {"pair": pair, "baseline": values["A"], "candidate": values["B"],
         "delta": values["B"] - values["A"]}
        for pair, values in sorted(paired.items())
    ]
    baseline = statistics.mean(row["baseline"] for row in pairs)
    candidate = statistics.mean(row["candidate"] for row in pairs)
    deltas = [row["delta"] for row in pairs]
    percent = 100 * (candidate / baseline - 1) if baseline else None
    return {
        "context": context,
        "pairs": pairs,
        "summary": {
            "pair_count": len(pairs),
            "baseline_mean": baseline,
            "candidate_mean": candidate,
            "mean_paired_delta": statistics.mean(deltas),
            "median_paired_delta": statistics.median(deltas),
            "min_paired_delta": min(deltas),
            "max_paired_delta": max(deltas),
            "change_percent_of_baseline_mean": percent,
        },
        "limits": "Descriptive readings only. Negative delta means lower B. No causal, significance or battery-life conclusion.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", help="homogeneous paired readings CSV; use - for stdin")
    args = parser.parse_args()
    try:
        if args.csv == "-":
            result = compare(sys.stdin)
        else:
            with open(args.csv, encoding="utf-8-sig", newline="") as stream:
                result = compare(stream)
        print(json.dumps(result, indent=2, allow_nan=False))
    except (OSError, UnicodeError, csv.Error, ValueError, OverflowError) as error:
        parser.exit(2, f"ERROR: {error}\n")


if __name__ == "__main__":
    main()
