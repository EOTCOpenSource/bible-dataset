

import argparse
import json
import os
import urllib.request
import xml.etree.ElementTree as ET


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


def write_json_file(data, json_path, indent=2):
    """Write a dictionary to a JSON file, creating parent folders if needed."""
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def load_xml_root(source):
    """Load the XML root element from a URL or a local file path."""
    if source.startswith(("http://", "https://")):


        if "github.com" in source and "/blob/" in source:
            source = source.replace("github.com", "raw.githubusercontent.com", 1)
            source = source.replace("/blob/", "/", 1)

        print(f"Downloading {source} ...")
        request = urllib.request.Request(source, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=60) as response:
            return ET.fromstring(response.read())

    return ET.parse(source).getroot()


def split_bible(source, output_dir="output"):
    root = load_xml_root(source)
    chapter_count = 0

    for testament in root.findall("testament"):
        testament_name = testament.get("name").lower()  

        for book in testament.findall("book"):
            book_number = int(book.get("number"))
            book_name = BOOK_NAMES[book_number - 1]

            for chapter in book.findall("chapter"):
                chapter_number = int(chapter.get("number"))

                data = {
                    "testament": testament_name,
                    "book": book_name,
                    "book_number": book_number,
                    "chapter": chapter_number,
                    "verses": {
                        verse.get("number"): (verse.text or "").strip()
                        for verse in chapter.findall("verse")
                    },
                }

                path = os.path.join(
                    output_dir, testament_name, book_name, f"{chapter_number}.json"
                )
                write_json_file(data, path)
                chapter_count += 1

    print(f"Done: wrote {chapter_count} chapter files to '{output_dir}/'")


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Split a Bible XML into chapter JSON files.")
    parser.add_argument("input", help="URL (or local path) of the Bible XML file")
    parser.add_argument("-o", "--output", default="output", help="Output folder (default: output)")
    args = parser.parse_args()

    split_bible(args.input, args.output)