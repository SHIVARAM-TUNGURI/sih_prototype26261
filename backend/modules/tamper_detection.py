"""
Document Authentication – Tamper Detection Module.

Detects document tampering via:
1. Error Level Analysis (ELA) – highlights inconsistently compressed regions
2. Metadata inspection – flags editing software, date mismatches
3. Text-region consistency analysis – font/alignment anomalies

Produces a tamper score (0.0–1.0) and an ELA heatmap image.
"""
import os
import io
import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

try:
    from PIL import Image, ExifTags
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False
    logger.warning("Pillow not available — tamper detection will be limited")

try:
    import cv2
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False
    logger.warning("OpenCV not available — ELA will be limited")


# ── Error Level Analysis ─────────────────────────────────────────────────────

def error_level_analysis(
    image_path: str, quality: int = 90
) -> tuple[np.ndarray | None, float]:
    """
    Perform Error Level Analysis on an image.

    Re-saves the image at a given JPEG quality, then computes the absolute
    difference between the original and the re-saved version. Edited regions
    tend to show higher error levels.

    Args:
        image_path: Path to the image file.
        quality: JPEG quality for re-compression (default 90).

    Returns:
        Tuple of (heatmap_array, tamper_score).
        heatmap_array is a numpy array (or None if processing fails).
        tamper_score is 0.0 (clean) to 1.0 (likely tampered).
    """
    if not _PIL_AVAILABLE or not _CV2_AVAILABLE:
        logger.warning("ELA requires Pillow and OpenCV")
        return None, 0.0

    try:
        # Load original
        original = Image.open(image_path).convert("RGB")
        original_array = np.array(original)

        # Re-save at specified quality
        buffer = io.BytesIO()
        original.save(buffer, format="JPEG", quality=quality)
        buffer.seek(0)
        resaved = Image.open(buffer).convert("RGB")
        resaved_array = np.array(resaved)

        # Compute absolute difference
        diff = np.abs(original_array.astype(np.int16) - resaved_array.astype(np.int16))

        # Amplify differences for visibility (scale by 10x, cap at 255)
        amplified = np.clip(diff * 10, 0, 255).astype(np.uint8)

        # Compute tamper score from mean intensity of the difference
        mean_diff = np.mean(diff)
        # Normalize to 0–1 range; typical values for clean images: 2–8,
        # tampered regions: 15–40+
        tamper_score = min(mean_diff / 30.0, 1.0)

        logger.info(
            "ELA complete for '%s': mean_diff=%.2f, tamper_score=%.3f",
            image_path, mean_diff, tamper_score,
        )
        return amplified, round(tamper_score, 4)

    except Exception as e:
        logger.error("ELA failed for '%s': %s", image_path, e)
        return None, 0.0


# ── Metadata Check ───────────────────────────────────────────────────────────

# Software tags that indicate document editing
EDITING_SOFTWARE_TAGS = [
    "photoshop", "gimp", "paint.net", "adobe", "illustrator",
    "corel", "inkscape", "pixlr", "canva", "affinity",
    "snapseed", "lightroom", "capture one",
]


def check_metadata(image_path: str) -> dict[str, Any]:
    """
    Inspect image metadata (EXIF) for signs of tampering.

    Flags:
    - Editing software tags in EXIF data
    - Creation and modification date mismatches
    - Missing metadata on supposed scanned documents

    Args:
        image_path: Path to the image file.

    Returns:
        Dictionary with:
            - flags (list[str]): Warning messages
            - editing_software (str | None): Detected editing software
            - dates (dict): Creation and modification dates found
            - suspicious (bool): Whether metadata raises concerns
    """
    result: dict[str, Any] = {
        "flags": [],
        "editing_software": None,
        "dates": {},
        "suspicious": False,
    }

    if not _PIL_AVAILABLE:
        result["flags"].append("Cannot check metadata — Pillow not available")
        return result

    try:
        img = Image.open(image_path)
        exif_data = img.getexif() if hasattr(img, "getexif") else {}

        # Collect metadata from EXIF and PNG text chunks
        tag_dict: dict[str, str] = {}
        if exif_data:
            for tag_id, value in exif_data.items():
                tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                tag_dict[tag_name] = str(value)

        # Check PNG text chunks
        if hasattr(img, "text") and img.text:
            for k, v in img.text.items():
                tag_dict[str(k)] = str(v)
        if hasattr(img, "info") and img.info:
            for k, v in img.info.items():
                if isinstance(v, (str, bytes)):
                    tag_dict[str(k)] = str(v)

        # Check for editing software
        for key in ("Software", "software", "Comment", "comment", "Source"):
            val = tag_dict.get(key, "").lower()
            for sw in EDITING_SOFTWARE_TAGS:
                if sw in val:
                    result["editing_software"] = tag_dict.get(key)
                    result["flags"].append(
                        f"Editing software detected in metadata: {tag_dict.get(key)}"
                    )
                    result["suspicious"] = True
                    break
            if result["editing_software"]:
                break

        # Check dates
        creation_date = tag_dict.get("DateTime", tag_dict.get("DateTimeOriginal"))
        modify_date = tag_dict.get("DateTimeDigitized")
        result["dates"] = {
            "creation": creation_date,
            "modification": modify_date,
        }

        if creation_date and modify_date and creation_date != modify_date:
            result["flags"].append(
                f"Date mismatch — creation: {creation_date}, modification: {modify_date}"
            )
            result["suspicious"] = True

        if not tag_dict:
            result["flags"].append(
                "No metadata found on document"
            )

        logger.info("Metadata check for '%s': %d flags", image_path, len(result["flags"]))
        return result

    except Exception as e:
        logger.error("Metadata check failed for '%s': %s", image_path, e)
        result["flags"].append(f"Metadata check error: {str(e)}")
        return result


# ── Text-Region Consistency ──────────────────────────────────────────────────

def analyze_text_consistency(image_path: str, tamper_score: float = 0.0) -> dict[str, Any]:
    """
    Analyze text-region consistency in a document image.

    For the prototype, this uses a simplified heuristic based on the ELA
    tamper score and image statistics rather than full bounding-box analysis.

    Args:
        image_path: Path to the image file.
        tamper_score: Pre-computed tamper score from ELA.

    Returns:
        Dictionary with consistency analysis results.
    """
    result: dict[str, Any] = {
        "font_consistency": "consistent",
        "alignment_consistency": "consistent",
        "anomalous_regions": [],
        "flags": [],
    }

    if not _CV2_AVAILABLE:
        return result

    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return result

        # Compute local standard deviation as a proxy for text consistency
        # Edited regions often have different noise patterns
        h, w = img.shape
        block_size = max(h // 10, 50)
        local_stds = []

        for y in range(0, h - block_size, block_size):
            for x in range(0, w - block_size, block_size):
                block = img[y:y + block_size, x:x + block_size]
                local_stds.append(np.std(block))

        if local_stds:
            overall_std = np.std(local_stds)
            mean_std = np.mean(local_stds)

            # High variation in local standard deviations suggests inconsistency
            if overall_std > mean_std * 0.5 and tamper_score > 0.3:
                result["font_consistency"] = "inconsistent"
                result["flags"].append(
                    "Significant variation in text region characteristics detected"
                )

        # If ELA already flagged tampering, add context
        if tamper_score > 0.4:
            result["anomalous_regions"].append({
                "description": "Regions with inconsistent compression detected by ELA",
                "confidence": tamper_score,
            })
            result["flags"].append(
                "Text regions show compression inconsistencies suggestive of editing"
            )

        logger.info("Text consistency analysis: %d flags", len(result["flags"]))
        return result

    except Exception as e:
        logger.error("Text consistency analysis failed: %s", e)
        return result


# ── Orchestrator ─────────────────────────────────────────────────────────────

def detect_tampering(image_path: str) -> dict[str, Any]:
    """
    Run the full tamper detection pipeline on a document image.

    Combines:
    1. Error Level Analysis (ELA)
    2. Metadata inspection
    3. Text-region consistency

    Args:
        image_path: Path to the document image.

    Returns:
        Dictionary with:
            - tamper_score (float): Overall score 0.0–1.0
            - heatmap_path (str | None): Path to saved ELA heatmap
            - details (dict): Breakdown from each analysis step
    """
    logger.info("Running tamper detection on: %s", image_path)

    details: dict[str, Any] = {}
    overall_score = 0.0

    # ── Step 1: ELA ──────────────────────────────────────────────────────
    heatmap_array, ela_score = error_level_analysis(image_path)
    details["ela"] = {"score": ela_score}

    heatmap_path = None
    if heatmap_array is not None:
        heatmap_path = image_path.rsplit(".", 1)[0] + "_heatmap.png"
        try:
            cv2.imwrite(heatmap_path, heatmap_array)
            details["ela"]["heatmap_saved"] = True
            logger.info("Heatmap saved: %s", heatmap_path)
        except Exception as e:
            logger.error("Failed to save heatmap: %s", e)
            heatmap_path = None

    # ── Step 2: Metadata ─────────────────────────────────────────────────
    meta_result = check_metadata(image_path)
    details["metadata"] = meta_result

    # ── Step 3: Text consistency ─────────────────────────────────────────
    text_result = analyze_text_consistency(image_path, ela_score)
    details["text_consistency"] = text_result

    # ── Combine scores ───────────────────────────────────────────────────
    # ELA is the primary signal (weight 0.6)
    # Metadata suspicion adds 0.25
    # Text inconsistency adds 0.15
    overall_score = ela_score * 0.6

    if meta_result.get("suspicious"):
        overall_score += 0.25
        if meta_result.get("editing_software"):
            overall_score = max(overall_score + 0.35, 0.75)  # Major flag for Photoshop/editor metadata

    if text_result.get("font_consistency") == "inconsistent":
        overall_score += 0.15

    overall_score = round(min(overall_score, 1.0), 4)

    logger.info(
        "Tamper detection complete: overall=%.3f (ela=%.3f, meta_suspicious=%s)",
        overall_score, ela_score, meta_result.get("suspicious"),
    )

    return {
        "tamper_score": overall_score,
        "heatmap_path": heatmap_path,
        "details": details,
    }
