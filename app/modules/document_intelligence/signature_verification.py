"""
Signature verification.

Real signature verification (the kind banks use) trains a Siamese CNN on
thousands of genuine/forged signature pairs - that's out of scope for a
3-week, 2-person project. What we're building here is an honest,
explainable substitute: structural similarity + stroke pattern comparison
between two signature crops. It catches "obviously different signature"
cases well; it will NOT catch a skilled forgery. Say this explicitly in
your report - overclaiming here is the fastest way to lose points on
"Explainable AI" if a judge asks a hard question about it.

Usage pattern: extract the signature region from the ID document (usually
a fixed area, or detected via contour analysis) and compare it against a
reference signature on file (e.g. from a previous verification or a
separate signature capture during onboarding).
"""

from typing import Dict, Optional

import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim


def _preprocess_signature(image_path: str) -> Optional[np.ndarray]:
    """Load, grayscale, threshold to isolate ink strokes from background."""
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None

    # Otsu thresholding - separates dark ink strokes from the (usually light) background
    _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Crop to the bounding box of the ink so signature position/padding
    # differences don't distort the comparison.
    coords = cv2.findNonZero(thresh)
    if coords is None:
        return thresh  # blank image, nothing to crop
    x, y, w, h = cv2.boundingRect(coords)
    cropped = thresh[y:y + h, x:x + w]

    # Normalize size so two signatures of different resolutions compare fairly
    resized = cv2.resize(cropped, (300, 150), interpolation=cv2.INTER_AREA)
    return resized


def compare_signatures(signature_a_path: str, signature_b_path: str) -> Dict:
    """
    Compares two signature crops (e.g. one from the ID document, one from
    a reference capture) using structural similarity (SSIM) on the
    preprocessed ink-stroke masks.

    Returns similarity in [0, 1] - not a legally-defensible forensic
    match, but a reasonable automated first-pass signal.
    """
    img_a = _preprocess_signature(signature_a_path)
    img_b = _preprocess_signature(signature_b_path)

    if img_a is None or img_b is None:
        return {
            "similarity": None,
            "match": False,
            "reason": "Could not read one or both signature images",
        }

    score, _ = ssim(img_a, img_b, full=True)
    score = max(0.0, float(score))  # SSIM can go slightly negative; clamp for readability

    # Threshold is a starting point - tune against real genuine/forged
    # sample pairs before trusting this number in your report.
    match = score >= 0.35

    return {
        "similarity": round(score, 4),
        "match": match,
        "reason": None if match else "Signature structure differs significantly from reference",
    }
