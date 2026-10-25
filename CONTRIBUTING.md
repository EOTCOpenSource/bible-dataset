# Contributing to the Bible Data Project

Thank you for your interest in contributing! Our mission is to make Biblical texts—especially Ethiopian, Semitic, Cushitic, and ancient source languages—**developer-friendly, open, standardized, and easily accessible** to software engineers, researchers, and mobile/web app developers worldwide.

Whether you are fixing a typo, digitizing a missing book, adding a new language, or improving documentation, your contributions are warmly welcomed.

---

## 🧭 Ways You Can Contribute

### 1. 🌍 Adding a New Translation or Language
We actively welcome new translations, particularly for Ethiopian, Horn of Africa, and historical languages (e.g., Sidama, Hadiyya, Kambaata, Afar, Silt'e, Gurage, Syriac, Latin Vulgate, etc.).
* Create a new folder under `data/<translation_id>/` (using lowercase ISO 639-3 or established codes, e.g. `data/sidama/`).
* Populate book JSON files following the standard schema below.
* Add your translation's catalog entry to `translations.json`.

### 2. 📜 Digitizing Missing Books
Several Ge'ez Old Testament books currently exist only as scanned manuscript pages (e.g. `Daniel`, `Isaiah`, `Job`, `1 & 2 Chronicles`, `Tobit`, `Judith`, `Ezra`).
* Transcribing these scans from [Dillmann's *Biblia Aethiopica*](https://esubalew.dev/metshaf-qidus/) into clean digital text is one of the highest-impact contributions you can make.

### 3. ✍️ Proofreading & Typo Fixes
* Correcting OCR errors, missing verse numbers, or irregular punctuation in existing translations.
* Please cite the authoritative print edition or manuscript when suggesting corrections.

### 4. 🏷️ Expanding Localized Book Names in `books.json`
* Help populate native localized book names in [`books.json`](file:///home/hena/Downloads/bibleData/books.json) (e.g. Oromo, Tigrinya, Wolaytta, Somali, Dawro, Gamo).

### 5. 💻 Tooling & Libraries
* Building client SDKs and packages (npm package, Python library, Flutter/Dart package).

---

## 📐 Dataset Specifications & Schema

### Folder Organization

```text
├── data/
│   ├── <version>/            # Canonical translations (up to 66 books)
│   │   ├── Genesis.json
│   │   ├── ...
│   │   └── Revelation.json
│   └── apocrypha/            # Dedicated folder for deuterocanonical books
│       ├── am2000/           # 15 narrow canon books
│       └── geez/             # 6 Ge'ez deuterocanonical books
├── metadata/                 # Mirror copies of discovery catalogs
├── books.json                # Canonical 66-book catalog (USFM, chapters, names)
├── apocrypha_books.json      # Catalog of the 15 deuterocanonical books
├── translations.json         # Master list of translations, language codes, & paths
└── README.md
```

### Book JSON Schema

Every book file inside `data/<version>/<Book_Name>.json` must strictly conform to this schema:

```json
{
  "translation": "am2000",
  "book": "John",
  "book_number": 43,
  "usfm": "JHN",
  "testament": "new",
  "chapters": [
    {
      "chapter": 1,
      "verses": {
        "1": "Verse text goes here...",
        "2": "Second verse text..."
      }
    },
    {
      "chapter": 2,
      "verses": {
        "1": "Chapter 2 verse 1..."
      }
    }
  ]
}
```

### Conventions & Rules

1. **Book Naming**:
   * Use canonical PascalCase with underscores for numbered books:
     `Genesis.json`, `1_Samuel.json`, `2_Kings.json`, `Song_of_Solomon.json`, `1_Corinthians.json`.
   * Standard book IDs and USFM codes must match [`books.json`](file:///home/hena/Downloads/bibleData/books.json) (or [`apocrypha_books.json`](file:///home/hena/Downloads/bibleData/apocrypha_books.json)).
2. **Text Normalization**:
   * All files must be encoded in **UTF-8** (without BOM).
   * Unicode text should be normalized (**NFC**).
   * Ensure texts are clean of zero-width spaces (`\u200b`), page breaks, or stray OCR artifacts.
   * For Ethiopic scripts, preserve traditional punctuation (`፡`, `።`, `፤`, `፥`, `፦`) and numerals where appropriate.
3. **Canon Integrity**:
   * Do not mix apocryphal/deuterocanonical books inside the standard `data/<version>/` folder.
   * Place deuterocanonical books exclusively inside `data/apocrypha/<version>/`.

---

## 🛠️ Step-by-Step Contribution Workflow

### Step 1: Fork & Clone
1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```bash
   git clone https://github.com/<your-username>/bibleData.git
   cd bibleData
   ```

### Step 2: Create a Feature Branch
Create a descriptive branch for your work:
```bash
git checkout -b feat/add-sidama-gospel-john
# or
git checkout -b fix/geez-psalms-typo
```

### Step 3: Make Your Changes & Validate
Add or edit the relevant JSON files. You can validate JSON syntax with:
```bash
python3 -m json.tool data/am2000/John.json > /dev/null
```

### Step 4: Update Metadata
If you added a new translation or new books, update:
* [`translations.json`](file:///home/hena/Downloads/bibleData/translations.json)
* [`metadata/translations.json`](file:///home/hena/Downloads/bibleData/metadata/translations.json)

### Step 5: Commit & Submit a Pull Request
1. Commit with a clear, concise message:
   ```bash
   git commit -m "feat(am2000): correct typo in John 3:16"
   ```
2. Push to your fork:
   ```bash
   git push origin feat/add-sidama-gospel-john
   ```
3. Open a **Pull Request** against the `main` branch. In your PR description, please include:
   * What was added or changed.
   * Source / citation for the text (e.g. manuscript, publisher, public domain year).

---

## 🤝 Community & Integrity

* **Source Provenance**: When submitting text, always state the public-domain status, licensing, or source publication to respect copyright and cultural heritage.
* **Accuracy First**: Sacred texts require meticulous attention to spelling, punctuation, and verse numbering.
* **Kindness & Collaboration**: Treat fellow contributors with respect and patience.

Thank you for helping preserve and open these ancient and living texts for developers everywhere!
