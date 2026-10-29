'use strict';
// Plain-node tests. No framework, no dev dependency.
const assert = require('assert');
const path = require('path');
const { execFileSync } = require('child_process');
const L = require('./index.js');

let n = 0;
const t = (name, fn) => { fn(); n++; console.log('  ok  ' + name); };

t('every style reproduces the golden file (FontVibe production output)', () => {
  const g = require(path.join(__dirname, '..', 'tests', 'golden.json'));
  assert.deepStrictEqual(Object.keys(g.outputs).sort(), [...L.keys].sort());
  let checked = 0;
  for (const [key, outs] of Object.entries(g.outputs)) {
    g.corpus.forEach((input, i) => {
      assert.strictEqual(L.transform(input, key), outs[i], key + ' on ' + JSON.stringify(input));
      checked++;
    });
  }
  assert.ok(checked > 4000);
});

t('120 styles, unique keys, metadata present', () => {
  assert.strictEqual(L.styles.length, 120);
  assert.strictEqual(new Set(L.keys).size, 120);
  for (const s of L.styles) {
    assert.ok(s.label && s.category && Array.isArray(s.steps) && s.steps.length);
    assert.ok(['high', 'medium', 'low'].includes(s.fontvibe_compat));
    for (const loc of ['en', 'es', 'pt', 'de', 'ja', 'zh']) assert.ok(s.category_labels[loc]);
  }
});

t('README examples', () => {
  assert.strictEqual(L.transform('Hello World', 'math_bold'), '𝐇𝐞𝐥𝐥𝐨 𝐖𝐨𝐫𝐥𝐝');
  assert.strictEqual(L.transform('Hello World', 'math_fraktur'), 'ℌ𝔢𝔩𝔩𝔬 𝔚𝔬𝔯𝔩𝔡');
  assert.strictEqual(L.transform('Top 10', 'circled'), 'Ⓣⓞⓟ ⑩');
  assert.strictEqual(L.transformAll('Hello').length, 120);
  assert.strictEqual(L.defancify('𝐇𝐞𝐥𝐥𝐨 🅦🅞🅡🅛🅓'), 'Hello WORLD');
  assert.strictEqual(L.defancify('ʜᴇʟʟᴏ'), 'hello');
});

t('Unicode holes are patched (italic h, fraktur H, double-struck R)', () => {
  assert.strictEqual(L.transform('h', 'math_italic'), 'ℎ');
  assert.strictEqual(L.transform('H', 'math_fraktur'), 'ℌ');
  assert.strictEqual(L.transform('R', 'math_double_struck'), 'ℝ');
});

t('nothing is dropped: unmapped characters pass through', () => {
  const s = 'Héllo 世界 👍🏽 ok';
  for (const key of ['math_bold', 'circled', 'small_caps', 'mimic_cjk', 'fullwidth']) {
    const out = L.transform(s, key);
    for (const c of ['é', '世', '界', '👍', '🏽']) assert.ok(out.includes(c), key + ' kept ' + c);
  }
});

t('chained keys work, including ad-hoc chains not in the list', () => {
  assert.strictEqual(L.transform('ab', 'math_bold+strikethrough'), '𝐚̶𝐛̶');
  assert.strictEqual(L.transform('ab', 'math_bold+deco_sparkle'), '✦ 𝐚𝐛 ✦');
});

t('unknown style throws instead of silently returning the input', () => {
  assert.throws(() => L.transform('x', 'no_such_style'), /unknown style/);
});

t('zalgo is deterministic', () => {
  assert.strictEqual(L.transform('Hello', 'zalgo'), L.transform('Hello', 'zalgo'));
  assert.notStrictEqual(L.transform('Hello', 'zalgo'), 'Hello');
});

t('defancify reverses every letter style that has both cases', () => {
  for (const key of ['math_bold', 'math_script', 'math_fraktur', 'math_double_struck', 'math_mono', 'fullwidth', 'circled']) {
    assert.strictEqual(L.defancify(L.transform('Hello World 2024', key)), 'Hello World 2024', key);
  }
  assert.strictEqual(L.defancify(L.transform('Hello', 'zalgo_max')), 'Hello');
  assert.strictEqual(L.defancify(L.transform('Hello', 'strikethrough')), 'Hello');
  assert.strictEqual(L.defancify('1️⃣2️⃣'), '12');
});

t('ESM entry exports the same API', () => {
  const out = execFileSync(process.execPath, ['--input-type=module', '-e',
    "import d, { transform, keys } from './index.mjs'; console.log(transform('a','math_bold'), keys.length, d.keys.length)"],
    { cwd: __dirname, encoding: 'utf8' });
  assert.strictEqual(out.trim(), '𝐚 120 120');
});

t('CLI', () => {
  const one = execFileSync(process.execPath, [path.join(__dirname, 'cli.js'), '--style', 'circled', 'abc'], { encoding: 'utf8' });
  assert.strictEqual(one.trim(), 'ⓐⓑⓒ');
  const de = execFileSync(process.execPath, [path.join(__dirname, 'cli.js'), '--defancify', '𝐚𝐛𝐜'], { encoding: 'utf8' });
  assert.strictEqual(de.trim(), 'abc');
});

console.log(n + ' passed');
