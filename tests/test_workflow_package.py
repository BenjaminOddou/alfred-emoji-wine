"""Structural checks of the Alfred workflow (info.plist graph, scripts, settings)."""

import os
import plistlib
import re
import shutil
import subprocess
import unittest

from tests.helpers import ROOT, SRC
from winelib import __version__
from winelib import actions
from winelib.languages import load_languages
from winelib.settings import Settings


class InfoPlist(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(SRC, "info.plist"), "rb") as handle:
            cls.plist = plistlib.load(handle)
        cls.objects = {o["uid"]: o for o in cls.plist["objects"]}

    def test_version_matches_package(self):
        self.assertEqual(self.plist["version"], __version__)

    def test_connections_point_to_existing_nodes(self):
        for source, links in self.plist["connections"].items():
            self.assertIn(source, self.objects)
            for link in links:
                self.assertIn(link["destinationuid"], self.objects)
                if "sourceoutputuid" in link:
                    conditions = self.objects[source]["config"].get("conditions", [])
                    self.assertIn(link["sourceoutputuid"], [c["uid"] for c in conditions])

    def test_every_node_is_laid_out_and_unique(self):
        self.assertEqual(set(self.plist["uidata"]), set(self.objects))
        positions = [(u["xpos"], u["ypos"]) for u in self.plist["uidata"].values()]
        self.assertEqual(len(positions), len(set(positions)))
        for x, y in positions:
            self.assertEqual((x % 5, y % 5), (0, 0))  # tidy grid

    def test_no_orphans(self):
        reachable_targets = {l["destinationuid"] for ls in self.plist["connections"].values() for l in ls}
        entry_types = ("input.keyword", "trigger.external")
        for uid, obj in self.objects.items():
            if uid not in reachable_targets and not obj["type"].endswith(entry_types):
                # Script filters opened by their own keyword are entry points too
                self.assertTrue(obj["config"].get("keyword"), obj["type"])

    def test_referenced_scripts_exist(self):
        for obj in self.objects.values():
            config = obj["config"]
            for key in ("scriptfile", "inputfile"):
                if config.get(key):
                    self.assertTrue(os.path.isfile(os.path.join(SRC, config[key])), config[key])
            for match in re.findall(r"python3 (\S+\.py)", config.get("script", "")):
                self.assertTrue(os.path.isfile(os.path.join(SRC, match)), match)

    def test_conditionals_route_known_actions(self):
        known = {actions.REFRESH, actions.COPY, actions.PASTE, actions.WEB, actions.TAG, actions.MENU}
        for obj in self.objects.values():
            for condition in obj["config"].get("conditions", []):
                if condition["inputstring"] == "{var:style}":
                    self.assertIn(condition["matchstring"], ("list", "grid"))
                    continue
                if condition["inputstring"] == "{query}":  # menu query goes to the list view
                    self.assertEqual(condition["outputlabel"], "menu")
                    continue
                self.assertEqual(condition["inputstring"], "{var:action}")
                self.assertIn(condition["matchstring"], known)

    def test_external_triggers_are_called_only_if_defined(self):
        defined = {o["config"]["triggerid"] for o in self.objects.values() if o["type"].endswith("trigger.external")}
        called = {o["config"]["externaltriggerid"] for o in self.objects.values()
                  if o["type"].endswith("callexternaltrigger")}
        self.assertTrue(called <= defined)
        self.assertEqual(defined, {"emoji", "api"})

    def test_settings_used_by_scripts_are_configurable(self):
        variables = {u["variable"] for u in self.plist["userconfigurationconfig"]}
        for name in ("language", "skin_tone", "sound", "padding", "emoji_dictionary",
                     "short_copy", "short_paste", "short_web", "style", "trigger1"):
            self.assertIn(name, variables)

    def test_defaults_are_valid_choices(self):
        for entry in self.plist["userconfigurationconfig"]:
            pairs = entry["config"].get("pairs")
            if pairs:
                self.assertIn(entry["config"]["default"], [value for _, value in pairs], entry["variable"])

    def test_languages_come_from_the_plist(self):
        languages = load_languages(os.path.join(SRC, "info.plist"))
        self.assertIn({"title": "🇫🇷 Français", "value": "fr"}, languages)

    def test_no_pillow_anywhere(self):
        for folder, _, files in os.walk(SRC):
            for name in files:
                if name.endswith(".py"):
                    with open(os.path.join(folder, name), encoding="utf-8") as handle:
                        self.assertNotIn("PIL", handle.read(), name)

    def test_readme_does_not_ask_to_install_pillow(self):
        with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as handle:
            self.assertNotIn("brew install pillow", handle.read().lower())


class Scripts(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "node not installed")
    def test_jxa_script_has_valid_syntax(self):
        done = subprocess.run(["node", "--check", os.path.join(SRC, "winelib", "render_icons.js")],
                              capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_notificator_is_executable(self):
        self.assertTrue(os.access(os.path.join(SRC, "notificator"), os.X_OK))

    def test_python38_syntax_only(self):
        # no `match` statements, no `X | Y` annotations, no walrus-less surprises: compile check
        import ast
        for folder, _, files in os.walk(SRC):
            for name in files:
                if name.endswith(".py"):
                    path = os.path.join(folder, name)
                    with open(path, encoding="utf-8") as handle:
                        ast.parse(handle.read(), path, feature_version=(3, 8))


if __name__ == "__main__":
    unittest.main()


class SingleKeyword(unittest.TestCase):
    def test_only_one_keyword(self):
        with open(os.path.join(SRC, "info.plist"), "rb") as handle:
            plist = plistlib.load(handle)
        keywords = [o["config"]["keyword"] for o in plist["objects"] if o["config"].get("keyword")]
        self.assertEqual(keywords, ["{var:trigger1}"])
        self.assertNotIn("trigger2", {u["variable"] for u in plist["userconfigurationconfig"]})

    def test_menu_query_is_routed_to_the_list_view(self):
        with open(os.path.join(SRC, "info.plist"), "rb") as handle:
            plist = plistlib.load(handle)
        objects = {o["uid"]: o for o in plist["objects"]}
        for uid, obj in objects.items():
            for condition in obj["config"].get("conditions", []):
                if condition["outputlabel"] == "menu" and condition["inputstring"] == "{query}":
                    self.assertTrue(re.search(condition["matchstring"], " >tags›"))
                    self.assertIsNone(re.search(condition["matchstring"], "smile"))
                    targets = [objects[l["destinationuid"]]["type"] for l in plist["connections"][uid]
                               if l.get("sourceoutputuid") == condition["uid"]]
                    self.assertEqual(targets, ["alfred.workflow.input.scriptfilter"])
                    return
        self.fail("no menu route")

    def test_tag_script_reopens_alfred_through_the_emoji_trigger(self):
        with open(os.path.join(SRC, "info.plist"), "rb") as handle:
            plist = plistlib.load(handle)
        objects = {o["uid"]: o for o in plist["objects"]}
        tags = next(u for u, o in objects.items() if "tags.py" in o["config"].get("script", ""))
        target = objects[plist["connections"][tags][0]["destinationuid"]]
        self.assertEqual(target["config"]["externaltriggerid"], "emoji")
        self.assertTrue(target["config"]["passinputasargument"])
