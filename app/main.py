from fastapi import FastAPI

from app.core.db import Base, engine
from app.api.routes_identity import router as identity_router
from app.api.routes_auth import router as auth_router

app = FastAPI(
    title="Enterprise Digital Identity, Trust & Deepfake Detection Platform",
    description="AI-236 Case Study - Week 1: Identity Verification Engine",
    version="0.1.0",
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
