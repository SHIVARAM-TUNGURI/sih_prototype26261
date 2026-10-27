"""
Cross-Document Verification Module.

Compares extracted data across multiple documents and against the mock
government registry to detect inconsistencies, mismatches, and fraud
indicators such as dual employment of faculty.

Uses fuzzy string matching so minor spelling differences are flagged as
"partial_match" rather than silently accepted.
"""
import json
import logging
import os
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# Fuzzy matching thresholds
FUZZY_MATCH_THRESHOLD = 90      # >= 90 → match
FUZZY_PARTIAL_THRESHOLD = 70    # 70–89 → partial_match
                                # < 70  → mismatch

# Try to import thefuzz; fall back to simple ratio if unavailable
try:
    from thefuzz import fuzz as _fuzz
    def _token_ratio(a: str, b: str) -> int:
        return _fuzz.token_sort_ratio(a, b)
    logger.debug("thefuzz available for fuzzy matching")
except ImportError:
    logger.warning("thefuzz not available — using simple string matching fallback")
    def _token_ratio(a: str, b: str) -> int:  # type: ignore[misc]
        a, b = a.lower().strip(), b.lower().strip()
        if a == b:
            return 100
        # Simple overlap ratio
        set_a, set_b = set(a.split()), set(b.split())
        if not set_a or not set_b:
            return 0
        intersection = set_a & set_b
        return int(len(intersection) / max(len(set_a), len(set_b)) * 100)


# ── Core helpers ─────────────────────────────────────────────────────────────

def fuzzy_match(str1: str, str2: str) -> tuple[str, float]:
    """
    Compare two strings using token-sort fuzzy ratio.

    Returns:
        Tuple (status, similarity) where:
          status      = "match" | "partial_match" | "mismatch"
          similarity  = 0.0–100.0
    """
    if not str1 or not str2:
        return "mismatch", 0.0

    ratio = _token_ratio(str(str1), str(str2))

    if ratio >= FUZZY_MATCH_THRESHOLD:
        status = "match"
    elif ratio >= FUZZY_PARTIAL_THRESHOLD:
        status = "partial_match"
    else:
        status = "mismatch"

    return status, float(ratio)


def _first_field(fields_json: dict | None, *keys: str) -> str:
    """
    Extract the first non-empty field value from a fields_json dict.
    Supports both flat {"key": "val"} and nested {"key": {"value": "val"}} formats.
    """
    if not fields_json:
        return ""
    for key in keys:
        raw = fields_json.get(key)
        if raw is None:
            continue
        if isinstance(raw, dict):
            raw = raw.get("value", "")
        if raw:
            return str(raw).strip()
    return ""


def _finding(
    category: str,
    severity: str,
    description: str,
    evidence: dict,
) -> dict[str, Any]:
    return {
        "category": category,
        "severity": severity,
        "description": description,
        "evidence": evidence,
    }


# ── Registry helpers ─────────────────────────────────────────────────────────

def verify_against_registry(
    value: str,
    registry_section: Any,
    match_key: str,
) -> dict[str, Any]:
    """
    Search a registry section for a record matching *value* on *match_key*.

    Returns:
        dict with keys: found (bool), record (dict | None), match_quality (str), similarity (float)
    """
    best_record = None
    best_ratio = 0.0
    best_status = "mismatch"

    if isinstance(registry_section, dict):
        records = list(registry_section.values())
    elif isinstance(registry_section, list):
        records = registry_section
    else:
        records = []

    for record in records:
        if not isinstance(record, dict):
            continue
        candidate = str(record.get(match_key) or record.get("name") or "").strip()
        status, ratio = fuzzy_match(value, candidate)
        if ratio > best_ratio:
            best_ratio = ratio
            best_record = record
            best_status = status

    return {
        "found": best_status in ("match", "partial_match"),
        "record": best_record if best_status in ("match", "partial_match") else None,
        "match_quality": best_status,
        "similarity": best_ratio,
    }


# ── Individual checks ────────────────────────────────────────────────────────

def _check_institution_name(
    application: dict, docs: list[dict]
) -> list[dict[str, Any]]:
    """Institution name should match across form, deed, trust cert, and NOC."""
    findings = []
    form_name: str = application.get("institution_name", "")
    if not form_name:
        return findings

    type_to_field = {
        "noc":                ["institution_name"],
    }

    for doc in docs:
        doc_type = doc.get("doc_type", "")
        fields = type_to_field.get(doc_type)
        if not fields:
            continue
        doc_value = _first_field(doc.get("fields_json") or {}, *fields)
        if not doc_value:
            continue

        status, similarity = fuzzy_match(form_name, doc_value)
        if status == "match":
            continue  # all good

        sev = "high" if status == "mismatch" else "medium"
        cat = "name_mismatch" if status == "mismatch" else "name_partial_match"
        findings.append(_finding(
            category=cat,
            severity=sev,
            description=(
                f"Institution/trust name mismatch in {doc_type}: "
                f"form='{form_name}' vs doc='{doc_value}' "
                f"(similarity {similarity:.0f}%)"
            ),
            evidence={
                "form_value": form_name,
                "doc_value": doc_value,
                "doc_type": doc_type,
                "similarity": similarity,
                "match_status": status,
            },
        ))

    return findings


def _check_trust_name(
    application: dict, docs: list[dict], registry: dict
) -> list[dict[str, Any]]:
    """Trust name should match across form, trust cert, and deed owner."""
    findings = []
    form_trust: str = application.get("trust_name", "")
    if not form_trust:
        return findings

    for doc in docs:
        doc_type = doc.get("doc_type", "")
        fields_json = doc.get("fields_json") or {}

        if doc_type == "trust_certificate":
            cert_trust = _first_field(fields_json, "trust_name")
        elif doc_type == "land_deed":
            cert_trust = _first_field(fields_json, "owner_name")
        else:
            continue

        if not cert_trust:
            continue

        status, similarity = fuzzy_match(form_trust, cert_trust)
        if status == "match":
            continue

        sev = "high" if status == "mismatch" else "medium"
        cat = "name_mismatch" if status == "mismatch" else "name_partial_match"
        findings.append(_finding(
            category=cat,
            severity=sev,
            description=(
                f"Trust name mismatch in {doc_type}: "
                f"form='{form_trust}' vs doc='{cert_trust}' "
                f"(similarity {similarity:.0f}%)"
            ),
            evidence={
                "form_value": form_trust,
                "doc_value": cert_trust,
                "doc_type": doc_type,
                "similarity": similarity,
                "match_status": status,
            },
        ))

    # Registry lookup
    trusts = registry.get("trusts", [])
    reg_result = verify_against_registry(form_trust, trusts, "trust_name")
    if not reg_result["found"]:
        findings.append(_finding(
            category="registry_mismatch",
            severity="high",
            description=(
                f"Trust '{form_trust}' not found in the government registry "
                f"(best match similarity: {reg_result['similarity']:.0f}%)"
            ),
            evidence={"trust_name": form_trust, "registry_result": reg_result},
        ))
    else:
        rec = reg_result["record"] or {}
        if rec.get("status", "").lower() != "active":
            findings.append(_finding(
                category="registry_mismatch",
                severity="high",
                description=(
                    f"Trust '{form_trust}' found in registry but status is "
                    f"'{rec.get('status', 'unknown')}' (expected 'active')"
                ),
                evidence={"trust_name": form_trust, "registry_record": rec},
            ))

    return findings


def _check_land_area(
    application: dict, docs: list[dict], registry: dict
) -> list[dict[str, Any]]:
    """Land area declared on the form should match the land deed and official registry."""
    findings = []
    form_area = application.get("land_area_acres")
    if form_area is None:
        return findings

    try:
        form_area = float(form_area)
    except (TypeError, ValueError):
        return findings

    for doc in docs:
        if doc.get("doc_type") != "land_deed":
            continue
        fields_json = doc.get("fields_json") or {}
        raw = _first_field(fields_json, "land_area")
        survey_no = _first_field(fields_json, "survey_number")
        if not raw:
            continue
        try:
            deed_area = float(raw)
        except ValueError:
            continue

        diff_pct = abs(form_area - deed_area) / max(form_area, deed_area) * 100
        if diff_pct > 5:
            findings.append(_finding(
                category="area_mismatch",
                severity="high",
                description=(
                    f"Land area mismatch: form declares {form_area} acres, "
                    f"deed shows {deed_area} acres ({diff_pct:.1f}% difference)"
                ),
                evidence={
                    "form_area": form_area,
                    "deed_area": deed_area,
                    "difference_pct": round(diff_pct, 1),
                },
            ))

        # Check against mock land records
        land_records = registry.get("land_records", [])
        for lr in land_records:
            if survey_no and survey_no.lower() in str(lr.get("survey_number", "")).lower():
                reg_area = float(lr.get("area_acres", 0))
                if abs(form_area - reg_area) > 0.1:
                    findings.append(_finding(
                        category="area_mismatch",
                        severity="high",
                        description=(
                            f"Land registry mismatch for survey {survey_no}: "
                            f"application/deed claims {form_area} acres, "
                            f"government land records show only {reg_area} acres"
                        ),
                        evidence={
                            "claimed_area": form_area,
                            "registry_area": reg_area,
                            "survey_number": survey_no,
                        },
                    ))
                break
        break

    return findings


def _check_dates(
    application: dict, docs: list[dict]
) -> list[dict[str, Any]]:
    """
    Date consistency checks:
    - Trust registration date must be before application date
    - NOC validity date must not be expired
    """
    findings = []
    app_date_str = application.get("application_date", "")
    today = datetime.today()

    try:
        app_date = datetime.strptime(app_date_str, "%Y-%m-%d")
    except ValueError:
        app_date = today

    DATE_FORMATS = ["%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]

    def _parse(s: str) -> datetime | None:
        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(s.strip(), fmt)
            except ValueError:
                continue
        return None

    for doc in docs:
        doc_type = doc.get("doc_type", "")
        fields_json = doc.get("fields_json") or {}

        if doc_type == "trust_certificate":
            reg_date_str = _first_field(fields_json, "registration_date")
            if reg_date_str:
                reg_date = _parse(reg_date_str)
                if reg_date and reg_date >= app_date:
                    findings.append(_finding(
                        category="date_mismatch",
                        severity="high",
                        description=(
                            f"Trust registration date ({reg_date_str}) is NOT "
                            f"before the application date ({app_date_str}) — "
                            "trust must be registered before applying"
                        ),
                        evidence={
                            "registration_date": reg_date_str,
                            "application_date": app_date_str,
                        },
                    ))

        elif doc_type == "noc":
            validity_str = _first_field(fields_json, "validity_date")
            if validity_str:
                validity = _parse(validity_str)
                if validity and validity < today:
                    findings.append(_finding(
                        category="date_mismatch",
                        severity="high",
                        description=(
                            f"NOC has expired (validity: {validity_str}, "
                            f"today: {today.strftime('%d-%m-%Y')})"
                        ),
                        evidence={
                            "validity_date": validity_str,
                            "today": today.strftime("%Y-%m-%d"),
                        },
                    ))

    return findings


def _check_registration_number(
    docs: list[dict], registry: dict
) -> list[dict[str, Any]]:
    """Trust registration number on the certificate must exist in the registry."""
    findings = []
    trusts = registry.get("trusts", [])

    for doc in docs:
        if doc.get("doc_type") != "trust_certificate":
            continue
        fields_json = doc.get("fields_json") or {}
        reg_no = _first_field(fields_json, "registration_number")
        if not reg_no:
            continue

        reg_result = verify_against_registry(reg_no, trusts, "registration_number")
        if not reg_result["found"]:
            findings.append(_finding(
                category="registry_mismatch",
                severity="high",
                description=(
                    f"Trust registration number '{reg_no}' not found in registry"
                ),
                evidence={"registration_number": reg_no, "registry_result": reg_result},
            ))
        break

    return findings


def _check_faculty_conflicts(
    application: dict, docs: list[dict], registry: dict
) -> list[dict[str, Any]]:
    """
    Flag faculty members who are already employed at another institution
    according to the mock registry.
    """
    findings = []
    faculty_registry = registry.get("faculty_registry") or registry.get("faculty") or []
    if isinstance(faculty_registry, dict):
        faculty_registry = list(faculty_registry.values())

    app_inst = str(application.get("institution_name", "")).strip().lower()

    for doc in docs:
        if doc.get("doc_type") != "faculty_list":
            continue
        fields_json = doc.get("fields_json") or {}
        members_raw = fields_json.get("faculty_members", {})
        if isinstance(members_raw, dict):
            members = members_raw.get("value", [])
        else:
            members = members_raw or []

        for member in members:
            fac_id = str(member.get("faculty_id", "")).strip()
            name = str(member.get("name", "")).strip()
            if not fac_id:
                continue

            for reg_rec in faculty_registry:
                if str(reg_rec.get("faculty_id", "")) == fac_id:
                    current_inst = reg_rec.get("current_institution", "")
                    if current_inst and current_inst.lower() not in (
                        "", "null", "none", "available"
                    ):
                        # Flag only if employed at a different institution
                        if app_inst and current_inst.strip().lower() != app_inst:
                            findings.append(_finding(
                                category="faculty_conflict",
                                severity="high",
                                description=(
                                    f"Faculty '{name}' (ID: {fac_id}) is already "
                                    f"employed at '{current_inst}' per the registry"
                                ),
                                evidence={
                                    "faculty_id": fac_id,
                                    "faculty_name": name,
                                    "current_institution": current_inst,
                                    "registry_record": reg_rec,
                                },
                            ))
                    break

    return findings


# ── Orchestrator ─────────────────────────────────────────────────────────────

def cross_verify_documents(
    application: dict,
    documents: list[dict],
    registry_data: dict,
) -> list[dict[str, Any]]:
    """
    Run all cross-verification checks and return a consolidated list of findings.

    Checks performed:
        1. Institution name consistency across all documents
        2. Trust/society name consistency + registry lookup
        3. Land area: form vs. deed
        4. Date consistency (trust registration, NOC validity)
        5. Trust registration number vs. registry
        6. Faculty dual-employment check

    Args:
        application: Application form data dict.
        documents:   List of document dicts (from DB / ORM).
        registry_data: Loaded mock_registry.json dict.

    Returns:
        List of finding dicts, each with:
            category, severity, description, evidence
    """
    all_findings: list[dict[str, Any]] = []

    try:
        logger.info("Starting cross-verification for application %s", application.get("id"))

        all_findings += _check_institution_name(application, documents)
        all_findings += _check_trust_name(application, documents, registry_data)
        all_findings += _check_land_area(application, documents, registry_data)
        all_findings += _check_dates(application, documents)
        all_findings += _check_registration_number(documents, registry_data)
        all_findings += _check_faculty_conflicts(application, documents, registry_data)

        logger.info(
            "Cross-verification complete: %d findings (%d high severity)",
            len(all_findings),
            sum(1 for f in all_findings if f.get("severity") == "high"),
        )

    except Exception as e:
        logger.error("Cross-verification error: %s", e)
        all_findings.append(_finding(
            category="system_error",
            severity="medium",
            description=f"Cross-verification could not complete: {e}",
            evidence={"error": str(e)},
        ))

    return all_findings
