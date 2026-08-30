#!/usr/bin/env python3
"""Report whether two Git revisions require a dataset release."""

import json
import subprocess
import sys
from collections import Counter
from collections.abc import Mapping


def resource_hashes(package: Mapping[str, object]) -> Counter[str]:
    resources = package.get("resources", [])
    if not isinstance(resources, list):
        raise ValueError("datapackage resources must be a list")

    hashes: Counter[str] = Counter()
    for resource in resources:
        if not isinstance(resource, dict):
            raise ValueError("datapackage resource must be an object")
        resource_hash = resource.get("hash")
        if not isinstance(resource_hash, str):
            raise ValueError("datapackage resource hash must be a string")
        hashes[resource_hash] += 1
    return hashes


def release_needed(
    previous: Mapping[str, Mapping[str, object]],
    current: Mapping[str, Mapping[str, object]],
) -> bool:
    if previous.keys() != current.keys():
        return True
    return any(
        resource_hashes(previous[name]) != resource_hashes(current[name])
        for name in current
    )


def git_output(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True)


def dataset_names(ref: str) -> set[str]:
    return set(git_output("ls-tree", "-d", "--name-only", f"{ref}:datasets").splitlines())


def package_at(ref: str, name: str) -> dict:
    return json.loads(git_output("show", f"{ref}:datasets/{name}/datapackage.json"))


def packages_at(ref: str) -> dict[str, dict]:
    return {name: package_at(ref, name) for name in dataset_names(ref)}


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit(f"Usage: {sys.argv[0]} <previous-revision> <current-revision>")

    previous_ref, current_ref = sys.argv[1:]
    if set(previous_ref) == {"0"}:
        print("true")
        return 0

    print(str(release_needed(packages_at(previous_ref), packages_at(current_ref))).lower())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
