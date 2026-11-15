"""Custom tags: {id, title, emojis[]} stored per language."""

import secrets
from typing import Dict, List, Optional

from .storage import read_json, write_json

Tag = Dict[str, object]


def load_tags(path: str) -> List[Tag]:
    data = read_json(path)
    return data if isinstance(data, list) else []


def save_tags(path: str, tags: List[Tag]) -> None:
    write_json(path, tags, indent=4)


def find_tag(tags: List[Tag], tag_id: str) -> Optional[Tag]:
    return next((t for t in tags if t["id"] == tag_id), None)


def create_tag(tags: List[Tag], title: str) -> Tag:
    tag = {"id": secrets.token_hex(6), "title": title.strip(), "emojis": []}
    tags.append(tag)
    return tag


def delete_tag(tags: List[Tag], tag_id: str) -> bool:
    tag = find_tag(tags, tag_id)
    if tag is None:
        return False
    tags.remove(tag)
    return True


def rename_tag(tags: List[Tag], tag_id: str, title: str) -> bool:
    tag = find_tag(tags, tag_id)
    if tag is None:
        return False
    tag["title"] = title.strip()
    return True


def link_emoji(tags: List[Tag], tag_id: str, emoji: str) -> bool:
    tag = find_tag(tags, tag_id)
    if tag is None:
        return False
    if emoji not in tag["emojis"]:
        tag["emojis"].append(emoji)
    return True


def unlink_emoji(tags: List[Tag], tag_id: str, emoji: str) -> bool:
    tag = find_tag(tags, tag_id)
    if tag is None or emoji not in tag["emojis"]:
        return False
    tag["emojis"].remove(emoji)
    return True


def emoji_tags_index(tags: List[Tag]) -> Dict[str, List[str]]:
    """{emoji: [tag titles]} for fast search enrichment."""
    index: Dict[str, List[str]] = {}
    for tag in tags:
        for emoji in tag["emojis"]:
            index.setdefault(emoji, []).append(tag["title"])
    return index
