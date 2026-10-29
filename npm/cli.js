#!/usr/bin/env node
'use strict';
const L = require('./index.js');

const args = process.argv.slice(2);
const flag = (name) => {
  const i = args.indexOf(name);
  if (i === -1) return null;
  const v = args[i + 1];
  args.splice(i, 2);
  return v == null ? '' : v;
};

if (args.includes('-h') || args.includes('--help')) {
  console.log(`usage: unicode-text-styles [text]                 every style
       unicode-text-styles --style <key> [text]   one style ("a+b" chains)
       unicode-text-styles --category <name> [text]
       unicode-text-styles --defancify [text]     styled text → plain
       unicode-text-styles --list                 style keys
text is read from stdin when omitted.

Styles from FontVibe — ${L.homepage} — CC BY 4.0`);
  process.exit(0);
}
if (args.includes('--list')) {
  for (const s of L.styles) console.log(s.key.padEnd(40) + s.category);
  process.exit(0);
}
const de = args.includes('--defancify');
if (de) args.splice(args.indexOf('--defancify'), 1);
const style = flag('--style');
const category = flag('--category');

const run = (text) => {
  try {
    if (de) return console.log(L.defancify(text));
    if (style) return console.log(L.transform(text, style));
    for (const r of L.transformAll(text, { category })) console.log(r.key.padEnd(40) + r.text);
  } catch (e) {
    console.error(e.message);
    process.exit(1);
  }
};

if (args.length) run(args.join(' '));
else {
  let d = '';
  process.stdin.on('data', (c) => (d += c)).on('end', () => run(d.replace(/\n$/, '')));
}
