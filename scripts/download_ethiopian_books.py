#!/usr/bin/env python3
"""
Download all files related to the additional books of the Ethiopian Bible from https://tohdee.github.io/
and organize them in 'ethiopian_additional_books/'.
"""

import os
import sys
import time
import urllib.request
from bs4 import BeautifulSoup

BASE_URL = "https://tohdee.github.io/"
OUTPUT_DIR = "/home/hena/Downloads/bibleData/ethiopian_additional_books"

# Define the targets:
# 1. Broad Canon 15 books (7 OT books in Ceee-Ebc + 8 NT books in Dbbb-Ebc + overview)
# 2. Narrow Canon additional books (Tobit, Judith, Wisdom, Sirach, Baruch, 4 Baruch, Esdras, etc.)

def get_file_metadata():
    with open('/tmp/tohdee_index.html', 'r', encoding='utf-8', errors='ignore') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    files = {}

    for a in soup.find_all('a', href=True):
        href = a['href'].strip()
        if href.startswith(('http', 'mailto', '#')):
            continue
        ext = href.split('.')[-1].lower() if '.' in href else ''
        if ext not in ['pdf', 'docx', 'odt']:
            continue

        parent_tr = a.find_parent('tr')
        row_text = parent_tr.get_text().strip().replace('\n', ' ') if parent_tr else ''
        title = a.get('title', '')
        link_text = a.get_text(strip=True)

        is_ebc = ('Ebc' in href or 'ebc' in href or 'Y702-EBC' in href)
        is_narrow = any(k in href for k in ['PaJ', 'AsI', 'RPt', 'Tob', 'Jdt', 'Wis', 'Sir', 'Bar', 'LJe', '1Es', '2Es', 'P151', 'Man']) and any(href.startswith(p) for p in ['Caaa-', 'Cbbb-', 'Cccc-', 'Cddd-', 'Dccc-', 'Eccc-'])

        if is_ebc or is_narrow:
            category = "Broad Canon (15 Books)" if is_ebc else "Ethiopian Deuterocanon / Narrow Canon"
            files[href] = {
                "href": href,
                "category": category,
                "link_text": link_text,
                "title": title,
                "row_text": row_text[:80],
                "filename": os.path.basename(href),
                "subfolder": os.path.dirname(href)
            }

    return files


def download_file(href, dest_path):
    url = BASE_URL + href
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                content = resp.read()
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                with open(dest_path, "wb") as out_f:
                    out_f.write(content)
                return True, len(content)
        except Exception as e:
            if attempt == 2:
                return False, str(e)
            time.sleep(1)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    metadata = get_file_metadata()
    print(f"Total target files identified: {len(metadata)}")

    downloaded = []
    failed = []

    for i, (href, info) in enumerate(sorted(metadata.items()), 1):
        filename = os.path.basename(href)
        # Store in subfolder matching section or flat
        dest = os.path.join(OUTPUT_DIR, info["subfolder"], filename)
        print(f"[{i}/{len(metadata)}] Downloading {filename} ({info['category']})...", end=" ", flush=True)
        success, res = download_file(href, dest)
        if success:
            print(f"OK ({res} bytes)")
            downloaded.append({**info, "size": res, "local_path": os.path.relpath(dest, OUTPUT_DIR)})
        else:
            print(f"FAILED ({res})")
            failed.append({**info, "error": res})

    # Generate README.md index in OUTPUT_DIR
    readme_path = os.path.join(OUTPUT_DIR, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("# Ethiopian Bible Additional Books Collection\n\n")
        f.write(f"Source: [{BASE_URL}]({BASE_URL})\n\n")
        f.write(f"Total downloaded files: **{len(downloaded)}** (Failures: {len(failed)})\n\n")

        for cat in ["Broad Canon (15 Books)", "Ethiopian Deuterocanon / Narrow Canon"]:
            f.write(f"## {cat}\n\n")
            f.write("| File | Type | Title / Description | Language / Source | Size |\n")
            f.write("| --- | --- | --- | --- | --- |\n")
            cat_files = [x for x in downloaded if x["category"] == cat]
            for item in sorted(cat_files, key=lambda x: x["local_path"]):
                ext = item["filename"].split(".")[-1].upper()
                size_kb = f"{item['size'] / 1024:.1f} KB" if item['size'] < 1024*1024 else f"{item['size'] / (1024*1024):.2f} MB"
                desc = item['title'] or item['row_text']
                f.write(f"| `{item['local_path']}` | {ext} | {desc} | {item['link_text']} | {size_kb} |\n")
            f.write("\n")

    print(f"\nAll done! {len(downloaded)} files downloaded to '{OUTPUT_DIR}'.")
    print(f"Index written to '{readme_path}'.")


if __name__ == "__main__":
    main()
