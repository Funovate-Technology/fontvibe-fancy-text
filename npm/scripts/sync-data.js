#!/usr/bin/env node
// Copies the data from the repo root into the package (runs before test and pack).
// data/ at the repo root is the single source of truth; it is never committed twice.
// The package gets a slim, minified copy: only what transform()/defancify() read, plus the
// per-style metadata. The derived fields (char_map, coverage, example) stay in the repo files —
// they would triple the size of every browser bundle that imports this.
'use strict';
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..', '..', 'data');
const dst = path.join(__dirname, '..', 'data');
const read = (f) => {
  const p = path.join(root, f);
  if (!fs.existsSync(p)) {
    console.error('[sync-data] missing ' + p + ' — run this from inside the repo');
    process.exit(1);
  }
  return JSON.parse(fs.readFileSync(p, 'utf8'));
};
const DROP = ['char_map', 'coverage', 'example', 'fontvibe_pages'];

const styles = read('styles.json');
for (const s of styles.styles) for (const k of DROP) delete s[k];
const df = read('defancify.json');

fs.mkdirSync(dst, { recursive: true });
fs.writeFileSync(path.join(dst, 'styles.json'), JSON.stringify(styles));
fs.writeFileSync(path.join(dst, 'defancify.json'), JSON.stringify({ map: df.map, strip: df.strip }));
console.log('[sync-data] ok');
