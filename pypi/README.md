# unicode-text-styles

**120 Unicode "fancy text" styles** — 𝐛𝐨𝐥𝐝, 𝓼𝓬𝓻𝓲𝓹𝓽, Ⓑⓤⓑⓑⓛⓔ, 𝔤𝔬𝔱𝔥𝔦𝔠, ꜱᴍᴀʟʟ ᴄᴀᴘꜱ, ʇxǝʇ uʍop ǝpᴉsdn,
zalgo, lookalike scripts, braille, morse — plus `defancify()` to turn them back into plain text.
The same engine as **[fontvibe.ai/tools/fancy-font-generator](https://fontvibe.ai/tools/fancy-font-generator)**,
byte for byte, and identical to the npm package of the same name. Pure Python, no dependencies.

```bash
pip install unicode-text-styles
```

```python
from unicode_text_styles import transform, transform_all, defancify

transform("Hello World", "math_bold")           # 𝐇𝐞𝐥𝐥𝐨 𝐖𝐨𝐫𝐥𝐝
transform("Top 10", "circled")                  # Ⓣⓞⓟ ⑩
transform("Hello", "math_bold+strikethrough")   # chain with "+"
transform_all("Hello")                          # [{key, label, category, text}, …] × 120
defancify("𝐇𝐞𝐥𝐥𝐨 🅦🅞🅡🅛🅓")                       # Hello WORLD
```

From the shell:

```bash
python -m unicode_text_styles "Hello World"             # every style
python -m unicode_text_styles --style math_fraktur Hi
python -m unicode_text_styles --defancify "𝐇𝐞𝐥𝐥𝐨"
```

## API

| | |
|---|---|
| `transform(text, key)` | One style. Unmapped characters pass through. Raises `KeyError` on an unknown key. |
| `transform_all(text, category=None)` | Every style, in fontvibe.ai's order. |
| `defancify(text)` | Styled characters → plain ASCII; strips the combining marks the styles add. |
| `get_style(key)` | The style's metadata and `steps`. |
| `styles`, `keys`, `categories` | Metadata: label, category, category labels in en/es/pt/de/ja/zh (style names are English only), `unicode_age`. |

Rendering varies by device and font — preview before you post. Unicode doesn't have every letter in every style (there's no superscript q);
missing ones pass through unchanged. `defancify` also folds real letters of other scripts that
lookalike styles borrow (Greek α → a), and can't undo upside-down order. Details, limits and the
language-neutral data files: **[the repository](https://github.com/Funovate-Technology/fontvibe-fancy-text)**.

## License and attribution

Code MIT; the style tables bundled in `data/` are CC BY 4.0. If you ship them, please credit:

```html
Text styles from <a href="https://fontvibe.ai/tools/fancy-font-generator">FontVibe</a> ·
<a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>
```

`rel="nofollow"` is fine. Plain text works too:
`Text styles from FontVibe — https://fontvibe.ai/tools/fancy-font-generator — CC BY 4.0`.
Please link the site rather than only the repo — it's where your users can actually use them.
