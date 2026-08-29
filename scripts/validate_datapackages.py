#!/usr/bin/env python3
"""Validate all Frictionless Data Packages under datasets/."""

import hashlib
import json
import sys
from pathlib import Path

from frictionless import Package, system

REQUIRED_FIELDS = {"name", "title", "description", "sources", "licenses"}
REQUIRED_RESOURCE_FIELDS = {"bytes", "hash"}


def compute_md5(path: Path) -> str:
    md5 = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    return md5.hexdigest()


def validate_package(dataset_dir: Path) -> list[str]:
    errors: list[str] = []
    datapackage_path = dataset_dir / "datapackage.json"

    if not datapackage_path.exists():
        errors.append(f"{dataset_dir.name}: missing datapackage.json")
        return errors

    try:
        descriptor = json.loads(datapackage_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{dataset_dir.name}: invalid JSON in datapackage.json: {exc}")
        return errors

    missing = REQUIRED_FIELDS - set(descriptor.keys())
    if missing:
        errors.append(f"{descriptor.get('name', dataset_dir.name)}: missing metadata fields: {sorted(missing)}")

    if not descriptor.get("resources"):
        errors.append(f"{descriptor.get('name', dataset_dir.name)}: no resources declared")
        return errors

    for resource in descriptor["resources"]:
        resource_path = dataset_dir / resource.get("path", "")
        if not resource_path.exists():
            errors.append(f"{descriptor.get('name', dataset_dir.name)}: resource file not found: {resource.get('path')}")
            continue

        missing_resource = REQUIRED_RESOURCE_FIELDS - set(resource.keys())
        if missing_resource:
            errors.append(
                f"{descriptor.get('name', dataset_dir.name)}: resource {resource.get('name')} missing fields: {sorted(missing_resource)}"
            )

        actual_bytes = resource_path.stat().st_size
        if "bytes" in resource and resource["bytes"] != actual_bytes:
            errors.append(
                f"{descriptor.get('name', dataset_dir.name)}: resource {resource.get('name')} bytes mismatch "
                f"(declared {resource['bytes']}, actual {actual_bytes})"
            )

        if "hash" in resource:
            actual_hash = compute_md5(resource_path)
            declared_hash = resource["hash"]
            if declared_hash != actual_hash:
                errors.append(
                    f"{descriptor.get('name', dataset_dir.name)}: resource {resource.get('name')} hash mismatch "
                    f"(declared {declared_hash[:16]}..., actual {actual_hash[:16]}...)"
                )

    # Validate with Frictionless itself.
    try:
        package = Package(descriptor, basepath=str(dataset_dir))
        report = package.validate()
        if not report.valid:
            for task in report.tasks:
                for error in task.errors:
                    errors.append(f"{descriptor.get('name', dataset_dir.name)}: frictionless error: {error}")
    except Exception as exc:
        errors.append(f"{descriptor.get('name', dataset_dir.name)}: frictionless validation failed: {exc}")

    return errors


def main() -> int:
    datasets_dir = Path(__file__).parent.parent / "datasets"
    if not datasets_dir.is_dir():
        print("No datasets/ directory found.", file=sys.stderr)
        return 1

    all_errors: list[str] = []
    for dataset_dir in sorted(datasets_dir.iterdir()):
        if not dataset_dir.is_dir():
            continue
        all_errors.extend(validate_package(dataset_dir))

    if all_errors:
        print("Validation failed:", file=sys.stderr)
        for error in all_errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print("All data packages are valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
