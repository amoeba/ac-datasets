from scripts.dataset_release_needed import release_needed


def package(resource_hash: str) -> dict:
    return {
        "resources": [
            {
                "name": "test",
                "path": "test.csv",
                "hash": resource_hash,
            }
        ]
    }


def test_new_dataset_requires_release():
    assert release_needed({}, {"test-dataset": package("new-hash")})


def test_removed_dataset_requires_release():
    assert release_needed({"test-dataset": package("old-hash")}, {})


def test_resource_checksum_change_requires_release():
    assert release_needed(
        {"test-dataset": package("old-hash")},
        {"test-dataset": package("new-hash")},
    )


def test_unchanged_resource_checksum_does_not_require_release():
    assert not release_needed(
        {"test-dataset": package("same-hash")},
        {"test-dataset": package("same-hash")},
    )


def test_metadata_change_without_checksum_change_does_not_require_release():
    previous = package("same-hash")
    current = package("same-hash")
    current["title"] = "Renamed dataset"
    current["resources"][0]["path"] = "renamed.csv"

    assert not release_needed({"test-dataset": previous}, {"test-dataset": current})
