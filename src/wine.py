#!/usr/bin/env python3
"""Script Filter (keyword `wine`): emoji search, or the menu when the query starts with ">"."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from winelib.search import respond  # noqa: E402
from winelib.settings import Settings  # noqa: E402


def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else ""
    sys.stdout.buffer.write(respond(Settings.from_env(workflow_dir=HERE), query))


if __name__ == "__main__":
    main()
