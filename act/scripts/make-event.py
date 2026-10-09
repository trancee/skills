#!/usr/bin/env python3
"""Emit a minimal local act event payload; not a complete GitHub webhook delivery."""

import argparse
import json
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="event", required=True)
    push = sub.add_parser("push", help="branch/tag ref payload")
    push.add_argument("--ref", required=True, help="full refs/heads/... or refs/tags/... ref")
    pr = sub.add_parser("pull_request", help="minimal PR head/base payload")
    pr.add_argument("--head-ref", required=True, help="head branch name, without refs/heads/")
    pr.add_argument("--base-ref", required=True, help="base branch name, without refs/heads/")
    dispatch = sub.add_parser("workflow_dispatch", help="manual inputs; values remain strings")
    dispatch.add_argument("--input", action="append", default=[], metavar="KEY=VALUE")
    args = parser.parse_args()
    payload = {"act": True}
    if args.event == "push":
        if not args.ref.startswith(("refs/heads/", "refs/tags/")) or args.ref.endswith("/"):
            parser.error("--ref must be a non-empty full refs/heads/... or refs/tags/... ref")
        payload["ref"] = args.ref
    elif args.event == "pull_request":
        if not args.head_ref.strip() or not args.base_ref.strip():
            parser.error("--head-ref and --base-ref must be non-empty branch names")
        payload["pull_request"] = {"head": {"ref": args.head_ref}, "base": {"ref": args.base_ref}}
    else:
        inputs = {}
        for item in args.input:
            key, separator, value = item.partition("=")
            if not separator or not key or key != key.strip():
                parser.error("--input requires a non-empty unpadded KEY=VALUE; quote the full argument")
            if key in inputs:
                parser.error(f"duplicate input {key!r}; supply each input once")
            inputs[key] = value
        payload["inputs"] = inputs
    json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
    print()
    print("Minimal local payload only; add any additional fields read by the workflow.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
