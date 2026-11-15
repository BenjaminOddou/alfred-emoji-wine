"""Helpers to build Script Filter JSON."""

import json
import unicodedata
from typing import Dict, List, Optional

from . import actions


def item(title: str, **fields) -> Dict:
    """Build an item; None-valued fields are dropped."""
    result = {"title": title}
    result.update({k: v for k, v in fields.items() if v is not None})
    return result


def icon(path: str) -> Dict[str, str]:
    return {"path": path}


def action_variables(action: str, **extra: str) -> Dict[str, str]:
    variables = {"action": action}
    variables.update(extra)
    return variables


def dump(items: List[Dict], **top_level) -> str:
    payload = {"items": items}
    payload.update(top_level)
    return json.dumps(payload, ensure_ascii=False)


def normalize(text: str) -> str:
    """Lower-case and strip accents so searches are forgiving."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def matches(query: str, *haystack: Optional[str]) -> bool:
    """True when every word of `query` appears somewhere in the haystack."""
    words = normalize(query).split()
    if not words:
        return True
    text = normalize(" ".join(h for h in haystack if h))
    return all(word in text for word in words)


def refresh_item(language_name: str, title: str) -> Dict:
    """The 'grab the data' call-to-action shown when the API is missing or outdated."""
    return item(
        title,
        subtitle="Press ⏎ to grab emoji data with language : %s" % language_name,
        arg="",
        variables=action_variables(actions.REFRESH),
        icon=icon("icons/info.webp"),
    )
