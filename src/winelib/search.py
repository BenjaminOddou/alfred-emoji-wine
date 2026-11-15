"""Build the Script Filter results of the `wine` search."""

import hashlib
import json
import os
import re
from urllib.parse import quote
from typing import Dict, List, Optional

from . import actions
from . import navigation as nav
from .alfred import action_variables, dump, icon, matches, refresh_item
from .emoji_data import icon_filename
from .settings import SHORTCUT_ARG, SHORTCUT_DISABLED, Settings
from .storage import read_json, write_json
from .tags_store import emoji_tags_index, load_tags

_SLUG_REMOVE = re.compile(r"[:(),]")
_SLUG_DASH = re.compile(r"[’\s]+")


def dictionary_slug(title: str) -> str:
    """URL slug used by emoji dictionaries ("Face with Tears" -> "face-with-tears")."""
    return _SLUG_DASH.sub("-", _SLUG_REMOVE.sub("", title).strip()).lower()


def dictionary_url(settings: Settings, emoji: str, title: Optional[str]) -> Optional[str]:
    if settings.emoji_dictionary == "emojiall.com":
        slug = "emoji/%s" % emoji
    elif title:
        slug = dictionary_slug(title)
    else:
        return None
    country = "%s/" % settings.language.lower() if settings.language != "en" else ""
    return "https://%s/%s%s" % (settings.emoji_dictionary, country, quote(slug, safe="/-"))


def _shortcuts(settings: Settings, emoji: str, url: Optional[str]):
    """(modifier, subtitle, action, payload) for every available action."""
    rows = [
        (settings.short_copy, 'copy "%s" to the clipboard' % emoji, actions.COPY, emoji),
        (settings.short_paste, 'paste "%s" into frontmost application' % emoji, actions.PASTE, emoji),
    ]
    if url:
        rows.append(
            (settings.short_web, "find the emoji in %s" % settings.emoji_dictionary, actions.WEB, url)
        )
    return rows


def build_item(entry: Dict, settings: Settings, tag_titles: List[str]) -> Dict:
    name, emoji, title, tags = entry["name"], entry["emoji"], entry["title"], entry["tags"]
    keywords = [title or name] + tags if tags is not None else [name]
    match = " ".join(keywords + tag_titles)

    translated = settings.language != "en" and bool(title)
    display = title if translated else name
    url = dictionary_url(settings, emoji, display if (translated or settings.language == "en") else None)

    icon_file = icon_filename(name) if entry["image"] else "unicode.png"
    element = {
        "uid": name,
        "title": display,
        "match": match,
        "icon": icon(os.path.join(settings.icons_dir, icon_file)),
    }
    mods = {}
    for shortcut, subtitle, action, payload in _shortcuts(settings, emoji, url):
        if not shortcut or shortcut == SHORTCUT_DISABLED:
            continue
        variables = action_variables(action)
        if shortcut == SHORTCUT_ARG:
            element.update(subtitle=subtitle[0].upper() + subtitle[1:], arg=payload, variables=variables)
            continue
        mod = {"subtitle": "Press ⏎ to " + subtitle, "arg": payload, "variables": variables}
        if action == actions.WEB:
            mod["icon"] = icon(settings.dictionary_icon)
        mods[shortcut] = mod
    if mods:
        element["mods"] = mods
    return element


def wanted_skin_tone(entry: Dict, skin_tone: str) -> bool:
    tones = entry["skin_tones"]
    return skin_tone == "all" or skin_tone in tones or "base" in tones


def build_items(api: Dict, tags: List[Dict], settings: Settings) -> List[Dict]:
    tag_index = emoji_tags_index(tags)
    return [
        build_item(entry, settings, tag_index.get(entry["emoji"], []))
        for entry in api["items"]
        if wanted_skin_tone(entry, settings.skin_tone)
    ]


def _stamp(path: str):
    try:
        stat = os.stat(path)
        return [stat.st_mtime_ns, stat.st_size]
    except OSError:
        return None


def cache_key(settings: Settings) -> str:
    """Changes whenever settings, api.json or the tags file change."""
    raw = json.dumps(
        [list(settings.fingerprint), settings.padding, _stamp(settings.api_file), _stamp(settings.tags_file)]
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _api_problem(api: Optional[Dict], settings: Settings, language_name: str) -> Optional[str]:
    """Response asking for a refresh when api.json is missing or outdated, else None."""
    if not api:
        return dump([refresh_item(language_name, "No API detected")])
    info = api["info"]
    if settings.language != info["lang"]["value"] or settings.workflow_version != info.get("workflow_version"):
        return dump([refresh_item(language_name, "Refresh the API")])
    return None


def cached_items(settings: Settings, language_name: str):
    """(pinned, items, None) for the current settings, or (None, None, refresh response).

    `pinned` are the Tags / API information / Refresh items. Everything is cached on disk.
    """
    key = cache_key(settings)
    cached = read_json(settings.search_cache_file)
    if isinstance(cached, dict) and cached.get("key") == key:
        return cached.get("pinned", []), cached["items"], None

    api = read_json(settings.api_file)
    problem = _api_problem(api, settings, language_name)
    if problem:
        return None, None, problem
    pinned = nav.data_items(api, language_name, grid=settings.style == "grid")
    items = build_items(api, read_json(settings.tags_file) or [], settings)
    write_json(settings.search_cache_file, {"key": key, "pinned": pinned, "items": items})
    return pinned, items, None


def respond(settings: Settings, language_name: str, query: str) -> str:
    """Single entry point of the `wine` Script Filter: emoji search or menu."""
    if nav.is_menu_query(query):
        api = read_json(settings.api_file)
        problem = _api_problem(api, settings, language_name)
        if problem:
            return problem
        return dump(nav.build_menu(query, api, load_tags(settings.tags_file), settings, language_name))

    pinned, items, problem = cached_items(settings, language_name)
    if problem:
        return problem
    query = query.strip()
    if not query:
        return dump(pinned + items)
    # while typing, pinned items stay on top only when they match (⏎ must never refresh by accident)
    return dump(
        [i for i in pinned if matches(query, i["title"])]
        + [i for i in items if matches(query, i["match"], i["title"])]
    )
