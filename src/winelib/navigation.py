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
"""

from typing import Dict, List, Optional, Tuple

from . import actions
from .alfred import action_variables, icon, item, matches
from .emoji_data import icon_filename
from .settings import Settings

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


def parse_query(query: str) -> Tuple[List[str], str]:
    """Split a menu query into (path segments, free text)."""
    query = query.lstrip()
    if query.startswith(MENU):
        query = query[len(MENU):]
    *path, text = query.split(SEP)
    return [segment.strip() for segment in path], text.strip()


def build_query(path: List[str], text: str = "") -> str:
    return MENU + "".join(segment + SEP for segment in path) + text


def _go(path: List[str]) -> str:
    """Query that navigates to `path`."""
    return build_query(path)


def goto_item(title: str, subtitle: str, target: str, icon_path: str = ICON_RETURN) -> Dict:
    """Navigation that reopens Alfred on `target` (⏎), or autocompletes it in place (⇥).

    ⏎ goes through the `menu` action -> `emoji` external trigger, which works everywhere
    (back to an empty search included, where an empty autocomplete would do nothing).
    """
    return item(
        title,
        subtitle=subtitle,
        arg=target,
        autocomplete=target,
        variables=action_variables(actions.MENU),
        icon=icon(icon_path),
    )


def _return_item(path: List[str]) -> Dict:
    return goto_item("Return", "Back to previous state", _go(path[:-1]))


def _tag_op(op: str, tag_id: str = "", **extra) -> Dict[str, str]:
    return action_variables(actions.TAG, tag_op=op, tag_id=tag_id, **extra)


def _emojis_subtitle(tag: Dict) -> str:
    return "Emojis: " + ", ".join(tag["emojis"]) if tag["emojis"] else "❌ No Emojis"


def _emoji_icon(settings: Settings, entry: Dict) -> Dict:
    name = icon_filename(entry["name"]) if entry["image"] else "unicode.png"
    return icon("%s/%s" % (settings.icons_dir, name))


def _emoji_title(entry: Dict) -> str:
    return entry["title"] or entry["name"]


def data_items(api: Dict, language_name: str, grid: bool = False) -> List[Dict]:
    """Tags, API information and Refresh: pinned on top of the search and of the menu."""
    info = api["info"]
    if grid:  # the grid cannot autocomplete: reopen Alfred on the menu (list view)
        tags = goto_item("Tags", "Create, modify or remove tags for %s" % language_name, _go(["tags"]), ICON_TAG)
        del tags["autocomplete"]
    else:
        tags = item(
            "Tags",
            subtitle="Create, modify or remove tags for %s" % language_name,
            valid=False,
            autocomplete=_go(["tags"]),
            icon=icon(ICON_TAG),
        )
    return [
        dict(tags, uid="emoji-wine-tags"),
        item(
            "API information",
            uid="emoji-wine-info",
            subtitle="Last update : %s ǀ %d Emojis ǀ %s ǀ Version : %s"
            % (info["time"], len(api["items"]), info["lang"]["title"], info.get("workflow_version", "unknown")),
            valid=False,
            icon=icon(ICON_INFO),
        ),
        item(
            "Refresh the API",
            uid="emoji-wine-refresh",
            subtitle="Press ⏎ to grab emoji data with language : %s" % language_name,
            arg="",
            variables=action_variables(actions.REFRESH),
            icon=icon(ICON_SYNC),
        ),
    ]


def root_items(api: Dict, language_name: str, text: str) -> List[Dict]:
    items = [goto_item("Back to search", "Search emojis", "")] + data_items(api, language_name)
    return [i for i in items if matches(text, i["title"])]


def tags_items(tags: List[Dict], text: str) -> List[Dict]:
    items = [_return_item(["tags"])]
    if text:
        items.append(
            item(
                "Create the tag '%s'" % text,
                subtitle="Press ⏎ to create it, or keep typing to filter the tags",
                arg=text,
                variables=_tag_op(OP_CREATE),
                icon=icon(ICON_NEW),
            )
        )
    else:
        items.append(
            item(
                "Add a new tag",
                subtitle="Type the name of the tag you want to create",
                valid=False,
                icon=icon(ICON_NEW),
            )
        )
    for tag in tags:
        if matches(text, tag["title"]):
            items.append(
                item(
                    tag["title"] or "No Title",
                    subtitle=_emojis_subtitle(tag),
                    valid=False,
                    autocomplete=_go(["tags", tag["id"]]),
                    icon=icon(ICON_TAG),
                )
            )
    return items


def tag_items(tag: Dict, api: Dict, settings: Settings, text: str) -> List[Dict]:
    path = ["tags", tag["id"]]
    items = [_return_item(path)]
    if text:
        items.append(
            item(
                "Rename the tag to '%s'" % text,
                subtitle="Current name: '%s'" % tag["title"],
                arg=text,
                variables=_tag_op(OP_RENAME, tag["id"]),
                icon=icon(ICON_TAG),
            )
        )
    else:
        items.append(
            item("Modify the tag's name", subtitle="Current name: '%s' ǀ type the new name" % tag["title"],
                 valid=False, icon=icon(ICON_TAG))
        )
    items.append(
        item("Link an emoji", subtitle="Link the tag to emojis", valid=False,
             autocomplete=_go(path + ["link"]), icon=icon(ICON_NEW))
    )
    if tag["emojis"]:
        items.append(
            item("Unlink an emoji", subtitle="Unlink the tag from emojis", valid=False,
                 autocomplete=_go(path + ["unlink"]), icon=icon(ICON_DELETE))
        )
    items.append(
        item("Delete the tag", subtitle="Erase '%s' for good" % tag["title"], arg="",
             variables=_tag_op(OP_DELETE, tag["id"]), icon=icon(ICON_DELETE))
    )
    linked = [e for e in api["items"] if e["emoji"] in tag["emojis"]]
    for entry in linked[:MAX_RESULTS]:
        items.append(item(_emoji_title(entry), subtitle=entry["emoji"], valid=False,
                          icon=_emoji_icon(settings, entry)))
    return items


def emoji_picker_items(tag: Dict, api: Dict, settings: Settings, text: str, linking: bool) -> List[Dict]:
    path = ["tags", tag["id"], OP_LINK if linking else OP_UNLINK]
    items = [_return_item(path)]
    op = OP_LINK if linking else OP_UNLINK
    count = 0
    for entry in api["items"]:
        if (entry["emoji"] in tag["emojis"]) == linking:
            continue
        if not matches(text, _emoji_title(entry), entry["name"], " ".join(entry["tags"] or [])):
            continue
        verb = "Add '%s' to" if linking else "Remove '%s' from"
        items.append(
            item(
                _emoji_title(entry),
                subtitle=(verb % tag["title"]) + " " + entry["emoji"],
                arg=entry["emoji"],
                variables=_tag_op(op, tag["id"]),
                icon=_emoji_icon(settings, entry),
            )
        )
        count += 1
        if count >= MAX_RESULTS:
            break
    return items


def build_menu(query: str, api: Dict, tags: List[Dict], settings: Settings, language_name: str) -> List[Dict]:
    """All items of the menu for `query`."""
    path, text = parse_query(query)
    if path[:1] != ["tags"]:
        return root_items(api, language_name, text if not path else "")
    if len(path) == 1:
        return tags_items(tags, text)
    tag = next((t for t in tags if t["id"] == path[1]), None)
    if tag is None:  # stale breadcrumb (tag deleted): fall back to the tag list
        return tags_items(tags, "")
    if len(path) == 2:
        return tag_items(tag, api, settings, text)
    if path[2] in (OP_LINK, OP_UNLINK):
        return emoji_picker_items(tag, api, settings, text, path[2] == OP_LINK)
    return tag_items(tag, api, settings, text)


def next_query(op: str, tag_id: str) -> str:
    """Where the user lands after a tag operation."""
    if op in (OP_CREATE, OP_DELETE):
        return build_query(["tags"])
    if op == OP_RENAME:
        return build_query(["tags", tag_id])
    return build_query(["tags", tag_id, op])  # stay in the picker to chain several emojis
