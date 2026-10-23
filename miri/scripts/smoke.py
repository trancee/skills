#!/usr/bin/env python3
"""Exercise bundled Miri fixtures in a disposable Cargo package.

Requires rustup proxies on PATH and an installed nightly with miri/rust-src.
Run cargo +<toolchain> miri setup first. No consumer source is modified.
Resets interpreter/compiler flags so weakened checks cannot yield false passes.
"""
from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toolchain", required=True, help="installed rustup nightly name, e.g. nightly-2026-10-23")
    parser.add_argument("--cargo", default="cargo", help="Cargo rustup proxy name or path")
    parser.add_argument("--target", help="optional interpreted target triple")
    parser.add_argument("--timeout", type=float, default=180, help="total execution limit in seconds")
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be finite and positive")
    if not re.fullmatch(r"nightly(?:-[0-9]{4}-[0-9]{2}-[0-9]{2})?(?:-[A-Za-z0-9_-]+)?", args.toolchain):
        parser.error("--toolchain must name a rustup nightly toolchain")
    if args.target and not re.fullmatch(r"[A-Za-z0-9_]+(?:-[A-Za-z0-9_]+)+", args.target):
        parser.error("--target must be a Rust target triple")
    cargo = str(Path(args.cargo).expanduser().absolute()) if os.path.dirname(args.cargo) else args.cargo
    env = os.environ.copy()
    for key in ("MIRIFLAGS", "RUSTFLAGS", "RUSTDOCFLAGS", "CARGO_ENCODED_RUSTFLAGS", "MIRI_SYSROOT", "MIRI_LIB_SRC", "MIRI_NO_STD"):
        env.pop(key, None)
    deadline = time.monotonic() + args.timeout
    try:
        with tempfile.TemporaryDirectory(prefix="miri-smoke-") as directory:
            project = Path(directory)
            env["CARGO_TARGET_DIR"] = str(project / "target")
            (project / "Cargo.toml").write_text(
                '[package]\nname = "miri-skill-smoke"\nversion = "0.1.0"\nedition = "2021"\n'
                '[lib]\npath = "smoke.rs"\n[workspace]\n', encoding="utf-8"
            )
            shutil.copyfile(Path(__file__).resolve().parents[1] / "assets" / "smoke.rs", project / "smoke.rs")
            command = [cargo, "+" + args.toolchain, "miri", "test", "--lib"]
            if args.target:
                command += ["--target", args.target]
            cases = [
                ("safe_", [], 0, r"test result: ok\. 3 passed"),
                ("tests::bad_use_after_free", ["--ignored", "--exact"], 1, r"Undefined Behavior:.*(?:freed|dangling)"),
                ("tests::bad_memory_leak", ["--ignored", "--exact"], 1, r"memory leaked"),
            ]
            for name, extra, expected_failure, diagnostic in cases:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(command, args.timeout)
                argv = command + ["--", name, *extra, "--nocapture"]
                print("RUN:", " ".join(argv), flush=True)
                result = subprocess.run(argv, cwd=project, env=env, capture_output=True, text=True, timeout=remaining)
                transcript = result.stdout + result.stderr
                print(transcript, end="" if transcript.endswith("\n") else "\n")
                if bool(result.returncode) != bool(expected_failure) or not re.search(diagnostic, transcript, re.IGNORECASE):
                    print(f"FAIL: {name}: exit {result.returncode}; expected "
                          f"{'a Miri rejection with the specified diagnostic' if expected_failure else 'three passing tests'}; "
                          "compilation/setup errors are not successful controls", file=sys.stderr)
                    return 1
                print(f"PASS: {name}: expected {'rejection' if expected_failure else 'acceptance'} observed")
    except (OSError, subprocess.TimeoutExpired) as error:
        print(f"FAIL: Miri smoke unavailable: {error}", file=sys.stderr)
        return 1
    print("PASS: safe ownership/boundary/endianness cases accepted; use-after-free and leak controls rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
