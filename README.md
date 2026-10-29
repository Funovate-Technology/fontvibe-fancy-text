# fancy text — Unicode text styles

**120 Unicode "fancy text" styles — 𝐛𝐨𝐥𝐝, 𝓼𝓬𝓻𝓲𝓹𝓽, Ⓑⓤⓑⓑⓛⓔ, 𝔤𝔬𝔱𝔥𝔦𝔠, ʇxǝʇ uʍop ǝpᴉsdn, z̮͗å̘l̪̒g͍̕ó̝ — as
language-neutral JSON, with identical JavaScript and Python libraries, and a reverse table
that turns them back into plain text.**

Try every style at **[fontvibe.ai/tools/fancy-font-generator](https://fontvibe.ai/tools/fancy-font-generator)**
— type once, tap any style to copy, no install. This repo is the engine and data behind that page,
pulled out so you can build on it.

```
   120   styles (106 base + 14 chained), 23 categories
 3,261   character mappings in data/charmap.csv, across 59 per-character styles
 4,560   test outputs, identical to FontVibe's production code, in both JS and Python
 1,547   styled characters in the de-fancify table; for 557 of them NFKC gives no or another answer
 1,812   distinct non-ASCII code points; the newest was added in Unicode 7.0
```

Every number above is recomputed by [`scripts/verify.py`](scripts/verify.py) (standard library
only), which fails if this README disagrees with the data. See [Verify it](#verify-it).

```bash
npm i unicode-text-styles        # or: npx unicode-text-styles "Hello World"
pip install unicode-text-styles  # or: python -m unicode_text_styles "Hello World"
```

---

## Quick start

```js
import { transform, transformAll, defancify } from 'unicode-text-styles'

transform('Hello World', 'math_bold')             // 𝐇𝐞𝐥𝐥𝐨 𝐖𝐨𝐫𝐥𝐝
transform('Hello World', 'math_fraktur')          // ℌ𝔢𝔩𝔩𝔬 𝔚𝔬𝔯𝔩𝔡
transform('Hello World', 'math_bold+strikethrough') // chain styles with "+"
transformAll('Hello').length                      // 120 — every style, in the site's order

defancify('𝐇𝐞𝐥𝐥𝐨 🅦🅞🅡🅛🅓')                         // Hello WORLD
```

```python
from unicode_text_styles import transform, transform_all, defancify

transform("Hello World", "circled")    # Ⓗⓔⓛⓛⓞ Ⓦⓞⓡⓛⓓ
transform("Top 10", "circled")         # Ⓣⓞⓟ ⑩  — 10 to 20 have their own code points
defancify("ʜᴇʟʟᴏ")                     # hello
```

No dependencies in either. The two produce byte-identical output — both are tested against the
same [golden file](tests/golden.json), captured from the code that runs on fontvibe.ai.

Not using JS or Python? Read [`data/styles.json`](data/styles.json) directly. Each style is a
short list of `steps` — `map`, `append`, `wrap`, `join`, `reverse`, … — specified precisely
enough in [SCHEMA.md](SCHEMA.md) to port in an afternoon, and the golden file tells you when
your port is right.

## Files

| File | What it is | Use it for |
|---|---|---|
| `data/styles.json` | All 120 styles: label, category (labels in en · es · pt · de · ja · zh), FontVibe's compatibility rating, the `steps` that define the style, plus derived `char_map`, `coverage`, `example`, `unicode_age` | **Start here.** Everything else is derived from it |
| `data/charmap.csv` | `style,input,output,output_codepoints` for every per-character style and every printable ASCII input | Spreadsheets, SQL, any language with a CSV reader |
| `data/defancify.json` | Styled character → plain ASCII, the combining marks to strip, and per-entry `details` | Moderation bots, search indexing, username normalisation |
| `data/stats.json` | Counts, machine-readable | |
| `tests/golden.json` | A fixed set of test inputs × all 120 styles, output from FontVibe's production code | Testing your own port |

Field definitions and the exact semantics of every step: [SCHEMA.md](SCHEMA.md).

## The styles

| Category | Styles |
|---|---|
| Bold, Italic, Cursive, Gothic, Outline, Sans, Monospace | Unicode's Mathematical Alphanumeric Symbols — 𝐁 𝐼 𝓒 𝔊 𝕆 𝖲 𝙼 — including the letters that live elsewhere (italic h is `ℎ` U+210E; fraktur H is `ℌ`) |
| Bubble, Squares | Enclosed Alphanumerics — Ⓐ 🅐 🄰 🅰 ⒜, and ① ➀ ➊ ⓵ for digits |
| Numbers | ⒈ ⚀ 1️⃣, and Roman numerals for 1–3999 (written with ordinary ASCII letters) |
| Tiny, Small Caps, Wide | ˢᵘᵖᵉʳ, ₛᵤbₛcᵣᵢₚₜ (Unicode has no subscript b or c), ꜱᴍᴀʟʟ ᴄᴀᴘꜱ, Ｆｕｌｌｗｉｄｔｈ, s p a c e d |
| Strikethrough, Underline, Glitch | combining marks — s̶t̶r̶i̶k̶e̶, u̲n̲d̲e̲r̲, and deterministic zalgo |
| Decorated | ꧁ wraps ꧂ and ♡j♡o♡i♡n♡s♡ |
| Mimic | lookalikes from other scripts — 卂乃匚 ᗩᗷᑕ ꍏꌃꉓ — and 🇦 regional indicators |
| Reverse, Runic, Translator, Case | upside-down, backwards, Elder Futhark, braille, morse, binary, Wingdings, camelCase / snake_case / … |

Zalgo here is **deterministic**: the same input always gives the same output, in both
languages. That matters if you render on the server and hydrate on the client, and it's what
lets the golden file test it.

---

## De-fancify

Fancy text is a common way past keyword filters and search: `𝐟𝐫𝐞𝐞 𝐜𝐫𝐲𝐩𝐭𝐨` doesn't match `free crypto`.
Unicode's own NFKC normalisation catches some of it, and the table records exactly how much:

```
 1,547   styled characters → plain ASCII
   990   of them Unicode NFKC normalisation already maps the same way
   557   NFKC leaves alone or maps elsewhere (⒜ → '(a)') — what the table adds
   190   of those are letters (Unicode category L*): Greek α, Yi ꍏ, Canadian syllabics ᗩ, CJK 卂, …
    22   glyphs stand for more than one character across styles

 2,918   styled A–Z / a–z / 0–9 characters (style × character), and what defancify gives back:
 2,298   exactly the original
   371   the original in the other case — the style has only one case
    39   a different character — a glyph shared between characters
    12   something longer — multi-character outputs such as braille digits
   198   nothing to undo — the style's output is plain ASCII already

    41   of 120 styles: defancify(transform("Hello World 2024")) is exactly "Hello World 2024"
    17   more give it back in a different case
```

What it does **not** do, plainly:

- **It folds real letters.** Those 190 are ordinary letters in some writing system. Run
  `defancify` over genuine Greek text and `α` becomes `a`. Each entry in
  `defancify.json → details` carries `is_letter` and `nfkc_agrees`; if your input can contain
  real Greek, Yi, Cyrillic or CJK, skip the `is_letter` entries.
- **It strips the combining marks these styles add** — and those include the ordinary accents
  (U+0300–U+036F). Text written in decomposed form (`e` + U+0301) loses its accents. Text in the
  usual precomposed form (`é`) is untouched.
- **It doesn't undo order or decoration.** Upside-down and backwards text stays reversed;
  wraps like `꧁ … ꧂` and separators like `♡` stay. Case styles (snake_case, …) aren't reversible.
- **Ambiguous glyphs get one answer.** Greek `ν` stands for both n and v in the lookalike style;
  every alternative is listed in `details[c].from`.
- **It only knows these 120 styles.** For general confusable / homoglyph detection across all of
  Unicode, [null8626/decancer](https://github.com/null8626/decancer) covers far more ground; this
  table is narrower and fully inspectable.

## Limits

Unicode doesn't have every letter in every style. Where a style has no glyph, the character
passes through unchanged — nothing is dropped, but the result is mixed.

Of the 33 styles that swap letters for other characters, 18 have no digit forms at all — digits pass through as plain 0–9. These have letter gaps too:

| Style | A–Z restyled | a–z restyled | Passed through unchanged |
|---|---:|---:|---|
| `small_caps` | 26 | 25 | `x` |
| `upside_down` | 26 | 21 | `losxz` |
| `superscript` | 25 | 25 | `Qq` |
| `subscript` | 17 | 17 | `BCDFGQWYZbcdfgqwyz` |
| `mimic_currency` | 21 | 21 | `IJQVXijqvx` |

(`upside_down`'s five already look the same upside down. The per-style `coverage` field in
`styles.json` gives these counts for every style.)

Also worth knowing:

- **Rendering varies by device and font.** These are real Unicode characters, so they copy and
  paste anywhere, but whether a given phone shows the glyph or a box depends on its fonts.
  `unicode_age` on each style is the Unicode version its newest code point was added in — a
  fact, not a guarantee; older systems are likelier to lack newer characters.
- **Combining-mark styles** (strikethrough, underline, zalgo, glitch, …) are rendered by stacking
  marks on the previous character; how well that looks depends heavily on the font.
- **`fontvibe_compat` is FontVibe's own editorial rating** (`high` / `medium` / `low`; `low` is
  what fontvibe.ai tags "may not show on all devices"). It is a judgement, not a measurement —
  use it as a starting point, not as a fact about any platform.
- **Screen readers** may announce mathematical letters as symbols, or skip them. Don't use fancy
  text for anything that has to be read by everyone — names, alt text, important instructions.
- **Lookalike styles are not translations.** `greek_style`, `mimic_*` and `runic` pick characters
  by shape (or by a rough phonetic match, for runes); the result is not Greek, Yi or Old Norse.
- **Morse, binary and braille** are encodings, not fonts. Braille is uncontracted (Grade 1) English.

---

## Verify it

```bash
python3 scripts/verify.py            # stdlib only; also runs the npm package if node is on PATH
python3 scripts/verify.py --online   # also checks every style's unicode_age against unicode.org
```

It checks, and exits non-zero on any failure:

1. the style, category and chain counts, against `styles.json` and `stats.json`
2. every `char_map` entry, `example` and `coverage` figure against the Python package's output,
   and `charmap.csv` against `char_map`
3. both packages against `tests/golden.json` — every output identical — and against each other
4. every de-fancify entry is produced by a style it names, and the round-trip counts above
5. every code point in the data is assigned in Unicode 16.0 (with `--online`: each style's age)
6. the three blocks of figures in this README are exactly what it just computed

The tests for each package: `cd npm && npm test` and
`cd pypi && python scripts/sync_data.py && python -m unittest discover -s tests`.

---

## Attribution

The data is CC BY 4.0, which asks you to credit the source "in any reasonable manner requested
by the licensor". Here's what we ask for — copy whichever fits:

**Markdown**
```markdown
Text styles from [FontVibe](https://fontvibe.ai/tools/fancy-font-generator) ·
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
```

**HTML**
```html
Text styles from <a href="https://fontvibe.ai/tools/fancy-font-generator">FontVibe</a> ·
<a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>
```

**Plain text** (for a CLI, a NOTICE file, an app's about screen)
```
Text styles from FontVibe — https://fontvibe.ai/tools/fancy-font-generator — CC BY 4.0
```

A few things worth saying plainly:

- **Add `rel="nofollow"` if you prefer.** It's your page; we're not asking you to pass ranking
  signals, and we'd rather you credit us with a nofollow link than not credit us at all.
- **A link is not strictly required** — CC BY's exact words are "to the extent reasonably
  practicable". In a terminal app or a printed piece, plain text is fine.
- **Please link the site, not just this repo.** `fontvibe.ai/tools/fancy-font-generator` is where
  the styles are live and one-tap copyable, which is what your users will actually find useful.
  The repo is the raw material behind it.
- **Using only the code** (the npm or PyPI package logic, MIT)? A credit is appreciated, not
  required beyond MIT's notice. The bundled style tables are the data, and are CC BY.

## Citing it

There's a [`CITATION.cff`](CITATION.cff), so GitHub's "Cite this repository" button works.
BibTeX:

```bibtex
@misc{fontvibe_fancy_text,
  title        = {FontVibe Fancy Text: Unicode Text Styles},
  author       = {{FontVibe}},
  year         = {2026},
  version      = {1.0.0},
  howpublished = {\url{https://fontvibe.ai/tools/fancy-font-generator}},
  note         = {120 Unicode text styles with JS and Python implementations and a reverse table. CC BY 4.0}
}
```

## License

- **Data** (`data/`, `tests/golden.json`, and the copies bundled in the packages): [CC BY 4.0](LICENSE).
- **Code** (`npm/`, `pypi/`, `scripts/`): [MIT](LICENSE-CODE).

What CC BY covers is this compilation — the selection of styles, the lookalike choices, the
labels and ratings, the reverse table. The characters themselves belong to nobody: which code
point is "mathematical bold capital A" is defined by Unicode, and you're free to build the same
tables yourself from the Unicode Character Database. See [NOTICE](NOTICE).

## Contributing

Spotted a better lookalike, a missing glyph, or a style that renders badly somewhere specific?
[Open an issue](https://github.com/Funovate-Technology/fontvibe-fancy-text/issues/new) — with the
device and app if it's a rendering problem, since that's the part we can't see from here.
PRs welcome; `key` is stable, and `python3 scripts/build.py && python3 scripts/verify.py` must pass.

---

Built and maintained by [FontVibe](https://fontvibe.ai). The live version is at
[fontvibe.ai/tools/fancy-font-generator](https://fontvibe.ai/tools/fancy-font-generator).
