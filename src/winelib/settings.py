"""Workflow settings, read once from the environment Alfred provides."""

import os
from dataclasses import dataclass
from typing import Mapping, Optional

DEFAULT_PADDING = 10
ICON_SIZE = 64
SHORTCUT_DISABLED = "False"  # value of the "Desactivated" popup entry
SHORTCUT_ARG = "arg"  # plain ⏎, no modifier

DICTIONARIES = ("emojipedia.org", "emojiterra.com", "emojiall.com")


@dataclass(frozen=True)
class Settings:
    language: str = "en"
    skin_tone: str = "all"
    sound: str = ""
    padding: int = DEFAULT_PADDING
    emoji_dictionary: str = "emojipedia.org"
    short_copy: str = "arg"
    short_paste: str = "cmd"
    short_web: str = "shift"
    cache_dir: str = ""
    data_dir: str = ""
    workflow_dir: str = ""
    workflow_version: str = ""
    style: str = "list"

    # ---- derived paths -------------------------------------------------
    @property
    def api_file(self) -> str:
        return os.path.join(self.cache_dir, "api.json")

    @property
    def tags_file(self) -> str:
        return os.path.join(self.data_dir, "tags-%s.json" % self.language)

    @property
    def icons_dir(self) -> str:
        return os.path.join(self.cache_dir, "icons")

    @property
    def assets_dir(self) -> str:
        return os.path.join(self.workflow_dir, "icons", "assets")

    @property
    def search_cache_file(self) -> str:
        return os.path.join(self.cache_dir, "search_items.json")

    @property
    def log_file(self) -> str:
        return os.path.join(self.cache_dir, "emoji_wine.log")

    @property
    def notificator(self) -> str:
        return os.path.join(self.workflow_dir, "notificator")

    @property
    def dictionary_icon(self) -> str:
        return os.path.join(self.icons_dir, self.emoji_dictionary.split(".")[0] + ".png")

    @property
    def fingerprint(self) -> tuple:
        """Everything that changes how search results are rendered."""
        return (
            self.language,
            self.skin_tone,
            self.emoji_dictionary,
            self.short_copy,
            self.short_paste,
            self.short_web,
            self.workflow_version,
            self.style,
        )

    # ---- construction --------------------------------------------------
    @classmethod
    def from_env(
        cls, environ: Optional[Mapping[str, str]] = None, workflow_dir: Optional[str] = None
    ) -> "Settings":
        env = os.environ if environ is None else environ
        try:
            padding = int(str(env.get("padding", DEFAULT_PADDING)).strip())
        except ValueError:
            padding = DEFAULT_PADDING
        settings = cls(
            language=env.get("language", "en"),
            skin_tone=env.get("skin_tone", "all"),
            sound=env.get("sound", ""),
            padding=max(0, padding),
            emoji_dictionary=env.get("emoji_dictionary", "emojipedia.org"),
            short_copy=env.get("short_copy", "arg"),
            short_paste=env.get("short_paste", "cmd"),
            short_web=env.get("short_web", "shift"),
            cache_dir=env.get("alfred_workflow_cache", ""),
            data_dir=env.get("alfred_workflow_data", ""),
            workflow_dir=workflow_dir or os.getcwd(),
            workflow_version=env.get("alfred_workflow_version", ""),
            style=env.get("style", "list"),
        )
        for folder in (settings.cache_dir, settings.data_dir):
            if folder:
                os.makedirs(folder, exist_ok=True)
        return settings
