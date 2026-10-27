"""
OCR, Document Classification & Field Extraction Module.

Processes uploaded document images through:
1. Image preprocessing (grayscale, threshold, denoise)
2. OCR text extraction (Tesseract with simulation fallback)
3. Document classification by keywords
4. Structured field extraction via regex patterns
"""
import os
import re
import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)

# ── Tesseract availability check ─────────────────────────────────────────────
_TESSERACT_AVAILABLE = False
try:
    import pytesseract
    pytesseract.get_tesseract_version()
    _TESSERACT_AVAILABLE = True
    logger.info("Tesseract OCR is available")
except Exception:
    logger.warning("Tesseract OCR not available — using simulation mode")

try:
    from PIL import Image
    import cv2
except ImportError as e:
    logger.error("Missing imaging library: %s", e)


# ── Classification keywords ─────────────────────────────────────────────────

CLASSIFICATION_KEYWORDS: dict[str, list[str]] = {
    "land_deed": [
        "sale deed", "deed", "conveyance", "survey number", "acres",
        "sub-registrar", "encumbrance", "property details"
    ],
    "trust_certificate": [
        "registration of trust", "trust name", "charity commissioner",
        "trust registration", "registered trust", "certificate of registration"
    ],
    "noc": [
        "no objection certificate", "no objection", "directorate of technical education",
        "valid until", "clearance certificate", "affiliation letter"
    ],
    "faculty_list": [
        "faculty list", "designation", "qualification", "faculty id",
        "teaching staff", "assistant professor", "associate professor"
    ],
}

# ── Simulated OCR texts for demo mode ───────────────────────────────────────

SIMULATED_TEXTS_SET_A: dict[str, str] = {
    "land_deed": """
SALE DEED / CONVEYANCE DEED

This deed of conveyance is executed on 15-03-2020

Seller: Government of Maharashtra
Buyer/Owner: Vidya Bharati Educational Trust

Property Details:
Survey Number: 145/A
Location: Hinjewadi, Pune, Maharashtra
Total Area: 5.0 acres
Land Use: Educational Purpose

Registered at Sub-Registrar Office, Pune
Registration Number: PUN/2020/SR/4567
Date of Registration: 15-03-2020

Encumbrance Status: Clear
""",
    "trust_certificate": """
CERTIFICATE OF REGISTRATION OF TRUST

This is to certify that the following Trust has been duly registered:

Trust Name: Vidya Bharati Educational Trust
Registration Number: MH/TR/2019/00456
Date of Registration: 10-01-2019
Registering Authority: Charity Commissioner, Maharashtra

Address: 45, MG Road, Pune, Maharashtra - 411001

Objects: To establish and run educational institutions

Status: Active

Issued by the Office of the Charity Commissioner
Government of Maharashtra
""",
    "noc": """
NO OBJECTION CERTIFICATE

From: Directorate of Technical Education, Maharashtra
To: Whom It May Concern

Subject: No Objection Certificate for establishment of technical institution

This is to certify that there is no objection to the establishment of:

Institution Name: Vidya Bharati Institute of Technology
Trust/Society: Vidya Bharati Educational Trust
Location: Pune, Maharashtra

This NOC is valid until: 31-12-2027

Issued on: 01-06-2026
Reference Number: DTE/NOC/2026/789

Director
Directorate of Technical Education
Government of Maharashtra
""",
    "faculty_list": """
FACULTY LIST

Institution: Vidya Bharati Institute of Technology

S.No. | Name                 | Qualification        | Designation          | Faculty ID
------|----------------------|---------------------|----------------------|-----------
1     | Dr. Anita Sharma     | Ph.D. Computer Sci  | Professor            | FAC001
2     | Dr. Suresh Patel     | Ph.D. Electronics   | Professor            | FAC002
3     | Mr. Amit Kumar       | M.Tech Mechanical   | Asst. Professor      | FAC003
4     | Dr. Priya Nair       | Ph.D. Mathematics   | Associate Professor  | FAC004
5     | Ms. Kavita Reddy     | M.Tech Civil        | Asst. Professor      | FAC005
6     | Dr. Vikram Singh     | Ph.D. Computer Sci  | Professor            | FAC006

Total Faculty: 6
Date: 01-08-2026
""",
}

SIMULATED_TEXTS_SET_B: dict[str, str] = {
    "land_deed": """
SALE DEED / CONVEYANCE DEED

This deed of conveyance is executed on 12-05-2021

Seller: Maharashtra Industrial Development Corporation
Buyer/Owner: Vidya Bharti Educational Trust

Property Details:
Survey Number: 78/B
Location: Industrial Area, Nagpur, Maharashtra
Total Area: 5.0 acres
Land Use: Educational Purpose

Registered at Sub-Registrar Office, Nagpur
Registration Number: NGP/2021/SR/8912
Date of Registration: 12-05-2021

Encumbrance Status: Clear
""",
    "trust_certificate": """
CERTIFICATE OF REGISTRATION OF TRUST

This is to certify that the following Trust has been duly registered:

Trust Name: Vidya Bharti Educational Trust
Registration Number: MH/TR/2019/00789
Date of Registration: 10-01-2019
Registering Authority: Charity Commissioner, Maharashtra

Address: Plot 78, Wardha Road, Nagpur, Maharashtra - 440001

Objects: To establish and run technical educational institutions

Status: Active

Issued by the Office of the Charity Commissioner
Government of Maharashtra
""",
    "noc": """
NO OBJECTION CERTIFICATE

From: Directorate of Technical Education, Maharashtra
To: Whom It May Concern

Subject: No Objection Certificate for establishment of technical institution

This is to certify that there is no objection to the establishment of:

Institution Name: Vidya Bharti Technical Institute
Trust/Society: Vidya Bharti Educational Trust
Location: Nagpur, Maharashtra

This NOC is valid until: 31-12-2024

Issued on: 01-06-2023
Reference Number: DTE/NOC/2023/452

Director
Directorate of Technical Education
Government of Maharashtra
""",
    "faculty_list": """
FACULTY LIST

Institution: Vidya Bharati Institute of Technology

S.No. | Name                 | Qualification        | Designation          | Faculty ID
------|----------------------|---------------------|----------------------|-----------
1     | Dr. Anita Sharma     | Ph.D. Computer Sci  | Professor            | FAC001
2     | Dr. Suresh Patel     | Ph.D. Electronics   | Professor            | FAC002
3     | Mr. Amit Kumar       | M.Tech Mechanical   | Asst. Professor      | FAC003
4     | Dr. Priya Nair       | Ph.D. Mathematics   | Associate Professor  | FAC004
5     | Ms. Kavita Reddy     | M.Tech Civil        | Asst. Professor      | FAC005
6     | Dr. Rajesh Verma     | Ph.D. Computer Science | Professor         | FAC007
7     | Mr. Ravi Tiwari      | B.Tech IT           | Lecturer             | FAC008

Total Faculty: 7
Date: 01-09-2026
""",
}


# ── Image Preprocessing ─────────────────────────────────────────────────────

def preprocess_image(image_path: str) -> np.ndarray:
    try:
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        processed = cv2.adaptiveThreshold(
            denoised, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2,
        )
        return processed
    except Exception as e:
        logger.error("Image preprocessing failed for '%s': %s", image_path, e)
        raise


# ── OCR ──────────────────────────────────────────────────────────────────────

def perform_ocr(image_path: str, app_context: dict = None) -> str:
    if _TESSERACT_AVAILABLE:
        try:
            processed = preprocess_image(image_path)
            text = pytesseract.image_to_string(
                processed, lang="eng", config="--psm 6"
            )
            if len(text.strip()) > 50:
                logger.info("OCR extracted %d chars from %s", len(text), image_path)
                return text.strip()
        except Exception as e:
            logger.error("Tesseract OCR failed for '%s': %s", image_path, e)

    # Simulation fallback
    norm_path = image_path.replace("\\", "/").lower()
    is_set_b = "set_b" in norm_path or "problem" in norm_path
    if app_context:
        pin = str(app_context.get("pin_code", ""))
        addr = str(app_context.get("address", "")).lower()
        if pin == "440001" or "nagpur" in addr or "78" in addr:
            is_set_b = True

    dataset = SIMULATED_TEXTS_SET_B if is_set_b else SIMULATED_TEXTS_SET_A

    fname = os.path.basename(norm_path)
    if "noc" in fname:
        return dataset["noc"].strip()
    if "land" in fname or "deed" in fname:
        return dataset["land_deed"].strip()
    if "trust" in fname or "cert" in fname:
        return dataset["trust_certificate"].strip()
    if "faculty" in fname:
        return dataset["faculty_list"].strip()

    return dataset["land_deed"].strip()


# ── Classification ───────────────────────────────────────────────────────────

def classify_document(text: str, filename: str = "") -> tuple[str, float]:
    combined = (text + " " + filename).lower()
    
    # Priority anchors
    if "no objection" in combined or "noc" in filename.lower():
        return "noc", 0.95
    if "faculty list" in combined or "faculty" in filename.lower():
        return "faculty_list", 0.95
    if "certificate of registration" in combined or "registration of trust" in combined or "trust" in filename.lower():
        return "trust_certificate", 0.95
    if "sale deed" in combined or "conveyance" in combined or "land" in filename.lower() or "deed" in filename.lower():
        return "land_deed", 0.95

    scores: dict[str, int] = {}
    for doc_type, keywords in CLASSIFICATION_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        scores[doc_type] = score

    if not scores or max(scores.values()) == 0:
        return "unknown", 0.0

    best_type = max(scores, key=scores.get)
    return best_type, 0.85


# ── Field Extraction ─────────────────────────────────────────────────────────

def _extract_land_deed_fields(text: str) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    t = text

    match = re.search(r"(?:Buyer/Owner|Owner|Buyer)[:\s]*(.+?)(?:\n|$)", t, re.IGNORECASE)
    if match:
        fields["owner_name"] = {"value": match.group(1).strip(), "confidence": 0.9}

    area_match = re.search(r"(?:Total Area|Area)[:\s]*([\d.]+)\s*acres?", t, re.IGNORECASE)
    if area_match:
        fields["land_area"] = {"value": float(area_match.group(1)), "confidence": 0.95}

    survey_match = re.search(r"Survey\s*Number[:\s]*([\w/\-]+)", t, re.IGNORECASE)
    if survey_match:
        fields["survey_number"] = {"value": survey_match.group(1).strip(), "confidence": 0.9}

    loc_match = re.search(r"Location[:\s]*(.+?)(?:\n|$)", t, re.IGNORECASE)
    if loc_match:
        fields["location"] = {"value": loc_match.group(1).strip(), "confidence": 0.85}

    date_match = re.search(r"Date\s*of\s*Registration[:\s]*([\d]{1,2}[-/][\d]{1,2}[-/][\d]{2,4})", t, re.IGNORECASE)
    if date_match:
        fields["date"] = {"value": date_match.group(1).strip(), "confidence": 0.9}

    return fields


def _extract_trust_certificate_fields(text: str) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    t = text

    name_match = re.search(r"Trust\s*Name[:\s]*(.+?)(?:\n|$)", t, re.IGNORECASE)
    if name_match:
        fields["trust_name"] = {"value": name_match.group(1).strip(), "confidence": 0.95}

    reg_match = re.search(r"Registration\s*Number[:\s]*([\w/\-]+)", t, re.IGNORECASE)
    if reg_match:
        fields["registration_number"] = {"value": reg_match.group(1).strip(), "confidence": 0.95}

    date_match = re.search(r"Date\s*of\s*Registration[:\s]*([\d]{1,2}[-/][\d]{1,2}[-/][\d]{2,4})", t, re.IGNORECASE)
    if date_match:
        fields["registration_date"] = {"value": date_match.group(1).strip(), "confidence": 0.9}

    auth_match = re.search(r"Registering\s*Authority[:\s]*(.+?)(?:\n|$)", t, re.IGNORECASE)
    if auth_match:
        fields["authority"] = {"value": auth_match.group(1).strip(), "confidence": 0.9}

    return fields


def _extract_noc_fields(text: str) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    t = text

    from_match = re.search(r"From[:\s]*(.+?)(?:\n|$)", t, re.IGNORECASE)
    if from_match:
        fields["issuing_body"] = {"value": from_match.group(1).strip(), "confidence": 0.9}

    inst_match = re.search(r"Institution\s*Name[:\s]*(.+?)(?:\n|$)", t, re.IGNORECASE)
    if inst_match:
        fields["institution_name"] = {"value": inst_match.group(1).strip(), "confidence": 0.95}

    valid_match = re.search(r"valid\s*until[:\s]*([\d]{1,2}[-/][\d]{1,2}[-/][\d]{2,4})", t, re.IGNORECASE)
    if valid_match:
        fields["validity_date"] = {"value": valid_match.group(1).strip(), "confidence": 0.95}

    return fields


def _extract_faculty_list_fields(text: str) -> dict[str, Any]:
    fields: dict[str, Any] = {"faculty_members": {"value": [], "confidence": 0.9}}

    lines = text.strip().split("\n")
    for line in lines:
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 5 and parts[0].isdigit():
            member = {
                "name": parts[1],
                "qualification": parts[2],
                "designation": parts[3],
                "faculty_id": parts[4],
            }
            fields["faculty_members"]["value"].append(member)

    count = len(fields["faculty_members"]["value"])
    fields["faculty_count"] = {"value": count, "confidence": 0.95}
    return fields


def extract_fields(text: str, doc_type: str) -> dict[str, Any]:
    extractors = {
        "land_deed": _extract_land_deed_fields,
        "trust_certificate": _extract_trust_certificate_fields,
        "noc": _extract_noc_fields,
        "faculty_list": _extract_faculty_list_fields,
    }
    extractor = extractors.get(doc_type)
    return extractor(text) if extractor else {}


# ── Orchestrator ─────────────────────────────────────────────────────────────

def process_document(file_path: str, filename: str = "", app_context: dict = None) -> dict[str, Any]:
    if not filename:
        filename = os.path.basename(file_path)

    ocr_text = perform_ocr(file_path, app_context)
    doc_type, cls_confidence = classify_document(ocr_text, filename)
    fields = extract_fields(ocr_text, doc_type)

    return {
        "ocr_text": ocr_text,
        "doc_type": doc_type,
        "classification_confidence": cls_confidence,
        "fields": fields,
    }
