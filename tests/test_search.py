import json
import os
import unittest

from tests.helpers import TempDirTestCase, make_settings
from winelib import search
from winelib.storage import write_json

API = {
    "info": {"time": "01-01-2026 10:00:00", "lang": {"title": "🇫🇷 Français", "value": "fr"},
             "workflow_version": "2.0.0"},
    "items": [
        {"name": "grinning face", "emoji": "😀", "title": "visage souriant", "tags": ["visage", "😀"],
         "image": True, "skin_tones": ["base"]},
        {"name": "waving hand", "emoji": "👋", "title": "main qui salue", "tags": ["main"],
         "image": False, "skin_tones": ["none"]},
        {"name": "waving hand: light skin tone", "emoji": "👋🏻", "title": None, "tags": None,
         "image": True, "skin_tones": ["light skin tone"]},
    ],
}


class Urls(TempDirTestCase):
    def test_slug(self):
        self.assertEqual(search.dictionary_slug("Face (with) Tears: Joy’s"), "face-with-tears-joy-s")

    def test_emojipedia_french(self):
        s = make_settings(self.tmp)
        self.assertEqual(search.dictionary_url(s, "😀", "visage souriant"),
                         "https://emojipedia.org/fr/visage-souriant")

    def test_english_has_no_country(self):
        s = make_settings(self.tmp, language="en")
        self.assertEqual(search.dictionary_url(s, "😀", "grinning face"),
                         "https://emojipedia.org/grinning-face")

    def test_emojiall_is_percent_encoded(self):
        s = make_settings(self.tmp, emoji_dictionary="emojiall.com")
        self.assertEqual(search.dictionary_url(s, "😀", None), "https://emojiall.com/fr/emoji/%F0%9F%98%80")

    def test_no_title_no_url(self):
        self.assertIsNone(search.dictionary_url(make_settings(self.tmp), "x", None))


class Items(TempDirTestCase):
    def build(self, **overrides):
        s = make_settings(self.tmp, **overrides)
        return s, search.build_items(API, [{"id": "a", "title": "joie", "emojis": ["😀"]}], s)

    def test_default_shortcuts(self):
        s, items = self.build()
        first = items[0]
        self.assertEqual(first["title"], "visage souriant")
        self.assertEqual(first["arg"], "😀")
        self.assertEqual(first["variables"], {"action": "copy"})
        self.assertEqual(first["mods"]["cmd"]["variables"], {"action": "paste"})
        self.assertEqual(first["mods"]["shift"]["arg"], "https://emojipedia.org/fr/visage-souriant")
        self.assertIn("joie", first["match"])
        self.assertTrue(first["icon"]["path"].endswith("grinning face.png"))

    def test_fallback_icon_when_no_image(self):
        _, items = self.build()
        self.assertTrue(items[1]["icon"]["path"].endswith("unicode.png"))

    def test_untranslated_uses_name_and_has_no_web_action(self):
        _, items = self.build()
        light = items[2]
        self.assertEqual(light["title"], "waving hand: light skin tone")
        self.assertNotIn("shift", light["mods"])

    def test_deactivated_shortcut_is_skipped(self):
        _, items = self.build(short_paste="False", short_web="False")
        self.assertNotIn("mods", items[0])

    def test_enter_can_be_assigned_to_another_action(self):
        _, items = self.build(short_copy="cmd", short_paste="arg")
        self.assertEqual(items[0]["variables"], {"action": "paste"})
        self.assertIn("cmd", items[0]["mods"])

    def test_skin_tone_filter(self):
        _, items = self.build(skin_tone="light skin tone")
        self.assertEqual([i["uid"] for i in items], ["grinning face", "waving hand: light skin tone"])
        _, items = self.build(skin_tone="none")
        self.assertEqual([i["uid"] for i in items], ["grinning face", "waving hand"])


def respond(settings, query=""):
    return search.respond(settings, "x", query)


class Response(TempDirTestCase):
    def test_no_api(self):
        items = json.loads(respond(make_settings(self.tmp)))["items"]
        self.assertEqual(items[0]["title"], "No API detected")
        self.assertEqual(items[0]["variables"], {"action": "refresh"})

    def test_outdated_api(self):
        s = make_settings(self.tmp, workflow_version="9.9.9")
        write_json(s.api_file, API)
        items = json.loads(respond(s))["items"]
        self.assertEqual(items[0]["title"], "Refresh the API")

    def test_language_mismatch(self):
        s = make_settings(self.tmp, language="en")
        write_json(s.api_file, API)
        self.assertEqual(json.loads(respond(s))["items"][0]["title"], "Refresh the API")
        self.assertEqual(json.loads(respond(s, ">"))["items"][0]["title"], "Refresh the API")

    def test_cache_is_used_then_invalidated_by_tags(self):
        s = make_settings(self.tmp)
        write_json(s.api_file, API)
        respond(s)
        self.assertTrue(os.path.exists(s.search_cache_file))
        write_json(s.search_cache_file, {"key": search.cache_key(s), "items": [{"title": "CACHED", "match": "c"}]})
        self.assertIn("CACHED", respond(s))
        write_json(s.tags_file, [{"id": "a", "title": "joie", "emojis": ["😀"]}])
        fresh = respond(s)
        self.assertNotIn("CACHED", fresh)
        self.assertIn("joie", fresh)

    def test_python_side_filtering(self):
        s = make_settings(self.tmp)
        write_json(s.api_file, API)
        write_json(s.tags_file, [{"id": "a", "title": "Joie", "emojis": ["😀"]}])
        titles = lambda q: [i["title"] for i in json.loads(respond(s, q))["items"]]
        self.assertEqual(titles("joie"), ["visage souriant"])  # custom tag
        self.assertEqual(titles("MAIN"), ["main qui salue"])  # case insensitive
        self.assertEqual(titles("zzz"), [])

    def test_data_items_pinned_on_top_of_empty_search(self):
        s = make_settings(self.tmp)
        write_json(s.api_file, API)
        items = json.loads(respond(s))["items"]
        self.assertEqual([i["title"] for i in items[:3]], ["Tags", "API information", "Refresh the API"])
        self.assertEqual((items[0]["valid"], items[0]["autocomplete"]), (False, ">tags›"))
        self.assertIn("3 Emojis", items[1]["subtitle"])
        self.assertEqual(items[2]["variables"], {"action": "refresh"})
        self.assertEqual(len(items), 6)

    def test_pinned_items_hidden_while_typing_unless_they_match(self):
        s = make_settings(self.tmp)
        write_json(s.api_file, API)
        titles = lambda q: [i["title"] for i in json.loads(respond(s, q))["items"]]
        self.assertNotIn("Refresh the API", titles("main"))
        self.assertEqual(titles("refresh"), ["Refresh the API"])

    def test_tags_item_in_grid_reopens_alfred_on_the_menu(self):
        s = make_settings(self.tmp, style="grid")
        write_json(s.api_file, API)
        tags = json.loads(respond(s))["items"][0]
        self.assertEqual((tags["arg"], tags["variables"]), (">tags›", {"action": "menu"}))
        self.assertNotIn("autocomplete", tags)

    def test_menu_mode(self):
        s = make_settings(self.tmp)
        write_json(s.api_file, API)
        items = json.loads(respond(s, ">tags›"))["items"]
        self.assertEqual(items[0]["title"], "Return")

    def test_cache_depends_on_settings(self):
        a = search.cache_key(make_settings(self.tmp))
        b = search.cache_key(make_settings(self.tmp, skin_tone="none"))
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
