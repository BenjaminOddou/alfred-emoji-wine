import glob
import os
import unittest

from tests.helpers import SRC
from winelib import png


class PngPadding(unittest.TestCase):
    def test_roundtrip(self):
        rows = [bytes([i, 0, 0, 255] * 3) for i in range(2)]
        data = png.write_rgba(3, 2, rows)
        self.assertEqual(png.read_rgba(data), (3, 2, rows))

    def test_pad_dimensions_and_content(self):
        pixel = bytes([10, 20, 30, 255])
        padded = png.pad_png(png.write_rgba(2, 2, [pixel * 2] * 2), 6)
        width, height, rows = png.read_rgba(padded)
        self.assertEqual((width, height), (8, 8))
        self.assertEqual(rows[0], bytes(32))  # transparent top margin
        self.assertEqual(rows[3][12:16], pixel)  # image starts at (3, 3)
        self.assertEqual(rows[2][12:16], bytes(4))

    def test_odd_padding(self):
        width, height, _ = png.read_rgba(png.pad_png(png.write_rgba(1, 1, [bytes(4)]), 5))
        self.assertEqual((width, height), (6, 6))

    def test_bundled_assets_are_readable(self):
        for path in glob.glob(os.path.join(SRC, "icons", "assets", "*.png")):
            with open(path, "rb") as handle:
                data = handle.read()
            width, height, rows = png.read_rgba(data)
            self.assertEqual(len(rows), height, path)
            self.assertTrue(all(len(r) == width * 4 for r in rows), path)
            padded = png.read_rgba(png.pad_png(data, 10))
            self.assertEqual(padded[:2], (width + 10, height + 10))

    def test_rejects_non_png(self):
        with self.assertRaises(ValueError):
            png.read_rgba(b"nope")


if __name__ == "__main__":
    unittest.main()
