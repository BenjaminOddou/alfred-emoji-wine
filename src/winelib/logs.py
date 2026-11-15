"""File logger + macOS notifications."""

import logging
import subprocess
from typing import Optional

from .settings import Settings

_LOGGER_NAME = "emoji_wine"


def get_logger(settings: Settings) -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)
    if not logger.handlers and settings.cache_dir:
        logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(settings.log_file, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(handler)
    return logger


def notify(settings: Settings, title: str, message: str, runner=subprocess.run) -> None:
    """Show a macOS notification through the bundled `notificator` script."""
    cmd = [
        settings.notificator,
        "--message", message,
        "--title", title,
        "--sound", settings.sound,
    ]
    try:
        runner(cmd, check=False)
    except OSError:
        pass  # a missing notifier must never break the workflow


def fail(settings: Settings, message: str, exc: Optional[BaseException] = None) -> None:
    """Log an error and tell the user where to look."""
    get_logger(settings).error("%s%s", message, " : %r" % exc if exc else "")
    notify(settings, "🚨 Error !", message)
