import os
import subprocess
import unittest

from tests.helpers import CLDR_ANNOTATIONS, CLDR_DERIVED, EMOJI_TEST, TempDirTestCase, make_settings
from winelib import api_builder, sources
from winelib.storage import read_json

LANGS = [{"title": "🇫🇷 Français", "value": "fr"}]


def fake_fetch(url):
    if url.endswith("emoji-test.txt"):
        return EMOJI_TEST
    return CLDR_DERIVED if "annotationsDerived" in url else CLDR_ANNOTATIONS


def fake_runner_factory(fail=()):
    def runner(cmd, **kwargs):
        icons_dir = cmd[5]
        import json
        with open(cmd[4], encoding="utf-8") as handle:
            jobs = json.load(handle)
        for job in jobs:
            if job["file"] not in fail:
                open(os.path.join(icons_dir, job["file"]), "wb").close()
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(list(fail)), stderr="")
    return runner


class Sources(unittest.TestCase):
    def test_cldr_urls(self):
        annotations, derived = sources.cldr_urls("zh-hant")
        self.assertTrue(annotations.endswith("/annotations/zh_hant.xml"))
        self.assertTrue(derived.endswith("/annotationsDerived/zh_hant.xml"))

    def test_fetch_all_runs_the_three_downloads(self):
        seen = []
        result = sources.fetch_all("fr", lambda url: seen.append(url) or url)
        self.assertEqual(sorted(seen), sorted(result))
        self.assertEqual(len(seen), 3)


class BuildApi(TempDirTestCase):
    def setUp(self):
        super().setUp()
        self.settings = make_settings(self.tmp)
        self.notes = []

    def build(self, **kwargs):
        return api_builder.build_api(
            self.settings, LANGS, fetch=fake_fetch,
            runner=kwargs.get("runner", fake_runner_factory()),
            notifier=lambda s, title, msg: self.notes.append(title),
        )

    def test_success(self):
        self.assertTrue(self.build())
        api = read_json(self.settings.api_file)
        self.assertEqual(api["info"]["lang"], {"title": "🇫🇷 Français", "value": "fr"})
        self.assertEqual(api["info"]["workflow_version"], "2.0.0")
        self.assertEqual(len(api["items"]), 5)
        self.assertTrue(all(i["image"] for i in api["items"]))
        self.assertIn("unicode.png", os.listdir(self.settings.icons_dir))
        self.assertEqual(self.notes, ["⏳ Please wait !", "✅ Success !"])

    def test_unrenderable_emoji_falls_back_to_unicode_icon(self):
        self.assertTrue(self.build(runner=fake_runner_factory(fail=("grinning face.png",))))
        items = {i["name"]: i for i in read_json(self.settings.api_file)["items"]}
        self.assertFalse(items["grinning face"]["image"])

    def test_second_run_only_renders_missing_icons(self):
        self.build()
        calls = []

        def runner(cmd, **kwargs):
            calls.append(cmd)
            raise AssertionError("nothing should be rendered")

        self.assertTrue(self.build(runner=runner))
        self.assertEqual(calls, [])

    def test_failure_keeps_old_data_and_notifies(self):
        self.build()
        before = read_json(self.settings.api_file)

        def boom(url):
            raise RuntimeError("offline")

        ok = api_builder.build_api(self.settings, LANGS, fetch=boom, notifier=lambda *a: None)
        self.assertFalse(ok)
        self.assertEqual(read_json(self.settings.api_file), before)


if __name__ == "__main__":
    unittest.main()
