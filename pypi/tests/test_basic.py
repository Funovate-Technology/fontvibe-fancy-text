"""Run with:  python scripts/sync_data.py && python -m unittest discover -s tests"""
import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

import unicode_text_styles as L  # noqa: E402
from unicode_text_styles.__main__ import main as cli  # noqa: E402

GOLDEN = HERE.parents[1] / "tests" / "golden.json"


class TestStyles(unittest.TestCase):
    @unittest.skipUnless(GOLDEN.exists(), "golden.json lives in the repo, not the sdist")
    def test_golden(self):
        g = json.loads(GOLDEN.read_text("utf-8"))
        self.assertEqual(sorted(g["outputs"]), sorted(L.keys))
        n = 0
        for key, outs in g["outputs"].items():
            for inp, want in zip(g["corpus"], outs):
                self.assertEqual(L.transform(inp, key), want, f"{key} on {inp!r}")
                n += 1
        self.assertGreater(n, 4000)

    def test_metadata(self):
        self.assertEqual(len(L.styles), 120)
        self.assertEqual(len(set(L.keys)), 120)
        for s in L.styles:
            self.assertIn(s["fontvibe_compat"], ("high", "medium", "low"))
            self.assertEqual(set(s["category_labels"]), {"en", "es", "pt", "de", "ja", "zh"})

    def test_readme_examples(self):
        self.assertEqual(L.transform("Hello World", "math_bold"), "𝐇𝐞𝐥𝐥𝐨 𝐖𝐨𝐫𝐥𝐝")
        self.assertEqual(L.transform("Hello World", "circled"), "Ⓗⓔⓛⓛⓞ Ⓦⓞⓡⓛⓓ")
        self.assertEqual(L.transform("Top 10", "circled"), "Ⓣⓞⓟ ⑩")
        self.assertEqual(L.defancify("ʜᴇʟʟᴏ"), "hello")
        self.assertEqual(L.defancify("𝐇𝐞𝐥𝐥𝐨 🅦🅞🅡🅛🅓"), "Hello WORLD")
        self.assertEqual(len(L.transform_all("Hello")), 120)

    def test_holes_patched(self):
        self.assertEqual(L.transform("h", "math_italic"), "ℎ")
        self.assertEqual(L.transform("H", "math_fraktur"), "ℌ")
        self.assertEqual(L.transform("R", "math_double_struck"), "ℝ")

    def test_passthrough(self):
        s = "Héllo 世界 👍🏽 ok"
        for key in ("math_bold", "circled", "small_caps", "mimic_cjk", "fullwidth"):
            out = L.transform(s, key)
            for c in ("é", "世", "界", "👍", "🏽"):
                self.assertIn(c, out, key)

    def test_chains_and_unknown(self):
        self.assertEqual(L.transform("ab", "math_bold+strikethrough"), "𝐚̶𝐛̶")
        self.assertEqual(L.transform("ab", "math_bold+deco_sparkle"), "✦ 𝐚𝐛 ✦")
        with self.assertRaises(KeyError):
            L.transform("x", "no_such_style")

    def test_js_number_quirk(self):
        # roman leaves out-of-range runs as JavaScript's String(parseInt(run)) would
        self.assertEqual(L.transform("0 007 4000", "roman_upper"), "0 VII 4000")
        self.assertEqual(L.transform("123456789012345678901234", "roman_upper"), "1.2345678901234569e+23")
        self.assertEqual(L.transform("1152921504606846976", "roman_upper"), "1152921504606847000")
        self.assertEqual(L.transform("99999999999999999999999", "roman_upper"), "1e+23")

    def test_zalgo_deterministic(self):
        self.assertEqual(L.transform("Hello", "zalgo"), L.transform("Hello", "zalgo"))
        self.assertEqual(L.defancify(L.transform("Hello", "zalgo_max")), "Hello")

    def test_defancify_round_trip(self):
        for key in ("math_bold", "math_script", "math_fraktur", "math_double_struck", "math_mono", "fullwidth", "circled"):
            self.assertEqual(L.defancify(L.transform("Hello World 2024", key)), "Hello World 2024", key)
        self.assertEqual(L.defancify("1️⃣2️⃣"), "12")

    def test_cli(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(cli(["--style", "circled", "abc"]), 0)
        self.assertEqual(buf.getvalue().strip(), "ⓐⓑⓒ")


if __name__ == "__main__":
    unittest.main()
