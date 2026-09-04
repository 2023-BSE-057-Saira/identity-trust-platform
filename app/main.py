from fastapi import FastAPI

from app.core.db import Base, engine
from app.api.routes_identity import router as identity_router
from app.api.routes_auth import router as auth_router
from app.api.routes_knowledge_graph import router as graph_router
from app.api.routes_copilot import router as copilot_router
from app.api.routes_dashboard import router as dashboard_router

app = FastAPI(
    title="Enterprise Digital Identity, Trust & Deepfake Detection Platform",
    description="AI-236 Case Study - Week 3: Knowledge Graph, AI Copilot, Dashboard backend",
    version="0.3.0",
)


@app.on_event("startup")
def on_startup():
    # For a demo/dev setup, creating tables directly is fine.
    # Switch to Alembic migrations before anything resembling production.
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(identity_router)
app.include_router(graph_router)
app.include_router(copilot_router)
app.include_router(dashboard_router)
