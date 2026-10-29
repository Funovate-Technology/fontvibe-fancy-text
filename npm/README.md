# unicode-text-styles

**120 Unicode "fancy text" styles** — 𝐛𝐨𝐥𝐝, 𝓼𝓬𝓻𝓲𝓹𝓽, Ⓑⓤⓑⓑⓛⓔ, 𝔤𝔬𝔱𝔥𝔦𝔠, ꜱᴍᴀʟʟ ᴄᴀᴘꜱ, ʇxǝʇ uʍop ǝpᴉsdn,
zalgo, lookalike scripts, braille, morse — plus `defancify()` to turn them back into plain text.
The same engine as **[fontvibe.ai/tools/fancy-font-generator](https://fontvibe.ai/tools/fancy-font-generator)**,
byte for byte. Zero dependencies; under 90 KB of JSON tables.

```bash
npm i unicode-text-styles
```

```js
const { transform, transformAll, defancify } = require('unicode-text-styles');

transform('Hello World', 'math_bold');               // 𝐇𝐞𝐥𝐥𝐨 𝐖𝐨𝐫𝐥𝐝
transform('Top 10', 'circled');                      // Ⓣⓞⓟ ⑩
transform('Hello', 'math_bold+strikethrough');       // chain with "+"
transformAll('Hello');                               // [{ key, label, category, text }, …] × 120
defancify('𝐇𝐞𝐥𝐥𝐨 🅦🅞🅡🅛🅓');                            // Hello WORLD
```

ESM and TypeScript work out of the box:

```ts
import { transform, styles, type Style } from 'unicode-text-styles';
```

Try it without installing:

```bash
npx unicode-text-styles "Hello World"            # every style
npx unicode-text-styles --style math_fraktur Hi
npx unicode-text-styles --defancify "𝐇𝐞𝐥𝐥𝐨"
npx unicode-text-styles --list
```

## API

| | |
|---|---|
| `transform(text, key)` | One style. Unmapped characters pass through. Throws on an unknown key. |
| `transformAll(text, { category? })` | Every style, in fontvibe.ai's order. |
| `defancify(text)` | Styled characters → plain ASCII; strips the combining marks the styles add. |
| `getStyle(key)` | The style's metadata and `steps`. |
| `styles`, `keys`, `categories` | Metadata: label, category, category labels in en/es/pt/de/ja/zh, `fontvibe_compat`, `unicode_age`. |

`fontvibe_compat` is **FontVibe's editorial rating** (`high` / `medium` / `low`), not a
measurement. Unicode doesn't have every letter in every style (there's no superscript q);
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
