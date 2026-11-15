#!/usr/bin/env python3
"""Run Script: apply a tag operation. Prints the menu query to reopen (via the `emoji` trigger)."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from winelib.logs import fail, get_logger  # noqa: E402
from winelib.navigation import build_query  # noqa: E402
from winelib.settings import Settings  # noqa: E402
from winelib.tag_actions import apply_operation  # noqa: E402
from winelib.tags_store import load_tags, save_tags  # noqa: E402


def run(settings: Settings, op: str, tag_id: str, value: str) -> str:
    """Apply the operation and return the menu query to go back to."""
    tags = load_tags(settings.tags_file)
    query = apply_operation(tags, op, tag_id, value)
    if query is None:
        fail(settings, "Something went wrong, check the logs and report it as a GitHub issue",
             ValueError("invalid tag operation %r (tag %r, value %r)" % (op, tag_id, value)))
        return build_query(["tags"])
    save_tags(settings.tags_file, tags)
    get_logger(settings).info("tag %s %s %s", op, tag_id, value)
    return query


def main() -> None:
    settings = Settings.from_env(workflow_dir=HERE)
    value = sys.argv[1] if len(sys.argv) > 1 else ""
    query = run(settings, os.environ.get("tag_op", ""), os.environ.get("tag_id", ""), value)
    print(query, end="")


if __name__ == "__main__":
    main()
