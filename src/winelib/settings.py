"""Workflow settings, read once from the environment Alfred provides."""

from __future__ import annotations

import os

DEFAULT_PADDING = 10
ICON_SIZE = 64
SHORTCUT_DISABLED = "False"  # value of the "Deactivated" popup entry
SHORTCUT_ARG = "arg"  # plain ⏎, no modifier

DICTIONARIES = ("emojipedia.org", "emojiterra.com", "emojiall.com")

# attribute: default. A plain class (no dataclass): the Script Filter runs at every keystroke.
DEFAULTS = {
    "language": "en",
    "skin_tone": "all",
    "sound": "",
    "padding": DEFAULT_PADDING,
    "emoji_dictionary": "emojipedia.org",
    "short_copy": "arg",
    "short_paste": "cmd",
    "short_web": "shift",
    "cache_dir": "",
    "data_dir": "",
    "workflow_dir": "",
    "workflow_version": "",
    "style": "list",
}
# attribute: environment variable, when they differ
ENV_NAMES = {
    "cache_dir": "alfred_workflow_cache",
    "data_dir": "alfred_workflow_data",
    "workflow_version": "alfred_workflow_version",
}


class Settings:
    __slots__ = tuple(DEFAULTS)

    def __init__(self, **values) -> None:
        unknown = set(values) - set(DEFAULTS)
        if unknown:
            raise TypeError("unknown settings: %s" % ", ".join(sorted(unknown)))
        for name, default in DEFAULTS.items():
            setattr(self, name, values.get(name, default))

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
    def plist_file(self) -> str:
        return os.path.join(self.workflow_dir, "info.plist")

    @property
    def index_file(self) -> str:
        return os.path.join(self.cache_dir, "search.index")

    @property
    def log_file(self) -> str:
        return os.path.join(self.cache_dir, "emoji_wine.log")

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
            self.padding,
            self.cache_dir,
        )

    # ---- construction --------------------------------------------------
    @classmethod
    def from_env(cls, environ=None, workflow_dir: str | None = None) -> Settings:
        env = os.environ if environ is None else environ
        values = {name: env.get(ENV_NAMES.get(name, name), default) for name, default in DEFAULTS.items()}
        try:
            values["padding"] = max(0, int(str(values["padding"]).strip()))
        except ValueError:
            values["padding"] = DEFAULT_PADDING
        values["workflow_dir"] = workflow_dir or os.getcwd()
        settings = cls(**values)
        for folder in (settings.cache_dir, settings.data_dir):
            if folder:
                os.makedirs(folder, exist_ok=True)
        return settings
