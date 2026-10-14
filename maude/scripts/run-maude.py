#!/usr/bin/env python3
"""Run a trusted Maude command file and check transcript evidence, not formal validity."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="trusted Maude command file; may contain arbitrary interpreter commands")
    parser.add_argument("--maude", default="maude", help="executable path/name; preserve matching MAUDE_LIB")
    parser.add_argument("--cwd", type=Path, help="load working directory; default: command file's parent")
    parser.add_argument("--timeout", type=float, default=30, help="wall-clock seconds; positive, default 30")
    parser.add_argument("--expect-result", action="append", default=[], metavar="SORT=VALUE", help="ordered non-counterexample result lines; repeat for every result")
    parser.add_argument("--counterexamples", type=int, default=0, help="expected result lines starting with counterexample(...)")
    parser.add_argument("--require", action="append", default=[], help="literal text required in stdout; not a completeness/proof check")
    parser.add_argument("--json", action="store_true", help="emit JSON with full stdout/stderr and evidence verdict")
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0 or args.counterexamples < 0:
        parser.error("--timeout must be finite and positive and --counterexamples non-negative")
    if not args.expect_result and not args.counterexamples and not any(args.require):
        parser.error("supply --expect-result, positive --counterexamples, or non-empty --require; an empty transcript is not execution evidence")
    expected = []
    for entry in args.expect_result:
        sort, separator, value = entry.partition("=")
        if not separator or not sort or not value:
            parser.error("--expect-result must be SORT=VALUE, with both parts non-empty")
        expected.append({"sort": sort, "value": value})
    command_file = args.file.expanduser().resolve()
    if not command_file.is_file():
        parser.error(f"command file not found: {command_file}; provide an existing reviewed .maude file")
    cwd = args.cwd.expanduser().resolve() if args.cwd else command_file.parent
    executable = str(Path(args.maude).expanduser().resolve()) if os.path.dirname(args.maude) else args.maude
    try:
        run = subprocess.run(
            [executable, "-no-banner", "-no-ansi-color", "-no-wrap", str(command_file)],
            cwd=cwd, input="quit\n", text=True, capture_output=True, timeout=args.timeout,
        )
    except subprocess.TimeoutExpired:
        print("error: Maude exceeded the wall-clock limit; no completed result or proof is claimed. Bound the query or raise --timeout deliberately.", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"error: {error}; check --maude, execution permission, --cwd, and the matching distribution/MAUDE_LIB", file=sys.stderr)
        return 2
    results = []
    counterexamples = 0
    for sort, value in re.findall(r"^result ([^:\n]+): (.*)$", run.stdout, flags=re.MULTILINE):
        if value.startswith("counterexample("):
            counterexamples += 1
        else:
            results.append({"sort": sort, "value": value})
    diagnostics = [line for line in (run.stdout + "\n" + run.stderr).splitlines() if re.match(r"^\s*(Warning|Error|Advisory|Fatal)\s*:", line, re.IGNORECASE)]
    errors = []
    if run.returncode != 0:
        errors.append(f"Maude process exited {run.returncode}")
    if diagnostics:
        errors.append("interpreter diagnostics detected; repair them before accepting results")
    if results != expected:
        errors.append(f"result sequence differs: expected {expected!r}, observed {results!r}")
    if counterexamples != args.counterexamples:
        errors.append(f"expected {args.counterexamples} counterexamples, observed {counterexamples}")
    for text in args.require:
        if text not in run.stdout:
            errors.append(f"required stdout evidence absent: {text!r}")
    report = {
        "valid": not errors, "processExit": run.returncode, "results": results,
        "counterexamples": counterexamples, "diagnostics": diagnostics, "errors": errors,
        "limits": "Transcript checks only: no confluence, termination, coherence, exhaustive-search, abstraction, or property-correctness proof.",
        "stdout": run.stdout, "stderr": run.stderr,
    }
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(run.stdout, end="")
        print(run.stderr, end="", file=sys.stderr)
        print("PASS: transcript evidence matched" if not errors else "FAIL: transcript evidence rejected")
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        print(report["limits"])
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
