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
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    documents = relationship("Document", back_populates="user")
    sessions = relationship("VerificationSession", back_populates="user")


class Document(Base):
    """
    Represents an uploaded ID / passport / license.
    """
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    document_type = Column(String, nullable=False)
    file_path = Column(String, nullable=False)

    extracted_fields = Column(JSON, nullable=True)
    ocr_confidence = Column(Float, nullable=True)

    is_forged = Column(Boolean, default=False)
    forgery_reasons = Column(JSON, nullable=True)
    forgery_score = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="documents")


class VerificationSession(Base):
    """
    One KYC attempt: ties together document check + face match + liveness +
    deepfake + voice + trust score.
    """
    __tablename__ = "verification_sessions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)
    document_id = Column(UUID(as_uuid=False), ForeignKey("documents.id"), nullable=True)

    selfie_path = Column(String, nullable=True)

    face_match_score = Column(Float, nullable=True)
    face_match_passed = Column(Boolean, nullable=True)

    liveness_passed = Column(Boolean, nullable=True)
    liveness_details = Column(JSON, nullable=True)

    deepfake_score = Column(Float, nullable=True)
    voice_match_score = Column(Float, nullable=True)
    voice_spoof_score = Column(Float, nullable=True)
    trust_score = Column(Float, nullable=True)

    device_fingerprint = Column(String, nullable=True, index=True)
    ip_address = Column(String, nullable=True, index=True)

    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="sessions")