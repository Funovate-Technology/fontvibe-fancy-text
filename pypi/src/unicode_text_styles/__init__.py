"""unicode-text-styles — the fancy-text styles behind
https://fontvibe.ai/tools/fancy-font-generator

Pure Python, no dependencies. Produces byte-identical output to the npm package
of the same name (both are tested against the same golden file).

Code: MIT. Style data (``data/*.json``): CC BY 4.0 — attribution required, see README.
"""
from __future__ import annotations

import json
import math
import re
from functools import reduce
from pathlib import Path
from typing import Dict, List, Optional

__all__ = [
    "transform", "transform_all", "defancify", "get_style",
    "styles", "keys", "categories", "UNICODE_VERSION", "HOMEPAGE",
]

HOMEPAGE = "https://fontvibe.ai/tools/fancy-font-generator"

_DATA_DIR = Path(__file__).resolve().parent / "data"


def _load(name: str):
    path = _DATA_DIR / name
    if not path.exists():
        raise RuntimeError(
            f"unicode-text-styles: data file is missing ({path}). The package was probably "
            "built without running scripts/sync_data.py; please open an issue at "
            "https://github.com/Funovate-Technology/fontvibe-fancy-text/issues"
        )
    with open(path, encoding="utf-8") as f:
        return json.load(f)


_DATA = _load("styles.json")
_DEFANCIFY = _load("defancify.json")

styles: List[dict] = _DATA["styles"]
keys: List[str] = [s["key"] for s in styles]
categories: List[str] = list(dict.fromkeys(s["category"] for s in styles))
UNICODE_VERSION: str = _DATA["unicode_version"]
_BY_KEY: Dict[str, dict] = {s["key"]: s for s in styles}

# JavaScript's \s, spelled out, so case conversions split words exactly as the npm package does.
_WS = "\t\n\v\f\r    -     　﻿"
_WORD_SPLIT = re.compile("[" + _WS + r"\-_]+")
_WS_SPLIT = re.compile("([" + _WS + "]+)")
_ASCII_LETTER = re.compile(r"[a-zA-Z]")
_DIGIT_RUN = re.compile(r"[0-9]+")
_RUNS = re.compile(r"[0-9]+|[^0-9]+")


def _first_upper(w: str) -> str:
    # JS uppercases charAt(0), a UTF-16 code unit. For an astral first character that is a
    # lone surrogate, which has no case — so the character is left as is. Mirror that.
    if not w:
        return w
    return w[0] if ord(w[0]) > 0xFFFF else w[0].upper()


def _words(s: str) -> List[str]:
    return [w for w in _WORD_SPLIT.split(s) if w]


def _title(s: str) -> str:
    return "".join(
        (_first_upper(w) + w[1:].lower()) if (w and not _WS_SPLIT.fullmatch(w)) else w
        for w in _WS_SPLIT.split(s)
    )


def _camel(s: str) -> str:
    return "".join(x if i == 0 else _first_upper(x) + x[1:] for i, x in enumerate(_words(s.lower())))


def _alternating(s: str) -> str:
    out, i = [], 0
    for c in s:
        if _ASCII_LETTER.fullmatch(c):
            out.append(c.lower() if i % 2 == 0 else c.upper())
            i += 1
        else:
            out.append(c)
    return "".join(out)


def _inverse(s: str) -> str:
    return "".join(c.lower() if c == c.upper() else c.upper() for c in s)


_CASE = {
    "title": _title,
    "camel": _camel,
    "snake": lambda s: "_".join(_words(s.lower())),
    "kebab": lambda s: "-".join(_words(s.lower())),
    "constant": lambda s: "_".join(_words(s.upper())),
    "alternating": _alternating,
    "inverse": _inverse,
}

_ROMAN = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
          (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]


def _js_number_string(run: str) -> str:
    """String(parseInt(run, 10)) as JavaScript computes it (doubles, shortest round-trip)."""
    x = float(int(run))
    if math.isinf(x):
        return "Infinity"
    if x < 1e21:
        r = repr(x)  # shortest round-trip digits, like JS
        if "e" not in r:
            return r[:-2] if r.endswith(".0") else r
        mant, exp = r.split("e")
        digits = mant.replace(".", "")
        return digits + "0" * (int(exp) - (len(digits) - 1))
    mant, exp = repr(x).split("e")
    mant = mant[:-2] if mant.endswith(".0") else mant
    return f"{mant}e+{int(exp)}"


def _roman(run: str, lower: bool) -> str:
    n = int(run)
    if n <= 0 or n > 3999:
        return _js_number_string(run)
    out = []
    for v, sym in _ROMAN:
        while n >= v:
            out.append(sym)
            n -= v
    r = "".join(out)
    return r.lower() if lower else r


def _lookup(st: dict, c: str) -> str:
    t = st["table"]
    mode = st.get("lookup", "exact")
    if mode == "lower":
        return t.get(c.lower(), c)
    if c in t:
        return t[c]
    if mode == "exact_then_lower":
        return t.get(c.lower(), c)
    return c


def _zalgo(st: dict, s: str) -> str:
    seed = 0x9E3779B9
    pools = st["pools"]
    out = []
    for c in s:
        if not _ASCII_LETTER.fullmatch(c):
            out.append(c)
            continue
        piece = [c]
        for name in ("up", "mid", "down"):
            pool = pools[name]
            for _ in range(st[name]):
                seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
                piece.append(pool[seed % len(pool)])
        out.append("".join(piece))
    return "".join(out)


def _apply(st: dict, s: str) -> str:
    op = st["op"]
    if op == "lower":
        return s.lower()
    if op == "upper":
        return s.upper()
    if op == "reverse":
        return s[::-1]
    if op == "wrap":
        return st["prefix"] + s + st["suffix"]
    if op == "join":
        return st["separator"].join(s)
    if op == "append":
        every = st["only"] == "all"
        return "".join(c + st["marks"] if every or _ASCII_LETTER.fullmatch(c) else c for c in s)
    if op == "case":
        return _CASE[st["mode"]](s)
    if op == "roman":
        return _DIGIT_RUN.sub(lambda m: _roman(m.group(0), st["case"] == "lower"), s)
    if op == "map":
        dg = st.get("digraphs")
        parts, i = [], 0
        while i < len(s):
            if dg and i + 1 < len(s):
                di = s[i].lower() + s[i + 1].lower()
                if di in dg:
                    parts.append(dg[di])
                    i += 2
                    continue
            parts.append(_lookup(st, s[i]))
            i += 1
        return st.get("join", "").join(parts)
    if op == "number_runs":
        t, whole = st["table"], st["whole"]
        out = []
        for seg in _RUNS.findall(s):
            if seg[0].isascii() and seg[0].isdigit() and seg in whole:
                out.append(whole[seg])
            else:
                out.append("".join(t.get(c, c) for c in seg))
        return "".join(out)
    if op == "zalgo":
        return _zalgo(st, s)
    raise ValueError(f"unicode-text-styles: unknown op {op!r}")


def transform(text: str, key: str) -> str:
    """Style ``text`` with one style. ``key`` may chain styles with "+",
    e.g. ``"math_bold+strikethrough"``. Characters a style has no glyph for pass through
    unchanged — nothing is dropped."""
    s = "" if text is None else str(text)
    if "+" in key and key not in _BY_KEY:
        return reduce(transform, key.split("+"), s)
    style = _BY_KEY.get(key)
    if style is None:
        raise KeyError(f"unicode-text-styles: unknown style {key!r} (see unicode_text_styles.keys)")
    for st in style["steps"]:
        s = _apply(st, s)
    return s


def transform_all(text: str, category: Optional[str] = None) -> List[dict]:
    """Every style applied to ``text``, in the order FontVibe shows them."""
    return [
        {"key": st["key"], "label": st["label"], "category": st["category"], "text": transform(text, st["key"])}
        for st in styles
        if category is None or st["category"] == category
    ]


_DF_MAP: Dict[str, str] = _DEFANCIFY["map"]
_DF_STRIP = frozenset(_DEFANCIFY["strip"])


def defancify(text: str) -> str:
    """Best-effort reverse: styled characters → plain ASCII, and the combining marks these
    styles add are removed. It cannot undo reversed / upside-down order, and it also folds
    real letters of other scripts that a style borrows (Greek, Cyrillic, …) — see README."""
    s = "" if text is None else str(text)
    return "".join("" if c in _DF_STRIP else _DF_MAP.get(c, c) for c in s)


def get_style(key: str) -> Optional[dict]:
    return _BY_KEY.get(key)
