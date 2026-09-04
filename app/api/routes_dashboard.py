from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_role
from app.models import User, VerificationSession

router = APIRouter(prefix="/api/v1/dashboard", tags=["executive-dashboard"])


# ============================================================
# WEEK 3 ENDPOINTS - Executive Dashboard (data layer only;
# the visual dashboard itself is Week 4 UI work)
# ============================================================

@router.get("/summary")
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("analyst", "admin")),
):
    """Verification success rate + alert counts - top-line dashboard numbers."""
    total = db.query(func.count(VerificationSession.id)).scalar() or 0
    passed = db.query(func.count(VerificationSession.id)).filter(VerificationSession.status == "passed").scalar() or 0
    failed = db.query(func.count(VerificationSession.id)).filter(VerificationSession.status == "failed").scalar() or 0
    review = db.query(func.count(VerificationSession.id)).filter(VerificationSession.status == "review").scalar() or 0
    avg_trust = db.query(func.avg(VerificationSession.trust_score)).scalar()

    deepfake_alerts = db.query(func.count(VerificationSession.id)).filter(
        VerificationSession.deepfake_score > 0.5
    ).scalar() or 0
    voice_spoof_alerts = db.query(func.count(VerificationSession.id)).filter(
        VerificationSession.voice_spoof_score > 0.6
    ).scalar() or 0

    return {
        "total_sessions": total,
        "verification_success_rate": round((passed / total) * 100, 1) if total else 0.0,
        "passed": passed,
        "failed": failed,
        "under_review": review,
        "average_trust_score": round(avg_trust, 1) if avg_trust is not None else None,
        "deepfake_alerts": deepfake_alerts,
        "voice_spoof_alerts": voice_spoof_alerts,
    }


@router.get("/trust-score-distribution")
def trust_score_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("analyst", "admin")),
):
    """Buckets sessions by trust score range - feeds a histogram on the dashboard."""
    buckets = {"0-25": 0, "26-50": 0, "51-75": 0, "76-100": 0}
    scores = db.query(VerificationSession.trust_score).filter(
        VerificationSession.trust_score.isnot(None)
    ).all()
    for (score,) in scores:
        if score <= 25:
            buckets["0-25"] += 1
        elif score <= 50:
            buckets["26-50"] += 1
        elif score <= 75:
            buckets["51-75"] += 1
        else:
            buckets["76-100"] += 1
    return {"distribution": buckets, "total_scored_sessions": len(scores)}


@router.get("/risk-trends")
def identity_risk_trends(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("analyst", "admin")),
):
    """Daily session counts by status - feeds a trend line chart."""
    rows = (
        db.query(
            func.date(VerificationSession.created_at).label("day"),
            VerificationSession.status,
            func.count(VerificationSession.id),
        )
        .group_by(func.date(VerificationSession.created_at), VerificationSession.status)
        .order_by(func.date(VerificationSession.created_at))
        .all()
    )
    trends = {}
    for day, status, count in rows:
        trends.setdefault(str(day), {})[status] = count
    return {"trends": trends}
