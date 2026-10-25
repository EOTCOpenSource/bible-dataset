#!/usr/bin/env python3
"""
BibleData SQLite Builder & Exporter

Converts project-standard JSON Bible translations (canonical and deuterocanonical)
into production-ready SQLite database files equipped with Full-Text Search (FTS5)
and optimized B-Tree indexes.

Usage:
    # Build a SQLite database for a single translation
    python3 scripts/convert_sqlite.py am2000

    # Build SQLite databases for multiple translations
    python3 scripts/convert_sqlite.py am2000 geez tigrinya1997

    # Build a single combined SQLite database containing multiple translations
    python3 scripts/convert_sqlite.py am2000 geez -o bibles.db --combined

    # Build SQLite databases for all available translations
    python3 scripts/convert_sqlite.py all

    # Reverse mode: Import an existing SQLite database into JSON files
    python3 scripts/convert_sqlite.py --import-sqlite input.sqlite3 -t geez
"""

import argparse
import glob
import json
import os
import re
import sqlite3
import sys
import time
from typing import Dict, List, Optional, Tuple, Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Colors for terminal output
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"


def load_catalogs():
    """Load metadata catalogs."""
    trans_map = {}
    trans_path = os.path.join(PROJECT_ROOT, "translations.json")
    if os.path.isfile(trans_path):
        with open(trans_path, "r", encoding="utf-8") as f:
            for item in json.load(f):
                trans_map[item["id"]] = item

    books_map = {}
    books_path = os.path.join(PROJECT_ROOT, "books.json")
    if os.path.isfile(books_path):
        with open(books_path, "r", encoding="utf-8") as f:
            for item in json.load(f):
                books_map[item["id"]] = item

    apoc_map = {}
    apoc_path = os.path.join(PROJECT_ROOT, "apocrypha_books.json")
    if os.path.isfile(apoc_path):
        with open(apoc_path, "r", encoding="utf-8") as f:
            for item in json.load(f):
                apoc_map[item["id"]] = item

    return trans_map, books_map, apoc_map


def init_database_schema(conn: sqlite3.Connection, enable_fts: bool = True):
    """Initializes tables, indexes, and full-text search virtual tables."""
    cur = conn.cursor()

    cur.execute("PRAGMA journal_mode = MEMORY;")
    cur.execute("PRAGMA synchronous = OFF;")

    # 1. Metadata table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)

    # 2. Translations table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS translations (
            id TEXT PRIMARY KEY,
            name TEXT,
            native_name TEXT,
            language_code TEXT,
            language_name TEXT,
            direction TEXT,
            script TEXT,
            testaments TEXT
        );
    """)

    # 3. Books table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS books (
            translation_id TEXT,
            book_name TEXT,
            book_number INTEGER,
            usfm TEXT,
            testament TEXT,
            chapters_count INTEGER,
            verses_count INTEGER,
            is_apocrypha INTEGER DEFAULT 0,
            PRIMARY KEY (translation_id, book_name)
        );
    """)

    # 4. Verses table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS verses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            translation_id TEXT NOT NULL,
            book_name TEXT NOT NULL,
            book_number INTEGER NOT NULL,
            usfm TEXT NOT NULL,
            testament TEXT NOT NULL,
            chapter INTEGER NOT NULL,
            verse INTEGER NOT NULL,
            text TEXT NOT NULL,
            is_apocrypha INTEGER DEFAULT 0
        );
    """)

    # Indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_verses_lookup ON verses(translation_id, book_name, chapter, verse);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_verses_usfm ON verses(translation_id, usfm, chapter, verse);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_verses_book ON verses(translation_id, book_number, chapter);")

    # 5. FTS5 Virtual Table (Full-Text Search)
    if enable_fts:
        cur.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS verses_fts USING fts5(
                text,
                content='verses',
                content_rowid='id',
                tokenize='unicode61'
            );
        """)
        cur.execute("""
            CREATE TRIGGER IF NOT EXISTS verses_ai AFTER INSERT ON verses BEGIN
                INSERT INTO verses_fts(rowid, text) VALUES (new.id, new.text);
            END;
        """)

    conn.commit()


def populate_translation(conn: sqlite3.Connection, trans_id: str, trans_meta: Dict[str, Any], include_apocrypha: bool = True) -> Tuple[int, int, int]:
    """Reads JSON files for a translation and inserts into SQLite tables."""
    cur = conn.cursor()

    # Insert into translations table
    testaments_str = ",".join(trans_meta.get("testaments", [])) if isinstance(trans_meta.get("testaments"), list) else str(trans_meta.get("testaments", ""))
    cur.execute("""
        INSERT OR REPLACE INTO translations 
        (id, name, native_name, language_code, language_name, direction, script, testaments)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        trans_id,
        trans_meta.get("name", trans_id),
        trans_meta.get("native_name", ""),
        trans_meta.get("language_code", ""),
        trans_meta.get("language_name", ""),
        trans_meta.get("direction", "ltr"),
        trans_meta.get("script", ""),
        testaments_str
    ))

    # Collect files
    file_queue: List[Tuple[str, int]] = []

    # Canonical files
    canonical_dir = os.path.join(PROJECT_ROOT, "data", trans_id)
    if os.path.isdir(canonical_dir):
        for bf in sorted(glob.glob(os.path.join(canonical_dir, "*.json"))):
            file_queue.append((bf, 0))

    # Apocrypha files
    if include_apocrypha:
        apoc_dir = os.path.join(PROJECT_ROOT, "data", "apocrypha", trans_id)
        if os.path.isdir(apoc_dir):
            for bf in sorted(glob.glob(os.path.join(apoc_dir, "*.json"))):
                file_queue.append((bf, 1))

    total_books = 0
    total_chapters = 0
    total_verses = 0

    verses_batch = []

    for file_path, is_apoc in file_queue:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"{YELLOW}Warning: skipping {file_path} due to error: {e}{RESET}")
            continue

        book_name = data.get("book", os.path.splitext(os.path.basename(file_path))[0])
        book_number = data.get("book_number", 0)
        usfm = data.get("usfm", "")
        testament = data.get("testament", "")
        chapters = data.get("chapters", [])

        book_verses_count = 0
        for ch_obj in chapters:
            ch_num = ch_obj.get("chapter", 0)
            verses_dict = ch_obj.get("verses", {})
            for v_str, text in verses_dict.items():
                v_num = int(v_str) if str(v_str).isdigit() else 0
                verses_batch.append((
                    trans_id, book_name, book_number, usfm, testament, ch_num, v_num, text, is_apoc
                ))
                book_verses_count += 1

        cur.execute("""
            INSERT OR REPLACE INTO books
            (translation_id, book_name, book_number, usfm, testament, chapters_count, verses_count, is_apocrypha)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trans_id, book_name, book_number, usfm, testament, len(chapters), book_verses_count, is_apoc
        ))

        total_books += 1
        total_chapters += len(chapters)
        total_verses += book_verses_count

    # Bulk insert verses
    if verses_batch:
        cur.executemany("""
            INSERT INTO verses 
            (translation_id, book_name, book_number, usfm, testament, chapter, verse, text, is_apocrypha)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, verses_batch)

    conn.commit()
    return total_books, total_chapters, total_verses


def build_sqlite_db(
    translation_ids: List[str],
    output_target: Optional[str] = None,
    combined: bool = False,
    enable_fts: bool = True,
    include_apocrypha: bool = True
):
    """Builds SQLite database(s) for specified translation IDs."""
    trans_map, _, _ = load_catalogs()

    available_ids = set()
    data_dir = os.path.join(PROJECT_ROOT, "data")
    if os.path.isdir(data_dir):
        for name in os.listdir(data_dir):
            if os.path.isdir(os.path.join(data_dir, name)) and name != "apocrypha":
                available_ids.add(name)

    # Handle 'all' keyword
    if "all" in [t.lower() for t in translation_ids]:
        target_ids = sorted(list(available_ids))
    else:
        target_ids = []
        for t in translation_ids:
            clean_t = t.strip()
            if clean_t in available_ids:
                target_ids.append(clean_t)
            else:
                print(f"{YELLOW}Warning: Translation '{clean_t}' not found in data/. Available: {sorted(list(available_ids))}{RESET}")

    if not target_ids:
        print(f"No valid translations specified to build. Available: {sorted(list(available_ids))}")
        return

    # Determine whether combined or separate
    is_combined = combined or (output_target and (output_target.endswith(".db") or output_target.endswith(".sqlite") or output_target.endswith(".sqlite3")))

    if is_combined:
        db_path = output_target if output_target else os.path.join(PROJECT_ROOT, "dist", "bible.db")
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        if os.path.exists(db_path):
            os.remove(db_path)

        print(f"{BOLD}{CYAN}Building combined SQLite database:{RESET} {db_path}")
        start_t = time.time()
        conn = sqlite3.connect(db_path)
        init_database_schema(conn, enable_fts=enable_fts)

        # Set metadata
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('schema_version', '1.0');")
        cur.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('created_at', datetime('now'));")
        cur.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('translations', ?);", (",".join(target_ids),))

        tot_books = 0
        tot_chapters = 0
        tot_verses = 0

        for t_id in target_ids:
            meta = trans_map.get(t_id, {"id": t_id, "name": t_id})
            b_cnt, c_cnt, v_cnt = populate_translation(conn, t_id, meta, include_apocrypha=include_apocrypha)
            tot_books += b_cnt
            tot_chapters += c_cnt
            tot_verses += v_cnt
            print(f"  {GREEN}✓{RESET} {t_id:15} -> {b_cnt:2} books, {c_cnt:4} chapters, {v_cnt:6,} verses")

        cur.execute("PRAGMA optimize;")
        conn.close()
        elapsed = time.time() - start_t
        file_size_mb = os.path.getsize(db_path) / (1024 * 1024)
        print(f"{GREEN}{BOLD}Done!{RESET} Created {db_path} ({file_size_mb:.2f} MB) in {elapsed:.2f}s [Total: {tot_books} books, {tot_verses:,} verses]\n")

    else:
        out_dir = output_target if output_target else os.path.join(PROJECT_ROOT, "dist")
        os.makedirs(out_dir, exist_ok=True)
        print(f"{BOLD}{CYAN}Building separate SQLite databases in:{RESET} {out_dir}/")

        for t_id in target_ids:
            db_path = os.path.join(out_dir, f"{t_id}.db")
            if os.path.exists(db_path):
                os.remove(db_path)

            start_t = time.time()
            conn = sqlite3.connect(db_path)
            init_database_schema(conn, enable_fts=enable_fts)

            cur = conn.cursor()
            cur.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('schema_version', '1.0');")
            cur.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('created_at', datetime('now'));")
            cur.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('translation_id', ?);", (t_id,))

            meta = trans_map.get(t_id, {"id": t_id, "name": t_id})
            b_cnt, c_cnt, v_cnt = populate_translation(conn, t_id, meta, include_apocrypha=include_apocrypha)

            cur.execute("PRAGMA optimize;")
            conn.close()
            elapsed = time.time() - start_t
            file_size_mb = os.path.getsize(db_path) / (1024 * 1024)
            print(f"  {GREEN}✓{RESET} {t_id:15} -> {db_path} ({file_size_mb:.2f} MB, {b_cnt} books, {v_cnt:,} verses in {elapsed:.2f}s)")


# Backward-compatible import mode: SQLite -> JSON
def import_from_sqlite(db_path: str, translation_id: str, output_dir: Optional[str] = None):
    """Imports an existing MyBible or Geez SQLite database into standard JSON files."""
    from scripts.convert import resolve_book_meta, write_json_file
    if not os.path.isfile(db_path):
        print(f"Error: Database file not found: {db_path}", file=sys.stderr)
        return

    if output_dir is None:
        output_dir = os.path.join(PROJECT_ROOT, "data", translation_id)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    books_meta = {}
    try:
        cur.execute("SELECT book_number, short_name, long_name FROM books")
        for b_num, s_name, l_name in cur.fetchall():
            books_meta[int(b_num)] = (s_name or "", l_name or "")
    except sqlite3.OperationalError:
        pass

    cur.execute("SELECT book_number, chapter, verse, text FROM verses ORDER BY book_number, chapter, verse")
    books_data = {}
    for b_num, ch_num, v_num, text in cur:
        b_num, ch_num = int(b_num), int(ch_num)
        if b_num not in books_data:
            books_data[b_num] = {}
        if ch_num not in books_data[b_num]:
            books_data[b_num][ch_num] = {}
        clean_txt = re.sub(r'</?[A-Za-z][^>]*>', '', str(text or "")).strip()
        books_data[b_num][ch_num][str(int(v_num))] = clean_txt

    conn.close()

    total_books = 0
    for b_num, chapters_map in books_data.items():
        s_name, l_name = books_meta.get(b_num, ("", ""))
        book_name, canonical_num, usfm, testament = resolve_book_meta(b_num, l_name or s_name)

        chapters_list = []
        for ch_num in sorted(chapters_map.keys()):
            chapters_list.append({"chapter": ch_num, "verses": chapters_map[ch_num]})

        doc = {
            "translation": translation_id,
            "book": book_name,
            "book_number": canonical_num,
            "usfm": usfm,
            "testament": testament,
            "chapters": chapters_list
        }
        write_json_file(doc, os.path.join(output_dir, f"{book_name}.json"))
        total_books += 1

    print(f"Imported {total_books} books to '{output_dir}/'")


def main():
    parser = argparse.ArgumentParser(
        description="Build high-performance SQLite database(s) from BibleData JSON files, or import SQLite into JSON."
    )
    parser.add_argument(
        "translations",
        nargs="*",
        default=["am2000"],
        help="List of translation IDs to export (e.g. am2000 geez tigrinya1997 or 'all'). Default: am2000"
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output file path (e.g. dist/my_bible.db) or output directory (default: dist/)"
    )
    parser.add_argument(
        "--combined",
        action="store_true",
        help="Combine all selected translations into a single SQLite database"
    )
    parser.add_argument(
        "--no-fts",
        action="store_true",
        help="Disable SQLite FTS5 (Full-Text Search) virtual table"
    )
    parser.add_argument(
        "--no-apocrypha",
        action="store_true",
        help="Exclude deuterocanonical / apocryphal books"
    )
    parser.add_argument(
        "--import-sqlite",
        default=None,
        help="Import mode: Path to SQLite database file to convert into JSON files"
    )
    parser.add_argument(
        "-t", "--translation",
        default="geez",
        help="Translation ID used when importing SQLite into JSON (default: geez)"
    )

    args = parser.parse_args()

    if args.import_sqlite:
        import_from_sqlite(args.import_sqlite, translation_id=args.translation, output_dir=args.output)
    else:
        build_sqlite_db(
            translation_ids=args.translations,
            output_target=args.output,
            combined=args.combined,
            enable_fts=not args.no_fts,
            include_apocrypha=not args.no_apocrypha
        )


if __name__ == "__main__":
    main()
