"""Pure data logic: parse Unicode / CLDR sources and build the emoji list."""

from __future__ import annotations

import re

SKIN_TONE_NAMES = {
    0x1F3FB: "light skin tone",
    0x1F3FC: "medium-light skin tone",
    0x1F3FD: "medium skin tone",
    0x1F3FE: "medium-dark skin tone",
    0x1F3FF: "dark skin tone",
}
# Emojis whose CLDR "tags" are better derived from their title.
TITLE_AS_TAGS_PREFIXES = ("flag:", "keycap:")
_VARIATION_SELECTOR = "️"
_STATUS_RE = re.compile(r"\s;\s(?:fully-qualified|component)\s+#\s(\S+)\sE[\d.]+\s(.+)$")
_FILENAME_RE = re.compile(r"[:/\\]")


def parse_emoji_test(text: str) -> list:
    """Extract [{emoji, name}] from unicode.org `emoji-test.txt`."""
    emojis = []
    for line in text.splitlines():
        if "; fully-qualified" not in line and "; component" not in line:
            continue
        match = _STATUS_RE.search(line)
        if match:
            emojis.append({"emoji": match.group(1), "name": match.group(2).strip()})
    return emojis


def remove_skin_tones(emoji: str) -> str:
    return "".join(c for c in emoji if ord(c) not in SKIN_TONE_NAMES)


def base_emojis_with_variants(emojis) -> set:
    """Base emojis that also exist with a skin tone modifier."""
    return {remove_skin_tones(e) for e in emojis if remove_skin_tones(e) != e}


def get_skin_tones(emoji: str, bases_with_variants: set) -> list:
    """Skin tone labels: 'none' (tone-less variant), 'base' (no variants) or tone names."""
    if emoji in bases_with_variants:
        return ["none"]
    tones = []
    for char in emoji:
        tone = SKIN_TONE_NAMES.get(ord(char))
        if tone and tone not in tones:
            tones.append(tone)
    return tones or ["base"]


def parse_annotations(*xml_documents: str) -> dict:
    """Index CLDR annotation files by codepoint: {cp: {"tts": str, "tags": [str]}}.

    The first document wins over the following ones (annotations before derived).
    """
    import xml.etree.ElementTree as ET  # refresh only

    index: dict = {}
    for document in xml_documents:
        for node in ET.fromstring(document).iter("annotation"):
            cp = node.get("cp")
            if not cp or node.text is None:
                continue
            entry = index.setdefault(cp, {"tts": None, "tags": None})
            if node.get("type") == "tts":
                entry["tts"] = entry["tts"] or node.text
            else:
                entry["tags"] = entry["tags"] or [t.strip() for t in node.text.split("|")]
    return index


def annotate(emoji: str, name: str, index: dict) -> tuple:
    """Return (title, tags) for an emoji, or (None, None) when it is not translated."""
    entry = index.get(emoji.replace(_VARIATION_SELECTOR, ""))
    if not entry or entry["tts"] is None or entry["tags"] is None:
        return None, None
    title = entry["tts"]
    if name.startswith(TITLE_AS_TAGS_PREFIXES):
        tags = title.replace(":", " ").split()
    else:
        tags = list(entry["tags"])
    tags.append(emoji)
    return title, tags


def build_items(emojis: list, index: dict, image_names: set | None = None) -> list:
    """Assemble the api.json `items` list.

    `image_names` holds the names whose icon was rendered; None means "all of them".
    """
    bases = base_emojis_with_variants(e["emoji"] for e in emojis)
    items = []
    for entry in emojis:
        emoji, name = entry["emoji"], entry["name"]
        title, tags = annotate(emoji, name, index)
        items.append(
            {
                "name": name,
                "emoji": emoji,
                "title": title,
                "tags": tags,
                "image": image_names is None or name in image_names,
                "skin_tones": get_skin_tones(emoji, bases),
            }
        )
    return items


def icon_filename(name: str) -> str:
    """File name of an emoji icon, derived from its unicode name."""
    return _FILENAME_RE.sub("", name) + ".png"
