# Schema

## `data/styles.json`

```json
{
  "unicode_version": "16.0.0",
  "styles": [
    {
      "key": "math_fraktur",
      "label": "Gothic",
      "category": "Gothic",
      "category_labels": { "en": "Gothic", "es": "Gótica", "…": "…" },
      "fontvibe_compat": "medium",
      "steps": [ { "op": "map", "table": { "A": "𝔄", "B": "𝔅", "C": "ℭ", "…": "…" } } ],
      "fontvibe_pages": [ "https://fontvibe.ai/tools/fancy-font-generator", "…" ],
      "kind": "map",
      "char_map": { "A": "𝔄", "…": "…" },
      "coverage": { "upper": 26, "lower": 26, "digits": 0 },
      "example": "ℌ𝔢𝔩𝔩𝔬 𝔚𝔬𝔯𝔩𝔡 123",
      "unicode_age": "3.1"
    }
  ]
}
```

Styles are in the order fontvibe.ai shows them.

| Field | Type | Notes |
|---|---|---|
| `key` | string | Stable identifier. Chained styles are their parts joined with `+`. |
| `label` | string | Display name, English. (fontvibe.ai shows style names in English in every language.) |
| `category` | string | One of 23, English. |
| `category_labels` | object | The category's display name in `en` `es` `pt` `de` `ja` `zh`, as fontvibe.ai shows it. |
| `fontvibe_compat` | string | `high` \| `medium` \| `low`. **FontVibe's editorial rating**, not a measurement. `low` is what fontvibe.ai tags "may not show on all devices". |
| `chain` | string[] | Only on chained styles: the base styles applied, in order. |
| `steps` | object[] | **The definition of the style.** Apply in order to the input string. See [Steps](#steps). |
| `fontvibe_pages` | string[] | The fontvibe.ai tool pages that feature this style. |
| `kind` | string | Derived: the step ops used, joined with `+`, ignoring `lower`/`upper`. |
| `char_map` | object | Derived, only for per-character styles: each printable ASCII character (U+0020–U+007E) → its output, where the output differs. For styles that also reverse (upside-down), this is the glyph only. |
| `coverage` | object | Derived: how many of `A–Z`, `a–z`, `0–9` the style changes. Omitted for styles that only wrap or join, where it would be meaningless. |
| `example` | string | Derived: the style applied to `Hello World 123`. |
| `unicode_age` | string | Derived: the Unicode version that added the newest code point this style can emit (from Unicode's `DerivedAge.txt`). `1.1` if it emits nothing newer than Unicode 1.1. |

Derived fields are written by `scripts/build.py` and checked by `scripts/verify.py`; edit
`steps`, never the derived fields. The npm and PyPI packages ship a slim copy without
`char_map`, `coverage`, `example` and `fontvibe_pages`.

## Steps

A style is a pipeline: start with the input string, apply each step to the result of the
previous one. Unless a step says otherwise, it works **per code point** (not per UTF-16 unit,
not per grapheme), and any character it has no rule for **passes through unchanged**.

| `op` | Parameters | Meaning |
|---|---|---|
| `lower` | — | Full Unicode lowercase of the whole string (JS `toLowerCase()`, Python `str.lower()`). |
| `upper` | — | Full Unicode uppercase of the whole string. |
| `map` | `table`, `lookup?`, `join?`, `digraphs?` | Replace each code point via `table`. `lookup`: `exact` (default) — `table[c]`; `lower` — `table[lower(c)]`; `exact_then_lower` — `table[c]`, else `table[lower(c)]`. If no entry, keep `c` (the original, not its lowercase). Outputs are joined with `join` (default `""`). If `digraphs` is present, first check whether lower(this char) + lower(next char) is a key; if so, emit that value and consume both. |
| `number_runs` | `table`, `whole` | Split the string into maximal runs of ASCII digits `[0-9]+` and runs of everything else. A digit run that is a key of `whole` (e.g. `"10"` → `⑩`) is replaced as a whole; every other run is mapped per code point through `table`. |
| `roman` | `case` | Replace each run of ASCII digits with its Roman numeral (`upper` or `lower` case) using the standard subtractive form. Runs whose value is 0 or above 3999 become the decimal value without leading zeros (`"000"` → `"0"`). |
| `append` | `marks`, `only` | After each code point (`only: "all"`) or each ASCII letter `[A-Za-z]` (`only: "ascii_letters"`), insert the string `marks` (combining characters). |
| `zalgo` | `up`, `mid`, `down`, `pools` | After each ASCII letter, insert `up` marks from `pools.up`, then `mid` from `pools.mid`, then `down` from `pools.down`, each chosen by the PRNG below. Other characters unchanged. |
| `wrap` | `prefix`, `suffix` | `prefix + s + suffix`. |
| `join` | `separator` | Insert `separator` between every two code points. |
| `reverse` | — | Reverse the order of code points. |
| `case` | `mode` | `title` · `camel` · `snake` · `kebab` · `constant` · `alternating` · `inverse` — see below. |

### Zalgo PRNG

A 32-bit linear congruential generator, **reset at the start of every call** so the same input
always yields the same output:

```
seed = 0x9E3779B9
next(n):  seed = (seed * 1664525 + 1013904223) mod 2^32;  return seed mod n
```

One `next(len(pool))` per inserted mark, in the order up → mid → down, letter by letter.

### Case modes

"Whitespace" below means exactly JavaScript's `\s`:
`\t \n \v \f \r U+0020 U+00A0 U+1680 U+2000–U+200A U+2028 U+2029 U+202F U+205F U+3000 U+FEFF`.
"Words" means the string split on runs of whitespace, `-` and `_`, empty pieces dropped.

| Mode | Rule |
|---|---|
| `title` | Split into whitespace runs and non-whitespace runs; in each non-whitespace run, uppercase the first character and lowercase the rest. |
| `camel` | Lowercase, split into words, uppercase the first character of every word but the first, concatenate. |
| `snake` / `kebab` | Lowercase, split into words, join with `_` / `-`. |
| `constant` | Uppercase, split into words, join with `_`. |
| `alternating` | Among ASCII letters only, alternate lower, upper, lower, … (other characters don't advance the count). |
| `inverse` | Per code point: if `c == upper(c)` then `lower(c)` else `upper(c)`. |

One quirk is kept on purpose, so that every implementation agrees with fontvibe.ai: in `title`
and `camel`, a word whose first character is outside the Basic Multilingual Plane (above
U+FFFF) keeps that character's case as is.

## `data/charmap.csv`

`style,input,output,output_codepoints` — one row per `char_map` entry, UTF-8, with a header row.
`output_codepoints` is space-separated `U+XXXX`.

## `data/defancify.json`

```json
{
  "unicode_version": "16.0.0",
  "map":   { "𝐀": "A", "⑩": "10", "…": "…" },
  "strip": [ "̀", "́", "…" ],
  "details": {
    "ν": { "to": "v", "from": ["n", "v"], "styles": ["greek_style"], "nfkc_agrees": false, "is_letter": true }
  }
}
```

To de-fancify: for each code point, drop it if it's in `strip`, else replace it via `map`, else
keep it.

| Field | Notes |
|---|---|
| `map` | Styled character → plain ASCII (usually one character; `⑩` → `10`). |
| `strip` | Combining marks and the emoji presentation characters (U+FE0F, U+20E3) that the styles add. |
| `details[c].from` | Every plain character some style turns into `c`. More than one means the glyph is ambiguous; `to` is our pick. |
| `details[c].styles` | The styles that produce `c`. |
| `details[c].nfkc_agrees` | `true` if Unicode NFKC normalisation already turns `c` into `to`. |
| `details[c].is_letter` | `true` if `c` is a letter (general category `L*`) — i.e. it may be real text in some script, and folding it may be wrong for your input. |

How a single answer is picked when several characters produce the same glyph: NFKC's answer if
it's one of them; otherwise, if the alternatives differ only in case, the case the style folds
to (or lowercase for "SMALL" characters, else uppercase); where the real Wingdings encoding and
the lookalike `mimic_wingdings` disagree, the real encoding; the remaining handful are listed by
hand in `scripts/build.py` with the reason.

## `tests/golden.json`

`{"corpus": [...], "outputs": {"<key>": [...]}}` — `outputs[key][i]` is what FontVibe's
production code returns for `corpus[i]`. A port is correct when it reproduces all of them.
