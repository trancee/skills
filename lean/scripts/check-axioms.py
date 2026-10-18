#!/usr/bin/env python3
"""Build named Lean modules and audit transitive axioms in a reviewed Lake project.

Not a sandbox or independent proof checker. Supports ordinary ASCII qualified
identifiers; use Lean directly for escaped/Unicode declaration names.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time


NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*")
STANDARD = {"propext", "Classical.choice", "Quot.sound"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True, help="reviewed Lake package root")
    parser.add_argument("--module", action="append", required=True, help="module to build/import; repeat as needed")
    parser.add_argument("--theorem", action="append", required=True, help="fully qualified declaration to audit; repeat as needed")
    parser.add_argument("--lake", default="lake", help="Lake executable/proxy; respects current elan environment")
    parser.add_argument("--timeout", type=float, default=120, help="total wall-clock limit in seconds, default 120")
    parser.add_argument("--json", action="store_true", help="emit report with full command transcripts")
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be finite and positive")
    if any(not NAME.fullmatch(name) for name in args.module + args.theorem):
        parser.error("use ordinary ASCII qualified identifiers; audit Unicode/escaped names directly in Lean")
    project = args.project.expanduser().resolve()
    if not project.is_dir() or not any((project / filename).is_file() for filename in ("lakefile.toml", "lakefile.lean")):
        parser.error("--project must contain lakefile.toml or lakefile.lean; select the actual package root")
    lake = str(Path(args.lake).expanduser().resolve()) if os.path.dirname(args.lake) else args.lake
    modules = list(dict.fromkeys(args.module))
    theorems = list(dict.fromkeys(args.theorem))
    report = {"accepted": False, "axioms": {}, "commands": [], "errors": [], "limits": "Reviewed-project build and axiom-policy evidence only; not isolation, statement validation, or independent kernel checking."}
    deadline = time.monotonic() + args.timeout

    def run(command: list[str], source: str | None = None) -> subprocess.CompletedProcess:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise subprocess.TimeoutExpired(command, args.timeout)
        result = subprocess.run(command, cwd=project, input=source, capture_output=True, text=True, timeout=remaining)
        report["commands"].append({"argv": command, "exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr})
        return result

    try:
        build = run([lake, "--wfail", "build", *("+" + module for module in modules)])
        if build.returncode:
            report["errors"].append("module build failed; repair diagnostics before auditing axioms")
        else:
            source = "".join(f"import {module}\n" for module in modules)
            source += "".join(f"#print axioms {name}\n" for name in theorems)
            audit = run([lake, "env", "lean", "-DwarningAsError=true", "--json", "--stdin"], source)
            if audit.returncode:
                report["errors"].append("Lean axiom query failed; inspect errors and exact declaration names")
            for line in audit.stdout.splitlines():
                message = json.loads(line)
                if not isinstance(message, dict):
                    raise ValueError("expected a Lean JSON message object")
                if message.get("severity") in {"error", "warning"}:
                    report["errors"].append(str(message.get("data", message)))
                text = message.get("data", "")
                if not isinstance(text, str) or message.get("severity") != "information":
                    continue
                for name in theorems:
                    if text == f"'{name}' does not depend on any axioms":
                        report["axioms"][name] = []
                    else:
                        match = re.fullmatch(re.escape(f"'{name}' depends on axioms: ") + r"\[([^\]]*)\]", text, re.DOTALL)
                        if match:
                            report["axioms"][name] = [axiom.strip() for axiom in match[1].split(",") if axiom.strip()]
            for name in theorems:
                if name not in report["axioms"]:
                    report["errors"].append(f"missing recognized axiom report for {name}; no acceptance inferred")
                    continue
                unexpected = set(report["axioms"][name]) - STANDARD
                if unexpected:
                    report["errors"].append(f"{name} uses non-standard axioms: {', '.join(sorted(unexpected))}; repair incomplete proofs or review assumptions explicitly")
    except (OSError, subprocess.TimeoutExpired, ValueError) as error:
        report["errors"].append(f"audit unavailable or output unrecognized: {error}")
    report["accepted"] = not report["errors"]
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for command in report["commands"]:
            print(command["stdout"], end="")
            print(command["stderr"], end="", file=sys.stderr)
        print("PASS: requested declarations use only standard axioms" if report["accepted"] else "FAIL: axiom audit not accepted")
        for error in report["errors"]:
            print(f"error: {error}", file=sys.stderr)
        print(report["limits"])
    return 0 if report["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
