#!/usr/bin/env python3
"""Recompute every derived file from data/styles.json.

data/styles.json is the source of truth for the algorithm (`steps`) and FontVibe's metadata.
Everything else — `char_map`, `coverage`, `example`, `unicode_age` inside styles.json, plus
data/charmap.csv, data/defancify.json and data/stats.json — is derived here, using the
Python package as the reference implementation. Run it after editing any `steps`.

    python3 scripts/build.py            # needs network once, for Unicode's DerivedAge.txt
"""
from __future__ import annotations

import csv
import importlib
import io
import json
import shutil
import subprocess
import sys
import unicodedata
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
UNICODE_VERSION = "16.0.0"
AGE_URL = f"https://www.unicode.org/Public/{UNICODE_VERSION}/ucd/DerivedAge.txt"
ASCII = [chr(c) for c in range(0x20, 0x7F)]
EXAMPLE = "Hello World 123"
PER_CHAR_OPS = {"lower", "upper", "map", "number_runs", "append", "reverse"}
DERIVED = ("kind", "char_map", "coverage", "example", "unicode_age")

# Lookalike styles reuse one glyph for two different letters (Greek "Ρ" stands in for both P
# and R). The reverse table needs one answer; these are picked by which letter the glyph
# actually resembles. All alternatives are kept in defancify.json → details[c].from.
# Where the real Wingdings encoding and the lookalike "mimic_wingdings" disagree, the real
# encoding wins (decoding genuine Wingdings text is the use case that has a right answer).
# The build fails on any ambiguous glyph not covered by one of these two rules.
AMBIGUOUS = {
    "Ρ": "P", "Υ": "Y", "γ": "y", "ν": "v", "ρ": "p", "φ": "f",  # greek_style
    "ᒎ": "J",                                                     # mimic_syllabics (I and J)
    "ᚲ": "k", "ᚹ": "w", "ᛁ": "i",                                  # runic (one rune, several letters)
    "ㄥ": "L",                                                     # mimic_cjk L vs upside_down 7
}


def load_ages():
    raw = urllib.request.urlopen(AGE_URL, timeout=30).read().decode("utf-8")
    ranges = []
    for line in raw.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        cps, age = (x.strip() for x in line.split(";"))
        lo, _, hi = cps.partition("..")
        ranges.append((int(lo, 16), int(hi or lo, 16), age))
    return ranges


def age_of(cp, ranges):
    for lo, hi, age in ranges:
        if lo <= cp <= hi:
            return age
    return None


def vkey(v):
    return tuple(int(x) for x in v.split("."))


def emitted_codepoints(style):
    """Every non-ASCII code point a style can produce, read from its steps."""
    out = set()

    def add(s):
        out.update(ord(c) for c in s if ord(c) > 0x7F)

    for st in style["steps"]:
        for k in ("prefix", "suffix", "separator", "marks"):
            if k in st:
                add(st[k])
        for k in ("table", "whole", "digraphs"):
            for v in st.get(k, {}).values():
                add(v)
        for pool in st.get("pools", {}).values():
            for v in pool:
                add(v)
    return out


def main():
    styles_path = DATA / "styles.json"
    spec_path = DATA / "styles.spec.json"
    if spec_path.exists():  # first run from the generator's output
        doc = {"unicode_version": UNICODE_VERSION, "styles": json.loads(spec_path.read_text("utf-8"))}
        spec_path.unlink()
    else:
        doc = json.loads(styles_path.read_text("utf-8"))
    for s in doc["styles"]:
        for k in DERIVED:
            s.pop(k, None)
    doc["unicode_version"] = UNICODE_VERSION
    write_json(styles_path, doc)
    if not (DATA / "defancify.json").exists():
        write_json(DATA / "defancify.json", {"map": {}, "strip": []})

    pkg = load_package()
    ranges = load_ages()

    # ── per-style derived fields ───────────────────────────────────
    rows = []
    for s in doc["styles"]:
        key = s["key"]
        ops = [st["op"] for st in s["steps"]]
        core = [o for o in ops if o not in ("lower", "upper")] or ["case"]
        s["kind"] = "+".join(dict.fromkeys(core))
        if set(ops) <= PER_CHAR_OPS:
            cm = {c: pkg.transform(c, key) for c in ASCII}
            s["char_map"] = {c: o for c, o in cm.items() if o != c}
            for c, o in s["char_map"].items():
                rows.append((key, c, o, " ".join(f"U+{ord(x):04X}" for x in o)))
        groups = {"upper": "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "lower": "abcdefghijklmnopqrstuvwxyz", "digits": "0123456789"}
        # How many of A–Z / a–z / 0–9 the style actually restyles. Omitted for styles that only
        # add decoration around or between characters (wrap / join), where it would read as "26".
        if not {"wrap", "join"} & set(ops):
            s["coverage"] = {g: sum(1 for c in chars if pkg.transform(c, key) != c) for g, chars in groups.items()}
        s["example"] = pkg.transform(EXAMPLE, key)
        ages = [age_of(cp, ranges) for cp in emitted_codepoints(s)]
        if any(a is None for a in ages):
            sys.exit(f"[build] {key} emits an unassigned code point")
        s["unicode_age"] = max(ages, key=vkey) if ages else "1.1"

    # ── reverse (de-fancify) table ─────────────────────────────────
    cands = defaultdict(set)
    seen_in = defaultdict(set)
    strip = set()
    for s in doc["styles"]:
        for st in s["steps"]:
            if st["op"] == "append":
                strip.update(st["marks"])
            if st["op"] == "zalgo":
                for pool in st["pools"].values():
                    strip.update(pool)
        for st in s["steps"]:
            for plain, out in list(st.get("whole", {}).items()):
                if len(out) == 1 and ord(out) > 0x7F:
                    cands[out].add(plain)
                    seen_in[out].add(s["key"])
        for plain, out in s.get("char_map", {}).items():
            body = "".join(c for c in out if unicodedata.category(c) not in ("Mn", "Me"))
            for c in out:
                if unicodedata.category(c) in ("Mn", "Me"):
                    strip.add(c)
            if len(body) == 1 and ord(body) > 0x7F:
                cands[body].add(plain)
                seen_in[body].add(s["key"])

    wingdings_src = {o: p for p, o in next(s for s in doc["styles"] if s["key"] == "wingdings")["char_map"].items()}
    # The case a style folds its input to, if any: braille lowercases first, so ⠁ → "a".
    folds = {}
    for s in doc["styles"]:
        st = s["steps"]
        folds[s["key"]] = ("lower" if any(x["op"] == "lower" or x.get("lookup") == "lower" for x in st)
                           else "upper" if any(x["op"] == "upper" for x in st) else None)
    rev, details, unresolved = {}, {}, []
    for c in sorted(cands, key=ord):
        options = cands[c]
        folded = {o.lower() for o in options}
        nfkc = unicodedata.normalize("NFKC", c)
        if len(options) == 1:
            to = next(iter(options))
        elif len(folded) == 1:
            if nfkc in options:
                to = nfkc
            elif all(folds[k] == "lower" for k in seen_in[c]) or "SMALL" in unicodedata.name(c, ""):
                to = next(iter(folded))
            else:
                to = next(iter(folded)).upper()
        elif "wingdings" in seen_in[c]:
            to = wingdings_src[c]
        elif c in AMBIGUOUS:
            to = AMBIGUOUS[c]
        else:
            unresolved.append((c, f"U+{ord(c):04X}", sorted(options), sorted(seen_in[c])))
            continue
        rev[c] = to
        details[c] = {
            "to": to,
            "from": sorted(options),
            "styles": sorted(seen_in[c]),
            "nfkc_agrees": nfkc == to,
            "is_letter": unicodedata.category(c).startswith("L"),
        }
    if unresolved:
        for u in unresolved:
            print("[build] ambiguous:", *u)
        sys.exit("[build] add the ambiguous glyphs above to AMBIGUOUS")

    write_json(DATA / "defancify.json", {
        "unicode_version": UNICODE_VERSION,
        "map": rev,
        "strip": sorted(strip, key=ord),
        "details": details,
    })
    write_json(styles_path, doc)

    with open(DATA / "charmap.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["style", "input", "output", "output_codepoints"])
        w.writerows(rows)

    cats = Counter(s["category"] for s in doc["styles"])
    stats = {
        "styles": len(doc["styles"]),
        "base_styles": sum(1 for s in doc["styles"] if "chain" not in s),
        "chained_styles": sum(1 for s in doc["styles"] if "chain" in s),
        "categories": len(cats),
        "by_category": dict(sorted(cats.items())),
        "by_kind": dict(sorted(Counter(s["kind"] for s in doc["styles"]).items())),
        "charmap_rows": len(rows),
        "defancify_entries": len(rev),
        "defancify_strip": len(strip),
        "unicode_version": UNICODE_VERSION,
    }
    write_json(DATA / "stats.json", stats)
    sync()
    print("[build] ok —", json.dumps(stats, ensure_ascii=False))


def write_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def sync():
    subprocess.run([sys.executable, str(ROOT / "pypi" / "scripts" / "sync_data.py")], check=True)
    subprocess.run(["node", str(ROOT / "npm" / "scripts" / "sync-data.js")], check=True)


def load_package():
    sync()
    sys.path.insert(0, str(ROOT / "pypi" / "src"))
    import unicode_text_styles as pkg
    return importlib.reload(pkg)


if __name__ == "__main__":
    main()
