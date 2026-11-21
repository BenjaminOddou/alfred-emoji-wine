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
        self.assertLessEqual(variables - {"trigger1"}, set(Settings.__slots__))

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

    def test_entry_points_are_executable(self):
        for name in ("wine.py", "refresh.py", "tags.py"):
            self.assertTrue(os.access(os.path.join(SRC, name), os.X_OK), name)

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
        (target,) = [objects[l["destinationuid"]] for l in plist["connections"][tags]
                     if objects[l["destinationuid"]]["type"].endswith("callexternaltrigger")]
        self.assertEqual(target["config"]["externaltriggerid"], "emoji")
        self.assertTrue(target["config"]["passinputasargument"])


class Alfred6Notifications(unittest.TestCase):
    """No Notificator anymore: Alfred 6 posts the notifications (macOS UserNotifications API)."""

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(SRC, "info.plist"), "rb") as handle:
            cls.plist = plistlib.load(handle)
        cls.objects = {o["uid"]: o for o in cls.plist["objects"]}

    def targets(self, uid, output=None):
        return [self.objects[l["destinationuid"]] for l in self.plist["connections"].get(uid, [])
                if output is None or l.get("sourceoutputuid") == output]

    def script(self, name):
        return next(u for u, o in self.objects.items() if "python3 %s" % name in o["config"].get("script", ""))

    def test_notificator_is_gone(self):
        self.assertFalse(os.path.exists(os.path.join(SRC, "notificator")))
        for folder, _, files in os.walk(SRC):
            for name in files:
                if name.endswith((".py", ".js")):
                    with open(os.path.join(folder, name), encoding="utf-8") as handle:
                        self.assertNotIn("notificator --", handle.read(), name)

    def test_scripts_end_with_a_notification_posted_by_alfred(self):
        for name in ("refresh.py", "tags.py"):
            (argument,) = [t for t in self.targets(self.script(name))
                           if t["type"] == "alfred.workflow.utility.argument"]
            self.assertEqual(argument["config"]["argument"], "{var:notify_text}")
            (post,) = self.targets(argument["uid"])
            self.assertEqual(post["type"], "alfred.workflow.output.notification")
            config = post["config"]
            self.assertTrue(config["onlyshowifquerypopulated"])  # empty text (tag success): no notification
            self.assertEqual((config["title"], config["text"]), ("{var:notify_title}", "{query}"))

    def test_refresh_starts_with_a_please_wait_notification(self):
        actions_uid = next(u for u, o in self.objects.items()
                           if any(c["matchstring"] == "refresh" for c in o["config"].get("conditions", [])))
        refresh_output = next(c["uid"] for c in self.objects[actions_uid]["config"]["conditions"]
                              if c["matchstring"] == "refresh")
        api = next(u for u, o in self.objects.items() if o["config"].get("triggerid") == "api")
        for uid, output in ((actions_uid, refresh_output), (api, None)):
            types = [t["type"] for t in self.targets(uid, output)]
            self.assertEqual(types, ["alfred.workflow.output.notification", "alfred.workflow.action.script"])
            wait = self.targets(uid, output)[0]["config"]
            self.assertFalse(wait["onlyshowifquerypopulated"])
            self.assertTrue(wait["title"].startswith("⏳"))

    def test_sound_choices_are_system_sounds(self):
        entry = next(c for c in self.plist["userconfigurationconfig"] if c["variable"] == "sound")
        values = [value for _, value in entry["config"]["pairs"]]
        self.assertIn("", values)  # mute
        self.assertNotIn("default", values)  # "Classic" was a Notificator sound
        system = {"Basso", "Blow", "Bottle", "Frog", "Funk", "Glass", "Hero", "Morse", "Ping", "Pop", "Purr",
                  "Sosumi", "Submarine", "Tink"}
        self.assertTrue(set(values) - {""} <= system)

    def test_readme_asks_for_alfred_6(self):
        self.assertIn("Alfred 6", self.plist["readme"])
        with open(os.path.join(ROOT, "README.md"), encoding="utf-8") as handle:
            self.assertIn("Alfred 6", handle.read())
