#!/usr/bin/env python3
"""Copy the data from the repo root into the package (run before test and build).

data/ at the repo root is the single source of truth; it is never committed twice.
The package gets a slim copy: only what transform()/defancify() read, plus the per-style
metadata. The derived fields (char_map, coverage, example) stay in the repo files.
"""
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2] / "data"
dst = Path(__file__).resolve().parents[1] / "src" / "unicode_text_styles" / "data"
DROP = ("char_map", "coverage", "example", "fontvibe_pages")


def read(name):
    p = root / name
    if not p.exists():
        sys.exit(f"[sync-data] missing {p} — run this from inside the repo")
    return json.loads(p.read_text("utf-8"))


styles = read("styles.json")
for s in styles["styles"]:
    for k in DROP:
        s.pop(k, None)
df = read("defancify.json")

dst.mkdir(parents=True, exist_ok=True)
dump = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
(dst / "styles.json").write_text(dump(styles), encoding="utf-8")
(dst / "defancify.json").write_text(dump({"map": df.get("map", {}), "strip": df.get("strip", [])}), encoding="utf-8")
print("[sync-data] ok")
