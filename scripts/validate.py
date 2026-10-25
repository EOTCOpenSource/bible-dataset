#!/usr/bin/env python3
"""
Bible Data Integrity & Schema Validator

Validates all JSON files in data/ for schema compliance, catalog consistency,
and UTF-8/text cleanliness. Also checks translations.json and books.json.
"""

import argparse
import glob
import json
import os
import re
import sys
from typing import Dict, List, Set, Any, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


class Validator:
    def __init__(self, root_dir: str = PROJECT_ROOT, verbose: bool = False):
        self.root = root_dir
        self.verbose = verbose
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.stats = {
            "translations": 0,
            "book_files": 0,
            "chapters": 0,
            "verses": 0,
        }
        self.books_catalog: Dict[str, Dict[str, Any]] = {}
        self.apocrypha_catalog: Dict[str, Dict[str, Any]] = {}
        self.translations_catalog: List[Dict[str, Any]] = []

    def log_error(self, msg: str):
        self.errors.append(msg)
        if self.verbose:
            print(f"{RED}ERROR:{RESET} {msg}", file=sys.stderr)

    def log_warn(self, msg: str):
        self.warnings.append(msg)
        if self.verbose:
            print(f"{YELLOW}WARN:{RESET} {msg}", file=sys.stderr)

    def load_catalogs(self):
        # 1. Load books.json
        books_file = os.path.join(self.root, "books.json")
        if not os.path.isfile(books_file):
            self.log_error("Master catalog books.json not found in root")
        else:
            with open(books_file, "r", encoding="utf-8") as f:
                books = json.load(f)
                if len(books) != 66:
                    self.log_error(f"books.json should contain 66 books, found {len(books)}")
                for b in books:
                    self.books_catalog[b["id"]] = b

        # 2. Load apocrypha_books.json
        apoc_file = os.path.join(self.root, "apocrypha_books.json")
        if os.path.isfile(apoc_file):
            with open(apoc_file, "r", encoding="utf-8") as f:
                for b in json.load(f):
                    self.apocrypha_catalog[b["id"]] = b

        # 3. Load translations.json
        trans_file = os.path.join(self.root, "translations.json")
        if not os.path.isfile(trans_file):
            self.log_error("Catalog translations.json not found in root")
        else:
            with open(trans_file, "r", encoding="utf-8") as f:
                self.translations_catalog = json.load(f)

    def validate_book_file(self, file_path: str, is_apocrypha: bool = False) -> Tuple[int, int]:
        rel_path = os.path.relpath(file_path, self.root)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            self.log_error(f"Failed to parse JSON in {rel_path}: {e}")
            return 0, 0

        # Required fields
        required_fields = ["translation", "book", "book_number", "usfm", "testament", "chapters"]
        for field in required_fields:
            if field not in data:
                self.log_error(f"{rel_path} missing required field '{field}'")

        expected_book = os.path.splitext(os.path.basename(file_path))[0]
        actual_book = data.get("book")
        if actual_book != expected_book:
            self.log_error(f"{rel_path}: 'book' attribute '{actual_book}' does not match file name '{expected_book}'")

        testament = data.get("testament")
        if testament not in ["old", "new"]:
            self.log_error(f"{rel_path}: invalid testament '{testament}', must be 'old' or 'new'")

        chapters = data.get("chapters")
        if not isinstance(chapters, list):
            self.log_error(f"{rel_path}: 'chapters' must be a list")
            return 0, 0

        if len(chapters) == 0:
            self.log_warn(f"{rel_path}: book has 0 chapters")

        file_verses = 0
        file_chapters = len(chapters)

        for ch in chapters:
            if not isinstance(ch, dict):
                self.log_error(f"{rel_path}: chapter entry is not a JSON object")
                continue
            ch_num = ch.get("chapter")
            if not isinstance(ch_num, int) or ch_num < 1:
                self.log_error(f"{rel_path}: chapter number {ch_num} is invalid")

            verses = ch.get("verses")
            if not isinstance(verses, dict):
                self.log_error(f"{rel_path} chapter {ch_num}: 'verses' must be a dictionary")
                continue

            for v_key, v_text in verses.items():
                if not str(v_key).isdigit():
                    self.log_error(f"{rel_path} chapter {ch_num}: verse key '{v_key}' is not numeric")
                if not isinstance(v_text, str):
                    self.log_error(f"{rel_path} chapter {ch_num} verse {v_key}: text must be a string")
                elif not v_text.strip():
                    self.log_warn(f"{rel_path} chapter {ch_num} verse {v_key}: empty text")
                else:
                    # Check for unstripped XML tags
                    if re.search(r'<(?:pb|f|J)[^>]*>', v_text):
                        self.log_warn(f"{rel_path} chapter {ch_num} verse {v_key}: contains unstripped XML/formatting tag")

                file_verses += 1

        return file_chapters, file_verses

    def validate_data_directory(self) -> Dict[str, Dict[str, int]]:
        data_dir = os.path.join(self.root, "data")
        if not os.path.isdir(data_dir):
            self.log_error("data/ directory not found")
            return {}

        counts_per_translation: Dict[str, Dict[str, int]] = {}

        # 1. Canonical translations
        for item in sorted(os.listdir(data_dir)):
            item_path = os.path.join(data_dir, item)
            if not os.path.isdir(item_path) or item == "apocrypha":
                continue

            trans_id = item
            counts_per_translation[trans_id] = {"books": 0, "chapters": 0, "verses": 0}
            book_files = glob.glob(os.path.join(item_path, "*.json"))

            for bf in book_files:
                ch_cnt, v_cnt = self.validate_book_file(bf, is_apocrypha=False)
                counts_per_translation[trans_id]["books"] += 1
                counts_per_translation[trans_id]["chapters"] += ch_cnt
                counts_per_translation[trans_id]["verses"] += v_cnt
                self.stats["book_files"] += 1
                self.stats["chapters"] += ch_cnt
                self.stats["verses"] += v_cnt

            self.stats["translations"] += 1

        # 2. Apocrypha translations
        apoc_dir = os.path.join(data_dir, "apocrypha")
        if os.path.isdir(apoc_dir):
            for sub in sorted(os.listdir(apoc_dir)):
                sub_path = os.path.join(apoc_dir, sub)
                if not os.path.isdir(sub_path):
                    continue
                for bf in glob.glob(os.path.join(sub_path, "*.json")):
                    ch_cnt, v_cnt = self.validate_book_file(bf, is_apocrypha=True)
                    self.stats["book_files"] += 1
                    self.stats["chapters"] += ch_cnt
                    self.stats["verses"] += v_cnt

        return counts_per_translation

    def validate_and_sync_translations_catalog(self, counts: Dict[str, Dict[str, int]], fix_stats: bool = False):
        trans_file = os.path.join(self.root, "translations.json")
        meta_trans_file = os.path.join(self.root, "metadata", "translations.json")

        if not os.path.isfile(trans_file):
            return

        with open(trans_file, "r", encoding="utf-8") as f:
            translations = json.load(f)

        updated = False
        for entry in translations:
            t_id = entry.get("id")
            if t_id not in counts:
                self.log_error(f"Translation '{t_id}' declared in translations.json does not exist in data/")
                continue

            actual = counts[t_id]
            decl_books = entry.get("books_count")
            decl_chapters = entry.get("chapters_count")
            decl_verses = entry.get("verses_count")

            if (decl_books, decl_chapters, decl_verses) != (actual["books"], actual["chapters"], actual["verses"]):
                msg = f"Counts mismatch for '{t_id}': declared ({decl_books}b, {decl_chapters}ch, {decl_verses}v) vs actual ({actual['books']}b, {actual['chapters']}ch, {actual['verses']}v)"
                if fix_stats:
                    entry["books_count"] = actual["books"]
                    entry["chapters_count"] = actual["chapters"]
                    entry["verses_count"] = actual["verses"]
                    updated = True
                    self.log_warn(f"{msg} -> Fixed automatically")
                else:
                    self.log_error(f"{msg} (run with --fix-stats to synchronize)")

            # Check declared books list matches files on disk
            t_path = os.path.join(self.root, "data", t_id)
            disk_books = sorted([os.path.splitext(f)[0] for f in os.listdir(t_path) if f.endswith(".json")])
            decl_books_list = entry.get("books", [])
            if set(disk_books) != set(decl_books_list):
                diff = set(disk_books) ^ set(decl_books_list)
                self.log_error(f"Declared books list mismatch in translations.json for '{t_id}': {diff}")

        if fix_stats and updated:
            with open(trans_file, "w", encoding="utf-8") as f:
                json.dump(translations, f, indent=2, ensure_ascii=False)
            if os.path.isfile(meta_trans_file):
                with open(meta_trans_file, "w", encoding="utf-8") as f:
                    json.dump(translations, f, indent=2, ensure_ascii=False)
            print(f"{GREEN}✓ Successfully synchronized translations.json and metadata/translations.json{RESET}")

    def run(self, fix_stats: bool = False) -> int:
        print(f"{BOLD}{CYAN}=== BibleData Schema & Dataset Integrity Validator ==={RESET}\n")
        self.load_catalogs()
        counts = self.validate_data_directory()
        self.validate_and_sync_translations_catalog(counts, fix_stats=fix_stats)

        print(f"{BOLD}Summary:{RESET}")
        print(f"  • Translations checked: {self.stats['translations']}")
        print(f"  • Book JSON files:      {self.stats['book_files']}")
        print(f"  • Total chapters:       {self.stats['chapters']:,}")
        print(f"  • Total verses:         {self.stats['verses']:,}")
        print()

        if self.warnings:
            print(f"{YELLOW}Warnings: {len(self.warnings)}{RESET}")
            if not self.verbose and len(self.warnings) > 5:
                print(f"  (Run with --verbose to view all {len(self.warnings)} warnings)")
            elif not self.verbose:
                for w in self.warnings:
                    print(f"  • {w}")

        if self.errors:
            print(f"{RED}{BOLD}Validation Failed: {len(self.errors)} errors detected.{RESET}")
            for err in self.errors[:15]:
                print(f"  {RED}✗{RESET} {err}")
            if len(self.errors) > 15:
                print(f"  ... and {len(self.errors) - 15} more errors.")
            return 1

        print(f"{GREEN}{BOLD}✓ All checks passed! Dataset schema and catalogs are 100% valid.{RESET}\n")
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate BibleData JSON files and metadata catalogs.")
    parser.add_argument("--fix-stats", action="store_true", help="Synchronize books/chapters/verses counts in translations.json")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print detailed validation logs")
    args = parser.parse_args()

    validator = Validator(verbose=args.verbose)
    exit_code = validator.run(fix_stats=args.fix_stats)
    sys.exit(exit_code)
