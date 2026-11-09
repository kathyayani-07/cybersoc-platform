from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base
from app.time_utils import utc_now_naive


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    full_name = Column(String(120), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default="viewer")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now_naive)
    updated_at = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)

    incidents = relationship("Incident", foreign_keys="Incident.owner_id", back_populates="owner")
    created_incidents = relationship("Incident", foreign_keys="Incident.created_by", back_populates="creator")
    audit_logs = relationship("AuditLog", back_populates="user")


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now_naive, nullable=False)


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False, default="Medium")
    priority = Column(String(20), nullable=False, default="Medium")
    status = Column(String(30), nullable=False, default="New")
    detection_source = Column(String(100), nullable=False, default="Manual")
    affected_asset = Column(String(150), nullable=False, default="Unknown")
    reported_by = Column(String(120), nullable=False, default="System")
    assigned_analyst = Column(String(120), nullable=True)
    detection_timestamp = Column(DateTime, default=utc_now_naive)
    last_updated = Column(DateTime, default=utc_now_naive, onupdate=utc_now_naive)
    resolution_timestamp = Column(DateTime, nullable=True)
    investigation_notes = Column(Text, default="")
    evidence_references = Column(Text, default="")
    ai_analysis_results = Column(Text, default="")
    recommended_response_actions = Column(Text, default="")
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    owner = relationship("User", foreign_keys=[owner_id], back_populates="incidents")
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_incidents")
    analyses = relationship("AIAnalysis", back_populates="incident")


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    provider = Column(String(50), default="demo")
    analysis_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now_naive)

    incident = relationship("Incident", back_populates="analyses")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    details = Column(Text, default="")
    created_at = Column(DateTime, default=utc_now_naive)

    user = relationship("User", back_populates="audit_logs")
