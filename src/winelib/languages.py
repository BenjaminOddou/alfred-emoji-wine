"""Language list, read from the workflow's own user configuration."""

from __future__ import annotations


def load_languages(plist_path: str = "info.plist") -> list:
    import plistlib  # only when building the data or asking for it: not at every keystroke

    with open(plist_path, "rb") as handle:
        info = plistlib.load(handle)
    for entry in info.get("userconfigurationconfig", []):
        if entry.get("variable") == "language":
            return [{"title": t, "value": v} for t, v in entry["config"]["pairs"]]
    return []


def language_title(languages: list, value: str) -> str:
    for entry in languages:
        if entry["value"] == value:
            return entry["title"]
    return value
