'use strict';
/*!
 * unicode-text-styles — the fancy-text styles behind https://fontvibe.ai/tools/fancy-font-generator
 * Code: MIT. Style data (data/*.json): CC BY 4.0 — attribution required, see README.
 */
const DATA = require('./data/styles.json');
const DEFANCIFY = require('./data/defancify.json');

const STYLES = DATA.styles;
const BY_KEY = new Map(STYLES.map((s) => [s.key, s]));

// Tables are plain JSON objects; turn them into Maps once so lookups can never hit
// Object.prototype, and so we don't rebuild them per call.
const compiled = new Map();
function compile(style) {
  let c = compiled.get(style.key);
  if (c) return c;
  c = style.steps.map((st) => {
    const out = Object.assign({}, st);
    if (st.table) out.table = new Map(Object.entries(st.table));
    if (st.whole) out.whole = new Map(Object.entries(st.whole));
    if (st.digraphs) out.digraphs = new Map(Object.entries(st.digraphs));
    return out;
  });
  compiled.set(style.key, c);
  return c;
}

// JavaScript's \s, spelled out so the Python port can use the identical set.
const WS = '\\t\\n\\v\\f\\r \\u00a0\\u1680\\u2000-\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000\\ufeff';
const WORD_SPLIT = new RegExp('[' + WS + '\\-_]+');
const WS_SPLIT = new RegExp('([' + WS + ']+)');

function words(s) {
  return s.split(WORD_SPLIT).filter(Boolean);
}

const CASE = {
  title: (s) => s.split(WS_SPLIT).map((w) => (w.trim() ? w.charAt(0).toUpperCase() + w.slice(1).toLowerCase() : w)).join(''),
  camel: (s) => words(s.toLowerCase()).map((x, i) => (i === 0 ? x : x.charAt(0).toUpperCase() + x.slice(1))).join(''),
  snake: (s) => words(s.toLowerCase()).join('_'),
  kebab: (s) => words(s.toLowerCase()).join('-'),
  constant: (s) => words(s.toUpperCase()).join('_'),
  alternating: (s) => {
    let i = 0;
    return Array.from(s).map((c) => {
      if (!/[a-z]/i.test(c)) return c;
      const r = i % 2 === 0 ? c.toLowerCase() : c.toUpperCase();
      i++;
      return r;
    }).join('');
  },
  inverse: (s) => Array.from(s).map((c) => (c === c.toUpperCase() ? c.toLowerCase() : c.toUpperCase())).join(''),
};

const ROMAN = [[1000, 'M'], [900, 'CM'], [500, 'D'], [400, 'CD'], [100, 'C'], [90, 'XC'],
  [50, 'L'], [40, 'XL'], [10, 'X'], [9, 'IX'], [5, 'V'], [4, 'IV'], [1, 'I']];
function toRoman(n, lower) {
  if (n <= 0 || n > 3999) return String(n);
  let out = '';
  for (const [v, sym] of ROMAN) while (n >= v) { out += sym; n -= v; }
  return lower ? out.toLowerCase() : out;
}

function lookup(st, c) {
  const t = st.table;
  if (st.lookup === 'lower') return t.has(c.toLowerCase()) ? t.get(c.toLowerCase()) : c;
  if (t.has(c)) return t.get(c);
  if (st.lookup === 'exact_then_lower' && t.has(c.toLowerCase())) return t.get(c.toLowerCase());
  return c;
}

const ASCII_LETTER = /^[a-zA-Z]$/;

function applyStep(st, s) {
  switch (st.op) {
    case 'lower': return s.toLowerCase();
    case 'upper': return s.toUpperCase();
    case 'reverse': return Array.from(s).reverse().join('');
    case 'wrap': return st.prefix + s + st.suffix;
    case 'join': return Array.from(s).join(st.separator);
    case 'append': return Array.from(s).map((c) => (st.only === 'all' || ASCII_LETTER.test(c) ? c + st.marks : c)).join('');
    case 'case': return CASE[st.mode](s);
    case 'roman': return s.replace(/[0-9]+/g, (run) => toRoman(parseInt(run, 10), st.case === 'lower'));
    case 'map': {
      const chars = Array.from(s);
      const parts = [];
      for (let i = 0; i < chars.length; i++) {
        if (st.digraphs && i + 1 < chars.length) {
          const di = chars[i].toLowerCase() + chars[i + 1].toLowerCase();
          if (st.digraphs.has(di)) { parts.push(st.digraphs.get(di)); i++; continue; }
        }
        parts.push(lookup(st, chars[i]));
      }
      return parts.join(st.join || '');
    }
    case 'number_runs':
      return (s.match(/[0-9]+|[^0-9]+/g) || []).map((seg) => {
        if (/^[0-9]/.test(seg) && st.whole.has(seg)) return st.whole.get(seg);
        return Array.from(seg).map((c) => (st.table.has(c) ? st.table.get(c) : c)).join('');
      }).join('');
    case 'zalgo': {
      let seed = 0x9e3779b9 >>> 0;
      const rnd = (n) => { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed % n; };
      const P = st.pools;
      return Array.from(s).map((c) => {
        if (!ASCII_LETTER.test(c)) return c;
        let out = c;
        for (let i = 0; i < st.up; i++) out += P.up[rnd(P.up.length)];
        for (let i = 0; i < st.mid; i++) out += P.mid[rnd(P.mid.length)];
        for (let i = 0; i < st.down; i++) out += P.down[rnd(P.down.length)];
        return out;
      }).join('');
    }
    default:
      throw new Error('unicode-text-styles: unknown op ' + st.op);
  }
}

/**
 * Style `text` with one style. `key` may chain styles with "+", e.g. "math_bold+strikethrough".
 * Characters a style has no glyph for are passed through unchanged — nothing is dropped.
 */
function transform(text, key) {
  const s = String(text == null ? '' : text);
  if (key.includes('+') && !BY_KEY.has(key)) return key.split('+').reduce((acc, k) => transform(acc, k), s);
  const style = BY_KEY.get(key);
  if (!style) throw new Error('unicode-text-styles: unknown style "' + key + '" (see .keys)');
  return compile(style).reduce((acc, st) => applyStep(st, acc), s);
}

/** Every style applied to `text`, in the order FontVibe shows them. */
function transformAll(text, opts) {
  const o = opts || {};
  return STYLES
    .filter((st) => !o.category || st.category === o.category)
    .map((st) => ({ key: st.key, label: st.label, category: st.category, text: transform(text, st.key) }));
}

const DF_MAP = new Map(Object.entries(DEFANCIFY.map));
const DF_STRIP = new Set(DEFANCIFY.strip);

/**
 * Best-effort reverse: styled characters → plain ASCII, and the combining marks these
 * styles add are removed. It cannot undo reversed / upside-down order, and it will also fold
 * real letters of other scripts that a style borrows (Greek, Cyrillic, …) — see README.
 */
function defancify(text) {
  return Array.from(String(text == null ? '' : text))
    .map((c) => (DF_STRIP.has(c) ? '' : DF_MAP.has(c) ? DF_MAP.get(c) : c))
    .join('');
}

function getStyle(key) {
  return BY_KEY.get(key) || null;
}

module.exports = {
  transform,
  transformAll,
  defancify,
  getStyle,
  styles: STYLES,
  keys: STYLES.map((s) => s.key),
  categories: [...new Set(STYLES.map((s) => s.category))],
  unicodeVersion: DATA.unicode_version,
  homepage: 'https://fontvibe.ai/tools/fancy-font-generator',
};
