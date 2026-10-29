#!/usr/bin/env python3
"""Check every claim the README makes. Standard library only.

    python3 scripts/verify.py            # offline checks
    python3 scripts/verify.py --online   # also checks each style's Unicode age against unicode.org

What it checks:
  1. counts — styles, base / chained, categories — against styles.json and stats.json
  2. every char_map entry, example and coverage figure equals the Python package's output,
     and (if `node` is on PATH) the npm package's output too; data/charmap.csv matches char_map
  3. both packages reproduce tests/golden.json — outputs captured from FontVibe's production
     implementation — exactly
  4. the de-fancify table: every entry is backed by a real style output, and how many
     (style, character) pairs round-trip, by outcome
  5. every code point the data can emit is assigned in the Unicode version the data states
  6. the figures block in README.md is exactly what this script computes

Exits non-zero on any failure.
"""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
import unicodedata
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ASCII = [chr(c) for c in range(0x20, 0x7F)]
ALNUM = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
PHRASE = "Hello World 2024"

failures = []


def check(ok, msg):
    print(("  ok    " if ok else "  FAIL  ") + msg)
    if not ok:
        failures.append(msg)


def load_python_package():
    subprocess.run([sys.executable, str(ROOT / "pypi" / "scripts" / "sync_data.py")], check=True, capture_output=True)
    sys.path.insert(0, str(ROOT / "pypi" / "src"))
    import unicode_text_styles
    return unicode_text_styles


def node_outputs(inputs):
    """{key: [transform(s) for s in inputs]} from the npm package, or None without node."""
    if not shutil.which("node"):
        return None
    subprocess.run(["node", str(ROOT / "npm" / "scripts" / "sync-data.js")], check=True, capture_output=True)
    script = (
        "const L=require(process.argv[1]);let d='';process.stdin.on('data',c=>d+=c).on('end',()=>{"
        "const xs=JSON.parse(d);const o={};for(const k of L.keys)o[k]=xs.map(s=>L.transform(s,k));"
        "o.__defancify__=xs.map(s=>L.defancify(s));process.stdout.write(JSON.stringify(o))})"
    )
    r = subprocess.run(["node", "-e", script, str(ROOT / "npm" / "index.js")],
                       input=json.dumps(inputs), capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def main():
    online = "--online" in sys.argv
    doc = json.loads((DATA / "styles.json").read_text("utf-8"))
    styles = doc["styles"]
    stats = json.loads((DATA / "stats.json").read_text("utf-8"))
    rev = json.loads((DATA / "defancify.json").read_text("utf-8"))
    golden = json.loads((ROOT / "tests" / "golden.json").read_text("utf-8"))
    L = load_python_package()
    fig = {}

    # ── 1. counts ──────────────────────────────────────────────────
    print("1. counts")
    keys = [s["key"] for s in styles]
    fig["styles"] = len(styles)
    fig["base"] = sum(1 for s in styles if "chain" not in s)
    fig["chained"] = sum(1 for s in styles if "chain" in s)
    fig["categories"] = len({s["category"] for s in styles})
    check(len(set(keys)) == len(keys), f"{len(keys)} style keys, all unique")
    check(stats["styles"] == fig["styles"] and stats["base_styles"] == fig["base"]
          and stats["chained_styles"] == fig["chained"] and stats["categories"] == fig["categories"],
          f"stats.json agrees: {fig['styles']} styles = {fig['base']} base + {fig['chained']} chained, {fig['categories']} categories")
    check(all("+".join(s["chain"]) == s["key"] and all(k in keys for k in s["chain"]) for s in styles if "chain" in s),
          "every chained style is made of styles that exist on their own")
    langs = {"en", "es", "pt", "de", "ja", "zh"}
    check(all(set(s["category_labels"]) == langs and all(s["category_labels"].values()) for s in styles),
          "every style has a category label in en/es/pt/de/ja/zh")
    banned = {"fontvibe_compat", "compat", "compatibility", "compat_notes"}
    check(not any(banned & set(s) for s in styles), "no compatibility rating fields are published (unverified heuristics)")

    # ── 2. data == library output ──────────────────────────────────
    print("2. data files vs library output")
    bad = [(s["key"], c) for s in styles for c, o in s.get("char_map", {}).items() if L.transform(c, s["key"]) != o]
    missing = [(s["key"], c) for s in styles if "char_map" in s for c in ASCII
               if c not in s["char_map"] and L.transform(c, s["key"]) != c]
    n_cm = sum(len(s.get("char_map", {})) for s in styles)
    fig["charmap_rows"] = n_cm
    fig["charmap_styles"] = sum(1 for s in styles if "char_map" in s)
    check(not bad and not missing, f"{n_cm} char_map entries across {fig['charmap_styles']} styles equal Python output, none missing")
    check(all(s["example"] == L.transform("Hello World 123", s["key"]) for s in styles), "every `example` equals Python output")
    groups = {"upper": "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "lower": "abcdefghijklmnopqrstuvwxyz", "digits": "0123456789"}
    check(all(s["coverage"] == {g: sum(1 for c in cs if L.transform(c, s["key"]) != c) for g, cs in groups.items()}
              for s in styles if "coverage" in s), f"every `coverage` figure recomputes ({sum('coverage' in s for s in styles)} styles)")
    # letter styles: base styles that substitute letters with other code points
    letter_styles = [s for s in styles if "chain" not in s and s["kind"] in ("map", "number_runs", "map+reverse")
                     and s["category"] not in ("Numbers", "Case", "Translator") and s["coverage"]["lower"] > 0]
    fig["letter_styles"] = len(letter_styles)
    fig["no_digits"] = sum(1 for s in letter_styles if s["coverage"]["digits"] == 0)
    fig["gaps"] = []
    for s in letter_styles:
        miss = [c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz" if L.transform(c, s["key"]) == c]
        if miss:
            fig["gaps"].append((s["key"], s["coverage"], "".join(miss)))
    with open(DATA / "charmap.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    expect = [(s["key"], c, o) for s in styles for c, o in s.get("char_map", {}).items()]
    check([(r["style"], r["input"], r["output"]) for r in rows] == expect, f"charmap.csv has the same {len(rows)} rows as char_map")
    check(all(r["output_codepoints"] == " ".join(f"U+{ord(x):04X}" for x in r["output"]) for r in rows), "charmap.csv code point column is correct")

    # ── 3. golden file (FontVibe production output) ────────────────
    print("3. both packages vs FontVibe's production implementation")
    corpus = golden["corpus"]
    check(set(golden["outputs"]) == set(keys), f"golden.json covers all {len(keys)} styles")
    n_g = sum(len(v) for v in golden["outputs"].values())
    py_bad = sum(L.transform(c, k) != e for k, outs in golden["outputs"].items() for c, e in zip(corpus, outs))
    check(py_bad == 0, f"Python: {n_g - py_bad}/{n_g} golden outputs identical")
    fig["golden"] = n_g
    probe = corpus + ASCII + [PHRASE, "Hello World 123"]
    js = node_outputs(probe)
    if js is None:
        print("  skip  node not found — npm package not checked")
    else:
        js_bad = sum(js[k][i] != e for k, outs in golden["outputs"].items() for i, e in enumerate(outs))
        check(js_bad == 0, f"npm:    {n_g - js_bad}/{n_g} golden outputs identical")
        same = all(js[k][i] == L.transform(x, k) for k in keys for i, x in enumerate(probe))
        same_df = all(js["__defancify__"][i] == L.defancify(x) for i, x in enumerate(probe))
        check(same and same_df, "npm and Python agree on every probe string, transform and defancify")

    # ── 4. de-fancify table ────────────────────────────────────────
    print("4. de-fancify table")
    m, det = rev["map"], rev["details"]
    fig["df_entries"] = len(m)
    check(set(m) == set(det) and all(det[c]["to"] == m[c] for c in m), f"{len(m)} entries; map and details agree")
    body = lambda s: "".join(x for x in s if unicodedata.category(x) not in ("Mn", "Me"))
    backed = all(
        any(body(L.transform(p, k)) == c for k in det[c]["styles"] for p in det[c]["from"])
        for c in m
    )
    check(backed, "every entry is produced by at least one of the styles it names")
    check(all(m[c] in det[c]["from"] for c in m), "every entry maps back to one of the characters that produce it")
    check(all(det[c]["nfkc_agrees"] == (unicodedata.normalize("NFKC", c) == m[c]) for c in m), "nfkc_agrees flags recompute")
    check(all(det[c]["is_letter"] == unicodedata.category(c).startswith("L") for c in m), "is_letter flags recompute")
    fig["df_nfkc"] = sum(1 for c in m if det[c]["nfkc_agrees"])
    fig["df_beyond_nfkc"] = len(m) - fig["df_nfkc"]
    fig["df_letters"] = sum(1 for c in m if det[c]["is_letter"] and not det[c]["nfkc_agrees"])
    fig["df_ambiguous"] = sum(1 for c in m if len({x.lower() for x in det[c]["from"]}) > 1)
    print(f"        {fig['df_nfkc']} already handled by NFKC, {fig['df_beyond_nfkc']} not; "
          f"{fig['df_letters']} of those are letters of a real script; {fig['df_ambiguous']} glyphs stand for >1 character")

    outcome = Counter()
    for s in styles:
        for c, o in s.get("char_map", {}).items():
            if c not in ALNUM:
                continue
            d = L.defancify(o)
            if all(ord(x) < 0x80 for x in o):
                outcome["ascii_output"] += 1
            elif d == c:
                outcome["exact"] += 1
            elif d.lower() == c.lower():
                outcome["case_lost"] += 1
            elif len(d) == 1 and d.isascii():
                outcome["ambiguous"] += 1
            else:
                outcome["other"] += 1
    fig["rt"] = outcome
    fig["rt_total"] = sum(outcome.values())
    print("        per-character round trip over A–Z a–z 0–9:", dict(outcome))
    check(outcome["exact"] > 0, "per-character round trip computed")
    phrase = Counter()
    for s in styles:
        d = L.defancify(L.transform(PHRASE, s["key"]))
        phrase["exact" if d == PHRASE else "case_only" if d.lower() == PHRASE.lower() else "no"] += 1
    fig["phrase"] = phrase
    print(f"        defancify(transform({PHRASE!r})) per style:", dict(phrase))

    # ── 5. Unicode assignment ──────────────────────────────────────
    print("5. Unicode")
    stated = doc["unicode_version"]
    cps = set()

    def walk(o):
        if isinstance(o, str):
            cps.update(ord(ch) for ch in o if ord(ch) > 0x7F)
        elif isinstance(o, dict):
            for k, v in o.items():
                walk(k)
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    for s in styles:
        walk(s["steps"])
        walk(s.get("char_map", {}))
        walk(s["example"])
    walk(list(m))
    walk(rev["strip"])
    fig["codepoints"] = len(cps)
    have = unicodedata.unidata_version
    if tuple(map(int, have.split("."))) >= tuple(map(int, stated.split("."))):
        unassigned = sorted(cp for cp in cps if unicodedata.category(chr(cp)) == "Cn")
        check(not unassigned, f"all {len(cps)} distinct non-ASCII code points are assigned (Python's Unicode {have} ≥ stated {stated})")
    else:
        print(f"  skip  this Python ships Unicode {have}, older than the stated {stated}; run with Python 3.14+ or --online")
    if online:
        url = f"https://www.unicode.org/Public/{stated}/ucd/DerivedAge.txt"
        raw = urllib.request.urlopen(url, timeout=30).read().decode("utf-8")
        ranges = []
        for line in raw.splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                a, age = (x.strip() for x in line.split(";"))
                lo, _, hi = a.partition("..")
                ranges.append((int(lo, 16), int(hi or lo, 16), age))
        age = lambda cp: next((g for lo, hi, g in ranges if lo <= cp <= hi), None)
        check(all(age(cp) for cp in cps), f"DerivedAge {stated}: all {len(cps)} code points assigned")
        vk = lambda v: tuple(map(int, v.split(".")))
        ok = True
        for s in styles:
            emitted = set()
            for st in s["steps"]:
                for k in ("prefix", "suffix", "separator", "marks"):
                    emitted.update(ord(x) for x in st.get(k, "") if ord(x) > 0x7F)
                for k in ("table", "whole", "digraphs"):
                    for v in st.get(k, {}).values():
                        emitted.update(ord(x) for x in v if ord(x) > 0x7F)
                for pool in st.get("pools", {}).values():
                    emitted.update(ord(x) for x in "".join(pool))
            want = max((age(cp) for cp in emitted), key=vk) if emitted else "1.1"
            ok &= want == s["unicode_age"]
        check(ok, "every style's unicode_age is the age of its newest code point")
    else:
        print("  skip  unicode_age per style (needs --online)")
    fig["age_counts"] = Counter(s["unicode_age"] for s in styles)
    fig["newest"] = max(fig["age_counts"], key=lambda v: tuple(map(int, v.split("."))))

    # ── 6. README figures block ────────────────────────────────────
    print("6. README")
    readme = (ROOT / "README.md").read_text("utf-8")
    for name, block in (("figures block", figures_block(fig)), ("de-fancify block", defancify_block(fig)),
                        ("limits table", limits_block(fig))):
        check(block in readme, f"README {name} matches this run exactly")
        if block not in readme:
            print("\n--- expected README " + name + " ---\n" + block + "\n---")

    print()
    if failures:
        print(f"{len(failures)} check(s) FAILED")
        sys.exit(1)
    print("all checks passed")


def figures_block(f):
    return "\n".join([
        "```",
        f"{f['styles']:>6,}   styles ({f['base']} base + {f['chained']} chained), {f['categories']} categories",
        f"{f['charmap_rows']:>6,}   character mappings in data/charmap.csv, across {f['charmap_styles']} per-character styles",
        f"{f['golden']:>6,}   test outputs, identical to FontVibe's production code, in both JS and Python",
        f"{f['df_entries']:>6,}   styled characters in the de-fancify table; for {f['df_beyond_nfkc']:,} of them NFKC gives no or another answer",
        f"{f['codepoints']:>6,}   distinct non-ASCII code points; the newest was added in Unicode {f['newest']}",
        "```",
    ])


def defancify_block(f):
    rt, ph = f["rt"], f["phrase"]
    return "\n".join([
        "```",
        f"{f['df_entries']:>6,}   styled characters → plain ASCII",
        f"{f['df_nfkc']:>6,}   of them Unicode NFKC normalisation already maps the same way",
        f"{f['df_beyond_nfkc']:>6,}   NFKC leaves alone or maps elsewhere (⒜ → '(a)') — what the table adds",
        f"{f['df_letters']:>6,}   of those are letters (Unicode category L*): Greek α, Yi ꍏ, Canadian syllabics ᗩ, CJK 卂, …",
        f"{f['df_ambiguous']:>6,}   glyphs stand for more than one character across styles",
        "",
        f"{f['rt_total']:>6,}   styled A–Z / a–z / 0–9 characters (style × character), and what defancify gives back:",
        f"{rt['exact']:>6,}   exactly the original",
        f"{rt['case_lost']:>6,}   the original in the other case — the style has only one case",
        f"{rt['ambiguous']:>6,}   a different character — a glyph shared between characters",
        f"{rt['other']:>6,}   something longer — multi-character outputs such as braille digits",
        f"{rt['ascii_output']:>6,}   nothing to undo — the style's output is plain ASCII already",
        "",
        f"{ph['exact']:>6,}   of {f['styles']} styles: defancify(transform(\"Hello World 2024\")) is exactly \"Hello World 2024\"",
        f"{ph['case_only']:>6,}   more give it back in a different case",
        "```",
    ])


def limits_block(f):
    lines = [
        f"Of the {f['letter_styles']} styles that swap letters for other characters, {f['no_digits']} have no digit forms "
        "at all — digits pass through as plain 0–9. These have letter gaps too:",
        "",
        "| Style | A–Z restyled | a–z restyled | Passed through unchanged |",
        "|---|---:|---:|---|",
    ]
    for key, cov, miss in f["gaps"]:
        lines.append(f"| `{key}` | {cov['upper']} | {cov['lower']} | `{miss}` |")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
