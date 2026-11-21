"""The `wine` Script Filter: emoji search, or the menu when the query starts with ">".

The script runs at every keystroke, so the results are prepared once in an index file (cache folder):

    line 1    key: settings + api.json and tags file stamps (the index is rebuilt when one changes)
    line 2    api.json "info"
    line 3    number of pinned rows
    then      pinned rows (Tags, API information, Refresh), then one row per emoji:
              shown TAB emoji TAB normalized search text TAB item JSON

A search compares the query words with the normalized text and copies the item JSON as is, in bytes: no
decoding, no JSON, no accent stripping per item, no plist. The search path doesn't even import json or re.
"""

from __future__ import annotations

import os

from . import actions
from . import navigation as nav
from .alfred import action_variables, dump, dumps, icon, normalize, refresh_item, response, words
from .settings import SHORTCUT_ARG, SHORTCUT_DISABLED, Settings
from .storage import read_bytes, read_json, write_file
from .tags_store import emoji_tags_index, load_tags

INDEX_FORMAT = 3  # bump when the rows change


def dictionary_slug(title: str) -> str:
    """URL slug used by emoji dictionaries ("Face with Tears" -> "face-with-tears")."""
    import re

    return re.sub(r"[’\s]+", "-", re.sub(r"[:(),]", "", title).strip()).lower()


def dictionary_url(settings: Settings, emoji: str, title: str | None) -> str | None:
    if settings.emoji_dictionary == "emojiall.com":
        slug = "emoji/%s" % emoji
    elif title:
        slug = dictionary_slug(title)
    else:
        return None
    from urllib.parse import quote

    country = "%s/" % settings.language.lower() if settings.language != "en" else ""
    return "https://%s/%s%s" % (settings.emoji_dictionary, country, quote(slug, safe="/-"))


def _shortcuts(settings: Settings, emoji: str, url: str | None) -> list:
    """(modifier, subtitle, action, payload) for every available action."""
    rows = [
        (settings.short_copy, 'copy "%s" to the clipboard' % emoji, actions.COPY, emoji),
        (settings.short_paste, 'paste "%s" into frontmost application' % emoji, actions.PASTE, emoji),
    ]
    if url:
        rows.append((settings.short_web, "find the emoji in %s" % settings.emoji_dictionary, actions.WEB, url))
    return rows


def build_item(entry: dict, settings: Settings, tag_titles: list) -> tuple:
    """(Alfred item, normalized search text) of an emoji. Items have no uid: Alfred keeps the script order."""
    from .emoji_data import icon_filename

    name, emoji, title, tags = entry["name"], entry["emoji"], entry["title"], entry["tags"]
    keywords = [title or name] + tags if tags is not None else [name]
    match = " ".join(keywords + tag_titles)

    translated = settings.language != "en" and bool(title)
    display = title if translated else name
    url = dictionary_url(settings, emoji, display if (translated or settings.language == "en") else None)

    icon_file = icon_filename(name) if entry["image"] else "unicode.png"
    element = {"title": display, "icon": icon(os.path.join(settings.icons_dir, icon_file))}
    if settings.style == "grid":  # the Grid View filters by itself; the list is filtered here
        element["match"] = match
    mods = {}
    for shortcut, subtitle, action, payload in _shortcuts(settings, emoji, url):
        if not shortcut or shortcut == SHORTCUT_DISABLED:
            continue  # strictmods: the modifier does nothing
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
    # each word once: a query word (no space) is in the text only if it is in one of its words
    return element, " ".join(dict.fromkeys(normalize(match + " " + display).split()))


def wanted_skin_tone(entry: dict, skin_tone: str) -> bool:
    tones = entry["skin_tones"]
    return skin_tone == "all" or skin_tone in tones or "base" in tones


def _row(shown: bool, emoji: str, text: str, element: dict) -> list:
    return [b"1" if shown else b"0", emoji.encode(), text.encode(), dumps(element).encode()]


class Index:
    """api.json ready to search. Rows hold UTF-8 bytes: [shown (b"1" / b"0"), emoji, search text, item JSON]
    (a UTF-8 substring matches exactly like the text it encodes)."""

    __slots__ = ("_info", "pinned", "rows")

    def __init__(self, info, pinned: list, rows: list) -> None:
        self._info, self.pinned, self.rows = info, pinned, rows

    @property
    def info(self) -> dict:
        if isinstance(self._info, bytes):  # parsed on demand: the menu needs it, a search doesn't
            import json

            self._info = json.loads(self._info)
        return self._info

    @property
    def language_name(self) -> str:
        return self.info["lang"]["title"]

    @classmethod
    def build(cls, api: dict, tags: list, settings: Settings) -> Index:
        tag_index = emoji_tags_index(tags)
        rows = []
        for entry in api["items"]:
            element, text = build_item(entry, settings, tag_index.get(entry["emoji"], []))
            rows.append(_row(wanted_skin_tone(entry, settings.skin_tone), entry["emoji"], text, element))
        index = cls(api["info"], [], rows)
        index.pinned = [_row(True, "", normalize(i["title"]), i)
                        for i in nav.data_items(index, grid=settings.style == "grid")]
        return index

    @classmethod
    def parse(cls, data: bytes, key: str) -> Index | None:
        lines = data.split(b"\n")
        if len(lines) < 3 or lines[0] != key.encode():
            return None
        rows = [line.split(b"\t", 3) for line in lines[3:] if line]
        pinned = int(lines[2])
        return cls(lines[1], rows[:pinned], rows[pinned:])

    def serialize(self, key: str) -> bytes:
        head = [key.encode(), dumps(self.info).encode(), b"%d" % len(self.pinned)]
        return b"\n".join(head + [b"\t".join(row) for row in self.pinned + self.rows])

    def find(self, query: str, shown_only: bool = True, pinned: bool = False):
        """Rows matching every word of `query`: shown ones only (preferred skin tone), pinned rows first."""
        query_words = [word.encode() for word in words(query)]
        for row in self.pinned + self.rows if pinned else self.rows:
            if (not shown_only or row[0] == b"1") and all(word in row[2] for word in query_words):
                yield row


def _stamp(path: str):
    try:
        stat = os.stat(path)
        return stat.st_mtime_ns, stat.st_size
    except OSError:
        return None


def index_key(settings: Settings) -> str:
    """Changes whenever settings, api.json or the tags file change."""
    return repr((INDEX_FORMAT, settings.fingerprint, _stamp(settings.api_file), _stamp(settings.tags_file)))


def _api_problem(api: dict | None, settings: Settings, language_name: str | None) -> bytes | None:
    """Response asking for a refresh when api.json is missing or outdated, else None."""
    if api and settings.language == api["info"]["lang"]["value"] \
            and settings.workflow_version == api["info"].get("workflow_version"):
        return None
    if language_name is None:  # read the plist only here, not at every keystroke
        from .languages import language_title, load_languages

        language_name = language_title(load_languages(settings.plist_file), settings.language)
    return dump([refresh_item(language_name, "Refresh the API" if api else "No API detected")])


def load_index(settings: Settings, language_name: str | None = None) -> tuple:
    """(index, None), or (None, refresh response) when api.json is missing or outdated."""
    key = index_key(settings)
    data = read_bytes(settings.index_file)
    index = Index.parse(data, key) if data else None
    if index is not None:
        return index, None
    api = read_json(settings.api_file)
    problem = _api_problem(api, settings, language_name)
    if problem:
        return None, problem
    index = Index.build(api, load_tags(settings.tags_file), settings)
    write_file(settings.index_file, index.serialize(key))
    return index, None


def respond(settings: Settings, query: str, language_name: str | None = None) -> bytes:
    """Single entry point of the `wine` Script Filter: emoji search or menu (UTF-8 JSON)."""
    index, problem = load_index(settings, language_name)
    if problem:
        return problem
    if nav.is_menu_query(query):
        return dump(nav.build_menu(query, index, load_tags(settings.tags_file)))
    # while typing, pinned items stay on top only when they match (⏎ must never refresh by accident)
    return response([row[3] for row in index.find(query, pinned=True)])
