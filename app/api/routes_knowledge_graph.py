from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_role
from app.models import User
from app.modules.knowledge_graph.graph_engine import (
    build_identity_graph,
    graph_to_json,
    get_user_subgraph_json,
    detect_fraud_rings,
)

router = APIRouter(prefix="/api/v1/graph", tags=["knowledge-graph"])


# ============================================================
# WEEK 3 ENDPOINTS - Identity Knowledge Graph
# ============================================================

@router.get("/full")
def get_full_graph(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("analyst", "admin")),
):
    """
    Full identity knowledge graph: User -> Device / Document / Phone / IP /
    Fraud Case relationships. Analyst/admin only.
    """
    g = build_identity_graph(db)
    return graph_to_json(g)


@router.get("/user/{user_id}")
def get_user_graph(
    user_id: str,
    hops: int = 2,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("analyst", "admin")),
):
    """
    Investigation view: everything connected to one user within N hops.
    Powers the AI Copilot's "compare this face with previous records" answers.
    """
    return get_user_subgraph_json(db, user_id, hops=hops)


@router.get("/fraud-rings")
def get_fraud_rings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("analyst", "admin")),
):
    """
    Week 4 differentiator, built directly on Week 3's graph: clusters of
    different users sharing a device fingerprint or IP address.
    """
    rings = detect_fraud_rings(db)
    return {"fraud_rings": rings, "rings_found": len(rings)}
