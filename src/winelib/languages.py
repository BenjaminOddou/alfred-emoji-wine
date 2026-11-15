"""Language list, read from the workflow's own user configuration."""

import os
import plistlib
from typing import Dict, List


def load_languages(plist_path: str = "info.plist") -> List[Dict[str, str]]:
    with open(plist_path, "rb") as handle:
        info = plistlib.load(handle)
    for entry in info.get("userconfigurationconfig", []):
        if entry.get("variable") == "language":
            return [{"title": t, "value": v} for t, v in entry["config"]["pairs"]]
    return []


def language_title(languages: List[Dict[str, str]], value: str) -> str:
    for entry in languages:
        if entry["value"] == value:
            return entry["title"]
    return value
