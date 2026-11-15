import unittest

from tests.helpers import CLDR_ANNOTATIONS, CLDR_DERIVED, EMOJI_TEST
from winelib import emoji_data as ed


class EmojiTestParsing(unittest.TestCase):
    def test_keeps_fully_qualified_and_component_only(self):
        emojis = ed.parse_emoji_test(EMOJI_TEST)
        self.assertEqual(
            [e["name"] for e in emojis],
            ["grinning face", "waving hand", "waving hand: light skin tone", "light skin tone", "flag: France"],
        )
        self.assertEqual(emojis[0]["emoji"], "😀")

    def test_ignores_garbage(self):
        self.assertEqual(ed.parse_emoji_test("nothing\n\n# ; fully-qualified"), [])


class SkinTones(unittest.TestCase):
    def test_remove_skin_tones(self):
        self.assertEqual(ed.remove_skin_tones("👋🏻"), "👋")

    def test_labels(self):
        bases = ed.base_emojis_with_variants(["👋", "👋🏻", "😀"])
        self.assertEqual(bases, {"👋"})
        self.assertEqual(ed.get_skin_tones("👋", bases), ["none"])
        self.assertEqual(ed.get_skin_tones("👋🏻", bases), ["light skin tone"])
        self.assertEqual(ed.get_skin_tones("😀", bases), ["base"])


class Annotations(unittest.TestCase):
    def setUp(self):
        self.index = ed.parse_annotations(CLDR_ANNOTATIONS, CLDR_DERIVED)

    def test_first_document_wins(self):
        self.assertEqual(self.index["😀"]["tags"], ["visage", "sourire"])

    def test_derived_documents_are_merged(self):
        self.assertEqual(self.index["👋🏻"]["tts"], "main qui salue : peau claire")

    def test_annotate_appends_emoji_to_tags(self):
        title, tags = ed.annotate("😀", "grinning face", self.index)
        self.assertEqual(title, "visage souriant")
        self.assertEqual(tags, ["visage", "sourire", "😀"])

    def test_annotate_flags_use_title_words(self):
        title, tags = ed.annotate("🇫🇷", "flag: France", self.index)
        self.assertEqual(tags, ["drapeau", "France", "🇫🇷"])

    def test_annotate_ignores_variation_selector(self):
        index = ed.parse_annotations('<ldml><annotations><annotation cp="☺">a | b</annotation>'
                                     '<annotation cp="☺" type="tts">t</annotation></annotations></ldml>')
        self.assertEqual(ed.annotate("☺️", "smiling face", index)[0], "t")

    def test_untranslated_emoji(self):
        self.assertEqual(ed.annotate("🏻", "light skin tone", self.index), (None, None))


class BuildItems(unittest.TestCase):
    def test_items(self):
        emojis = ed.parse_emoji_test(EMOJI_TEST)
        items = ed.build_items(emojis, ed.parse_annotations(CLDR_ANNOTATIONS), {"grinning face"})
        by_name = {i["name"]: i for i in items}
        self.assertTrue(by_name["grinning face"]["image"])
        self.assertFalse(by_name["waving hand"]["image"])
        self.assertEqual(by_name["waving hand"]["skin_tones"], ["none"])
        self.assertEqual(by_name["grinning face"]["title"], "visage souriant")
        self.assertIsNone(by_name["light skin tone"]["title"])

    def test_icon_filename(self):
        self.assertEqual(ed.icon_filename("flag: France"), "flag France.png")
        self.assertEqual(ed.icon_filename("a/b"), "ab.png")


if __name__ == "__main__":
    unittest.main()
