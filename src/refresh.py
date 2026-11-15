#!/usr/bin/env python3
"""Run Script: download emoji data, render icons and write api.json."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from winelib.api_builder import build_api  # noqa: E402
from winelib.languages import load_languages  # noqa: E402
from winelib.settings import Settings  # noqa: E402


def main() -> int:
    settings = Settings.from_env(workflow_dir=HERE)
    languages = load_languages(os.path.join(HERE, "info.plist"))
    return 0 if build_api(settings, languages) else 1


if __name__ == "__main__":
    sys.exit(main())
