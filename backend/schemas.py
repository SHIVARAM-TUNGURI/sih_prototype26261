"""
Pydantic schemas for API request/response validation.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


# ── Application ──────────────────────────────────────────────────────────────

class ApplicationCreate(BaseModel):
    institution_name: str = Field(..., min_length=1)
    trust_name: str = Field(..., min_length=1)
    address: str = Field(..., min_length=1)
    pin_code: str = Field(..., pattern=r"^\d{6}$")
    land_area_acres: float = Field(..., gt=0)
    proposed_courses: str = Field(..., min_length=1)
    total_intake: int = Field(..., gt=0)
    faculty_count: int = Field(..., gt=0)
    application_date: str = Field(..., description="YYYY-MM-DD format")


class ApplicationResponse(BaseModel):
    id: int
    institution_name: str
    trust_name: str
    address: str
    pin_code: str
    land_area_acres: float
    proposed_courses: str
    total_intake: int
    faculty_count: int
    application_date: str
    application_type: str
    status: str
    trust_score: Optional[float] = None
    compliance_score: Optional[float] = None
    route: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApplicationListItem(BaseModel):
    id: int
    institution_name: str
    status: str
    trust_score: Optional[float] = None
    compliance_score: Optional[float] = None
    route: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Document ─────────────────────────────────────────────────────────────────

class DocumentResponse(BaseModel):
    id: int
    application_id: int
    doc_type: Optional[str] = None
    original_filename: str
    file_hash: str
    fields_json: Optional[dict[str, Any]] = None
    classification_confidence: Optional[float] = None
    tamper_score: Optional[float] = None
    tamper_details: Optional[dict[str, Any]] = None
    heatmap_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class HashVerifyResponse(BaseModel):
    document_id: int
    original_hash: str
    current_hash: str
    status: str  # "verified" or "altered"


# ── Findings ─────────────────────────────────────────────────────────────────

class FindingResponse(BaseModel):
    id: int
    category: str
    severity: str
    description: str
    evidence: Optional[dict[str, Any]] = None

    class Config:
        from_attributes = True


# ── Rule Results ─────────────────────────────────────────────────────────────

class RuleResultResponse(BaseModel):
    id: int
    rule_id: str
    rule_description: str
    status: str
    evidence: Optional[dict[str, Any]] = None
    clause_reference: Optional[str] = None
    clause_text: Optional[str] = None
    severity: str

    class Config:
        from_attributes = True


# ── Report ───────────────────────────────────────────────────────────────────

class ApplicationReport(BaseModel):
    application: ApplicationResponse
    documents: list[DocumentResponse] = []
    findings: list[FindingResponse] = []
    rule_results: list[RuleResultResponse] = []
    score_breakdown: Optional[dict[str, Any]] = None


# ── Decision ─────────────────────────────────────────────────────────────────

class DecisionRequest(BaseModel):
    action: str = Field(..., pattern=r"^(approve|reject|raise_deficiency)$")
    officer_id: str = Field(..., min_length=1)
    remarks: Optional[str] = None


class DecisionResponse(BaseModel):
    application_id: int
    action: str
    new_status: str
    deficiency_note: Optional[str] = None
    timestamp: datetime


# ── Pre-validation ───────────────────────────────────────────────────────────

class PreValidationResult(BaseModel):
    passed: bool
    issues: list[str] = []
    missing_documents: list[str] = []


# ── Processing ───────────────────────────────────────────────────────────────

class ProcessingResult(BaseModel):
    application_id: int
    status: str
    trust_score: Optional[float] = None
    compliance_score: Optional[float] = None
    route: Optional[str] = None
    findings_count: int = 0
    rule_results_count: int = 0
    message: str = ""
