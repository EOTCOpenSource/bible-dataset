#!/usr/bin/env python3
"""
Export this dataset into the "80-weahadu" JSON layout.

This only reads files from this repository. The 80-weahadu project is used as
a reference for the *shape* of the output; none of its data is read or copied.

Output layout (default: dist/weahadu/):

    editions.json                  index of every exported edition
    <edition>/meta.json            edition metadata + its book list
    <edition>/books/NN-slug.json   one file per book

Book file shape:

    {
      "edition": "am-2000", "book": "GEN", "usfm_id": "GEN", "order": 1,
      "chapters": [{ "n": 1, "verses": [{ "n": 1, "t": "..." }] }]
    }

Filenames use a fixed canon slot ("01-genesis.json" is Genesis in every
edition), so a 27-book edition has gaps in the numbering instead of renumbering.

Usage:
    python scripts/convert_weahadu.py                      # all translations
    python scripts/convert_weahadu.py -t am2000 geez       # selected ones
    python scripts/convert_weahadu.py -o out --indent 0    # compact output
"""

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Canon slots for the deuterocanonical / EOTC books, keyed by this dataset's
# usfm code. The Ethiopic 1-2 Maccabees and 1-2 Esdras are different works from
# the Greek ones, so they get EOTC slugs (e.g. 1ES -> "ezra-sutuel").
DEUTERO_SLOTS: Dict[str, tuple] = {
    "TOB": (40, "tobit"),
    "JDT": (41, "yodit"),
    "WIS": (43, "wisdom-of-solomon"),
    "SIR": (44, "sirach"),
    "BAR": (45, "baruch"),
    "LJE": (46, "teref-ermias"),
    "1MA": (49, "1-maccabees"),
    "2MA": (50, "2-maccabees"),
    "1ES": (51, "ezra-sutuel"),
    "3MA": (53, "3-maccabees"),
    "2ES": (54, "ezra-kalie"),
    "TEG": (55, "admonition"),  # Book of Admonition sits in the 4MA slot
    "JUB": (57, "kufale"),
    "ENO": (58, "enoch"),
    "4BA": (100, "rest-of-baruch"),  # no slot in the reference canon; new slot
}
# The reference canon uses 4MA as the id for the Book of Admonition.
USFM_ALIASES = {"TEG": "4MA"}

# Old Testament keeps its number (1-39); the New Testament starts at slot 59.
NT_OFFSET = 19

# Default edition ids follow the "<lang>-<name or year>" pattern.
DEFAULT_EDITION_IDS = {
    "am1954": "am-1954",
    "am2000": "am-2000",
    "tigrinya1997": "ti-1997",
    "oromiffa": "om-oromiffa",
    "somali": "so-somali",
    "wolayta": "wal-wolayta",
    "dawro": "dwr-dawro",
    "gamo": "gmv-gamo",
    "geez": "gez-geez",
    "coptic": "cop-coptic",
    "greekOriginal": "grc-original",
    "hebrewBible": "he-bible",
    "hebrewOriginal": "he-original",
}

# ISO 639-3 -> ISO 639-1 where a two-letter code exists.
LANG_CODES = {"amh": "am", "tir": "ti", "orm": "om", "som": "so", "heb": "he"}
# Script names -> ISO 15924 codes.
SCRIPT_CODES = {
    "Ethiopic": "Ethi", "Latin": "Latn", "Greek": "Grek",
    "Hebrew": "Hebr", "Coptic": "Copt",
}

UPSTREAM = "https://github.com/Beblia/Holy-Bible-XML-Format"


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(data: Any, path: str, indent: Optional[int]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        if indent:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        else:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")


def find_metadata(name: str) -> str:
    """Prefer metadata/<name>, fall back to the repo root copy."""
    for path in (os.path.join(PROJECT_ROOT, "metadata", name), os.path.join(PROJECT_ROOT, name)):
        if os.path.isfile(path):
            return path
    sys.exit(f"error: {name} not found in metadata/ or project root")


def slugify(book_id: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", book_id.lower()).strip("-")


def canon_slot(usfm: str, number: int, book_id: str) -> tuple:
    """Return (order, slug) for a book."""
    if usfm in DEUTERO_SLOTS:
        return DEUTERO_SLOTS[usfm]
    if number <= 39:
        return number, slugify(book_id)
    if number <= 66:
        return number + NT_OFFSET, slugify(book_id)
    raise ValueError(f"no canon slot for {usfm} ({book_id})")


def canon_label(book_files: List[dict], has_apocrypha: bool) -> str:
    if has_apocrypha:
        return "eotc-81"
    testaments = {b["testament"] for b in book_files}
    if len(book_files) >= 66:
        return "protestant-66"
    if testaments == {"new"}:
        return "nt-27"
    if testaments == {"old"}:
        return "ot-39"
    return "partial"


def parse_year(translation_id: str) -> Optional[int]:
    m = re.search(r"(1[0-9]{3}|20[0-9]{2})", translation_id)
    return int(m.group(1)) if m else None


# Languages whose editions get the Ge'ez numeral form of each verse number.
GEEZ_NUMERAL_LANGS = {"am", "gez", "ti"}


def geez_numeral(n: int) -> str:
    """Ge'ez numeral for 1-9999, e.g. 1 -> ፩, 23 -> ፳፫, 150 -> ፻፶."""
    ones = "፩፪፫፬፭፮፯፰፱"
    tens = "፲፳፴፵፶፷፸፹፺"

    def below_100(x: int) -> str:
        return (tens[x // 10 - 1] if x >= 10 else "") + (ones[x % 10 - 1] if x % 10 else "")

    hundreds, rest = divmod(n, 100)
    if not hundreds:
        return below_100(rest)
    return (below_100(hundreds) if hundreds > 1 else "") + "፻" + below_100(rest)


def convert_book(src: dict, edition: str, geez_alt: bool = False) -> dict:
    """Turn one source book into the target shape."""
    usfm = USFM_ALIASES.get(src["usfm"], src["usfm"])
    order, _ = canon_slot(src["usfm"], src["book_number"], src["book"])
    chapters = []
    for ch in src["chapters"]:
        verses = []
        for key, text in sorted(ch["verses"].items(), key=lambda kv: int(kv[0]) if kv[0].isdigit() else 10**9):
            # Keep non-numeric verse numbers (e.g. "3b") as strings.
            n: Any = int(key) if key.isdigit() else key
            verse: Dict[str, Any] = {"n": n, "t": text}
            if geez_alt and isinstance(n, int) and 0 < n < 10000:
                verse["alt"] = geez_numeral(n)
            verses.append(verse)
        chapters.append({"n": ch["chapter"], "verses": verses})
    return {"edition": edition, "book": usfm, "usfm_id": usfm, "order": order, "chapters": chapters}


def book_name(meta: Optional[dict], lang: str, fallback: str) -> str:
    if not meta:
        return fallback.replace("_", " ")
    if lang == "am" and meta.get("amharic_name"):
        return meta["amharic_name"]
    return meta.get("name") or fallback.replace("_", " ")


def export_translation(t: dict, edition: str, books_meta: dict, out_dir: str, indent: Optional[int]) -> dict:
    tid = t["id"]
    lang = LANG_CODES.get(t["language_code"], t["language_code"])
    sources = []
    canon_dir = os.path.join(PROJECT_ROOT, "data", tid)
    apoc_dir = os.path.join(PROJECT_ROOT, "data", "apocrypha", tid)
    for folder in (canon_dir, apoc_dir):
        if os.path.isdir(folder):
            sources += [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".json")]
    if not sources:
        print(f"  skip {tid}: no book files")
        return {}

    books = []
    for path in sources:
        src = load_json(path)
        order, slug = canon_slot(src["usfm"], src["book_number"], src["book"])
        target = convert_book(src, edition, geez_alt=lang in GEEZ_NUMERAL_LANGS)
        fname = f"{order:02d}-{slug}.json"
        write_json(target, os.path.join(out_dir, edition, "books", fname), indent)
        books.append({
            "src": src, "order": order, "file": f"books/{fname}", "usfm": target["book"],
            "chapters": len(target["chapters"]),
            "verses": sum(len(c["verses"]) for c in target["chapters"]),
        })
    books.sort(key=lambda b: b["order"])

    meta_books = []
    for pos, b in enumerate(books, start=1):
        src = b["src"]
        name = book_name(books_meta.get(src["usfm"]), lang, src["book"])
        meta_books.append({
            "id": b["usfm"], "usfm_id": b["usfm"], "file": b["file"], "order": b["order"],
            "position": pos, "name": name, "abbr": None,
            "chapters": b["chapters"], "verses": b["verses"],
        })

    stats = {
        "books": len(books),
        "chapters": sum(b["chapters"] for b in books),
        "verses": sum(b["verses"] for b in books),
    }
    has_apoc = any(b["order"] in {v[0] for v in DEUTERO_SLOTS.values()} for b in books)
    meta = {
        "id": edition,
        "language": lang,
        "script": SCRIPT_CODES.get(t.get("script"), t.get("script")),
        "title": t.get("native_name") or t["name"],
        "abbrev": tid,
        "title_en": t["name"],
        "year": parse_year(tid),
        "era": None,
        "canon": canon_label([b["src"] for b in books], has_apoc),
        "publisher": None,
        "language_name": t.get("language_name"),
        "direction": t.get("direction", "ltr"),
        "source": {
            "project": "EOTCOpenSource",
            "dataset": "bible-dataset",
            "translation": tid,
            "upstream": UPSTREAM,
        },
        "stats": stats,
        "books": meta_books,
    }
    write_json(meta, os.path.join(out_dir, edition, "meta.json"), indent)
    print(f"  {tid} -> {edition}: {stats['books']} books, {stats['chapters']} chapters, {stats['verses']} verses")
    return {k: meta[k] for k in ("id", "title", "title_en", "abbrev", "language", "language_name",
                                  "script", "year", "era", "canon", "publisher", "stats")}


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the dataset into the 80-weahadu JSON layout.")
    parser.add_argument("-t", "--translations", nargs="*", help="Translation ids to export (default: all)")
    parser.add_argument("-o", "--output", default=os.path.join(PROJECT_ROOT, "dist", "weahadu"),
                        help="Output folder (default: dist/weahadu)")
    parser.add_argument("--indent", type=int, default=1, help="JSON indent; 0 for compact (default: 1)")
    args = parser.parse_args()

    translations = load_json(find_metadata("translations.json"))
    books_meta = {b["usfm"]: b for b in load_json(find_metadata("books.json"))}
    books_meta.update({b["usfm"]: b for b in load_json(find_metadata("apocrypha_books.json"))})

    wanted = set(args.translations or [])
    unknown = wanted - {t["id"] for t in translations}
    if unknown:
        sys.exit(f"error: unknown translation(s): {', '.join(sorted(unknown))}")

    editions = []
    for t in translations:
        if wanted and t["id"] not in wanted:
            continue
        edition = DEFAULT_EDITION_IDS.get(t["id"], t["id"])
        entry = export_translation(t, edition, books_meta, args.output, args.indent)
        if entry:
            editions.append(entry)

    # Book registry built from this repo's own metadata: identity and order only.
    canon = []
    for b in books_meta.values():
        order, slug = canon_slot(b["usfm"], b["number"], b["id"])
        usfm = USFM_ALIASES.get(b["usfm"], b["usfm"])
        testament = "deuterocanonical" if b["usfm"] in DEUTERO_SLOTS else b["testament"]
        canon.append({"id": usfm, "order": order, "slug": slug, "file": f"{order:02d}-{slug}.json",
                      "name_en": b["name"], "testament": testament, "section": None})
    canon.sort(key=lambda c: c["order"])
    write_json(canon, os.path.join(args.output, "canon.json"), args.indent)

    write_json({"editions": editions, "canon": "canon.json"}, os.path.join(args.output, "editions.json"), args.indent)
    print(f"Wrote {len(editions)} edition(s) to {args.output}")


if __name__ == "__main__":
    main()
