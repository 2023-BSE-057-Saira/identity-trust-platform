import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.db import Base


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    full_name = Column(String, nullable=True)
    phone_number = Column(String, nullable=True, index=True)

    # --- Auth fields ---
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="applicant")  # applicant, analyst, admin
    # "applicant" = normal end user going through KYC
    # "analyst"   = security team using the AI Identity Copilot / dashboard
    # "admin"     = full access
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    documents = relationship("Document", back_populates="user")
    sessions = relationship("VerificationSession", back_populates="user")


class Document(Base):
    """
    Represents an uploaded ID / passport / license.
    This table doubles as an input node for the Week 3 Knowledge Graph
    (User -> Document edges), so keep extracted_fields structured.
    """
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    document_type = Column(String, nullable=False)  # national_id, passport, license, employee_id, residence_permit
    file_path = Column(String, nullable=False)

    extracted_fields = Column(JSON, nullable=True)   # OCR output: name, dob, doc_number, expiry, mrz, etc.
    ocr_confidence = Column(Float, nullable=True)

    is_forged = Column(Boolean, default=False)
    forgery_reasons = Column(JSON, nullable=True)     # list of triggered checks, for explainability
    forgery_score = Column(Float, nullable=True)      # 0.0 (clean) - 1.0 (highly suspicious)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="documents")


class VerificationSession(Base):
    """
    One KYC attempt: ties together document check + face match + liveness result.
    Trust Scoring Engine (Week 2) will read from this table.
    """
    __tablename__ = "verification_sessions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    document_id = Column(UUID(as_uuid=False), ForeignKey("documents.id"), nullable=True)

    selfie_path = Column(String, nullable=True)

    face_match_score = Column(Float, nullable=True)     # cosine similarity, 0-1
    face_match_passed = Column(Boolean, nullable=True)

    liveness_passed = Column(Boolean, nullable=True)
    liveness_details = Column(JSON, nullable=True)       # e.g. {"blinks_detected": 2, "ear_min": 0.18}

    # Filled in during Week 2 (kept here now so schema doesn't need migration later)
    deepfake_score = Column(Float, nullable=True)
    voice_match_score = Column(Float, nullable=True)
    trust_score = Column(Float, nullable=True)

    device_fingerprint = Column(String, nullable=True, index=True)  # feeds Week 3 knowledge graph
    ip_address = Column(String, nullable=True, index=True)

    status = Column(String, default="pending")  # pending, passed, failed, review
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="sessions")
