import json
import hashlib
from pathlib import Path

import pytest

from scripts.validate_datapackages import validate_package


def make_datapackage(**overrides) -> dict:
    descriptor = {
        "name": "test-dataset",
        "title": "Test Dataset",
        "description": "A dataset for testing.",
        "sources": [{"title": "Test Source", "path": "https://example.com"}],
        "licenses": [{"name": "CC0-1.0", "path": "https://creativecommons.org/publicdomain/zero/1.0/"}],
        "resources": [
            {
                "name": "test",
                "path": "test.csv",
                "format": "csv",
                "mediatype": "text/csv",
            }
        ],
    }
    descriptor.update(overrides)
    return descriptor


def write_dataset(tmp_path: Path, descriptor: dict, csv_content: str = "", name: str = "test-dataset") -> Path:
    dataset_dir = tmp_path / name
    dataset_dir.mkdir()
    csv_path = dataset_dir / "test.csv"
    csv_path.write_text(csv_content, encoding="utf-8")

    for resource in descriptor.get("resources", []):
        if resource.get("path") == "test.csv":
            resource["bytes"] = csv_path.stat().st_size
            resource["hash"] = hashlib.md5(csv_path.read_bytes(), usedforsecurity=False).hexdigest()

    (dataset_dir / "datapackage.json").write_text(json.dumps(descriptor), encoding="utf-8")
    return dataset_dir


def test_missing_datapackage(tmp_path: Path):
    dataset_dir = tmp_path / "empty-dataset"
    dataset_dir.mkdir()
    errors = validate_package(dataset_dir)
    assert any("missing datapackage.json" in e for e in errors)


def test_missing_required_metadata(tmp_path: Path):
    for field in ["name", "title", "description", "sources", "licenses"]:
        descriptor = make_datapackage()
        del descriptor[field]
        dataset_dir = write_dataset(tmp_path, descriptor, name=f"test-dataset-{field}")
        errors = validate_package(dataset_dir)
        assert any(f"missing metadata fields" in e and field in e for e in errors)


def test_no_resources(tmp_path: Path):
    descriptor = make_datapackage(resources=[])
    dataset_dir = write_dataset(tmp_path, descriptor, csv_content="a,b\n1,2\n")
    errors = validate_package(dataset_dir)
    assert any("no resources declared" in e for e in errors)


def test_resource_file_not_found(tmp_path: Path):
    descriptor = make_datapackage()
    descriptor["resources"][0]["path"] = "missing.csv"
    dataset_dir = write_dataset(tmp_path, descriptor, csv_content="a,b\n1,2\n")
    (dataset_dir / "test.csv").unlink()
    errors = validate_package(dataset_dir)
    assert any("resource file not found" in e for e in errors)


def test_missing_resource_bytes(tmp_path: Path):
    descriptor = make_datapackage()
    dataset_dir = write_dataset(tmp_path, descriptor, csv_content="a,b\n1,2\n")
    descriptor = json.loads((dataset_dir / "datapackage.json").read_text(encoding="utf-8"))
    del descriptor["resources"][0]["bytes"]
    (dataset_dir / "datapackage.json").write_text(json.dumps(descriptor), encoding="utf-8")
    errors = validate_package(dataset_dir)
    assert any("missing fields" in e and "bytes" in e for e in errors)


def test_missing_resource_hash(tmp_path: Path):
    descriptor = make_datapackage()
    dataset_dir = write_dataset(tmp_path, descriptor, csv_content="a,b\n1,2\n")
    descriptor = json.loads((dataset_dir / "datapackage.json").read_text(encoding="utf-8"))
    del descriptor["resources"][0]["hash"]
    (dataset_dir / "datapackage.json").write_text(json.dumps(descriptor), encoding="utf-8")
    errors = validate_package(dataset_dir)
    assert any("missing fields" in e and "hash" in e for e in errors)


def test_bytes_mismatch(tmp_path: Path):
    descriptor = make_datapackage()
    dataset_dir = write_dataset(tmp_path, descriptor, csv_content="a,b\n1,2\n")
    descriptor["resources"][0]["bytes"] = 999
    (dataset_dir / "datapackage.json").write_text(json.dumps(descriptor), encoding="utf-8")
    errors = validate_package(dataset_dir)
    assert any("bytes mismatch" in e for e in errors)


def test_hash_mismatch(tmp_path: Path):
    descriptor = make_datapackage()
    dataset_dir = write_dataset(tmp_path, descriptor, csv_content="a,b\n1,2\n")
    descriptor["resources"][0]["hash"] = "00000000000000000000000000000000"
    (dataset_dir / "datapackage.json").write_text(json.dumps(descriptor), encoding="utf-8")
    errors = validate_package(dataset_dir)
    assert any("hash mismatch" in e for e in errors)


def test_valid_dataset(tmp_path: Path):
    descriptor = make_datapackage()
    dataset_dir = write_dataset(tmp_path, descriptor, csv_content="a,b\n1,2\n")
    errors = validate_package(dataset_dir)
    assert errors == []


def test_frictionless_schema_error(tmp_path: Path):
    descriptor = make_datapackage()
    dataset_dir = write_dataset(tmp_path, descriptor, csv_content="a,b\n1,2\n")
    # Declare a field that does not exist so frictionless reports a schema error.
    descriptor["resources"][0]["schema"] = {
        "fields": [
            {"name": "a", "type": "integer"},
            {"name": "b", "type": "integer"},
            {"name": "c", "type": "integer"},
        ]
    }
    (dataset_dir / "datapackage.json").write_text(json.dumps(descriptor), encoding="utf-8")
    errors = validate_package(dataset_dir)
    assert any("frictionless error" in e for e in errors)
