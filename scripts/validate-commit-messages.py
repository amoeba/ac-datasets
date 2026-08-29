#!/usr/bin/env python3
"""Validate this repository's commit-message convention."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


SUBJECT_PATTERN = re.compile(
    r"^(?:"
    r"dataset\([a-z0-9]+(?:[-_][a-z0-9]+)*\)"
    r"|repo(?:\([a-z0-9]+(?:[-_][a-z0-9]+)*\))?"
    r")!?: \S(?:.*\S)?$"
)


def subject_from_message(message: str) -> str:
    return message.splitlines()[0] if message else ""


def validate_subject(subject: str) -> str | None:
    if SUBJECT_PATTERN.fullmatch(subject):
        return None
    return (
        f"Invalid commit subject: {subject!r}\n"
        "Expected one of:\n"
        "  dataset(<dataset-name>): <description>\n"
        "  repo: <description>\n"
        "  repo(<scope>): <description>\n"
        "Add ! immediately before : for a breaking change."
    )


def messages_from_range(commit_range: str) -> list[tuple[str, str]]:
    commit_ids = subprocess.run(
        ["git", "rev-list", "--reverse", commit_range],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    messages = []
    for commit_id in commit_ids:
        message = subprocess.run(
            ["git", "log", "-1", "--format=%B", commit_id],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        messages.append((commit_id, message))
    return messages


def main() -> int:
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--message-file", type=Path)
    source.add_argument("--range", dest="commit_range")
    args = parser.parse_args()

    if args.message_file:
        messages = [("commit message", args.message_file.read_text())]
    else:
        messages = messages_from_range(args.commit_range)

    errors = [
        f"{commit_id}: {error}"
        for commit_id, message in messages
        if (error := validate_subject(subject_from_message(message))) is not None
    ]
    if errors:
        print("\n\n".join(errors), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
