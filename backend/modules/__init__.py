"""
Processing modules for the SIH26261 prototype.
"""
from modules.intake import validate_application, check_document_completeness
from modules.ocr_extraction import process_document
from modules.tamper_detection import detect_tampering
from modules.cross_verification import cross_verify_documents
from modules.rules_engine import run_compliance_check, load_rules, load_clauses
from modules.scoring import calculate_compliance_score, calculate_trust_score, determine_route
from modules.integrity import compute_hash, verify_hash
