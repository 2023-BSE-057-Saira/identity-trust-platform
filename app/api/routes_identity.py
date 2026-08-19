import os
import shutil
import uuid

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models import User, Document, VerificationSession
from app.modules.document_intelligence.ocr import extract_text, parse_fields
from app.modules.document_intelligence.forgery_checks import (
    validate_passport_mrz,
    detect_image_tampering,
)
from app.modules.document_intelligence.consistency_checks import check_document_consistency
from app.modules.document_intelligence.signature_verification import compare_signatures
from app.modules.face_verification.face_match import match_faces
from app.modules.face_verification.liveness import run_blink_liveness

router = APIRouter(prefix="/api/v1/identity", tags=["identity"])

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _save_upload(file: UploadFile) -> str:
    ext = os.path.splitext(file.filename)[1]
    path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}{ext}")
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return path


@router.post("/document/upload")
async def upload_document(
    document_type: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Step 1: upload ID/passport, run OCR + forgery checks.
    Returns extracted fields + forgery signal so the analyst/copilot can
    explain the result later.
    """
    path = _save_upload(file)

    ocr_lines = extract_text(path)
    fields = parse_fields(ocr_lines)
    tampering = detect_image_tampering(path)

    mrz_result = None
    if document_type == "passport" and fields["mrz_lines"]:
        mrz_result = validate_passport_mrz(fields["mrz_lines"])

    consistency_result = check_document_consistency(fields, mrz_lines=fields.get("mrz_lines"))

    forgery_reasons = []
    if tampering.get("flag"):
        forgery_reasons.append(f"Image tampering signal detected (score={tampering['tampering_score']})")
    if mrz_result and not mrz_result["valid"]:
        forgery_reasons.append(mrz_result["reason"])
    if not consistency_result["consistent"]:
        forgery_reasons.extend(consistency_result["issues"])

    forgery_score = tampering.get("tampering_score") or 0.0
    is_forged = len(forgery_reasons) > 0

    doc = Document(
        user_id=current_user.id,
        document_type=document_type,
        file_path=path,
        extracted_fields=fields,
        ocr_confidence=(
            sum(l["confidence"] for l in ocr_lines) / len(ocr_lines) if ocr_lines else None
        ),
        is_forged=is_forged,
        forgery_reasons=forgery_reasons,
        forgery_score=forgery_score,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {
        "document_id": doc.id,
        "extracted_fields": fields,
        "tampering_check": tampering,
        "mrz_check": mrz_result,
        "consistency_check": consistency_result,
        "is_forged": is_forged,
        "forgery_reasons": forgery_reasons,
    }


@router.post("/document/verify-signature")
async def verify_signature(
    document_id: str,
    reference_signature: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Compares the signature crop from the uploaded document (document_image)
    against a separately-provided reference signature image.

    NOTE: this expects reference_signature to already be a cropped signature
    image, not a full document - crop it before uploading, either manually
    for the demo or with a contour-detection step you add later.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="This document does not belong to you")

    ref_path = _save_upload(reference_signature)
    # For the demo: comparing against the same document image is a placeholder -
    # in practice, doc.file_path here should be a pre-cropped signature region
    # from the document, not the whole document image. Crop this yourself for
    # your test documents, or add an auto-crop step (contour detection on a
    # fixed signature zone) as a follow-up improvement.
    result = compare_signatures(doc.file_path, ref_path)

    return {"document_id": doc.id, **result}


@router.post("/face/verify")
async def verify_face(
    document_id: str,
    selfie: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Step 2: match selfie against the face on the previously uploaded document.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="This document does not belong to you")

    selfie_path = _save_upload(selfie)
    match_result = match_faces(doc.file_path, selfie_path)

    session = VerificationSession(
        user_id=current_user.id,
        document_id=doc.id,
        selfie_path=selfie_path,
        face_match_score=match_result.get("score"),
        face_match_passed=match_result.get("passed"),
        status="pending",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {"session_id": session.id, **match_result}


@router.post("/liveness/check")
async def check_liveness(
    session_id: str,
    video: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Step 3: active liveness via blink detection on a short video clip.
    """
    session = db.query(VerificationSession).filter(VerificationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Verification session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="This session does not belong to you")

    video_path = _save_upload(video)
    liveness_result = run_blink_liveness(video_path)

    session.liveness_passed = liveness_result.get("liveness_passed")
    session.liveness_details = liveness_result

    # Basic status rollup for week 1 - trust scoring engine replaces this in week 2
    if session.face_match_passed and session.liveness_passed:
        session.status = "passed"
    elif session.face_match_passed is False or session.liveness_passed is False:
        session.status = "failed"
    else:
        session.status = "review"

    db.commit()

    return {"session_id": session.id, "status": session.status, **liveness_result}
