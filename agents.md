# Adding a new dataset

This project publishes Asheron's Call datasets through Datasette and deploys them with Dokku.

## Commit convention

Use `dataset(<name>): <description>` for dataset changes and `repo: <description>`
or `repo(<scope>): <description>` for everything else. Add `!` before `:` for
breaking changes. Do not push directly to `main`; open a pull request.

> **Use `uv` for all Python work in this repo.** Install dependencies with `uv sync`, run tools with `uv run`, and add packages with `uv add`.

## Where to put the data

- Most datasets belong in the `datasets/` folder, organized as `datasets/<name>/<name>.csv`.
- External datasets are fine. If the data lives elsewhere (a URL, another repo, an API), document the source in the metadata instead of copying it into `datasets/`.

## Add a metadata record

Every dataset must have a metadata record in `metadata.json` at the project root. Datasette reads this file automatically.

Example entry for a CSV named `datasets/locations/locations.csv`:

```json
{
  "title": "ac-datasets",
  "description": "Miscellaneous Asheron's Call datasets.",
  "databases": {
    "locations": {
      "tables": {
        "locations": {
          "title": "Locations",
          "description": "Named locations in Dereth, including dungeons and points of interest.",
          "source": "Asheron's Call community data",
          "source_url": "https://github.com/amoeba/ac-datasets",
          "license": "CC0",
          "license_url": "https://creativecommons.org/publicdomain/zero/1.0/"
        }
      }
    }
  }
}
```

When you add a new CSV, add a matching table entry under `databases.locations.tables`.

## Add a Frictionless Data Package

Every dataset folder must also contain a `datapackage.json` describing the data package. CI validates these packages on every push.

To create or update a data package for a dataset:

```bash
uv run scripts/generate_datapackage.py datasets/<name> --write
```

This writes `datasets/<name>/datapackage.json` with inferred schema, accurate file size, and an MD5 checksum. Review the generated file and fill in `title`, `description`, `sources`, and `licenses`.

To validate all data packages locally:

```bash
uv run scripts/validate_datapackages.py
```

To run the unit tests:

```bash
uv run pytest
```

The validator checks that:
- every folder under `datasets/` contains a `datapackage.json`
- each package is valid Frictionless Data
- required metadata (`name`, `title`, `description`, `sources`, `licenses`) is present
- reported file sizes and checksums match the actual files

CI runs these checks on every push and pull request. The workflow also runs `scripts/generate_datapackage.py --check` to make sure committed `datapackage.json` files are not stale.

## Hook it up to Datasette and Dokku

Datasette serves SQLite databases, not CSVs directly. The deployment pulls a pre-built database from GitHub Releases.

1. Build or update the SQLite database from the CSVs:

   ```bash
   csvs-to-sqlite datasets/locations/locations.csv locations.db
   ```

2. Attach the database to a GitHub Release named `latest`:

   ```bash
   gh release upload latest locations.db --clobber
   ```

   `bin/post_compile` downloads this file during the Dokku deploy:

   ```bash
   wget https://github.com/amoeba/ac-datasets/releases/download/latest/locations.db
   ```

3. The `Procfile` serves the downloaded database:

   ```
   web: datasette . -h 0.0.0.0 -p $PORT --cors
   ```

4. Deploy to Dokku as usual:

   ```bash
   git push dokku main
   ```

## Checklist

- [ ] CSV added to `datasets/<name>/<name>.csv` (or external source documented)
- [ ] Metadata entry added to `metadata.json`
- [ ] `datapackage.json` added to `datasets/<name>/` and validated with `uv run scripts/validate_datapackages.py`
- [ ] `locations.db` rebuilt and uploaded to the `latest` GitHub Release
- [ ] Changes committed and pushed to Dokku
