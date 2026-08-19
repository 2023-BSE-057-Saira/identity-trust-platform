"""
OCR extraction for ID cards, passports, licenses.

Using pytesseract (wraps the Tesseract OCR engine) instead of PaddleOCR.
PaddleOCR/PaddlePaddle were dropped because paddlepaddle 2.6.2 pins an old
protobuf version that hard-conflicts with mediapipe/onnxruntime (needed for
face matching and liveness) - those three packages cannot coexist in one
environment on Windows. pytesseract has no such conflict and is a completely
standard, widely-used OCR choice.

IMPORTANT - Windows setup requirement:
pytesseract is just a Python wrapper - it calls the actual Tesseract OCR
engine, which is a SEPARATE program you must install on your system (not
just `pip install`). Download it from:
https://github.com/UB-Mannheim/tesseract/wiki
Install it, then note the install path (usually
C:\\Program Files\\Tesseract-OCR\\tesseract.exe) - you may need to set that
path explicitly, see TESSERACT_CMD below.
"""

import os
import re
from typing import Dict, List, Optional

import pytesseract
from PIL import Image

# If Tesseract isn't on your system PATH, uncomment and set this to your
# actual install path:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

TESSERACT_CMD_ENV = os.getenv("TESSERACT_CMD")
if TESSERACT_CMD_ENV:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD_ENV


def extract_text(image_path: str) -> List[Dict]:
    """
    Runs OCR on an image and returns a list of {"text": str, "confidence": float, "box": [...]}
    matching the same shape the rest of the codebase expects (so nothing
    downstream needs to change).
    """
    img = Image.open(image_path)
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

    extracted = []
    n_boxes = len(data["text"])
    for i in range(n_boxes):
        text = data["text"][i].strip()
        conf = data["conf"][i]
        if not text or conf == -1:
            continue

        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
        box = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]

        extracted.append({
            "text": text,
            "confidence": float(conf) / 100.0,  # tesseract gives 0-100, normalize to 0-1
            "box": box,
        })

    return extracted


def parse_fields(ocr_lines: List[Dict]) -> Dict:
    """
    Heuristic field parser. This is intentionally simple regex matching -
    good enough for a demo, and you should say explicitly in your report that
    a production system would use a trained NER model or template-matching
    per document type instead of regex.

    Uses keyword-anchored parsing (looks for "DOB:", "EXPIRY:", "ID:" etc.
    immediately before the value) rather than blindly grabbing the first
    date/alphanumeric match in the whole text - that first approach breaks
    as soon as a document has more than one date or the word "EXPIRY"
    itself gets matched as if it were an ID number.
    """
    full_text = " ".join(line["text"] for line in ocr_lines)

    fields = {
        "raw_text": full_text,
        "document_number": _find_labeled_value(full_text, ["ID", "DOCUMENT NO", "DOC NO", "PASSPORT NO"], r"[A-Z0-9]{6,12}"),
        "date_of_birth": _find_labeled_value(full_text, ["DOB", "DATE OF BIRTH", "BIRTH"], r"\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2}"),
        "expiry_date": _find_labeled_value(full_text, ["EXPIRY", "EXPIRES", "EXP DATE", "VALID UNTIL"], r"\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2}"),
        "mrz_lines": _find_mrz_lines(ocr_lines),
    }
    return fields


def _find_labeled_value(text: str, labels: List[str], value_pattern: str) -> Optional[str]:
    """
    Looks for `<label>: <value>` or `<label> <value>` right after one of the
    given labels, so "EXPIRY: 01/01/2030" doesn't get confused with
    "DOB: 15/06/1995" even though both are dates in the same document.
    """
    upper_text = text.upper()
    for label in labels:
        # Match the label, optional colon/space, then capture the value pattern
        pattern = rf"{re.escape(label)}\s*:?\s*({value_pattern})"
        match = re.search(pattern, upper_text)
        if match:
            return match.group(1)
    return None


def _find_mrz_lines(ocr_lines: List[Dict]) -> List[str]:
    """
    Passports have a Machine Readable Zone: 2-3 lines of exactly 44 chars
    using only A-Z, 0-9, and '<'. This detects candidate MRZ lines so
    forgery_checks.py can validate the checksum.

    NOTE: tesseract's default engine struggles more with MRZ's dense
    monospace font than PaddleOCR did - if MRZ detection is unreliable on
    your test passports, tell me and I'll add a dedicated MRZ-region OCR
    pass (crop bottom of image + tesseract config tuned for MRZ font).
    """
    mrz_candidates = []
    for line in ocr_lines:
        cleaned = line["text"].replace(" ", "")
        if len(cleaned) >= 30 and re.fullmatch(r"[A-Z0-9<]+", cleaned.upper()):
            mrz_candidates.append(cleaned.upper())
    return mrz_candidates
