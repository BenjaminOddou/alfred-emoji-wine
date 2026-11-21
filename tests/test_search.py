import json
import os
import unittest
from unittest import mock

from tests.helpers import TempDirTestCase, make_settings
from winelib import search
from winelib.storage import read_bytes, write_json

API = {
    "info": {"time": "01-01-2026 10:00:00", "lang": {"title": "🇫🇷 Français", "value": "fr"},
             "workflow_version": "2.1.0"},
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
        return s, [search.build_item(entry, s, ["joie"] if entry["emoji"] == "😀" else [])[0]
                   for entry in API["items"]]

    def test_default_shortcuts(self):
        s, items = self.build()
        first = items[0]
        self.assertEqual(first["title"], "visage souriant")
        self.assertEqual(first["arg"], "😀")
        self.assertEqual(first["variables"], {"action": "copy"})
        self.assertEqual(first["mods"]["cmd"]["variables"], {"action": "paste"})
        self.assertEqual(first["mods"]["shift"]["arg"], "https://emojipedia.org/fr/visage-souriant")
        self.assertTrue(first["icon"]["path"].endswith("grinning face.png"))

    def test_no_uid_and_no_match_in_the_list(self):
        """No uid: Alfred learns nothing and keeps the script order. The list is filtered by the script."""
        _, items = self.build()
        self.assertTrue(all("uid" not in i and "match" not in i for i in items))

    def test_grid_items_keep_match_for_the_grid_filter(self):
        _, items = self.build(style="grid")
        self.assertIn("joie", items[0]["match"])
        self.assertNotIn("uid", items[0])

    def test_search_text_is_normalized(self):
        s = make_settings(self.tmp)
        _, text = search.build_item(API["items"][0], s, ["Joie Été"])
        self.assertIn("joie ete", text)
        self.assertIn("visage souriant", text)

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
        def shown(skin_tone):
            s = make_settings(self.tmp, skin_tone=skin_tone)
            return [json.loads(row[3])["title"] for row in search.Index.build(API, [], s).find("")]

        self.assertEqual(shown("light skin tone"), ["visage souriant", "waving hand: light skin tone"])
        self.assertEqual(shown("none"), ["visage souriant", "main qui salue"])


def respond(settings, query=""):
    return json.loads(search.respond(settings, query, "x"))


def titles(settings, query=""):
    return [i["title"] for i in respond(settings, query)["items"]]


class Response(TempDirTestCase):
    def setUp(self):
        super().setUp()
        self.settings = make_settings(self.tmp)
        write_json(self.settings.api_file, API)

    def test_no_api(self):
        items = respond(make_settings(os.path.join(self.tmp, "empty")))["items"]
        self.assertEqual(items[0]["title"], "No API detected")
        self.assertEqual(items[0]["variables"], {"action": "refresh"})

    def test_outdated_api(self):
        s = make_settings(self.tmp, workflow_version="9.9.9")
        self.assertEqual(respond(s)["items"][0]["title"], "Refresh the API")

    def test_language_mismatch(self):
        s = make_settings(self.tmp, language="en")
        self.assertEqual(respond(s)["items"][0]["title"], "Refresh the API")
        self.assertEqual(respond(s, ">")["items"][0]["title"], "Refresh the API")

    def test_language_name_comes_from_the_plist_only_when_asking_for_a_refresh(self):
        s = make_settings(self.tmp, language="en")
        item = json.loads(search.respond(s, ""))["items"][0]
        self.assertIn("🇬🇧 English", item["subtitle"])
        with mock.patch("winelib.languages.load_languages", side_effect=AssertionError("plist read")):
            json.loads(search.respond(self.settings, "main"))

    def test_alfred6_keys_keep_the_script_order(self):
        data = respond(self.settings)
        self.assertEqual((data["skipknowledge"], data["strictmods"], data["iconresize"]), (True, True, "fit"))
        self.assertTrue(all("uid" not in i for i in data["items"]))
        self.assertTrue(respond(self.settings, ">")["skipknowledge"])
        self.assertTrue(respond(make_settings(os.path.join(self.tmp, "empty")))["strictmods"])

    def test_index_is_used_then_invalidated_by_tags(self):
        respond(self.settings)
        self.assertTrue(os.path.exists(self.settings.index_file))
        index = search.Index.parse(read_bytes(self.settings.index_file), search.index_key(self.settings))
        index.rows[0][3] = b'{"title":"CACHED"}'
        with open(self.settings.index_file, "wb") as handle:
            handle.write(index.serialize(search.index_key(self.settings)))
        self.assertIn("CACHED", titles(self.settings))
        write_json(self.settings.tags_file, [{"id": "a", "title": "joie", "emojis": ["😀"]}])
        self.assertNotIn("CACHED", titles(self.settings))
        self.assertEqual(titles(self.settings, "joie"), ["visage souriant"])

    def test_corrupt_index_is_rebuilt(self):
        with open(self.settings.index_file, "wb") as handle:
            handle.write(b"garbage")
        self.assertEqual(len(titles(self.settings)), 6)

    def test_index_survives_unicode_line_separators(self):
        api = json.loads(json.dumps(API))
        api["items"][0]["title"] = "ligne deux"
        write_json(self.settings.api_file, api)
        respond(self.settings)
        self.assertIn("ligne deux", titles(self.settings))

    def test_python_side_filtering(self):
        write_json(self.settings.tags_file, [{"id": "a", "title": "Joie", "emojis": ["😀"]}])
        self.assertEqual(titles(self.settings, "joie"), ["visage souriant"])  # custom tag
        self.assertEqual(titles(self.settings, "MAIN"), ["main qui salue"])  # case insensitive
        self.assertEqual(titles(self.settings, "VISAGÉ sour"), ["visage souriant"])  # accents, several words
        self.assertEqual(titles(self.settings, "zzz"), [])

    def test_data_items_pinned_on_top_of_empty_search(self):
        items = respond(self.settings)["items"]
        self.assertEqual([i["title"] for i in items[:3]], ["Tags", "API information", "Refresh the API"])
        self.assertEqual((items[0]["valid"], items[0]["autocomplete"]), (False, ">tags›"))
        self.assertIn("3 Emojis", items[1]["subtitle"])
        self.assertIn("🇫🇷 Français", items[1]["subtitle"])
        self.assertEqual(items[2]["variables"], {"action": "refresh"})
        self.assertEqual(len(items), 6)

    def test_pinned_items_hidden_while_typing_unless_they_match(self):
        self.assertNotIn("Refresh the API", titles(self.settings, "main"))
        self.assertEqual(titles(self.settings, "refresh"), ["Refresh the API"])
        self.assertEqual(titles(self.settings, "ta")[0], "Tags")

    def test_tags_item_in_grid_reopens_alfred_on_the_menu(self):
        s = make_settings(self.tmp, style="grid")
        tags = respond(s)["items"][0]
        self.assertEqual((tags["arg"], tags["variables"]), (">tags›", {"action": "menu"}))
        self.assertNotIn("autocomplete", tags)

    def test_menu_mode(self):
        self.assertEqual(respond(self.settings, ">tags›")["items"][0]["title"], "Return")

    def test_index_key_depends_on_settings(self):
        a = search.index_key(make_settings(self.tmp))
        b = search.index_key(make_settings(self.tmp, skin_tone="none"))
        self.assertNotEqual(a, b)
        self.assertNotIn("\n", a)


if __name__ == "__main__":
    unittest.main()
