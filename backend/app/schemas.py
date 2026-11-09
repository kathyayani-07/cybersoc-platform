from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer, field_validator, model_validator

from app.time_utils import as_utc_naive, utc_isoformat


class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase):
    password: str
    role: str = "viewer"


class UserOut(UserBase):
    id: int
    role: str
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class LoginRequest(BaseModel):
    username: str
    password: str


class IncidentCreate(BaseModel):
    title: str
    description: str
    category: str
    severity: str = "Medium"
    priority: str = "Medium"
    status: str = "New"
    detection_source: str = "Manual"
    affected_asset: str = "Unknown"
    reported_by: str = "System"
    assigned_analyst: str | None = None
    detection_timestamp: datetime | None = None
    last_updated: datetime | None = None
    resolution_timestamp: datetime | None = None
    investigation_notes: str | None = None
    evidence_references: str | None = None
    recommended_response_actions: str | None = None

    @field_validator("detection_timestamp", "last_updated", "resolution_timestamp")
    @classmethod
    def normalize_timestamps_to_utc(cls, value: datetime | None) -> datetime | None:
        return as_utc_naive(value) if value else None


class IncidentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    severity: str | None = None
    priority: str | None = None
    status: str | None = None
    detection_source: str | None = None
    affected_asset: str | None = None
    reported_by: str | None = None
    assigned_analyst: str | None = None
    detection_timestamp: datetime | None = None
    last_updated: datetime | None = None
    resolution_timestamp: datetime | None = None
    investigation_notes: str | None = None
    evidence_references: str | None = None
    recommended_response_actions: str | None = None

    @field_validator("detection_timestamp", "last_updated", "resolution_timestamp")
    @classmethod
    def normalize_timestamps_to_utc(cls, value: datetime | None) -> datetime | None:
        return as_utc_naive(value) if value else None


class IncidentOut(IncidentCreate):
    id: int
    owner_id: int
    created_by: int | None = None
    model_config = ConfigDict(from_attributes=True)

    @field_serializer("detection_timestamp", "last_updated", "resolution_timestamp", when_used="json")
    def serialize_timestamps_as_utc(self, value: datetime | None) -> str | None:
        return utc_isoformat(value)


class AnalysisRequest(BaseModel):
    description: str = Field(default="", max_length=20000)
    log_text: str | None = Field(default=None, max_length=20000)
    incident_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def require_evidence(self):
        if not self.description.strip() and not (self.log_text or "").strip():
            raise ValueError("Enter an incident description or a security log excerpt.")
        return self


class AnalysisContent(BaseModel):
    classification: str = Field(min_length=1)
    suggested_severity: Literal["Critical", "High", "Medium", "Low"]
    executive_summary: str = Field(min_length=1)
    suspicious_activity: list[str]
    indicators_of_compromise: list[str]
    potential_impact: str = Field(min_length=1)
    affected_systems: list[str]
    investigation_steps: list[str]
    containment_recommendations: list[str]
    remediation_suggestions: list[str]
    monitoring_recommendations: list[str]
    rationale: str = Field(min_length=1)


class AnalysisResult(BaseModel):
    provider: Literal["Demo AI"]
    classification: str
    suggested_severity: str
    executive_summary: str
    suspicious_activity: list[str]
    indicators_of_compromise: list[str]
    potential_impact: str
    affected_systems: list[str]
    investigation_steps: list[str]
    containment_recommendations: list[str]
    remediation_suggestions: list[str]
    monitoring_recommendations: list[str]
    rationale: str
    timestamp: datetime
    saved: bool = False

    @field_serializer("timestamp", when_used="json")
    def serialize_timestamp_as_utc(self, value: datetime) -> str:
        return utc_isoformat(value) or ""
