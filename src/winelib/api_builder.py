"""Build api.json (emoji list) and the icons folder."""

import datetime
import subprocess
from typing import Callable

from . import emoji_data, icons, sources
from .languages import language_title
from .logs import fail, get_logger, notify
from .settings import Settings
from .storage import write_json


def build_api(
    settings: Settings,
    languages,
    fetch: sources.Fetcher = sources.fetch_url,
    runner=subprocess.run,
    notifier: Callable = notify,
) -> bool:
    """Refresh data + icons. Returns True on success; failures are reported to the user."""
    logger = get_logger(settings)
    notifier(settings, "⏳ Please wait !", "Emojis data is being gathered, this can take some time...")
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
            "lang": {"title": language_title(languages, settings.language), "value": settings.language},
            "workflow_version": settings.workflow_version,
        }
        write_json(settings.api_file, {"info": info, "items": items}, indent=1)
    except Exception as exc:  # network, parsing or rendering: tell the user, keep the old data
        fail(settings, "Something went wrong, check the logs and create a GitHub issue", exc)
        return False
    logger.info("API refreshed with language : %s", settings.language)
    notifier(settings, "✅ Success !", "Data updated. You can search emojis")
    return True
