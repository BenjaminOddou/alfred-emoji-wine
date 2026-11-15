import os
import unittest

from tests.helpers import TempDirTestCase
from winelib.settings import Settings
from winelib.storage import read_json, write_json


class Storage(TempDirTestCase):
    def test_roundtrip_and_atomicity(self):
        path = os.path.join(self.tmp, "sub", "a.json")
        write_json(path, {"é": 1})
        self.assertEqual(read_json(path), {"é": 1})
        self.assertEqual(os.listdir(os.path.dirname(path)), ["a.json"])

    def test_tolerant_reads(self):
        self.assertIsNone(read_json(os.path.join(self.tmp, "missing.json")))
        empty = os.path.join(self.tmp, "empty.json")
        open(empty, "w").close()
        self.assertIsNone(read_json(empty))
        broken = os.path.join(self.tmp, "broken.json")
        with open(broken, "w") as handle:
            handle.write("{nope")
        self.assertIsNone(read_json(broken))


class SettingsFromEnv(TempDirTestCase):
    def test_from_env(self):
        env = {"language": "ja", "padding": " 4 ", "alfred_workflow_cache": os.path.join(self.tmp, "c"),
               "alfred_workflow_data": os.path.join(self.tmp, "d"), "alfred_workflow_version": "2.0.0"}
        s = Settings.from_env(env, workflow_dir="/wf")
        self.assertEqual((s.language, s.padding), ("ja", 4))
        self.assertTrue(os.path.isdir(s.cache_dir) and os.path.isdir(s.data_dir))
        self.assertTrue(s.tags_file.endswith("tags-ja.json"))
        self.assertEqual(s.assets_dir, "/wf/icons/assets")

    def test_bad_padding_falls_back(self):
        self.assertEqual(Settings.from_env({"padding": "abc"}, workflow_dir="/wf").padding, 10)
        self.assertEqual(Settings.from_env({"padding": "-3"}, workflow_dir="/wf").padding, 0)


if __name__ == "__main__":
    unittest.main()
