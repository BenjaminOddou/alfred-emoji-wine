import json
import os
import subprocess
import sys
import unittest

from tests.helpers import SRC, TempDirTestCase, make_settings
from tests.test_search import API
from winelib import navigation as nav
from winelib import tag_actions, tags_store
from winelib.alfred import matches
from winelib.search import Index
from winelib.storage import read_json, write_json


def titles(items):
    return [i["title"] for i in items]


class TagStore(unittest.TestCase):
    def test_lifecycle(self):
        tags = []
        tag = tags_store.create_tag(tags, "  joie ")
        self.assertEqual(tag["title"], "joie")
        self.assertTrue(tags_store.link_emoji(tags, tag["id"], "😀"))
        self.assertTrue(tags_store.link_emoji(tags, tag["id"], "😀"))
        self.assertEqual(tag["emojis"], ["😀"])  # no duplicates, order kept
        self.assertEqual(tags_store.emoji_tags_index(tags), {"😀": ["joie"]})
        self.assertTrue(tags_store.rename_tag(tags, tag["id"], "bonheur"))
        self.assertTrue(tags_store.unlink_emoji(tags, tag["id"], "😀"))
        self.assertFalse(tags_store.unlink_emoji(tags, tag["id"], "😀"))
        self.assertTrue(tags_store.delete_tag(tags, tag["id"]))
        self.assertFalse(tags_store.delete_tag(tags, tag["id"]))

    def test_unknown_tag(self):
        self.assertFalse(tags_store.link_emoji([], "nope", "😀"))
        self.assertFalse(tags_store.rename_tag([], "nope", "x"))


class Actions(unittest.TestCase):
    def test_next_queries(self):
        tags = []
        self.assertEqual(tag_actions.apply_operation(tags, "create", "", "joie"), ">tags›")
        tid = tags[0]["id"]
        self.assertEqual(tag_actions.apply_operation(tags, "link", tid, "😀"), ">tags›%s›link›" % tid)
        self.assertEqual(tag_actions.apply_operation(tags, "unlink", tid, "😀"), ">tags›%s›unlink›" % tid)
        self.assertEqual(tag_actions.apply_operation(tags, "rename", tid, "x"), ">tags›%s›" % tid)
        self.assertEqual(tag_actions.apply_operation(tags, "delete", tid, ""), ">tags›")

    def test_invalid_operations(self):
        tags = []
        self.assertIsNone(tag_actions.apply_operation(tags, "create", "", "   "))
        self.assertIsNone(tag_actions.apply_operation(tags, "delete", "nope", ""))
        self.assertIsNone(tag_actions.apply_operation(tags, "explode", "", ""))


class Query(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(nav.parse_query(">"), ([], ""))
        self.assertEqual(nav.parse_query(" >tag"), ([], "tag"))
        self.assertTrue(nav.is_menu_query(" >"))
        self.assertFalse(nav.is_menu_query("smile"))
        self.assertEqual(nav.parse_query(">tags›"), (["tags"], ""))
        self.assertEqual(nav.parse_query(">tags›ab›link› smile "), (["tags", "ab", "link"], "smile"))

    def test_build_roundtrip(self):
        self.assertEqual(nav.build_query(["tags", "ab"], "x"), ">tags›ab›x")

    def test_matches_ignores_case_and_accents(self):
        self.assertTrue(matches("ÉTÉ sol", "été du soleil"))
        self.assertFalse(matches("lune", "soleil"))
        self.assertTrue(matches("", "anything"))


class Menu(TempDirTestCase):
    def setUp(self):
        super().setUp()
        self.settings = make_settings(self.tmp)
        self.tags = [{"id": "t1", "title": "joie", "emojis": ["😀"]}, {"id": "t2", "title": "vide", "emojis": []}]

    def menu(self, query, tags=None):
        tags = self.tags if tags is None else tags
        return nav.build_menu(query, Index.build(API, tags, self.settings), tags)

    def test_root(self):
        items = self.menu(">")
        self.assertEqual(titles(items), ["Back to search", "Tags", "API information", "Refresh the API"])
        self.assertEqual((items[0]["arg"], items[0]["variables"]), ("", {"action": "menu"}))
        self.assertEqual(items[1]["autocomplete"], ">tags›")
        self.assertFalse(items[1]["valid"])
        self.assertIn("3 Emojis", items[2]["subtitle"])
        self.assertEqual(items[3]["variables"], {"action": "refresh"})

    def test_root_filter(self):
        self.assertEqual(titles(self.menu(">tag")), ["Tags"])

    def test_tag_list(self):
        items = self.menu(">tags›")
        self.assertEqual(titles(items), ["Return", "Add a new tag", "joie", "vide"])
        self.assertEqual(items[0]["autocomplete"], ">")
        self.assertEqual(items[2]["autocomplete"], ">tags›t1›")
        self.assertEqual(items[3]["subtitle"], "❌ No Emojis")

    def test_typing_offers_creation_and_filters(self):
        items = self.menu(">tags›jo")
        self.assertEqual(titles(items), ["Return", "Create the tag 'jo'", "joie"])
        create = items[1]
        self.assertEqual((create["arg"], create["variables"]["tag_op"]), ("jo", "create"))

    def test_tag_detail(self):
        items = self.menu(">tags›t1›")
        self.assertEqual(
            titles(items),
            ["Return", "Modify the tag's name", "Link an emoji", "Unlink an emoji", "Delete the tag", "visage souriant"],
        )
        self.assertEqual(items[0]["autocomplete"], ">tags›")
        self.assertEqual(items[2]["autocomplete"], ">tags›t1›link›")
        self.assertEqual(items[4]["variables"]["tag_op"], "delete")
        self.assertEqual(items[4]["variables"]["tag_id"], "t1")

    def test_tag_without_emoji_cannot_unlink(self):
        self.assertNotIn("Unlink an emoji", titles(self.menu(">tags›t2›")))

    def test_rename(self):
        rename = self.menu(">tags›t1›bonheur")[1]
        self.assertEqual((rename["arg"], rename["variables"]["tag_op"]), ("bonheur", "rename"))

    def test_link_picker_excludes_linked(self):
        items = self.menu(">tags›t1›link›")
        self.assertEqual(items[0]["autocomplete"], ">tags›t1›")
        self.assertNotIn("visage souriant", titles(items))
        self.assertEqual(items[1]["arg"], "👋")
        self.assertEqual(items[1]["variables"]["tag_op"], "link")

    def test_link_picker_filters(self):
        self.assertEqual(titles(self.menu(">tags›t1›link›salue")), ["Return", "main qui salue"])

    def test_unlink_picker_only_linked(self):
        items = self.menu(">tags›t1›unlink›")
        self.assertEqual(titles(items), ["Return", "visage souriant"])
        self.assertEqual(items[1]["variables"]["tag_op"], "unlink")

    def test_unlink_picker_shows_every_skin_tone(self):
        """A linked emoji hidden by the skin tone preference can still be unlinked."""
        self.settings = make_settings(self.tmp, skin_tone="none")
        tags = [{"id": "t1", "title": "salut", "emojis": ["👋🏻"]}]
        items = self.menu(">tags›t1›unlink›", tags)
        self.assertEqual(titles(items), ["Return", "waving hand: light skin tone"])
        self.assertEqual(items[1]["arg"], "👋🏻")
        self.assertEqual(titles(self.menu(">tags›t1›", tags))[-1], "waving hand: light skin tone")

    def test_emoji_rows_use_the_search_items(self):
        row = self.menu(">tags›t1›")[-1]
        self.assertEqual((row["subtitle"], row["valid"]), ("😀", False))
        self.assertTrue(row["icon"]["path"].endswith("grinning face.png"))

    def test_results_are_capped(self):
        api = {"info": API["info"], "items": [
            {"name": "e%d" % i, "emoji": "x%d" % i, "title": None, "tags": None, "image": False, "skin_tones": ["base"]}
            for i in range(500)]}
        items = nav.build_menu(">tags›t2›link›", Index.build(api, self.tags, self.settings), self.tags)
        self.assertEqual(len(items), nav.MAX_RESULTS + 1)

    def test_stale_breadcrumb_falls_back_to_tag_list(self):
        self.assertEqual(titles(self.menu(">tags›gone›"))[:2], ["Return", "Add a new tag"])

    def test_every_valid_tag_item_carries_the_tag_action(self):
        for query in [">tags›x", ">tags›t1›x", ">tags›t1›", ">tags›t1›link›", ">tags›t1›unlink›"]:
            for entry in self.menu(query):
                if entry["title"] == "Return":
                    continue
                if entry.get("valid", True):
                    self.assertEqual(entry["variables"]["action"], "tag", (query, entry["title"]))

    def test_return_is_a_real_action(self):
        """⏎ on Return reopens Alfred on the parent level (menu action), ⇥ autocompletes it."""
        expected = {">tags›": ">", ">tags›t1›": ">tags›", ">tags›t1›link›": ">tags›t1›", ">tags›t1›unlink›": ">tags›t1›"}
        for query, parent in expected.items():
            back = self.menu(query)[0]
            self.assertEqual(back["title"], "Return")
            self.assertNotIn("valid", back)  # valid -> ⏎ runs the action
            self.assertEqual((back["arg"], back["autocomplete"]), (parent, parent))
            self.assertEqual(back["variables"], {"action": "menu"})


class EntryPoints(TempDirTestCase):
    """End-to-end: run the real scripts the way Alfred does."""

    def env(self):
        s = make_settings(self.tmp)
        env = dict(os.environ, language="fr", skin_tone="all", sound="", padding="10",
                   emoji_dictionary="emojipedia.org", short_copy="arg", short_paste="cmd",
                   short_web="shift", alfred_workflow_cache=s.cache_dir, alfred_workflow_data=s.data_dir,
                   alfred_workflow_version="2.1.0")
        write_json(s.api_file, API)
        return s, env

    def run_script(self, name, env, *args):
        done = subprocess.run([sys.executable, os.path.join(SRC, name), *args], env=env,
                              capture_output=True, text=True, cwd=self.tmp)
        self.assertEqual(done.returncode, 0, done.stderr)
        return done.stdout

    def run_tags(self, env, op, tag_id, value):
        """tags.py prints the Alfred JSON: arg (the menu query) + the notification variables."""
        out = json.loads(self.run_script("tags.py", dict(env, tag_op=op, tag_id=tag_id), value))
        return out["alfredworkflow"]["arg"], out["alfredworkflow"]["variables"]

    def test_wine(self):
        _, env = self.env()
        items = json.loads(self.run_script("wine.py", env))["items"]
        self.assertEqual(len(items), 6)  # Tags, API information, Refresh + 3 emojis
        self.assertEqual(items[0]["title"], "Tags")
        items = json.loads(self.run_script("wine.py", env, "salue"))["items"]
        self.assertEqual([i["title"] for i in items], ["main qui salue"])

    def test_menu(self):
        _, env = self.env()
        items = json.loads(self.run_script("wine.py", env, ">tags›"))["items"]
        self.assertEqual(items[0]["title"], "Return")

    def test_tags_script_full_flow(self):
        s, env = self.env()
        no_notification = {"notify_title": "", "notify_text": ""}
        self.assertEqual(self.run_tags(env, "create", "", "joie"), (">tags›", no_notification))
        tag = read_json(s.tags_file)[0]
        self.assertEqual(self.run_tags(env, "link", tag["id"], "😀")[0], ">tags›%s›link›" % tag["id"])
        self.assertEqual(read_json(s.tags_file)[0]["emojis"], ["😀"])
        items = json.loads(self.run_script("wine.py", env, "joie"))["items"]
        self.assertEqual([i["title"] for i in items], ["visage souriant"])  # index rebuilt with the tag
        self.run_tags(env, "delete", tag["id"], "")
        self.assertEqual(read_json(s.tags_file), [])

    def test_tags_script_bad_operation_notifies_an_error(self):
        s, env = self.env()
        arg, variables = self.run_tags(env, "nope", "", "x")
        self.assertEqual(arg, ">tags›")
        self.assertEqual(variables["notify_title"], "🚨 Error!")
        self.assertIn("GitHub issue", variables["notify_text"])
        with open(s.log_file, encoding="utf-8") as handle:
            self.assertIn("invalid tag operation", handle.read())

    def test_tags_script_is_silent_with_notifications_off(self):
        s, env = self.env()
        env["notify"] = "0"
        self.assertEqual(self.run_tags(env, "nope", "", "x"), (">tags›", {"notify_title": "", "notify_text": ""}))
        with open(s.log_file, encoding="utf-8") as handle:
            self.assertIn("invalid tag operation", handle.read())  # still logged


if __name__ == "__main__":
    unittest.main()
