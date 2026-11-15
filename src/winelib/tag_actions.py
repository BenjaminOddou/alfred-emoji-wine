"""Apply a tag operation chosen in the menu and report where to navigate next."""

from typing import Dict, List, Optional

from . import navigation as nav
from . import tags_store as store


def apply_operation(tags: List[Dict], op: str, tag_id: str, value: str) -> Optional[str]:
    """Mutate `tags` in place. Returns the next query, or None when the operation is invalid."""
    if op == nav.OP_CREATE:
        if not value.strip():
            return None
        store.create_tag(tags, value)
    elif op == nav.OP_DELETE:
        if not store.delete_tag(tags, tag_id):
            return None
    elif op == nav.OP_RENAME:
        if not value.strip() or not store.rename_tag(tags, tag_id, value):
            return None
    elif op == nav.OP_LINK:
        if not store.link_emoji(tags, tag_id, value):
            return None
    elif op == nav.OP_UNLINK:
        if not store.unlink_emoji(tags, tag_id, value):
            return None
    else:
        return None
    return nav.next_query(op, tag_id)
