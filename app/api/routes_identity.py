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
from app.modules.deepfake_detection.detector import analyze_video_frames
from app.modules.voice_auth.voice_analysis import match_speakers, detect_voice_spoof
from app.modules.trust_scoring.engine import compute_trust_score

router = APIRouter(prefix="/api/v1/identity", tags=["identity"])

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _save_upload(file: UploadFile) -> str:
    ext = os.path.splitext(file.filename)[1]
    path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}{ext}")
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return path


# ============================================================
# WEEK 1 ENDPOINTS
# ============================================================

@router.post("/document/upload")
async def upload_document(
    document_type: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Step 1: upload ID/passport, run OCR + forgery + consistency checks.
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
    Compares the signature crop from the uploaded document against a
    separately-provided reference signature image.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="This document does not belong to you")

    ref_path = _save_upload(reference_signature)
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

    if session.face_match_passed and session.liveness_passed:
        session.status = "passed"
    elif session.face_match_passed is False or session.liveness_passed is False:
        session.status = "failed"
    else:
        session.status = "review"

    db.commit()

    return {"session_id": session.id, "status": session.status, **liveness_result}


# ============================================================
# WEEK 2 ENDPOINTS
# ============================================================

@router.post("/deepfake/analyze")
async def analyze_deepfake(
    session_id: str,
    video: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Step 4: analyzes a video for deepfake/manipulation artifacts and
    stores the score on the verification session.
    """
    session = db.query(VerificationSession).filter(VerificationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Verification session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="This session does not belong to you")

    video_path = _save_upload(video)
    result = analyze_video_frames(video_path)

    session.deepfake_score = result.get("deepfake_score")
    db.commit()

    return {"session_id": session.id, **result}


@router.post("/voice/verify")
async def verify_voice(
    session_id: str,
    reference_audio: UploadFile = File(...),
    test_audio: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Step 5: compares reference vs. test voice clips (speaker match) and
    checks the reference clip for spoof/replay signals.
    """
    session = db.query(VerificationSession).filter(VerificationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Verification session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="This session does not belong to you")

    ref_path = _save_upload(reference_audio)
    test_path = _save_upload(test_audio)

    match_result = match_speakers(ref_path, test_path)
    spoof_result = detect_voice_spoof(ref_path)

    session.voice_match_score = match_result.get("score")
    session.voice_spoof_score = spoof_result.get("spoof_score")
    db.commit()

    return {"session_id": session.id, "match": match_result, "spoof_check": spoof_result}


@router.post("/trust-score/compute")
async def compute_session_trust_score(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Step 6: pulls every stored signal for this session and computes the
    final explainable trust score.
    """
    session = db.query(VerificationSession).filter(VerificationSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Verification session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="This session does not belong to you")

    document = None
    if session.document_id:
        document = db.query(Document).filter(Document.id == session.document_id).first()

    voice_match_passed = None
    if session.voice_match_score is not None:
        voice_match_passed = session.voice_match_score >= 0.98

    result = compute_trust_score(
        face_match_score=session.face_match_score,
        face_match_passed=session.face_match_passed,
        liveness_passed=session.liveness_passed,
        document_is_forged=document.is_forged if document else None,
        document_forgery_score=document.forgery_score if document else None,
        deepfake_score=session.deepfake_score,
        voice_match_score=session.voice_match_score,
        voice_match_passed=voice_match_passed,
        voice_spoof_score=session.voice_spoof_score,
    )

    session.trust_score = result["trust_score"]
    if result["risk_level"] == "low":
        session.status = "passed"
    elif result["risk_level"] == "medium":
        session.status = "review"
    else:
        session.status = "failed"
    db.commit()

    return {"session_id": session.id, **result}