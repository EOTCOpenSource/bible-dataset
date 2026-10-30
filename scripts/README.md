# BibleData Engineering Scripts & Tooling

This directory contains command-line utilities for data ingestion, format conversion, SQLite database compilation, Ge'ez text normalization, and dataset validation.

---

## 🛠️ Tooling Overview

| Script | Purpose |
| :--- | :--- |
| [`convert_sqlite.py`](convert_sqlite.py) | **Builds high-performance SQLite databases** (with FTS5 Full-Text Search) from JSON files, or imports SQLite modules into JSON. |
| [`convert.py`](convert.py) | Splits and transforms monolithic XML Bible files into project-standard `data/<translation>/<Book>.json` files. |
| [`validate.py`](validate.py) | Comprehensive dataset validator for JSON schema compliance, catalog consistency, and chapter/verse statistics. |
| [`normalize_geez.py`](normalize_geez.py) | Cleans Ge'ez texts by stripping stray OCR tags (`<pb/>`, `<f>`), irregular punctuation, and non-Ethiopic formatting artifacts. |
| [`convert_weahadu.py`](convert_weahadu.py) | Exports the dataset into the 80-weahadu JSON layout (`<edition>/meta.json` + `<edition>/books/NN-slug.json`). |

---

## 🔁 `convert_weahadu.py`: Export to the 80-weahadu Layout

Writes every translation (or the ones you pick) into the same JSON shape used by the 80-weahadu project, so both datasets can be read by the same code. It only reads this repository's files; source files are never changed.

```bash
python scripts/convert_weahadu.py                    # all translations -> dist/weahadu/
python scripts/convert_weahadu.py -t am2000 geez     # selected translations
python scripts/convert_weahadu.py -o out --indent 0  # custom folder, compact JSON
```

Output:

```
dist/weahadu/
  canon.json                  book registry (id, order, slug, file)
  editions.json               index of exported editions
  am-2000/meta.json           edition metadata + book list with stats
  am-2000/books/01-genesis.json
```

Book file shape (verses are an array; `n` is an integer):

```json
{
  "edition": "am-2000", "book": "GEN", "usfm_id": "GEN", "order": 1,
  "chapters": [{ "n": 1, "verses": [{ "n": 1, "t": "...", "alt": "፩" }] }]
}
```

Notes:
- Filenames use a fixed canon slot, so `01-genesis.json` is Genesis in every edition. The New Testament starts at slot 59 (`59-matthew.json`), leaving 40–58 for the deuterocanonical books.
- The Ethiopic 1–2 Maccabees and 1–2 Esdras are different works from the Greek ones, so they keep EOTC names (`51-ezra-sutuel.json`, `54-ezra-kalie.json`). `TEG` (Book of Admonition) is written as `4MA`, matching the EOTC slot. `4BA` (Rest of Baruch) gets a new slot, `100-rest-of-baruch.json`.
- `alt` (the Ge'ez numeral of the verse number) is added for Amharic, Ge'ez and Tigrinya editions.
- Optional fields from the 80-weahadu format (`headings`, `refs`, `notes`, `lines`) are not produced because the source XML does not contain that data.

---

## 📦 `convert_sqlite.py`: SQLite Database Builder

`convert_sqlite.py` converts the JSON dataset into production-ready SQLite databases. It automatically indexes canonical books, includes deuterocanonical/apocrypha collections, builds B-tree indexes for instant verse retrieval, and configures **SQLite FTS5 (Full-Text Search)**.

### 🚀 Usage Examples

#### 1. Single Translation
Build a standalone SQLite database for one translation (outputs `dist/<translation_id>.db`):
```bash
python3 scripts/convert_sqlite.py am2000
# Output: dist/am2000.db (includes canonical books + 15 apocrypha books)
```

#### 2. Multiple Translations (Separate Databases)
Build individual SQLite databases for multiple translations simultaneously:
```bash
python3 scripts/convert_sqlite.py am2000 geez tigrinya1997 oromiffa
# Outputs: dist/am2000.db, dist/geez.db, dist/tigrinya1997.db, dist/oromiffa.db
```

#### 3. Combined Database (Multiple Translations in One File)
Combine multiple translations into a single SQLite file (useful for multi-language or parallel Bible apps):
```bash
python3 scripts/convert_sqlite.py am2000 geez greekOriginal hebrewBible --combined -o dist/multilingual.db
```

#### 4. Export All Available Translations
Build SQLite databases for all 13 translations in one run:
```bash
python3 scripts/convert_sqlite.py all
```

#### 5. Custom Options
```bash
# Specify custom output path
python3 scripts/convert_sqlite.py am2000 -o /path/to/my_bible.sqlite

# Exclude deuterocanonical / apocrypha books
python3 scripts/convert_sqlite.py am2000 --no-apocrypha

# Disable FTS5 full-text search table (reduces database file size)
python3 scripts/convert_sqlite.py am2000 --no-fts

# Reverse mode: Import an existing SQLite database into standard JSON files
python3 scripts/convert_sqlite.py --import-sqlite path/to/external.db -t geez
```

---

## 🗄️ SQLite Database Schema

When compiled, the SQLite database exposes the following optimized schema:

### 1. `translations`
Metadata describing each translation included in the database:
```sql
CREATE TABLE translations (
    id TEXT PRIMARY KEY,             -- e.g. 'am2000'
    name TEXT,                       -- English display name
    native_name TEXT,                -- Localized name (e.g. 'የ2000 ዓ.ም. የአማርኛ መጽሐፍ ቅዱስ')
    language_code TEXT,              -- ISO 639-3 code (e.g. 'amh')
    language_name TEXT,              -- 'Amharic'
    direction TEXT,                  -- 'ltr' or 'rtl'
    script TEXT,                     -- 'Ethiopic', 'Latin', 'Greek', 'Hebrew', etc.
    testaments TEXT                  -- 'old,new' or 'new'
);
```

### 2. `books`
Canonical catalog and chapter/verse statistics per translation:
```sql
CREATE TABLE books (
    translation_id TEXT,             -- e.g. 'am2000'
    book_name TEXT,                  -- e.g. 'Genesis', 'John', 'Enoch'
    book_number INTEGER,             -- 1-66 (or >66 for apocrypha)
    usfm TEXT,                       -- Standard 3-letter code (e.g. 'JHN', 'ENO')
    testament TEXT,                  -- 'old' or 'new'
    chapters_count INTEGER,
    verses_count INTEGER,
    is_apocrypha INTEGER DEFAULT 0,  -- 0 for canonical, 1 for deuterocanonical
    PRIMARY KEY (translation_id, book_name)
);
```

### 3. `verses`
Individual verse texts with fast B-Tree lookup indexes:
```sql
CREATE TABLE verses (
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

-- Fast lookup indexes
CREATE INDEX idx_verses_lookup ON verses(translation_id, book_name, chapter, verse);
CREATE INDEX idx_verses_usfm ON verses(translation_id, usfm, chapter, verse);
CREATE INDEX idx_verses_book ON verses(translation_id, book_number, chapter);
```

### 4. `verses_fts` (FTS5 Full-Text Search)
A virtual table enabling sub-millisecond keyword searches across all languages and scripts:
```sql
CREATE VIRTUAL TABLE verses_fts USING fts5(
    text,
    content='verses',
    content_rowid='id',
    tokenize='unicode61'
);
```

---

## 🔍 SQL Query Cheat-Sheet

### Query a Specific Verse (e.g. John 1:1)
```sql
SELECT text 
FROM verses 
WHERE translation_id = 'am2000' 
  AND book_name = 'John' 
  AND chapter = 1 
  AND verse = 1;
```

### Query Parallel Verses Across Multiple Translations
```sql
SELECT translation_id, text 
FROM verses 
WHERE book_name = 'John' 
  AND chapter = 1 
  AND verse = 1 
ORDER BY translation_id;
```

### Sub-Millisecond Full-Text Search (FTS5)
Search for a keyword and generate highlighted snippets:
```sql
SELECT v.book_name, v.chapter, v.verse, snippet(verses_fts, 0, '<b>', '</b>', '...', 10) AS preview
FROM verses v
JOIN verses_fts f ON v.id = f.rowid
WHERE v.translation_id = 'am2000' 
  AND verses_fts MATCH 'ብርሃን'
LIMIT 10;
```

---

## 🧪 `validate.py`: Dataset Validator

Run this script before committing any changes to ensure JSON schema compliance and catalog integrity:

```bash
# Run full dataset validation
python3 scripts/validate.py

# Run in verbose mode to view detailed warnings
python3 scripts/validate.py -v

# Automatically recalculate and sync translations.json verse/chapter counts
python3 scripts/validate.py --fix-stats
```

---

## 🔄 `convert.py`: Monolithic XML to Book JSON

Convert a downloaded XML Bible (such as Zefania or OpenSong XML) into the standard book-level schema:

```bash
python3 scripts/convert.py path/to/bible.xml -t am2000 -o data/am2000/
```
