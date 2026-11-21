"""Script Filter JSON, Run Script output and text matching."""

from __future__ import annotations

import unicodedata
from itertools import filterfalse

from . import actions

# Alfred 6 top-level keys, on every response:
# - skipknowledge: results keep the script order (Tags / API information / Refresh stay on top, items have
#   no uid so Alfred learns nothing either);
# - strictmods: a modifier a row doesn't define (deactivated shortcut, no dictionary page, menu rows) does
#   nothing, instead of running the ⏎ action;
# - iconresize: icons keep their aspect ratio.
_HEAD = b'{"skipknowledge":true,"strictmods":true,"iconresize":"fit","items":['
_TAIL = b"]}"


def item(title: str, **fields) -> dict:
    """Build an item; None-valued fields are dropped."""
    result = {"title": title}
    result.update({k: v for k, v in fields.items() if v is not None})
    return result


def icon(path: str) -> dict:
    return {"path": path}


def action_variables(action: str, **extra: str) -> dict:
    variables = {"action": action}
    variables.update(extra)
    return variables


def dumps(data) -> str:
    """Compact JSON (Alfred reads every byte of it at each keystroke)."""
    import json  # not at import time: a search copies ready-made JSON and never needs it

    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def response(serialized_items: list) -> bytes:
    """Script Filter response (UTF-8) from items already serialized with `dumps` and encoded."""
    return _HEAD + b",".join(serialized_items) + _TAIL


def dump(items: list) -> bytes:
    return response([dumps(i).encode() for i in items])


def run_output(arg: str = "", title: str = "", text: str = "") -> str:
    """Run Script output: `arg` goes on, `notify_title` / `notify_text` feed the Post Notification output
    (Alfred 6 posts it with the macOS UserNotifications API; an empty text shows nothing)."""
    return dumps({"alfredworkflow": {"arg": arg, "variables": {"notify_title": title, "notify_text": text}}})


def normalize(text: str) -> str:
    """Lower-case, strip accents and squash whitespace so searches are forgiving."""
    text = unicodedata.normalize("NFKD", text.casefold())
    if not text.isascii():
        text = "".join(filterfalse(unicodedata.combining, text))  # C loop: the index normalizes ~4000 rows
    return " ".join(text.split())


def words(query: str) -> list:
    return normalize(query).split()


def matches(query: str, *haystack: str | None) -> bool:
    """True when every word of `query` appears somewhere in the haystack."""
    query_words = words(query)
    if not query_words:
        return True
    text = normalize(" ".join(h for h in haystack if h))
    return all(word in text for word in query_words)


def refresh_item(language_name: str, title: str) -> dict:
    """The 'grab the data' call-to-action shown when the API is missing or outdated."""
    return item(
        title,
        subtitle="Press ⏎ to grab emoji data with language : %s" % language_name,
        arg="",
        variables=action_variables(actions.REFRESH),
        icon=icon("icons/info.webp"),
    )
