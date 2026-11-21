"""Icon generation: emoji glyphs through AppKit (osascript/JXA), assets with pure Python."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile

from . import png
from .emoji_data import icon_filename
from .settings import ICON_SIZE

RENDER_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "render_icons.js")
PADDING_MARKER = ".padding"


def icons_are_current(icons_dir: str, padding: int) -> bool:
    """True when the icons folder was rendered with the same padding."""
    try:
        with open(os.path.join(icons_dir, PADDING_MARKER), encoding="utf-8") as handle:
            return handle.read().strip() == str(padding)
    except OSError:
        return False


def prepare_icons_dir(icons_dir: str, padding: int) -> None:
    """Create the icons folder; wipe it when the padding changed (cached icons are stale)."""
    if os.path.isdir(icons_dir) and not icons_are_current(icons_dir, padding):
        for entry in os.listdir(icons_dir):
            path = os.path.join(icons_dir, entry)
            if os.path.isfile(path):
                os.unlink(path)
    os.makedirs(icons_dir, exist_ok=True)
    with open(os.path.join(icons_dir, PADDING_MARKER), "w", encoding="utf-8") as handle:
        handle.write(str(padding))


def missing_jobs(emojis: list, icons_dir: str) -> list:
    """Jobs for the emojis that have no icon yet (icons do not depend on the language)."""
    jobs, seen = [], set()
    for entry in emojis:
        filename = icon_filename(entry["name"])
        if filename in seen or os.path.exists(os.path.join(icons_dir, filename)):
            continue
        seen.add(filename)
        jobs.append({"emoji": entry["emoji"], "file": filename})
    return jobs


def render_emoji_icons(
    jobs: list,
    icons_dir: str,
    padding: int,
    runner=subprocess.run,
) -> list:
    """Render every job with a single osascript call. Returns the files that failed."""
    if not jobs:
        return []
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
        json.dump(jobs, handle, ensure_ascii=False)
        jobs_path = handle.name
    try:
        result = runner(
            ["osascript", "-l", "JavaScript", RENDER_SCRIPT, jobs_path, icons_dir,
             str(ICON_SIZE), str(padding)],
            capture_output=True, text=True, check=True,
        )
    finally:
        os.unlink(jobs_path)
    output = (result.stdout or "").strip()
    return json.loads(output) if output else []


def install_assets(assets_dir: str, icons_dir: str, padding: int) -> None:
    """Copy the bundled icons (unicode fallback, dictionaries) with transparent padding."""
    for name in os.listdir(assets_dir):
        if not name.endswith(".png"):
            continue
        with open(os.path.join(assets_dir, name), "rb") as handle:
            data = handle.read()
        with open(os.path.join(icons_dir, name), "wb") as handle:
            handle.write(png.pad_png(data, padding) if padding else data)


def rendered_names(emojis: list, icons_dir: str) -> set:
    """Names of the emojis that have an icon on disk."""
    return {e["name"] for e in emojis if os.path.exists(os.path.join(icons_dir, icon_filename(e["name"])))}
