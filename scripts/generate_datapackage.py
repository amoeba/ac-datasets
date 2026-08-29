#!/usr/bin/env python3
"""Generate or update a Frictionless Data Package for a dataset folder."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

from frictionless import describe


def compute_md5(path: Path) -> str:
    md5 = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    return md5.hexdigest()


def generate_datapackage(dataset_dir: Path) -> dict:
    if not dataset_dir.is_dir():
        raise SystemExit(f"Not a directory: {dataset_dir}")

    resources = []
    for csv_path in sorted(dataset_dir.glob("*.csv")):
        resource = describe(str(csv_path)).to_descriptor()
        # Make path relative to the datapackage.json location.
        resource["path"] = csv_path.name
        resource["bytes"] = csv_path.stat().st_size
        resource["hash"] = compute_md5(csv_path)
        resources.append(resource)

    package_dict = {
        "profile": "data-package",
        "resources": resources,
    }

    # Preserve existing metadata if present.
    existing = dataset_dir / "datapackage.json"
    if existing.exists():
        existing_descriptor = json.loads(existing.read_text(encoding="utf-8"))
        for key in ("name", "title", "description", "homepage", "sources", "licenses", "contributors"):
            if key in existing_descriptor:
                package_dict[key] = existing_descriptor[key]

    # Set a default name from the folder name if not present.
    package_dict.setdefault("name", dataset_dir.name)

    return package_dict


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a datapackage.json for a dataset folder.")
    parser.add_argument("dataset_dir", type=Path, help="Path to the dataset folder.")
    parser.add_argument("--write", action="store_true", help="Write datapackage.json to the folder.")
    parser.add_argument("--check", action="store_true", help="Exit with error if datapackage.json would change.")
    args = parser.parse_args()

    descriptor = generate_datapackage(args.dataset_dir)
    output = json.dumps(descriptor, indent=2, ensure_ascii=False) + "\n"

    out_path = args.dataset_dir / "datapackage.json"
    if args.check:
        if not out_path.exists():
            print(f"Would create {out_path}", file=sys.stderr)
            return 1
        existing = out_path.read_text(encoding="utf-8")
        if existing != output:
            print(f"{out_path} is out of date; run `uv run scripts/generate-datapackage.py {args.dataset_dir} --write`", file=sys.stderr)
            return 1
        print(f"{out_path} is up to date.")
        return 0

    if args.write:
        out_path.write_text(output, encoding="utf-8")
        print(f"Wrote {out_path}")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
