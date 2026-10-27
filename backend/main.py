"""
SIH26261 – AI-Powered Application Validation, Document Authentication
& Regulatory Compliance Verification

Main FastAPI application with all API endpoints.
"""
import os
import json
import shutil
import hashlib
import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from database import get_db, init_db
from models import Application, Document, Finding, RuleResult, AuditLog
from schemas import (
    ApplicationCreate, ApplicationResponse, ApplicationListItem,
    DocumentResponse, HashVerifyResponse, FindingResponse,
    RuleResultResponse, ApplicationReport, DecisionRequest,
    DecisionResponse, PreValidationResult, ProcessingResult,
)

# ── Setup ────────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s")
logger = logging.getLogger("sih26261")

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title="SIH26261 – AICTE Smart Verification",
    description="AI-Powered Application Validation, Document Authentication & Regulatory Compliance Verification",
    version="1.0.0-prototype",
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("Database initialized")


# ── Helpers ──────────────────────────────────────────────────────────────────

def _load_json(filename: str) -> dict:
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _app_upload_dir(app_id: int) -> str:
    d = os.path.join(UPLOAD_DIR, str(app_id))
    os.makedirs(d, exist_ok=True)
    return d


def _to_dict(obj) -> dict:
    """Convert an ORM object's relevant columns to a plain dict."""
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


# ── 1  Applications ─────────────────────────────────────────────────────────

@app.post("/applications", response_model=ApplicationResponse, status_code=201)
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)):
    """Create a new application with form data."""
    from modules.intake import validate_application

    app_data = payload.model_dump()
    validation = validate_application(app_data)
    if not validation["passed"]:
        raise HTTPException(status_code=422, detail={
            "message": "Application pre-validation failed",
            "issues": validation["issues"],
        })

    record = Application(**app_data)
    db.add(record)
    db.commit()
    db.refresh(record)
    logger.info("Application %d created for %s", record.id, record.institution_name)
    return record


@app.get("/applications", response_model=list[ApplicationListItem])
def list_applications(
    status: Optional[str] = None,
    route: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Officer queue – list all applications, optionally filtered."""
    q = db.query(Application)
    if status:
        q = q.filter(Application.status == status)
    if route:
        q = q.filter(Application.route == route)
    return q.order_by(Application.created_at.desc()).all()


@app.get("/applications/{app_id}", response_model=ApplicationResponse)
def get_application(app_id: int, db: Session = Depends(get_db)):
    record = db.query(Application).filter(Application.id == app_id).first()
    if not record:
        raise HTTPException(404, "Application not found")
    return record


@app.get("/applications/{app_id}/status")
def get_application_status(app_id: int, db: Session = Depends(get_db)):
    """
    Applicant-facing status lookup.
    Deliberately returns NO scores, findings, rule results or routing - only
    the stage of the application and any message the officer chose to send.
    """
    record = db.query(Application).filter(Application.id == app_id).first()
    if not record:
        raise HTTPException(404, "Application not found")

    # Internal statuses -> what the applicant is allowed to see
    stage_map = {
        "submitted":  ("under_review", "Under Review"),
        "processing": ("under_review", "Under Review"),
        "processed":  ("under_review", "Under Review"),
        "deficiency": ("query_raised", "Query Raised"),
        "approved":   ("approved", "Approved"),
        "rejected":   ("rejected", "Rejected"),
    }
    code, label = stage_map.get(record.status, ("under_review", "Under Review"))

    messages = {
        "under_review": "Your application has been received and is being reviewed by an AICTE officer.",
        "query_raised": "The reviewing officer has raised a query. Please read the message below and respond with the requested clarification or documents.",
        "approved": "Your application has been approved.",
        "rejected": "Your application has been rejected.",
    }

    officer_message = None
    if code in ("query_raised", "approved", "rejected"):
        wanted = {"query_raised": "raise_deficiency", "approved": "approve", "rejected": "reject"}[code]
        latest = (
            db.query(AuditLog)
            .filter(AuditLog.application_id == app_id, AuditLog.action == wanted)
            .order_by(AuditLog.timestamp.desc())
            .first()
        )
        if latest and latest.details:
            officer_message = latest.details

    return {
        "application_id": record.id,
        "institution_name": record.institution_name,
        "application_type": record.application_type,
        "status_code": code,
        "status_label": label,
        "message": messages[code],
        "officer_message": officer_message,
        "submitted_on": record.created_at.isoformat() if record.created_at else None,
        "last_updated": record.updated_at.isoformat() if record.updated_at else None,
    }


# ── 2  Document Upload ───────────────────────────────────────────────────────

@app.post("/applications/{app_id}/documents", response_model=list[DocumentResponse])
async def upload_documents(
    app_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """Upload one or more documents for an application."""
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise HTTPException(404, "Application not found")

    from modules.integrity import compute_hash

    dest_dir = _app_upload_dir(app_id)
    created = []
    for f in files:
        file_path = os.path.join(dest_dir, f.filename)
        with open(file_path, "wb") as out:
            content = await f.read()
            out.write(content)

        file_hash = compute_hash(file_path)

        doc = Document(
            application_id=app_id,
            original_filename=f.filename,
            file_path=file_path,
            file_hash=file_hash,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        created.append(doc)
        logger.info("Document %d uploaded: %s (hash %s…)", doc.id, f.filename, file_hash[:12])

    return created


# ── 3  Full Processing Pipeline ──────────────────────────────────────────────

@app.post("/applications/{app_id}/process", response_model=ProcessingResult)
def process_application(app_id: int, db: Session = Depends(get_db)):
    """Run the complete processing pipeline on an application."""
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise HTTPException(404, "Application not found")

    application.status = "processing"
    db.commit()

    docs = db.query(Document).filter(Document.application_id == app_id).all()
    if not docs:
        raise HTTPException(422, "No documents uploaded for this application")

    from modules.intake import check_document_completeness
    from modules.ocr_extraction import process_document
    from modules.tamper_detection import detect_tampering
    from modules.cross_verification import cross_verify_documents
    from modules.rules_engine import run_compliance_check
    from modules.scoring import calculate_compliance_score, calculate_trust_score, determine_route

    registry = _load_json("mock_registry.json")
    app_dict = _to_dict(application)

    # ─ Step 1: Document completeness ─
    doc_types_uploaded = []
    for doc in docs:
        # Process each document (OCR, classify, extract)
        try:
            result = process_document(doc.file_path, doc.original_filename, app_context=app_dict)
            doc.doc_type = result.get("doc_type")
            doc.ocr_text = result.get("ocr_text", "")
            doc.fields_json = result.get("fields", {})
            doc.classification_confidence = result.get("classification_confidence", 0.0)
            if doc.doc_type:
                doc_types_uploaded.append(doc.doc_type)
            db.commit()
            logger.info("Doc %d classified as %s (confidence %.2f)", doc.id, doc.doc_type, doc.classification_confidence or 0)
        except Exception as e:
            logger.error("OCR/extraction failed for doc %d: %s", doc.id, e)

    completeness = check_document_completeness([{"doc_type": dt} for dt in doc_types_uploaded])
    if completeness.get("missing_documents"):
        for md in completeness["missing_documents"]:
            finding = Finding(
                application_id=app_id,
                category="completeness",
                severity="high",
                description=f"Missing required document: {md}",
                evidence={"missing_type": md},
            )
            db.add(finding)
        db.commit()

    # ─ Step 2: Tamper detection ─
    tamper_scores = []
    for doc in docs:
        try:
            tamper_result = detect_tampering(doc.file_path)
            doc.tamper_score = tamper_result.get("tamper_score", 0.0)
            doc.tamper_details = tamper_result.get("details", {})
            doc.heatmap_path = tamper_result.get("heatmap_path")
            tamper_scores.append(doc.tamper_score)
            db.commit()
            logger.info("Doc %d tamper score: %.3f", doc.id, doc.tamper_score)
        except Exception as e:
            logger.error("Tamper detection failed for doc %d: %s", doc.id, e)
            tamper_scores.append(0.0)

    # ─ Step 3: Cross-verification ─
    docs_data = [_to_dict(d) for d in docs]
    try:
        cv_findings = cross_verify_documents(app_dict, docs_data, registry)
        for cvf in cv_findings:
            finding = Finding(
                application_id=app_id,
                category=cvf.get("category", "cross_verification"),
                severity=cvf.get("severity", "medium"),
                description=cvf["description"],
                evidence=cvf.get("evidence", {}),
            )
            db.add(finding)
        db.commit()
        logger.info("Cross-verification produced %d findings", len(cv_findings))
    except Exception as e:
        logger.error("Cross-verification failed: %s", e)
        cv_findings = []

    # ─ Step 4: Regulatory compliance ─
    try:
        rule_results = run_compliance_check(app_dict, docs_data, registry)
        for rr in rule_results:
            result_record = RuleResult(
                application_id=app_id,
                rule_id=rr["rule_id"],
                rule_description=rr.get("description", ""),
                status=rr["status"],
                evidence=rr.get("evidence", {}),
                clause_reference=rr.get("clause_reference", ""),
                clause_text=rr.get("clause_text", ""),
                severity=rr.get("severity", "minor"),
            )
            db.add(result_record)
        db.commit()
        logger.info("Compliance check: %d rule results", len(rule_results))
    except Exception as e:
        logger.error("Compliance check failed: %s", e)
        rule_results = []

    # ─ Step 5: Scoring ─
    all_findings = db.query(Finding).filter(Finding.application_id == app_id).all()
    findings_dicts = [_to_dict(f) for f in all_findings]

    compliance_score = calculate_compliance_score(rule_results)
    trust_score, deductions = calculate_trust_score(findings_dicts, tamper_scores)
    route = determine_route(trust_score, compliance_score)

    application.trust_score = round(trust_score, 1)
    application.compliance_score = round(compliance_score, 1)
    application.route = route
    application.status = "processed"
    db.commit()

    # Audit log
    audit = AuditLog(
        application_id=app_id,
        actor="system",
        action="process",
        details=json.dumps({
            "trust_score": application.trust_score,
            "compliance_score": application.compliance_score,
            "route": route,
            "deductions": deductions,
        }),
    )
    db.add(audit)
    db.commit()

    logger.info(
        "Application %d processed: trust=%.1f compliance=%.1f route=%s",
        app_id, trust_score, compliance_score, route,
    )

    return ProcessingResult(
        application_id=app_id,
        status="processed",
        trust_score=application.trust_score,
        compliance_score=application.compliance_score,
        route=route,
        findings_count=len(all_findings),
        rule_results_count=len(rule_results),
        message=f"Processing complete. Route: {route}",
    )


# ── 4  Report ────────────────────────────────────────────────────────────────

@app.get("/applications/{app_id}/report", response_model=ApplicationReport)
def get_report(app_id: int, db: Session = Depends(get_db)):
    """Full application report with scores, findings, and rule results."""
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise HTTPException(404, "Application not found")

    documents = db.query(Document).filter(Document.application_id == app_id).all()
    findings = db.query(Finding).filter(Finding.application_id == app_id).all()
    rule_results = db.query(RuleResult).filter(RuleResult.application_id == app_id).all()

    return ApplicationReport(
        application=application,
        documents=documents,
        findings=findings,
        rule_results=rule_results,
        score_breakdown={
            "trust_score": application.trust_score,
            "compliance_score": application.compliance_score,
            "route": application.route,
        },
    )


# ── 5  Heatmap ───────────────────────────────────────────────────────────────

@app.get("/documents/{doc_id}/heatmap")
def get_heatmap(doc_id: int, db: Session = Depends(get_db)):
    """Return the tamper-detection ELA heatmap image."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")
    if not doc.heatmap_path or not os.path.exists(doc.heatmap_path):
        raise HTTPException(404, "Heatmap not available for this document")
    return FileResponse(doc.heatmap_path, media_type="image/png")


# ── 6  Decision ──────────────────────────────────────────────────────────────

@app.post("/applications/{app_id}/decision", response_model=DecisionResponse)
def submit_decision(app_id: int, payload: DecisionRequest, db: Session = Depends(get_db)):
    """Officer decision: approve, reject, or raise deficiency."""
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise HTTPException(404, "Application not found")

    action_to_status = {
        "approve": "approved",
        "reject": "rejected",
        "raise_deficiency": "deficiency",
    }
    new_status = action_to_status[payload.action]
    application.status = new_status
    db.commit()

    deficiency_note = None
    if payload.action == "raise_deficiency":
        findings = db.query(Finding).filter(Finding.application_id == app_id).all()
        lines = [f"DEFICIENCY NOTICE – Application #{app_id}", "=" * 50, ""]
        lines.append(f"Institution: {application.institution_name}")
        lines.append(f"Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        lines.append("")
        lines.append("The following issues require resolution:")
        lines.append("")
        for i, f in enumerate(findings, 1):
            lines.append(f"  {i}. [{f.severity.upper()}] {f.description}")
        if payload.remarks:
            lines.append("")
            lines.append(f"Additional remarks: {payload.remarks}")
        deficiency_note = "\n".join(lines)

    audit = AuditLog(
        application_id=app_id,
        actor=payload.officer_id,
        action=payload.action,
        details=payload.remarks or deficiency_note or "",
    )
    db.add(audit)
    db.commit()

    logger.info("Application %d: %s by %s", app_id, payload.action, payload.officer_id)

    return DecisionResponse(
        application_id=app_id,
        action=payload.action,
        new_status=new_status,
        deficiency_note=deficiency_note,
        timestamp=datetime.utcnow(),
    )


# ── 7  Hash Verification ────────────────────────────────────────────────────

@app.get("/documents/{doc_id}/verify-hash", response_model=HashVerifyResponse)
def verify_hash(doc_id: int, db: Session = Depends(get_db)):
    """Recompute the SHA-256 hash of a document and compare with stored hash."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Document not found")

    from modules.integrity import verify_hash as _verify

    result = _verify(doc.file_path, doc.file_hash)
    return HashVerifyResponse(
        document_id=doc_id,
        original_hash=doc.file_hash,
        current_hash=result["current_hash"],
        status=result["status"],
    )


# ── 8  Audit Log ─────────────────────────────────────────────────────────────

@app.get("/applications/{app_id}/audit-log")
def get_audit_log(app_id: int, db: Session = Depends(get_db)):
    logs = db.query(AuditLog).filter(AuditLog.application_id == app_id).order_by(AuditLog.timestamp.desc()).all()
    return [
        {
            "id": l.id,
            "actor": l.actor,
            "action": l.action,
            "details": l.details,
            "timestamp": l.timestamp.isoformat() if l.timestamp else None,
        }
        for l in logs
    ]


# ── 9  Serve uploaded files ─────────────────────────────────────────────────

@app.get("/uploads/{app_id}/{filename}")
def serve_upload(app_id: int, filename: str):
    file_path = os.path.join(UPLOAD_DIR, str(app_id), filename)
    if not os.path.exists(file_path):
        raise HTTPException(404, "File not found")
    return FileResponse(file_path)


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
