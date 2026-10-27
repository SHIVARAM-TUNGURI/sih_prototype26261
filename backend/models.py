"""
SQLAlchemy ORM models for the SIH26261 prototype.

Tables:
  - applications: Core application records
  - documents: Uploaded documents with OCR results and tamper scores
  - findings: Cross-verification and validation findings
  - rule_results: Regulatory compliance check outcomes
  - audit_log: Officer actions audit trail
"""
import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from database import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    institution_name = Column(String(500), nullable=False)
    trust_name = Column(String(500), nullable=False)
    address = Column(Text)
    pin_code = Column(String(10))
    land_area_acres = Column(Float)
    proposed_courses = Column(Text)  # comma-separated
    total_intake = Column(Integer)
    faculty_count = Column(Integer)
    application_date = Column(String(20))
    application_type = Column(String(100), default="New Engineering Institution Approval")
    status = Column(String(50), default="submitted")  # submitted, processing, processed, approved, rejected, deficiency
    trust_score = Column(Float, default=None)
    compliance_score = Column(Float, default=None)
    route = Column(String(50), default=None)  # fast-track, standard, senior-review
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    documents = relationship("Document", back_populates="application", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="application", cascade="all, delete-orphan")
    rule_results = relationship("RuleResult", back_populates="application", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="application", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    doc_type = Column(String(100))  # land_deed, trust_certificate, noc, faculty_list
    original_filename = Column(String(500))
    file_path = Column(String(1000))
    file_hash = Column(String(64))  # SHA-256
    ocr_text = Column(Text)
    fields_json = Column(JSON)  # extracted structured fields
    classification_confidence = Column(Float)
    tamper_score = Column(Float)  # 0.0 (clean) to 1.0 (definitely tampered)
    tamper_details = Column(JSON)  # detailed tamper analysis results
    heatmap_path = Column(String(1000))  # path to ELA heatmap image
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    application = relationship("Application", back_populates="documents")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    category = Column(String(100))  # cross_verification, tamper, completeness
    severity = Column(String(20))  # high, medium, low
    description = Column(Text)
    evidence = Column(JSON)  # supporting data
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    application = relationship("Application", back_populates="findings")


class RuleResult(Base):
    __tablename__ = "rule_results"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    rule_id = Column(String(20))
    rule_description = Column(Text)
    status = Column(String(30))  # compliant, non_compliant, needs_clarification
    evidence = Column(JSON)
    clause_reference = Column(Text)
    clause_text = Column(Text)
    severity = Column(String(20))  # critical, major, minor
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    application = relationship("Application", back_populates="rule_results")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    actor = Column(String(200))  # officer name/ID
    action = Column(String(50))  # approve, reject, raise_deficiency, process
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    application = relationship("Application", back_populates="audit_logs")
