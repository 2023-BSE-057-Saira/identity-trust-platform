from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_role
from app.models import User, Document, VerificationSession
from app.modules.trust_scoring.engine import compute_trust_score
from app.modules.identity_copilot.copilot import answer_question

router = APIRouter(prefix="/api/v1/copilot", tags=["ai-copilot"])


class CopilotQuestion(BaseModel):
    session_id: str
    question: str


# ============================================================
# WEEK 3 ENDPOINT - AI Identity Copilot
# ============================================================

@router.post("/ask")
def ask_copilot(
    payload: CopilotQuestion,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("analyst", "admin")),
):
    """
    AI Identity Copilot: answers analyst questions about a specific
    verification session, grounded in its trust score breakdown.

    Example questions (straight from the case study spec):
    - "Why did verification fail?"
    - "Explain the fraud indicators."
    - "Generate investigation summary."
    - "Recommend verification action."
    - "Show deepfake probability."
    """
    session = db.query(VerificationSession).filter(VerificationSession.id == payload.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Verification session not found")

    document = None
    if session.document_id:
        document = db.query(Document).filter(Document.id == session.document_id).first()

    voice_match_passed = None
    if session.voice_match_score is not None:
        voice_match_passed = session.voice_match_score >= 0.98

    context = compute_trust_score(
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

    result = answer_question(payload.question, context)
    return {"session_id": session.id, "question": payload.question, **result}
