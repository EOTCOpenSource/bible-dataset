#!/usr/bin/env python3
"""
Convert Geez (or MyBible format) SQLite Bible databases to canonical book JSON files,
matching the project's standard structure: data/<translation>/<Book_Name>.json
"""

import argparse
import json
import os
import re
import sqlite3
from typing import Dict, Optional, Tuple, Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

CANONICAL_BOOKS: Dict[int, Dict[str, Any]] = {}
BOOKS_BY_NAME: Dict[str, Dict[str, Any]] = {}


def load_metadata():
    """Load canonical books and apocrypha metadata."""
    global CANONICAL_BOOKS, BOOKS_BY_NAME
    books_json_path = os.path.join(PROJECT_ROOT, "books.json")
    if os.path.isfile(books_json_path):
        with open(books_json_path, "r", encoding="utf-8") as f:
            for item in json.load(f):
                num = item["number"]
                CANONICAL_BOOKS[num] = item
                BOOKS_BY_NAME[item["id"].lower().replace("_", "")] = item
                BOOKS_BY_NAME[item["name"].lower().replace("_", "")] = item

    apoc_json_path = os.path.join(PROJECT_ROOT, "apocrypha_books.json")
    if os.path.isfile(apoc_json_path):
        with open(apoc_json_path, "r", encoding="utf-8") as f:
            for item in json.load(f):
                BOOKS_BY_NAME[item["id"].lower().replace("_", "")] = item
                BOOKS_BY_NAME[item["name"].lower().replace("_", "")] = item


load_metadata()

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
    230: "Psalms",
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

NORMALIZED_BOOK_MAP = {
    name.lower().replace("_", ""): name for name in BOOK_NAMES
}
NORMALIZED_BOOK_MAP.update({
    "psalm": "Psalms",
    "songofsongs": "Song_of_Solomon",
    "canticleofcanticles": "Song_of_Solomon",
})


def resolve_book(db_book_num: int, long_name: Optional[str] = None, short_name: Optional[str] = None) -> Tuple[str, int, str, str]:
    """
    Resolves canonical book name, 1-based canonical book number, USFM code, and testament ("old" or "new").
    """
    canonical_name = None

    if long_name:
        clean_name = long_name.strip().lower().replace(" ", "").replace("_", "")
        if clean_name in BOOKS_BY_NAME:
            meta = BOOKS_BY_NAME[clean_name]
            return meta["id"], meta["number"], meta["usfm"], meta["testament"]
        if clean_name in NORMALIZED_BOOK_MAP:
            canonical_name = NORMALIZED_BOOK_MAP[clean_name]

    if not canonical_name and short_name:
        clean_short = short_name.strip().lower().replace(" ", "").replace("_", "")
        if clean_short in BOOKS_BY_NAME:
            meta = BOOKS_BY_NAME[clean_short]
            return meta["id"], meta["number"], meta["usfm"], meta["testament"]
        if clean_short in NORMALIZED_BOOK_MAP:
            canonical_name = NORMALIZED_BOOK_MAP[clean_short]

    if not canonical_name and db_book_num in MYBIBLE_BOOK_NUMBERS:
        canonical_name = MYBIBLE_BOOK_NUMBERS[db_book_num]

    if not canonical_name:
        if 1 <= db_book_num <= len(BOOK_NAMES):
            canonical_name = BOOK_NAMES[db_book_num - 1]
        else:
            canonical_name = f"Book_{db_book_num}"

    clean_key = canonical_name.lower().replace("_", "")
    if clean_key in BOOKS_BY_NAME:
        meta = BOOKS_BY_NAME[clean_key]
        return meta["id"], meta["number"], meta["usfm"], meta["testament"]

    if canonical_name in BOOK_NAMES:
        num = BOOK_NAMES.index(canonical_name) + 1
        testament = "old" if num <= 39 else "new"
        return canonical_name, num, canonical_name[:3].upper(), testament

    return canonical_name, db_book_num, "UNK", "old"


def clean_verse(text: str) -> str:
    """Normalize verse text by stripping XML/HTML tags and non-Amharic symbols."""
    if not text:
        return ""
    t = re.sub(r'<pb\s*/?>', '', text)
    t = re.sub(r'<f>.*?</f>', '', t, flags=re.DOTALL)
    t = re.sub(r'</?[A-Za-z][^>]*>', '', t)
    t = re.sub(r'[«»!()[\]]', '', t)
    t = re.sub(r'[ \t\r\n]+', ' ', t)
    t = re.sub(r'\s+([።፥፣፤፡፦፠፨])', r'\1', t)
    return t.strip()


def write_json_file(data: dict, json_path: str, indent: int = 2):
    """Write a dictionary to a JSON file, creating parent folders if needed."""
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def convert_sqlite_to_json(db_path: str, translation_id: str = "geez", output_dir: Optional[str] = None, indent: int = 2):
    if not os.path.isfile(db_path):
        raise FileNotFoundError(f"Database file not found: {db_path}")

    if output_dir is None:
        output_dir = os.path.join(PROJECT_ROOT, "data", translation_id)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    books_meta: Dict[int, Tuple[str, str]] = {}
    try:
        cursor.execute("SELECT book_number, short_name, long_name FROM books")
        for b_num, s_name, l_name in cursor.fetchall():
            books_meta[int(b_num)] = (s_name or "", l_name or "")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
        SELECT book_number, chapter, verse, text
        FROM verses
        ORDER BY book_number, chapter, verse
    """)

    # Group verses: book_number -> chapter_number -> {verse_str: text}
    books_data: Dict[int, Dict[int, Dict[str, str]]] = {}

    for b_num, ch_num, v_num, text in cursor:
        b_num = int(b_num)
        ch_num = int(ch_num)
        if b_num not in books_data:
            books_data[b_num] = {}
        if ch_num not in books_data[b_num]:
            books_data[b_num][ch_num] = {}
        books_data[b_num][ch_num][str(int(v_num))] = clean_verse(text)

    conn.close()

    total_books = 0
    total_chapters = 0
    total_verses = 0

    for b_num, chapters_map in books_data.items():
        short_name, long_name = books_meta.get(b_num, ("", ""))
        book_name, book_number, usfm, testament = resolve_book(b_num, long_name, short_name)

        chapters_list = []
        for ch_num in sorted(chapters_map.keys()):
            verses_dict = chapters_map[ch_num]
            chapters_list.append({
                "chapter": ch_num,
                "verses": verses_dict
            })
            total_chapters += 1
            total_verses += len(verses_dict)

        data = {
            "translation": translation_id,
            "book": book_name,
            "book_number": book_number,
            "usfm": usfm,
            "testament": testament,
            "chapters": chapters_list
        }

        path = os.path.join(output_dir, f"{book_name}.json")
        write_json_file(data, path, indent=indent)
        total_books += 1

    print(f"Success: Converted {total_books} books, {total_chapters} chapters, {total_verses} verses to '{output_dir}/'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert Geez / MyBible SQLite database to project standard book JSON files.")
    parser.add_argument("input", nargs="?", default="Geez.SQLite3", help="Path to SQLite3 file (default: Geez.SQLite3)")
    parser.add_argument("-t", "--translation", default="geez", help="Translation ID (default: geez)")
    parser.add_argument("-o", "--output", default=None, help="Output directory (default: data/<translation>)")
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation level (default: 2)")
    args = parser.parse_args()

    convert_sqlite_to_json(args.input, translation_id=args.translation, output_dir=args.output, indent=args.indent)
