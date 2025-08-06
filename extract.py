#!/usr/bin/env python3
import re
import os
import csv
from pathlib import Path
from PIL import Image
import pytesseract

# ——— CONFIG ———
# Folder containing your page screenshots
INPUT_DIR = Path("screenshots")
# Output CSV
OUTPUT_CSV = Path("bini_pairs.csv")
# Tesseract config (adjust if you have a Bini-trained model)
TESSERACT_LANG = "eng"  # or e.g. "ben" if you have a Bini model

# ——— HELPERS ———
def crop_columns(img: Image.Image):
    """Split image in two equal vertical halves."""
    w, h = img.size
    left  = img.crop((0,   0,   w//2, h))
    right = img.crop((w//2, 0,   w,    h))
    return left, right

def ocr_to_lines(img: Image.Image):
    """OCR the image and return a list of text lines."""
    text = pytesseract.image_to_string(img, lang=TESSERACT_LANG)
    # split on newline, drop empties
    return [line.strip() for line in text.splitlines() if line.strip()]

# regex to catch: headword [pron] gloss
ENTRY_RE = re.compile(r"""
    ^\s*
    (?P<headword>[^\[\]]+?)      # anything up to first [
    \s*\[ [^\]]+ \]              # drop the [...] pronunciation
    \s*(?P<gloss>.+?)            # the rest of the line = gloss
    $
""", re.VERBOSE)

def parse_entries(lines):
    """From list of OCR lines, extract (headword, gloss) pairs."""
    entries = []
    for line in lines:
        m = ENTRY_RE.match(line)
        if m:
            head = m.group("headword").strip()
            gloss = m.group("gloss").strip()
            entries.append((head, gloss))
    return entries

# ——— MAIN PIPELINE ———
def main():
    all_entries = []

    for img_path in sorted(INPUT_DIR.glob("*.[pj][pn]g")):
        print(f"Processing {img_path.name}…")
        img = Image.open(img_path)
        for col_img in crop_columns(img):
            lines = ocr_to_lines(col_img)
            entries = parse_entries(lines)
            all_entries.extend(entries)

    # dedupe while preserving order
    seen = set()
    unique = []
    for head, gloss in all_entries:
        if head not in seen:
            seen.add(head)
            unique.append((head, gloss))

    # write CSV
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["bini", "english"])
        writer.writerows(unique)

    print(f"Done!  Wrote {len(unique)} entries to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
