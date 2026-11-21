#!/usr/bin/env python3
"""Run Script: download emoji data, render icons and write api.json. Prints the notification to post."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from winelib.api_builder import build_api  # noqa: E402
from winelib.languages import language_title, load_languages  # noqa: E402
from winelib.logs import script_output  # noqa: E402
from winelib.settings import Settings  # noqa: E402


def main() -> None:
    settings = Settings.from_env(workflow_dir=HERE)
    language_name = language_title(load_languages(settings.plist_file), settings.language)
    print(script_output(settings, notice=build_api(settings, language_name)), end="")


if __name__ == "__main__":
    main()
