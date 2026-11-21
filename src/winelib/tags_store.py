"""Custom tags: {id, title, emojis[]} stored per language."""

from __future__ import annotations

import os

from .storage import read_json, write_json


def load_tags(path: str) -> list:
    data = read_json(path)
    return data if isinstance(data, list) else []


def save_tags(path: str, tags: list) -> None:
    write_json(path, tags, indent=4)


def find_tag(tags: list, tag_id: str) -> dict | None:
    return next((t for t in tags if t["id"] == tag_id), None)


def create_tag(tags: list, title: str) -> dict:
    tag = {"id": os.urandom(6).hex(), "title": title.strip(), "emojis": []}
    tags.append(tag)
    return tag


def delete_tag(tags: list, tag_id: str) -> bool:
    tag = find_tag(tags, tag_id)
    if tag is None:
        return False
    tags.remove(tag)
    return True


def rename_tag(tags: list, tag_id: str, title: str) -> bool:
    tag = find_tag(tags, tag_id)
    if tag is None:
        return False
    tag["title"] = title.strip()
    return True


def link_emoji(tags: list, tag_id: str, emoji: str) -> bool:
    tag = find_tag(tags, tag_id)
    if tag is None:
        return False
    if emoji not in tag["emojis"]:
        tag["emojis"].append(emoji)
    return True


def unlink_emoji(tags: list, tag_id: str, emoji: str) -> bool:
    tag = find_tag(tags, tag_id)
    if tag is None or emoji not in tag["emojis"]:
        return False
    tag["emojis"].remove(emoji)
    return True


def emoji_tags_index(tags: list) -> dict:
    """{emoji: [tag titles]} for fast search enrichment."""
    index: dict = {}
    for tag in tags:
        for emoji in tag["emojis"]:
            index.setdefault(emoji, []).append(tag["title"])
    return index
