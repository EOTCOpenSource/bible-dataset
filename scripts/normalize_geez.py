#!/usr/bin/env python3
"""
Normalize Ge'ez Bible JSON files by removing XML/HTML tags (like <pb/>, <f>...</f>, <J>...</J>),
footnote markers, and non-Ethiopic/non-Amharic symbols so the text is clean and readable for humans.
"""

import argparse
import glob
import json
import os
import re
from typing import Dict, Any


def clean_verse(text: str) -> str:
    if not text:
        return ""

    # 1. Remove page break tags: <pb/>, <pb>
    t = re.sub(r'<pb\s*/?>', '', text)

    # 2. Remove footnote tags and their full contents (<f>...</f>), e.g. ⓐ..ⓩ, [1]..[99]
    t = re.sub(r'<f>.*?</f>', '', t, flags=re.DOTALL)

    # 3. Strip any formatting tags (<J>, </J>, <i>, </i>, <b>, </b>, etc.) preserving inner text
    t = re.sub(r'</?[A-Za-z][^>]*>', '', t)

    # 4. Remove non-Ethiopic quotation marks, brackets, and Latin exclamation marks
    # Keep Ethiopic letters, Ethiopic punctuation (፡ ። ፣ ፤ ፥ ፦ ፠ ፨), Ethiopic numerals (፩-፼)
    t = re.sub(r'[«»!()[\]]', '', t)

    # 5. Collapse multiple whitespace characters into a single space
    t = re.sub(r'[ \t\r\n]+', ' ', t)

    # 6. Remove space before Ethiopic punctuation marks (e.g., ' ።' -> '።')
    t = re.sub(r'\s+([።፥፣፤፡፦፠፨])', r'\1', t)

    return t.strip()


def normalize_json_file(file_path: str, indent: int = 2) -> bool:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    changed = False
    verses: Dict[str, Any] = data.get("verses", {})
    new_verses = {}

    for v_num, text in verses.items():
        cleaned = clean_verse(text)
        if cleaned != text:
            changed = True
        new_verses[v_num] = cleaned

    data["verses"] = new_verses

    if changed:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
            f.write("\n")

    return changed


def normalize_directory(target_dir: str, indent: int = 2):
    if not os.path.isdir(target_dir):
        raise NotADirectoryError(f"Directory not found: {target_dir}")

    files = sorted(glob.glob(os.path.join(target_dir, "**", "*.json"), recursive=True))
    total_files = len(files)
    modified_files = 0

    print(f"Scanning {total_files} JSON files in '{target_dir}'...")
    for file_path in files:
        if normalize_json_file(file_path, indent=indent):
            modified_files += 1

    print(f"Done: Normalized {modified_files} of {total_files} files in '{target_dir}'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normalize Ge'ez Bible JSON files by removing tags and non-Amharic symbols.")
    parser.add_argument("target", nargs="?", default="geez2", help="Target directory to normalize (default: geez2)")
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation level (default: 2)")
    args = parser.parse_args()

    normalize_directory(args.target, indent=args.indent)
