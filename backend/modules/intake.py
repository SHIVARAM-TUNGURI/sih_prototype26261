"""
Application Intake & Pre-validation Module.

Validates application data for completeness and correctness before
full processing begins. Checks mandatory fields, format constraints,
logical rules, and document completeness.
"""
import re
import logging
from datetime import datetime, date
from typing import Any

logger = logging.getLogger(__name__)

# Required fields and their human-readable labels
MANDATORY_FIELDS = {
    "institution_name": "Institution Name",
    "trust_name": "Trust/Society Name",
    "address": "Address",
    "pin_code": "PIN Code",
    "land_area_acres": "Land Area (acres)",
    "proposed_courses": "Proposed Courses",
    "total_intake": "Total Intake",
    "faculty_count": "Faculty Count",
    "application_date": "Application Date",
}

# Required document types for a complete application
REQUIRED_DOCUMENTS = [
    "land_deed",
    "trust_certificate",
    "noc",
    "faculty_list",
]


def validate_application(app_data: dict[str, Any]) -> dict[str, Any]:
    """
    Validate application data for mandatory fields, format, and logical rules.

    Args:
        app_data: Dictionary of application form data.

    Returns:
        Dictionary with keys:
            - passed (bool): True if all validations passed.
            - issues (list[str]): Human-readable list of issues found.
            - missing_documents (list[str]): Always empty from this function
              (document check is separate).
    """
    issues: list[str] = []

    try:
        # ── 1. Mandatory field presence ──────────────────────────────────
        for field, label in MANDATORY_FIELDS.items():
            value = app_data.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                issues.append(f"Missing mandatory field: {label}")

        # If critical fields are missing, return early
        if issues:
            logger.info("Pre-validation failed: %d missing fields", len(issues))
            return {"passed": False, "issues": issues, "missing_documents": []}

        # ── 2. Format validation ─────────────────────────────────────────

        # PIN code must be exactly 6 digits
        pin_code = str(app_data.get("pin_code", ""))
        if not re.match(r"^\d{6}$", pin_code):
            issues.append(
                f"PIN code must be exactly 6 digits, got: '{pin_code}'"
            )

        # Application date must be in YYYY-MM-DD format
        app_date_str = str(app_data.get("application_date", ""))
        app_date: date | None = None
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", app_date_str):
            issues.append(
                f"Application date must be in YYYY-MM-DD format, got: '{app_date_str}'"
            )
        else:
            try:
                app_date = datetime.strptime(app_date_str, "%Y-%m-%d").date()
            except ValueError:
                issues.append(
                    f"Application date is not a valid date: '{app_date_str}'"
                )

        # Total intake must be positive integer
        total_intake = app_data.get("total_intake", 0)
        try:
            total_intake = int(total_intake)
            if total_intake <= 0:
                issues.append("Total intake must be greater than 0")
        except (ValueError, TypeError):
            issues.append(f"Total intake must be a valid integer, got: '{total_intake}'")

        # Faculty count must be positive integer
        faculty_count = app_data.get("faculty_count", 0)
        try:
            faculty_count = int(faculty_count)
            if faculty_count <= 0:
                issues.append("Faculty count must be greater than 0")
        except (ValueError, TypeError):
            issues.append(
                f"Faculty count must be a valid integer, got: '{faculty_count}'"
            )

        # ── 3. Logical rules ─────────────────────────────────────────────

        # Application date must not be in the future
        if app_date is not None and app_date > date.today():
            issues.append("Application date cannot be in the future")

        # Land area must be positive
        land_area = app_data.get("land_area_acres", 0)
        try:
            land_area = float(land_area)
            if land_area <= 0:
                issues.append("Land area must be greater than 0 acres")
        except (ValueError, TypeError):
            issues.append(
                f"Land area must be a valid number, got: '{land_area}'"
            )

        # Institution name length sanity check
        inst_name = str(app_data.get("institution_name", ""))
        if len(inst_name) < 3:
            issues.append("Institution name is too short (minimum 3 characters)")

        passed = len(issues) == 0
        if passed:
            logger.info("Pre-validation passed for '%s'", inst_name)
        else:
            logger.info(
                "Pre-validation found %d issues for '%s'",
                len(issues),
                inst_name,
            )

        return {"passed": passed, "issues": issues, "missing_documents": []}

    except Exception as e:
        logger.error("Unexpected error during application validation: %s", e)
        return {
            "passed": False,
            "issues": [f"Internal validation error: {str(e)}"],
            "missing_documents": [],
        }


def check_document_completeness(documents: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Check whether all required document types have been uploaded.

    Args:
        documents: List of document metadata dicts, each expected to have
                   a 'doc_type' key (or 'type', 'document_type').

    Returns:
        Dictionary with keys:
            - passed (bool): True if no documents are missing.
            - issues (list[str]): Human-readable list of issues.
            - missing_documents (list[str]): List of missing document type identifiers.
    """
    try:
        # Extract document types from the uploaded list
        uploaded_types: set[str] = set()
        for doc in documents:
            doc_type = (
                doc.get("doc_type")
                or doc.get("type")
                or doc.get("document_type")
                or ""
            )
            if doc_type:
                uploaded_types.add(doc_type.lower().strip())

        # Determine which required documents are missing
        missing: list[str] = [
            req for req in REQUIRED_DOCUMENTS if req not in uploaded_types
        ]

        issues: list[str] = []
        for m in missing:
            label = m.replace("_", " ").title()
            issues.append(f"Required document missing: {label}")

        passed = len(missing) == 0
        if passed:
            logger.info("Document completeness check passed")
        else:
            logger.info("Missing documents: %s", missing)

        return {"passed": passed, "issues": issues, "missing_documents": missing}

    except Exception as e:
        logger.error("Error checking document completeness: %s", e)
        return {
            "passed": False,
            "issues": [f"Error checking documents: {str(e)}"],
            "missing_documents": list(REQUIRED_DOCUMENTS),
        }
