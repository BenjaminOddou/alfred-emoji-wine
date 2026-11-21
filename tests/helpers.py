"""Shared fixtures for the test-suite."""

import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from winelib.settings import Settings  # noqa: E402

EMOJI_TEST = """# comment
1F600                                                  ; fully-qualified     # 😀 E1.0 grinning face
1F44B                                                  ; fully-qualified     # 👋 E0.6 waving hand
1F44B 1F3FB                                            ; fully-qualified     # 👋🏻 E1.0 waving hand: light skin tone
1F3FB                                                  ; component           # 🏻 E1.0 light skin tone
1F1EB 1F1F7                                            ; fully-qualified     # 🇫🇷 E0.6 flag: France
263A                                                   ; unqualified         # ☺ E0.6 smiling face
"""

CLDR_ANNOTATIONS = """<ldml><annotations>
<annotation cp="😀">visage | sourire</annotation>
<annotation cp="😀" type="tts">visage souriant</annotation>
<annotation cp="👋">main | salut</annotation>
<annotation cp="👋" type="tts">main qui salue</annotation>
<annotation cp="🇫🇷">drapeau | France</annotation>
<annotation cp="🇫🇷" type="tts">drapeau : France</annotation>
</annotations></ldml>"""

CLDR_DERIVED = """<ldml><annotations>
<annotation cp="👋🏻">main | salut</annotation>
<annotation cp="👋🏻" type="tts">main qui salue : peau claire</annotation>
<annotation cp="😀">ignored because the first file wins</annotation>
</annotations></ldml>"""


def make_settings(tmp: str, **overrides) -> Settings:
    values = dict(
        language="fr",
        skin_tone="all",
        sound="",
        padding=10,
        emoji_dictionary="emojipedia.org",
        short_copy="arg",
        short_paste="cmd",
        short_web="shift",
        cache_dir=os.path.join(tmp, "cache"),
        data_dir=os.path.join(tmp, "data"),
        workflow_dir=SRC,
        workflow_version="2.1.0",
    )
    values.update(overrides)
    settings = Settings(**values)
    os.makedirs(settings.cache_dir, exist_ok=True)
    os.makedirs(settings.data_dir, exist_ok=True)
    return settings


class TempDirTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = self._tmp.name
