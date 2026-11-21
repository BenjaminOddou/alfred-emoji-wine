"""Build api.json (emoji list) and the icons folder."""

from __future__ import annotations

import datetime
import subprocess

from . import emoji_data, icons, sources
from .logs import failure, get_logger, remove_notificator, success
from .settings import Settings
from .storage import write_json


def build_api(
    settings: Settings,
    language_name: str,
    fetch=sources.fetch_url,
    runner=subprocess.run,
) -> tuple:
    """Refresh data + icons. Returns the (title, text) notification; a failure keeps the old data."""
    logger = get_logger(settings)
    remove_notificator(settings.cache_dir)
    try:
        emoji_test, annotations, derived = sources.fetch_all(settings.language, fetch)
        emojis = emoji_data.parse_emoji_test(emoji_test)
        index = emoji_data.parse_annotations(annotations, derived)

        icons.prepare_icons_dir(settings.icons_dir, settings.padding)
        failed = icons.render_emoji_icons(
            icons.missing_jobs(emojis, settings.icons_dir),
            settings.icons_dir, settings.padding, runner,
        )
        for filename in failed:
            logger.error("%s cannot be turned into an image", filename)
        icons.install_assets(settings.assets_dir, settings.icons_dir, settings.padding)

        items = emoji_data.build_items(emojis, index, icons.rendered_names(emojis, settings.icons_dir))
        info = {
            "time": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
            "lang": {"title": language_name, "value": settings.language},
            "workflow_version": settings.workflow_version,
        }
        write_json(settings.api_file, {"info": info, "items": items})
    except Exception as exc:  # network, parsing or rendering: tell the user, keep the old data
        return failure(settings, "Something went wrong, check the logs and create a GitHub issue", exc)
    return success(settings, "%d emojis ready in %s. You can search emojis" % (len(items), language_name))
