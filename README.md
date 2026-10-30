# Bible Data API & Dataset

A developer-friendly, multi-language Bible dataset featuring 13 translations (Semitic, Cushitic, Omotic, Greek, Coptic), standard metadata, clean book-level JSON files, and a dedicated deuterocanonical/apocrypha collection bundled cleanly into `data/`.

---

## 🚀 Dataset Structure

All translation and apocrypha datasets are bundled inside the [`data/`](data/) directory.

### 1. Canonical Translations: `data/<version>/<book>.json`
Every translation folder strictly contains only canonical books (up to the standard 66 books). Each book is a single JSON file where **`chapters` is an array of objects**:

```text
data/<version>/<book>.json
```

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
        "1": "በመጀመሪያ ቃል ነበረ፤ ቃልም በእግዚአብሔር ዘንድ ነበረ፤ ቃልም እግዚአብሔር ነበረ።",
        "2": "ይህም በመጀመሪያ በእግዚአብሔር ዘንድ ነበረ።"
      }
    }
  ]
}
```

### 2. Apocrypha & Deuterocanonical: `data/apocrypha/<version>/<book>.json`
The 15 additional deuterocanonical / narrow canon books are kept in a separate, dedicated folder so the standard 66-canon structure remains untouched:

```text
data/
├── apocrypha/
│   ├── am2000/   # 15 books (Jubilees, Enoch, 1-3 Maccabees, Tobit, Judith, Sirach, Wisdom, etc.)
│   └── geez/     # 6 digitized text books (Jubilees, Enoch, Sirach, Wisdom, Baruch, 4 Baruch)
├── am1954/
├── am2000/
├── geez/
└── ...
```

---

## 📖 Discovery Catalogs (Metadata)

| File | Purpose |
| :--- | :--- |
| [`translations.json`](translations.json) | Catalog of all 13 versions with language codes, native names, direction (`ltr`/`rtl`), canonical book counts, and apocrypha paths. |
| [`books.json`](books.json) | Master list of the 66 canonical books with standard USFM 3-letter codes (`GEN`, `JHN`), book order (1–66), chapter counts, and Amharic names. |
| [`apocrypha_books.json`](apocrypha_books.json) | Catalog of the 15 deuterocanonical/apocryphal books with USFM codes (`JUB`, `ENO`, `TOB`, etc.), Amharic names, and chapter counts. |

### Available Translations

| Version ID | Language | Native Name | Direction | Script | Testaments | Canonical Books | Apocrypha Books |
| :--- | :--- | :--- | :---: | :--- | :---: | :---: | :---: |
| [**`am1954`**](data/am1954/) | Amharic (`amh`) | የአፄ ኃይለ ሥላሴ 1954 መጽሐፍ ቅዱስ | LTR | Ethiopic | OT, NT | 66 | — |
| [**`am2000`**](data/am2000/) | Amharic (`amh`) | የ2000 ዓ.ም. የአማርኛ መጽሐፍ ቅዱስ | LTR | Ethiopic | OT, NT | 66 | 15 in [`data/apocrypha/am2000/`](data/apocrypha/am2000) |
| [**`coptic`**](data/coptic/) | Coptic (`cop`) | Ϯⲇⲓⲁⲑⲏⲕⲏ ⲛ̀ⲃⲉⲣⲓ | LTR | Coptic | NT | 27 | — |
| [**`dawro`**](data/dawro/) | Dawro (`dwr`) | ዳውሮ ቃላ | LTR | Ethiopic | NT | 27 | — |
| [**`gamo`**](data/gamo/) | Gamo (`gmv`) | ጋሞ ቃላ | LTR | Ethiopic | NT | 27 | — |
| [**`geez`**](data/geez/) | Ge'ez (`gez`) | መጽሐፍ ቅዱስ በግዕዝ (Dillmann Edition) | LTR | Ethiopic | OT, NT | 53 | 6 in [`data/apocrypha/geez/`](data/apocrypha/geez) |
| [**`greekOriginal`**](data/greekOriginal/) | Greek (`grc`) | Ἡ Καινὴ Διαθήκη | LTR | Greek | NT | 27 | — |
| [**`hebrewBible`**](data/hebrewBible/) | Hebrew (`heb`) | תנ״ך והבריት החדשה | RTL | Hebrew | OT, NT | 66 | — |
| [**`hebrewOriginal`**](data/hebrewOriginal/) | Hebrew (`heb`) | תורה, נביאים וכתובים | RTL | Hebrew | OT | 39 | — |
| [**`oromiffa`**](data/oromiffa/) | Oromo (`orm`) | Macaafa Qulqulluu | LTR | Latin | OT, NT | 66 | — |
| [**`somali`**](data/somali/) | Somali (`som`) | Kitaabka Quduuska Ah | LTR | Latin | OT, NT | 66 | — |
| [**`tigrinya1997`**](data/tigrinya1997/) | Tigrinya (`tir`) | መጽሐፍ ቅዱስ ብትግርኛ 1997 | LTR | Ethiopic | OT, NT | 66 | — |
| [**`wolayta`**](data/wolayta/) | Wolaytta (`wal`) | ዎላይታ ጌሻ ማፃፋ | LTR | Ethiopic | OT, NT | 66 | — |

---

## 💡 Developer Quickstart

### 1. Python (Query Canonical & Apocrypha)

```python
import json

# Query canonical book: John 1:1
with open("data/am2000/John.json", "r", encoding="utf-8") as f:
    john = json.load(f)
print("John 1:1:", john["chapters"][0]["verses"]["1"])

# Query apocryphal book: Enoch 1:1
with open("data/apocrypha/am2000/Enoch.json", "r", encoding="utf-8") as f:
    enoch = json.load(f)
print("Enoch 1:1:", enoch["chapters"][0]["verses"]["1"])
```

### 2. JavaScript / TypeScript

```typescript
import john from './data/am2000/John.json';
import enoch from './data/apocrypha/am2000/Enoch.json';

const john1v1 = john.chapters[0].verses["1"];
const enoch1v1 = enoch.chapters[0].verses["1"];
console.log(john1v1, enoch1v1);
```

---

## 🙏 Credits & Sources

Most of the Bible text in this dataset was converted from the XML Bibles published by **[Beblia — Holy Bible XML Format](https://github.com/Beblia/Holy-Bible-XML-Format)** (200+ languages, 1000+ versions, collected by the Beblia team at [beblia.com](https://beblia.com)). Thank you to the Beblia team for compiling these texts and making them openly available.

The Beblia repository has no formal license file. Its README says the files may be used "at your own discretion, no need to ask for permission", with no warranty.

### ⚠️ Translation copyrights

Beblia's permission covers its XML compilation. It cannot waive the copyright of the translations themselves, which stays with each translation's publisher. Several of the source files carry their own notice in the `<bible>` header, for example:

| Translation | Notice in the source XML header |
| :--- | :--- |
| `am2000` | Bible Society of Ethiopia |
| `dawro` | © 2011, Wycliffe Bible Translators, Inc. All rights reserved |
| `gamo` | © 2011, Wycliffe Bible Translators, Inc. All rights reserved |
| `wolayta` | © 2002, Bible Society of Ethiopia |
| `somali` | © 2008, Society for International Ministries |
| `coptic` | Attribution: 2006, J. Warren Wells, editor |

Some texts are public domain (for example the Greek GNT 1904 and older Hebrew editions). The Ge'ez text (Dillmann edition) and the Ge'ez apocrypha are not part of the Beblia collection; they came from other sources.

**What this means for you:** this dataset is free to use for personal study, research and non-commercial ministry. Before redistributing a copyrighted translation commercially, or bundling it in a published app, check its license and get permission from its publisher (for example the Bible Society of Ethiopia or Wycliffe). If you hold rights to one of these translations and want it credited differently or removed, please open an issue.

---

## 🤝 Contributing

We welcome community contributions! Please read our [**`CONTRIBUTING.md`**](CONTRIBUTING.md) guide for details on:
- Adding new languages and regional translations (Sidama, Hadiyya, Afar, etc.)
- Expanding digitized Ge'ez Old Testament / Deuterocanonical books
- Correcting typos and proofreading
- Localized book names and audio timestamps
- Building client SDKs and utilities
