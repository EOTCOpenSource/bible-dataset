#!/usr/bin/env python3
"""
Convert Bible XML files (such as Zefania / OpenSong / OSIS / custom XML) into
canonical book JSON files conforming to the BibleData schema:
data/<translation>/<Book_Name>.json
"""

import argparse
import json
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional

# Load canonical metadata if available
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

CANONICAL_BOOKS: Dict[int, Dict[str, Any]] = {}
BOOKS_BY_NAME: Dict[str, Dict[str, Any]] = {}


def load_metadata():
    """Load canonical books metadata from books.json."""
    global CANONICAL_BOOKS, BOOKS_BY_NAME
    books_json_path = os.path.join(PROJECT_ROOT, "books.json")
    if os.path.isfile(books_json_path):
        with open(books_json_path, "r", encoding="utf-8") as f:
            for item in json.load(f):
                num = item["number"]
                CANONICAL_BOOKS[num] = item
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


def resolve_book_meta(book_number: int, book_name_hint: Optional[str] = None):
    """Resolve book name, USFM code, book number, and testament."""
    if book_number in CANONICAL_BOOKS:
        meta = CANONICAL_BOOKS[book_number]
        return meta["id"], meta["number"], meta["usfm"], meta["testament"]

    if book_name_hint:
        clean = book_name_hint.lower().replace(" ", "").replace("_", "")
        if clean in BOOKS_BY_NAME:
            meta = BOOKS_BY_NAME[clean]
            return meta["id"], meta["number"], meta["usfm"], meta["testament"]

    # Fallback to index
    if 1 <= book_number <= len(BOOK_NAMES):
        canonical_name = BOOK_NAMES[book_number - 1]
        testament = "old" if book_number <= 39 else "new"
        return canonical_name, book_number, canonical_name[:3].upper(), testament

    return f"Book_{book_number}", book_number, "UNK", "old"


def write_json_file(data: dict, json_path: str, indent: int = 2):
    """Write a dictionary to a JSON file, creating parent folders if needed."""
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def load_xml_root(source: str):
    """Load XML root element from a URL or local file path."""
    if source.startswith(("http://", "https://")):
        if "github.com" in source and "/blob/" in source:
            source = source.replace("github.com", "raw.githubusercontent.com", 1)
            source = source.replace("/blob/", "/", 1)
        print(f"Downloading {source} ...")
        req = urllib.request.Request(source, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            return ET.fromstring(resp.read())
    return ET.parse(source).getroot()


def convert_xml_to_json(source: str, translation_id: str, output_dir: Optional[str] = None, indent: int = 2):
    """
    Convert an XML Bible to project-standard book JSON files.
    Output: <output_dir>/<Book_Name>.json
    """
    if output_dir is None:
        output_dir = os.path.join(PROJECT_ROOT, "data", translation_id)

    root = load_xml_root(source)
    books_written = 0
    total_chapters = 0
    total_verses = 0

    for testament in root.findall("testament"):
        testament_hint = (testament.get("name") or "old").lower()

        for book in testament.findall("book"):
            b_num_attr = book.get("number")
            book_number = int(b_num_attr) if b_num_attr else (books_written + 1)
            b_name_hint = book.get("name") or book.get("id")

            book_name, book_number, usfm, testament_name = resolve_book_meta(book_number, b_name_hint)

            chapters_list = []
            for chapter in book.findall("chapter"):
                ch_num_attr = chapter.get("number")
                chapter_number = int(ch_num_attr) if ch_num_attr else (len(chapters_list) + 1)

                verses_dict = {}
                for verse in chapter.findall("verse"):
                    v_num = str(verse.get("number", len(verses_dict) + 1))
                    text = (verse.text or "").strip()
                    verses_dict[v_num] = text
                    total_verses += 1

                chapters_list.append({
                    "chapter": chapter_number,
                    "verses": verses_dict
                })
                total_chapters += 1

            book_data = {
                "translation": translation_id,
                "book": book_name,
                "book_number": book_number,
                "usfm": usfm,
                "testament": testament_name or testament_hint,
                "chapters": chapters_list
            }

            file_path = os.path.join(output_dir, f"{book_name}.json")
            write_json_file(book_data, file_path, indent=indent)
            books_written += 1

    print(f"Success: Wrote {books_written} books, {total_chapters} chapters, {total_verses} verses to '{output_dir}/'")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert a Bible XML file into project standard book JSON files.")
    parser.add_argument("input", help="URL or local path to Bible XML file")
    parser.add_argument("-t", "--translation", required=True, help="Translation ID (e.g. am2000, sidama)")
    parser.add_argument("-o", "--output", default=None, help="Output folder (default: data/<translation>)")
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation level (default: 2)")
    args = parser.parse_args()

    convert_xml_to_json(args.input, args.translation, output_dir=args.output, indent=args.indent)
