"""
Document forgery detection.

The MRZ (Machine Readable Zone) checksum validation here is the REAL ICAO 9303
algorithm used by actual passport readers worldwide - this isn't a toy check,
it's genuinely how e-gates validate passports. Good talking point in your demo:
"we implemented the same checksum standard used in airport e-gates."

Other checks (image tampering, font consistency) are simplified heuristics -
be upfront about that distinction when you present.
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple

# ICAO 9303 character values: 0-9 = 0-9, A-Z = 10-35, '<' = 0
_MRZ_CHAR_VALUES = {c: i for i, c in enumerate("0123456789")}
_MRZ_CHAR_VALUES.update({c: i + 10 for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ")})
_MRZ_CHAR_VALUES["<"] = 0
_MRZ_WEIGHTS = [7, 3, 1]


def _mrz_char_value(c: str) -> int:
    return _MRZ_CHAR_VALUES.get(c, 0)


def compute_mrz_checksum(data: str) -> int:
    """Standard ICAO 9303 weighted checksum (mod 10)."""
    total = 0
    for i, char in enumerate(data):
        total += _mrz_char_value(char) * _MRZ_WEIGHTS[i % 3]
    return total % 10


def validate_passport_mrz(mrz_lines: List[str]) -> Dict:
    """
    Validates the second MRZ line of a TD3 (passport) MRZ, which contains:
    positions 0-9: document number + check digit
    positions 13-19: date of birth (YYMMDD) + check digit
    positions 21-27: expiry date (YYMMDD) + check digit
    positions 28-42: personal number + check digit
    positions 43: composite check digit

    Returns a result dict with pass/fail per field so you can show WHICH
    field failed in the forensic report (feeds your Explainable AI piece).
    """
    result = {"valid": False, "checks": {}, "reason": None}

    if len(mrz_lines) < 2:
        result["reason"] = "MRZ not detected or incomplete (need 2 lines for TD3 passport format)"
        return result

    line2 = mrz_lines[1].ljust(44, "<")[:44]

    doc_number = line2[0:9]
    doc_check = line2[9]
    dob = line2[13:19]
    dob_check = line2[19]
    expiry = line2[21:27]
    expiry_check = line2[27]

    checks = {
        "document_number": compute_mrz_checksum(doc_number) == _safe_int(doc_check),
        "date_of_birth": compute_mrz_checksum(dob) == _safe_int(dob_check),
        "expiry_date": compute_mrz_checksum(expiry) == _safe_int(expiry_check),
    }

    result["checks"] = checks
    result["valid"] = all(checks.values())
    if not result["valid"]:
        failed = [k for k, v in checks.items() if not v]
        result["reason"] = f"MRZ checksum failed for: {', '.join(failed)}"

    return result


def _safe_int(c: str) -> int:
    return int(c) if c.isdigit() else -1


def detect_image_tampering(image_path: str) -> Dict:
    """
    Simplified tampering heuristics - NOT a substitute for a trained forensic
    model, but demonstrates real forensic signal:

    1. Error Level Analysis (ELA) proxy: recompress the image at a known
       quality and diff against the original. Edited regions often show
       different compression artifacts than the rest of the image.
    2. Noise inconsistency: local noise variance should be roughly uniform
       across a genuine, unedited photo. Spliced regions often show a
       noise-variance discontinuity.
    """
    img = cv2.imread(image_path)
    if img is None:
        return {"tampering_score": None, "reason": "could not read image"}

    ela_score = _error_level_analysis(img)
    noise_score = _noise_variance_map(img)

    # Combine into one score, 0 (clean) - 1 (suspicious). Weights are a
    # starting point - tune against real tampered/clean samples before
    # trusting this in your report's numbers.
    tampering_score = round(0.6 * ela_score + 0.4 * noise_score, 3)

    return {
        "tampering_score": tampering_score,
        "ela_score": round(ela_score, 3),
        "noise_score": round(noise_score, 3),
        "flag": tampering_score > 0.5,
    }


def _error_level_analysis(img: np.ndarray, quality: int = 90) -> float:
    encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    _, encoded = cv2.imencode(".jpg", img, encode_params)
    recompressed = cv2.imdecode(encoded, cv2.IMREAD_COLOR)

    diff = cv2.absdiff(img, recompressed).astype(np.float32)
    score = float(np.mean(diff) / 255.0)
    return min(score * 10, 1.0)  # scale up since raw diff is usually tiny


def _noise_variance_map(img: np.ndarray, grid: int = 8) -> float:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    cell_h, cell_w = h // grid, w // grid

    variances = []
    for i in range(grid):
        for j in range(grid):
            cell = gray[i * cell_h:(i + 1) * cell_h, j * cell_w:(j + 1) * cell_w]
            if cell.size > 0:
                variances.append(np.var(cell))

    if not variances:
        return 0.0

    # High std-dev of local variances = inconsistent noise = possible splicing
    variances = np.array(variances)
    inconsistency = float(np.std(variances) / (np.mean(variances) + 1e-6))
    return min(inconsistency / 5.0, 1.0)  # normalize roughly into 0-1
