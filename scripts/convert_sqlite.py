#!/usr/bin/env python3
"""
Convert Geez (or MyBible format) SQLite Bible databases to chapter JSON files,
matching the project's folder structure: <output_dir>/<testament>/<book>/<chapter>.json
"""

import argparse
import json
import os
import re
import sqlite3
from typing import Dict, Optional, Tuple

BOOK_NAMES = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua",
    "Judges", "Ruth", "1_Samuel", "2_Samuel", "1_Kings", "2_Kings",
    "1_Chronicles", "2_Chronicles", "Ezra", "Nehemiah", "Esther", "Job",
    "Psalms", "Proverbs", "Ecclesiastes", "Song_of_Solomon", "Isaiah",
    "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos",
    "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai",
    "Zechariah", "Malachi",
    "Matthew", "Mark", "Luke", "John", "Acts", "Romans", "1_Corinthians",
    "2_Corinthians", "Galatians", "Ephesians", "Philippians", "Colossians",
    "1_Thessalonians", "2_Thessalonians", "1_Timothy", "2_Timothy", "Titus",
    "Philemon", "Hebrews", "James", "1_Peter", "2_Peter", "1_John", "2_John",
    "3_John", "Jude", "Revelation",
]

# Standard MyBible book_number mapping (e.g. 10 -> Genesis, 230 -> Psalms, 470 -> Matthew)
MYBIBLE_BOOK_NUMBERS = {
    10: "Genesis", 20: "Exodus", 30: "Leviticus", 40: "Numbers", 50: "Deuteronomy",
    60: "Joshua", 70: "Judges", 80: "Ruth", 90: "1_Samuel", 100: "2_Samuel",
    110: "1_Kings", 120: "2_Kings", 130: "1_Chronicles", 140: "2_Chronicles",
    150: "Ezra", 160: "Nehemiah", 170: "Esther", 180: "Job", 190: "Psalms",
    200: "Proverbs", 210: "Ecclesiastes", 220: "Song_of_Solomon",
    230: "Psalms",  # In some MyBible module variations Job is 220 and Psalms is 230
    240: "Proverbs", 250: "Ecclesiastes", 260: "Song_of_Solomon",
    290: "Isaiah", 300: "Jeremiah", 310: "Lamentations", 330: "Ezekiel",
    340: "Daniel", 350: "Hosea", 360: "Joel", 370: "Amos", 380: "Obadiah",
    390: "Jonah", 400: "Micah", 410: "Nahum", 420: "Habakkuk", 430: "Zephaniah",
    440: "Haggai", 450: "Zechariah", 460: "Malachi",
    470: "Matthew", 480: "Mark", 490: "Luke", 500: "John", 510: "Acts",
    520: "Romans", 530: "1_Corinthians", 540: "2_Corinthians", 550: "Galatians",
    560: "Ephesians", 570: "Philippians", 580: "Colossians", 590: "1_Thessalonians",
    600: "2_Thessalonians", 610: "1_Timothy", 620: "2_Timothy", 630: "Titus",
    640: "Philemon", 650: "Hebrews", 660: "James", 670: "1_Peter", 680: "2_Peter",
    690: "1_John", 700: "2_John", 710: "3_John", 720: "Jude", 730: "Revelation",
}

# Mapping normalized book names (lowercase, no spaces/underscores) to canonical BOOK_NAMES entry
NORMALIZED_BOOK_MAP = {
    name.lower().replace("_", ""): name for name in BOOK_NAMES
}
# Common alternate aliases
NORMALIZED_BOOK_MAP.update({
    "psalm": "Psalms",
    "songofsongs": "Song_of_Solomon",
    "canticleofcanticles": "Song_of_Solomon",
})


def resolve_book(db_book_num: int, long_name: Optional[str] = None, short_name: Optional[str] = None) -> Tuple[str, int, str]:
    """
    Resolves canonical book name, 1-based canonical book number, and testament ("old" or "new").
    """
    canonical_name = None

    if long_name:
        clean_name = long_name.strip().lower().replace(" ", "").replace("_", "")
        if clean_name in NORMALIZED_BOOK_MAP:
            canonical_name = NORMALIZED_BOOK_MAP[clean_name]

    if not canonical_name and short_name:
        clean_short = short_name.strip().lower().replace(" ", "").replace("_", "")
        if clean_short in NORMALIZED_BOOK_MAP:
            canonical_name = NORMALIZED_BOOK_MAP[clean_short]

    if not canonical_name and db_book_num in MYBIBLE_BOOK_NUMBERS:
        canonical_name = MYBIBLE_BOOK_NUMBERS[db_book_num]

    if not canonical_name:
        if 1 <= db_book_num <= len(BOOK_NAMES):
            canonical_name = BOOK_NAMES[db_book_num - 1]
        else:
            canonical_name = f"Book_{db_book_num}"

    if canonical_name in BOOK_NAMES:
        canonical_book_number = BOOK_NAMES.index(canonical_name) + 1
    else:
        canonical_book_number = db_book_num

    testament = "old" if canonical_book_number <= 39 else "new"
    return canonical_name, canonical_book_number, testament


def clean_verse(text: str) -> str:
    """Normalize verse text by stripping XML/HTML tags and non-Amharic symbols."""
    if not text:
        return ""
    # Remove page break tags
    t = re.sub(r'<pb\s*/?>', '', text)
    # Remove footnote tags and contents (<f>...</f>)
    t = re.sub(r'<f>.*?</f>', '', t, flags=re.DOTALL)
    # Strip any formatting tags (<J>, </J>, etc.) preserving inner text
    t = re.sub(r'</?[A-Za-z][^>]*>', '', t)
    # Remove non-Ethiopic quotation marks, brackets, and Latin punctuation
    t = re.sub(r'[«»!()[\]]', '', t)
    # Collapse whitespace
    t = re.sub(r'[ \t\r\n]+', ' ', t)
    # Remove space before Ethiopic punctuation marks
    t = re.sub(r'\s+([።፥፣፤፡፦፠፨])', r'\1', t)
    return t.strip()


def write_json_file(data: dict, json_path: str, indent: int = 2):
    """Write a dictionary to a JSON file, creating parent folders if needed."""
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def convert_sqlite_to_json(db_path: str, output_dir: str = "geez", indent: int = 2):
    if not os.path.isfile(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Load books table if available
    books_meta: Dict[int, Tuple[str, str]] = {}
    try:
        cursor.execute("SELECT book_number, short_name, long_name FROM books")
        for b_num, s_name, l_name in cursor.fetchall():
            books_meta[int(b_num)] = (s_name or "", l_name or "")
    except sqlite3.OperationalError:
        pass

    # Fetch verses grouped by book_number, chapter, verse
    cursor.execute("""
        SELECT book_number, chapter, verse, text
        FROM verses
        ORDER BY book_number, chapter, verse
    """)

    current_key = None
    current_verses = {}
    chapter_count = 0
    book_count = set()

    def flush_chapter(key, verses_dict):
        nonlocal chapter_count
        if key is None:
            return
        b_num, ch_num = key
        short_name, long_name = books_meta.get(b_num, ("", ""))
        book_name, book_number, testament = resolve_book(b_num, long_name, short_name)

        data = {
            "testament": testament,
            "book": book_name,
            "book_number": book_number,
            "chapter": ch_num,
            "verses": verses_dict,
        }

        path = os.path.join(output_dir, testament, book_name, f"{ch_num}.json")
        write_json_file(data, path, indent=indent)
        chapter_count += 1
        book_count.add(book_name)

    for b_num, ch_num, v_num, text in cursor:
        b_num = int(b_num)
        ch_num = int(ch_num)
        key = (b_num, ch_num)

        if key != current_key:
            if current_key is not None:
                flush_chapter(current_key, current_verses)
            current_key = key
            current_verses = {}

        current_verses[str(int(v_num))] = clean_verse(text)

    if current_key is not None:
        flush_chapter(current_key, current_verses)

    conn.close()
    print(f"Done: Converted {len(book_count)} books and {chapter_count} chapters to '{output_dir}/'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Geez SQLite Bible database to chapter JSON files.")
    parser.add_argument("input", nargs="?", default="Geez.SQLite3", help="Path to SQLite3 file (default: Geez.SQLite3)")
    parser.add_argument("-o", "--output", default="geez", help="Output directory (default: geez)")
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation level (default: 2)")
    args = parser.parse_args()

    convert_sqlite_to_json(args.input, args.output, indent=args.indent)
