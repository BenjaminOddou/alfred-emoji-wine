"""Apply a tag operation chosen in the menu and report where to navigate next."""

from __future__ import annotations

from . import navigation as nav
from . import tags_store as store


def apply_operation(tags: list, op: str, tag_id: str, value: str) -> str | None:
    """Mutate `tags` in place. Returns the next query, or None when the operation is invalid."""
    if op == nav.OP_CREATE:
        ok = bool(value.strip()) and bool(store.create_tag(tags, value))
    elif op == nav.OP_RENAME:
        ok = bool(value.strip()) and store.rename_tag(tags, tag_id, value)
    elif op == nav.OP_DELETE:
        ok = store.delete_tag(tags, tag_id)
    elif op == nav.OP_LINK:
        ok = store.link_emoji(tags, tag_id, value)
    elif op == nav.OP_UNLINK:
        ok = store.unlink_emoji(tags, tag_id, value)
    else:
        ok = False
    return nav.next_query(op, tag_id) if ok else None
