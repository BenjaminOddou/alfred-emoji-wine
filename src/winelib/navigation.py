"""In-place navigation of the menu (tags & data).

The menu lives in the same Script Filter as the search (`wine`): a query starting with ">" opens it.
The whole navigation state is in the query, like a breadcrumb:

    ">"                      root menu
    ">tags›"                 list of tags
    ">tags›<id>›"            one tag
    ">tags›<id>›link›"       emojis that can be linked to the tag
    ">tags›<id>›unlink›"     emojis linked to the tag

Everything after the last "›" is free text (a filter, or the name of a tag to create / rename).
Navigation items are invalid items with an `autocomplete`, so Alfred changes the query in place:
no window reload, no external trigger, and Return / Tab / typing all behave the same everywhere.
Emojis come from the search index (search.Index), so the menu never reads api.json.
"""

from __future__ import annotations

from . import actions
from .alfred import action_variables, icon, item, matches

MENU = ">"  # a query starting with this opens the menu instead of searching emojis
SEP = "›"
MAX_RESULTS = 120  # keeps huge emoji lists snappy; type to narrow down

ICON_SYNC = "icons/sync.webp"
ICON_TAG = "icons/tag.webp"
ICON_INFO = "icons/info.webp"
ICON_NEW = "icons/new.webp"
ICON_DELETE = "icons/delete.webp"
ICON_RETURN = "icons/return.webp"

# tag operations (value of the `tag_op` variable)
OP_CREATE, OP_RENAME, OP_DELETE, OP_LINK, OP_UNLINK = "create", "rename", "delete", "link", "unlink"


def is_menu_query(query: str) -> bool:
    return query.lstrip().startswith(MENU)


def parse_query(query: str) -> tuple:
    """Split a menu query into (path segments, free text)."""
    query = query.lstrip()
    if query.startswith(MENU):
        query = query[len(MENU):]
    *path, text = query.split(SEP)
    return [segment.strip() for segment in path], text.strip()


def build_query(path: list, text: str = "") -> str:
    return MENU + "".join(segment + SEP for segment in path) + text


def goto_item(title: str, subtitle: str, target: str, icon_path: str = ICON_RETURN) -> dict:
    """Navigation that reopens Alfred on `target` (⏎), or autocompletes it in place (⇥).

    ⏎ goes through the `menu` action -> `emoji` external trigger, which works everywhere
    (back to an empty search included, where an empty autocomplete would do nothing).
    """
    return item(title, subtitle=subtitle, arg=target, autocomplete=target,
                variables=action_variables(actions.MENU), icon=icon(icon_path))


def _return_item(path: list) -> dict:
    return goto_item("Return", "Back to previous state", build_query(path[:-1]))


def _tag_op(op: str, tag_id: str = "") -> dict:
    return action_variables(actions.TAG, tag_op=op, tag_id=tag_id)


def _emojis_subtitle(tag: dict) -> str:
    return "Emojis: " + ", ".join(tag["emojis"]) if tag["emojis"] else "❌ No Emojis"


def data_items(index, grid: bool = False) -> list:
    """Tags, API information and Refresh: pinned on top of the search and of the menu."""
    info, language_name = index.info, index.language_name
    subtitle = "Create, modify or remove tags for %s" % language_name
    if grid:  # the grid cannot autocomplete: reopen Alfred on the menu (list view)
        tags = goto_item("Tags", subtitle, build_query(["tags"]), ICON_TAG)
        del tags["autocomplete"]
    else:
        tags = item("Tags", subtitle=subtitle, valid=False, autocomplete=build_query(["tags"]), icon=icon(ICON_TAG))
    return [
        tags,
        item(
            "API information",
            subtitle="Last update : %s ǀ %d Emojis ǀ %s ǀ Version : %s"
            % (info["time"], len(index.rows), language_name, info.get("workflow_version", "unknown")),
            valid=False,
            icon=icon(ICON_INFO),
        ),
        item(
            "Refresh the API",
            subtitle="Press ⏎ to grab emoji data with language : %s" % language_name,
            arg="",
            variables=action_variables(actions.REFRESH),
            icon=icon(ICON_SYNC),
        ),
    ]


def root_items(index, text: str) -> list:
    items = [goto_item("Back to search", "Search emojis", "")] + data_items(index)
    return [i for i in items if matches(text, i["title"])]


def tags_items(tags: list, text: str) -> list:
    items = [_return_item(["tags"])]
    if text:
        items.append(item("Create the tag '%s'" % text, arg=text, variables=_tag_op(OP_CREATE), icon=icon(ICON_NEW),
                          subtitle="Press ⏎ to create it, or keep typing to filter the tags"))
    else:
        items.append(item("Add a new tag", subtitle="Type the name of the tag you want to create", valid=False,
                          icon=icon(ICON_NEW)))
    for tag in tags:
        if matches(text, tag["title"]):
            items.append(item(tag["title"] or "No Title", subtitle=_emojis_subtitle(tag), valid=False,
                              autocomplete=build_query(["tags", tag["id"]]), icon=icon(ICON_TAG)))
    return items


def _emoji(row: list) -> dict:
    """Title and icon of an index row (its search item)."""
    import json

    element = json.loads(row[3])
    return {"title": element["title"], "icon": element["icon"]}


def tag_items(tag: dict, index, text: str) -> list:
    path = ["tags", tag["id"]]
    items = [_return_item(path)]
    if text:
        items.append(item("Rename the tag to '%s'" % text, subtitle="Current name: '%s'" % tag["title"], arg=text,
                          variables=_tag_op(OP_RENAME, tag["id"]), icon=icon(ICON_TAG)))
    else:
        items.append(item("Modify the tag's name", subtitle="Current name: '%s' ǀ type the new name" % tag["title"],
                          valid=False, icon=icon(ICON_TAG)))
    items.append(item("Link an emoji", subtitle="Link the tag to emojis", valid=False,
                      autocomplete=build_query(path + [OP_LINK]), icon=icon(ICON_NEW)))
    if tag["emojis"]:
        items.append(item("Unlink an emoji", subtitle="Unlink the tag from emojis", valid=False,
                          autocomplete=build_query(path + [OP_UNLINK]), icon=icon(ICON_DELETE)))
    items.append(item("Delete the tag", subtitle="Erase '%s' for good" % tag["title"], arg="",
                      variables=_tag_op(OP_DELETE, tag["id"]), icon=icon(ICON_DELETE)))
    linked = {emoji.encode() for emoji in tag["emojis"]}
    for row in [r for r in index.rows if r[1] in linked][:MAX_RESULTS]:
        items.append(dict(_emoji(row), subtitle=row[1].decode(), valid=False))
    return items


def emoji_picker_items(tag: dict, index, text: str, linking: bool) -> list:
    op = OP_LINK if linking else OP_UNLINK
    items = [_return_item(["tags", tag["id"], op])]
    linked = {emoji.encode() for emoji in tag["emojis"]}
    verb = ("Add '%s' to" if linking else "Remove '%s' from") % tag["title"]
    for row in index.find(text, shown_only=False):  # every skin tone: a linked emoji can always be unlinked
        if (row[1] in linked) != linking:
            emoji = row[1].decode()
            items.append(dict(_emoji(row), subtitle="%s %s" % (verb, emoji), arg=emoji,
                              variables=_tag_op(op, tag["id"])))
            if len(items) > MAX_RESULTS:
                break
    return items


def build_menu(query: str, index, tags: list) -> list:
    """All items of the menu for `query`."""
    path, text = parse_query(query)
    if path[:1] != ["tags"]:
        return root_items(index, text if not path else "")
    if len(path) == 1:
        return tags_items(tags, text)
    tag = next((t for t in tags if t["id"] == path[1]), None)
    if tag is None:  # stale breadcrumb (tag deleted): fall back to the tag list
        return tags_items(tags, "")
    if len(path) > 2 and path[2] in (OP_LINK, OP_UNLINK):
        return emoji_picker_items(tag, index, text, path[2] == OP_LINK)
    return tag_items(tag, index, text)


def next_query(op: str, tag_id: str) -> str:
    """Where the user lands after a tag operation."""
    if op in (OP_CREATE, OP_DELETE):
        return build_query(["tags"])
    if op == OP_RENAME:
        return build_query(["tags", tag_id])
    return build_query(["tags", tag_id, op])  # stay in the picker to chain several emojis
