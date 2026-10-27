"""
Scoring & Risk Routing Module.

Computes compliance scores, trust scores, and determines the review
route (fast-track / standard / senior-review) for each application.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Weight multipliers for rule severity levels
SEVERITY_WEIGHTS: dict[str, int] = {
    "critical": 3,
    "major": 2,
    "minor": 1,
}

# Trust-score penalty amounts
PENALTY_TAMPER_FLAG = 30
PENALTY_NAME_MISMATCH = 15
PENALTY_AREA_MISMATCH = 15
PENALTY_REGISTRY_FAILURE = 20
PENALTY_FACULTY_CONFLICT = 10


def calculate_compliance_score(rule_results: list[dict[str, Any]]) -> float:
    """
    Calculate a weighted compliance score based on rule evaluation results.

    Each rule has a severity (critical=3×, major=2×, minor=1×).
    Score = (weighted_passed / total_weight) × 100.

    Args:
        rule_results: List of dicts, each with at least:
            - status (str): "compliant", "non_compliant", or "needs_clarification"
            - severity (str): "critical", "major", or "minor"

    Returns:
        Compliance score from 0.0 to 100.0.
    """
    try:
        if not rule_results:
            logger.warning("No rule results to score — returning 100.0")
            return 100.0

        total_weight = 0.0
        passed_weight = 0.0

        for result in rule_results:
            severity = result.get("severity", "minor")
            weight = SEVERITY_WEIGHTS.get(severity, 1)
            total_weight += weight

            status = result.get("status", "non_compliant")
            if status == "compliant":
                passed_weight += weight
            elif status == "needs_clarification":
                # Partial credit for items that need clarification
                passed_weight += weight * 0.5

        if total_weight == 0:
            return 100.0

        score = (passed_weight / total_weight) * 100.0
        score = round(min(max(score, 0.0), 100.0), 2)

        logger.info(
            "Compliance score: %.2f (passed_weight=%.1f / total_weight=%.1f)",
            score,
            passed_weight,
            total_weight,
        )
        return score

    except Exception as e:
        logger.error("Error calculating compliance score: %s", e)
        return 0.0


def calculate_trust_score(
    findings: list[dict[str, Any]],
    tamper_scores: list[float],
) -> tuple[float, list[dict[str, str]]]:
    """
    Calculate a trust score starting from 100, applying penalties for
    document tampering, cross-verification mismatches, and registry failures.

    Penalty schedule:
        - Tamper flag (tamper_score > 0.4):  -30
        - Name mismatch:                     -15
        - Area mismatch:                     -15
        - Registry lookup failure:           -20
        - Faculty conflict (each):           -10

    Args:
        findings: List of cross-verification finding dicts, each with
                  'category' and 'severity' keys.
        tamper_scores: List of tamper scores (0.0–1.0) for each document.

    Returns:
        Tuple of (trust_score, deductions) where deductions is a list of
        dicts with 'penalty', 'reason', and 'amount' keys.
    """
    try:
        score = 100.0
        deductions: list[dict[str, str]] = []

        # ── Tamper penalties ─────────────────────────────────────────────
        tamper_flagged = any(s > 0.4 for s in tamper_scores)
        if tamper_flagged:
            max_tamper = max(tamper_scores) if tamper_scores else 0.0
            score -= PENALTY_TAMPER_FLAG
            deductions.append({
                "penalty": "tamper_flag",
                "reason": f"Document tampering detected (max score: {max_tamper:.2f})",
                "amount": str(PENALTY_TAMPER_FLAG),
            })

        # ── Cross-verification penalties ─────────────────────────────────
        for finding in findings:
            category = finding.get("category", "").lower()
            severity = finding.get("severity", "").lower()

            if "name" in category and "mismatch" in category:
                score -= PENALTY_NAME_MISMATCH
                deductions.append({
                    "penalty": "name_mismatch",
                    "reason": finding.get("description", "Name mismatch across documents"),
                    "amount": str(PENALTY_NAME_MISMATCH),
                })

            elif "area" in category and "mismatch" in category:
                score -= PENALTY_AREA_MISMATCH
                deductions.append({
                    "penalty": "area_mismatch",
                    "reason": finding.get("description", "Land area mismatch"),
                    "amount": str(PENALTY_AREA_MISMATCH),
                })

            elif "registry" in category:
                score -= PENALTY_REGISTRY_FAILURE
                deductions.append({
                    "penalty": "registry_failure",
                    "reason": finding.get("description", "Registry lookup failed"),
                    "amount": str(PENALTY_REGISTRY_FAILURE),
                })

            elif "faculty" in category and ("conflict" in category or "dual" in category):
                score -= PENALTY_FACULTY_CONFLICT
                deductions.append({
                    "penalty": "faculty_conflict",
                    "reason": finding.get("description", "Faculty dual employment detected"),
                    "amount": str(PENALTY_FACULTY_CONFLICT),
                })

        # Clamp to [0, 100]
        score = round(min(max(score, 0.0), 100.0), 2)

        logger.info(
            "Trust score: %.2f (%d deductions applied)",
            score,
            len(deductions),
        )
        return score, deductions

    except Exception as e:
        logger.error("Error calculating trust score: %s", e)
        return 0.0, [{"penalty": "error", "reason": str(e), "amount": "100"}]


def determine_route(trust_score: float, compliance_score: float) -> str:
    """
    Determine the review route based on the average of trust and compliance scores.

    Route thresholds:
        - >= 80: "fast-track"
        - 50–79: "standard"
        - < 50:  "senior-review"

    Args:
        trust_score: Trust score (0–100).
        compliance_score: Compliance score (0–100).

    Returns:
        Route string: "fast-track", "standard", or "senior-review".
    """
    try:
        avg_score = (trust_score + compliance_score) / 2.0

        if avg_score >= 80:
            route = "fast-track"
        elif avg_score >= 50:
            route = "standard"
        else:
            route = "senior-review"

        logger.info(
            "Route determination: trust=%.2f, compliance=%.2f, avg=%.2f → %s",
            trust_score,
            compliance_score,
            avg_score,
            route,
        )
        return route

    except Exception as e:
        logger.error("Error determining route: %s", e)
        return "senior-review"
