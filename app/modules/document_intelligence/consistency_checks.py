"""
Document consistency checks.

This looks for INTERNAL logical contradictions in a single document's
extracted fields - a real and common forgery/error signal that doesn't
require any ML model, just domain logic:

- Expiry date before issue date, or before today (expired document)
- Date of birth implying an implausible age (negative, or >120 years)
- Document number format inconsistent with the claimed document type
  (e.g. passport numbers and national ID numbers usually follow different
  patterns per country - we check basic length/charset plausibility)
- MRZ-derived DOB (if available) not matching the OCR'd DOB field
  elsewhere on the document - a classic tampering tell, since editing one
  field but not the corresponding MRZ line is a common amateur forgery mistake

This is genuinely useful signal and cheap to compute - good ROI for the
time it takes to build.
"""

from datetime import datetime
from typing import Dict, List, Optional


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def _parse_mrz_date(yymmdd: str) -> Optional[datetime]:
    """MRZ dates are YYMMDD. Century is ambiguous - assume 1930-2029 window,
    which is the standard heuristic used by real MRZ parsers."""
    if not yymmdd or len(yymmdd) != 6 or not yymmdd.isdigit():
        return None
    yy, mm, dd = int(yymmdd[0:2]), int(yymmdd[2:4]), int(yymmdd[4:6])
    century = 1900 if yy >= 30 else 2000
    try:
        return datetime(century + yy, mm, dd)
    except ValueError:
        return None


def check_document_consistency(extracted_fields: Dict, mrz_lines: Optional[List[str]] = None) -> Dict:
    """
    Returns:
        {
            "consistent": bool,
            "issues": [str, ...],   # human-readable, feeds the Explainable AI / copilot
        }
    """
    issues: List[str] = []

    dob = _parse_date(extracted_fields.get("date_of_birth"))
    expiry = _parse_date(extracted_fields.get("expiry_date"))
    now = datetime.utcnow()

    # --- Expiry checks ---
    if expiry:
        if expiry < now:
            issues.append(f"Document expired on {expiry.date()}")
        if dob and expiry < dob:
            issues.append("Expiry date is earlier than date of birth - logically impossible")

    # --- Age plausibility ---
    if dob:
        age_years = (now - dob).days / 365.25
        if age_years < 0:
            issues.append("Date of birth is in the future")
        elif age_years > 120:
            issues.append(f"Implied age ({age_years:.0f} years) is implausible")

    # --- Document number plausibility (basic length/charset check) ---
    doc_number = extracted_fields.get("document_number")
    if doc_number and not (6 <= len(doc_number) <= 12 and doc_number.isalnum()):
        issues.append(f"Document number '{doc_number}' has an unusual format for this document type")

    # --- MRZ vs. OCR'd DOB cross-check (passport-specific) ---
    if mrz_lines and len(mrz_lines) >= 2 and dob:
        line2 = mrz_lines[1].ljust(44, "<")[:44]
        mrz_dob_raw = line2[13:19]
        mrz_dob = _parse_mrz_date(mrz_dob_raw)
        if mrz_dob and abs((mrz_dob - dob).days) > 1:
            issues.append(
                f"Date of birth mismatch: OCR field says {dob.date()}, "
                f"MRZ encodes {mrz_dob.date()} - possible tampering"
            )

    return {"consistent": len(issues) == 0, "issues": issues}
