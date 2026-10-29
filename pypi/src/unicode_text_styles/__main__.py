"""Command line: python -m unicode_text_styles [--style KEY | --category NAME | --defancify | --list] [text]"""
from __future__ import annotations

import argparse
import sys

from . import HOMEPAGE, defancify, styles, transform, transform_all


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="unicode-text-styles",
        description="Unicode fancy-text styles. Text is read from stdin when omitted.",
        epilog=f"Styles from FontVibe — {HOMEPAGE} — CC BY 4.0",
    )
    p.add_argument("text", nargs="*")
    p.add_argument("--style", help='one style key ("a+b" chains)')
    p.add_argument("--category", help="only styles in this category")
    p.add_argument("--defancify", action="store_true", help="styled text → plain")
    p.add_argument("--list", action="store_true", help="list style keys")
    a = p.parse_args(argv)

    if a.list:
        for s in styles:
            print(f"{s['key']:<40}{s['category']}")
        return 0
    text = " ".join(a.text) if a.text else sys.stdin.read().rstrip("\n")
    try:
        if a.defancify:
            print(defancify(text))
        elif a.style:
            print(transform(text, a.style))
        else:
            for r in transform_all(text, a.category):
                print(f"{r['key']:<40}{r['text']}")
    except KeyError as e:
        print(e.args[0], file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
