# ac-datasets

Miscellanous Asheron's Call datasets

## Commit convention

Every commit subject uses one of these forms:

```text
dataset(<dataset-name>): <description>
repo: <description>
repo(<scope>): <description>
```

`dataset` is for changes to a named dataset; use its lowercase, hyphen- or
underscore-separated directory name. Use `repo` for all other changes, with an
optional lowercase scope. Descriptions are required.

For a breaking change, add `!` immediately before the colon:

```text
dataset(locations)!: rename the location identifier column
repo(deployment)!: remove the legacy release step
```

The other Conventional Commits breaking-change marker is a `BREAKING CHANGE:`
footer in the commit body. It may be used to explain the impact, but `!` is the
required marker in this repository.

Install the tracked local commit hook once per clone:

```bash
git config core.hooksPath .githooks
```

GitHub also validates every pull request commit and enforces the same subject
pattern on `main`. Direct pushes, force pushes, and branch deletion are blocked;
changes must arrive through a pull request.
