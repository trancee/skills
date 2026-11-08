#!/usr/bin/env python3
"""Inventory regular corpus/artifact files without decoding or changing them."""

import argparse
import hashlib
import json
from pathlib import Path
import sys


def inventory(root):
    if root.is_symlink():
        raise ValueError(f"symbolic-link input is not supported: {root}")
    if root.is_file():
        files = [(root.name, root)]
    elif root.is_dir():
        files = []
        for path in sorted(root.rglob("*")):
            if path.is_symlink():
                raise ValueError(f"symbolic link in corpus: {path}")
            if path.is_dir():
                continue
            if not path.is_file():
                raise ValueError(f"non-regular corpus entry: {path}")
            files.append((path.relative_to(root).as_posix(), path))
    else:
        raise ValueError(f"expected an existing regular file or directory: {root}")
    records = []
    for name, path in files:
        digest = hashlib.sha256()
        size = 0
        with path.open("rb") as stream:
            while chunk := stream.read(65536):
                size += len(chunk)
                digest.update(chunk)
        records.append({"path": name, "bytes": size, "sha256": digest.hexdigest()})
    return {"files": records, "file_count": len(records), "total_bytes": sum(r["bytes"] for r in records)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="corpus directory or one crashing-input file")
    args = parser.parse_args()
    try:
        print(json.dumps(inventory(args.path), indent=2))
    except (OSError, ValueError) as error:
        parser.exit(2, f"ERROR: {error}\n")


if __name__ == "__main__":
    main()
