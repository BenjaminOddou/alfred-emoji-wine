import json
import os
import subprocess
import unittest

from tests.helpers import SRC, TempDirTestCase
from winelib import icons


class IconJobs(TempDirTestCase):
    def test_missing_jobs_skip_existing_and_duplicates(self):
        folder = os.path.join(self.tmp, "icons")
        os.makedirs(folder)
        open(os.path.join(folder, "grinning face.png"), "w").close()
        emojis = [
            {"emoji": "😀", "name": "grinning face"},
            {"emoji": "🇫🇷", "name": "flag: France"},
            {"emoji": "🇫🇷", "name": "flag: France"},
        ]
        self.assertEqual(icons.missing_jobs(emojis, folder), [{"emoji": "🇫🇷", "file": "flag France.png"}])

    def test_padding_change_wipes_stale_icons(self):
        folder = os.path.join(self.tmp, "icons")
        icons.prepare_icons_dir(folder, 10)
        stale = os.path.join(folder, "x.png")
        open(stale, "w").close()
        icons.prepare_icons_dir(folder, 10)
        self.assertTrue(os.path.exists(stale))
        icons.prepare_icons_dir(folder, 20)
        self.assertFalse(os.path.exists(stale))
        self.assertTrue(icons.icons_are_current(folder, 20))


class Rendering(TempDirTestCase):
    def test_render_calls_osascript_once(self):
        calls = []

        def runner(cmd, **kwargs):
            calls.append(cmd)
            with open(cmd[4], encoding="utf-8") as handle:
                self.assertEqual(json.load(handle), [{"emoji": "😀", "file": "a.png"}])
            return subprocess.CompletedProcess(cmd, 0, stdout='["a.png"]\n', stderr="")

        failed = icons.render_emoji_icons([{"emoji": "😀", "file": "a.png"}], self.tmp, 10, runner)
        self.assertEqual(failed, ["a.png"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][:3], ["osascript", "-l", "JavaScript"])
        self.assertEqual(calls[0][5:], [self.tmp, "64", "10"])

    def test_nothing_to_render(self):
        self.assertEqual(icons.render_emoji_icons([], self.tmp, 10, runner=None), [])

    def test_install_assets_pads_pngs(self):
        target = os.path.join(self.tmp, "icons")
        os.makedirs(target)
        icons.install_assets(os.path.join(SRC, "icons", "assets"), target, 10)
        self.assertIn("unicode.png", os.listdir(target))

    def test_render_script_exists(self):
        self.assertTrue(os.path.exists(icons.RENDER_SCRIPT))


if __name__ == "__main__":
    unittest.main()
