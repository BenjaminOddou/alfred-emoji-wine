"""Log file, and what the Run Scripts report to the user.

No more Notificator: a Run Script prints its arg plus `notify_title` / `notify_text`, and Alfred 6 posts the
notification itself (Arg and Vars → Post Notification). The sound is played here with `afplay`.
"""

from __future__ import annotations

import glob
import logging
import os

from .alfred import run_output
from .settings import Settings

_LOGGER_NAME = "emoji_wine"
SOUNDS_DIR = "/System/Library/Sounds"
SUCCESS = "✅ Success!"
ERROR = "🚨 Error!"


def get_logger(settings: Settings) -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)
    if not logger.handlers and settings.cache_dir:
        logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(settings.log_file, encoding="utf-8", delay=True)
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(handler)
        logger.propagate = False
    return logger


def success(settings: Settings, message: str) -> tuple:
    """Log `message`; returns the (title, text) of the notification."""
    get_logger(settings).info(message)
    return SUCCESS, message


def failure(settings: Settings, message: str, exc: BaseException | None = None) -> tuple:
    """Log an error (with its traceback); returns the (title, text) of the notification."""
    get_logger(settings).error("%s%s", message, " : %r" % exc if exc else "", exc_info=exc)
    return ERROR, message


def play(sound: str, popen=None) -> None:
    """Play a macOS system sound without waiting for it (a missing sound or player is ignored)."""
    path = os.path.join(SOUNDS_DIR, sound + ".aiff")
    if not sound or not os.path.isfile(path):
        return
    import subprocess

    try:
        (popen or subprocess.Popen)(["afplay", path], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL, start_new_session=True)
    except OSError:
        pass


def script_output(settings: Settings, arg: str = "", notice: tuple = ("", ""), popen=None) -> str:
    """What a Run Script prints: Alfred posts `notice` (title, text) when the text is not empty."""
    title, text = notice
    if text:
        play(settings.sound, popen)
    return run_output(arg, title, text)


def remove_notificator(cache_dir: str) -> None:
    """2.0 leftover: the helper app Notificator built in the cache folder."""
    import shutil

    for app in glob.glob(os.path.join(glob.escape(cache_dir), "Notificator for *.app")):
        shutil.rmtree(app, ignore_errors=True)
