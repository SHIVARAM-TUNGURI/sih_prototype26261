"""
generate_samples.py - Generate sample document images for SIH26261 demo.

Creates two sets of synthetic scanned documents using Pillow:
  - Set A: Clean, consistent application documents
  - Set B: Problem application with tampering, mismatches, and expired NOC

Usage:
    python generate_samples.py

Output:
    demo_data/set_a/  - Clean document images
    demo_data/set_b/  - Problem document images

DISCLAIMER: All names, organizations, and data are entirely fictional
and created solely for demonstration purposes.
"""

from __future__ import annotations

import math
import os
import textwrap
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PAGE_W, PAGE_H = 1200, 1600
BG_COLOR = (252, 250, 245)       # Slightly off-white "paper"
BORDER_COLOR = (60, 60, 80)
TEXT_COLOR = (30, 30, 40)
HEADER_COLOR = (20, 20, 80)
SEAL_COLOR = (180, 40, 40)
STAMP_COLOR = (0, 100, 0)
LIGHT_GRAY = (200, 200, 200)
TABLE_LINE = (100, 100, 120)
TAMPER_BG = (255, 255, 255)      # Pure white rectangle for tampered region

SCRIPT_DIR = Path(__file__).resolve().parent
SET_A_DIR = SCRIPT_DIR / "set_a"
SET_B_DIR = SCRIPT_DIR / "set_b"


# ---------------------------------------------------------------------------
# Font helpers (gracefully fall back to default bitmap font)
# ---------------------------------------------------------------------------

def _try_load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Attempt to load a TrueType font; fall back to default if unavailable."""
    # Common system font paths (Windows / Linux / macOS)
    candidates = [
        "arial.ttf",
        "arialbd.ttf" if bold else "arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in candidates:
        if not path:
            continue
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    # Ultimate fallback
    return ImageFont.load_default()


def get_fonts() -> dict:
    """Return a dict of pre-loaded fonts at various sizes."""
    return {
        "title": _try_load_font(36, bold=True),
        "subtitle": _try_load_font(24, bold=True),
        "body": _try_load_font(20),
        "body_bold": _try_load_font(20, bold=True),
        "small": _try_load_font(16),
        "seal": _try_load_font(14, bold=True),
        "stamp": _try_load_font(18, bold=True),
        "table_header": _try_load_font(17, bold=True),
        "table_cell": _try_load_font(16),
    }


FONTS = get_fonts()


# ---------------------------------------------------------------------------
# Drawing primitives
# ---------------------------------------------------------------------------

def create_page() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Create a blank page with paper background and border."""
    img = Image.new("RGB", (PAGE_W, PAGE_H), BG_COLOR)
    draw = ImageDraw.Draw(img)
    # Double border
    draw.rectangle([20, 20, PAGE_W - 20, PAGE_H - 20], outline=BORDER_COLOR, width=3)
    draw.rectangle([30, 30, PAGE_W - 30, PAGE_H - 30], outline=BORDER_COLOR, width=1)
    return img, draw


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: tuple = TEXT_COLOR,
) -> int:
    """Draw horizontally-centred text and return the next y position."""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (PAGE_W - tw) // 2
    draw.text((x, y), text, font=font, fill=fill)
    return y + th + 10


def draw_left_text(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: tuple = TEXT_COLOR,
    max_width: int = 1100,
) -> int:
    """Draw left-aligned text (with word-wrap) and return next y position."""
    # Rough character-width estimate for wrapping
    avg_char_w = max(font.getlength("M") if hasattr(font, "getlength") else 12, 1)
    wrap_chars = int(max_width / avg_char_w)
    lines = textwrap.wrap(text, width=wrap_chars)
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        bbox = draw.textbbox((0, 0), line, font=font)
        y += (bbox[3] - bbox[1]) + 6
    return y


def draw_field(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    label: str,
    value: str,
) -> int:
    """Draw a 'Label: Value' field line."""
    draw.text((x, y), f"{label}: ", font=FONTS["body_bold"], fill=TEXT_COLOR)
    label_w = draw.textlength(f"{label}: ", font=FONTS["body_bold"])
    draw.text((x + label_w, y), value, font=FONTS["body"], fill=TEXT_COLOR)
    return y + 32


def draw_seal(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    radius: int,
    text_lines: list[str],
    color: tuple = SEAL_COLOR,
) -> None:
    """Draw a circular 'seal' / 'stamp' with text inside."""
    # Outer circle
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        outline=color,
        width=3,
    )
    # Inner circle
    inner_r = radius - 10
    draw.ellipse(
        [cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r],
        outline=color,
        width=1,
    )
    # Text lines centred inside
    total_h = len(text_lines) * 20
    start_y = cy - total_h // 2
    for i, line in enumerate(text_lines):
        bbox = draw.textbbox((0, 0), line, font=FONTS["seal"])
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw // 2, start_y + i * 20), line, font=FONTS["seal"], fill=color)


def draw_stamp_rectangle(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text: str,
    color: tuple = STAMP_COLOR,
) -> None:
    """Draw a rectangular rubber-stamp style mark."""
    font = FONTS["stamp"]
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = 10
    draw.rectangle(
        [x, y, x + tw + 2 * pad, y + th + 2 * pad],
        outline=color,
        width=3,
    )
    draw.text((x + pad, y + pad), text, font=font, fill=color)


def draw_horizontal_line(draw: ImageDraw.ImageDraw, y: int, margin: int = 60) -> int:
    """Draw a thin horizontal rule across the page."""
    draw.line([(margin, y), (PAGE_W - margin, y)], fill=LIGHT_GRAY, width=1)
    return y + 15


# ---------------------------------------------------------------------------
# Set A document generators (clean application)
# ---------------------------------------------------------------------------

def gen_land_deed_a() -> Image.Image:
    """Generate a clean land deed for Set A."""
    img, draw = create_page()
    y = 60

    # Header
    y = draw_centered_text(draw, y, "GOVERNMENT OF MAHARASHTRA", FONTS["subtitle"], HEADER_COLOR)
    y = draw_centered_text(draw, y, "Office of the Sub-Registrar, Pune", FONTS["body"], HEADER_COLOR)
    y = draw_horizontal_line(draw, y + 10)

    # Title
    y = draw_centered_text(draw, y + 10, "SALE DEED / CONVEYANCE DEED", FONTS["title"], HEADER_COLOR)
    y = draw_horizontal_line(draw, y + 5)
    y += 20

    # Content fields
    x = 80
    y = draw_field(draw, x, y, "Document No", "PUN/SD/2020/003456")
    y = draw_field(draw, x, y, "Date of Execution", "15-03-2020")
    y = draw_field(draw, x, y, "Date of Registration", "18-03-2020")
    y += 10

    y = draw_left_text(draw, x, y,
        "This Sale Deed is executed by Shri. Ramesh Kulkarni (Seller) in favour of "
        "Vidya Bharati Educational Trust (Buyer/Purchaser), represented by its "
        "Managing Trustee, Shri. Mohan Joshi.",
        FONTS["body"])
    y += 15

    y = draw_field(draw, x, y, "Property Description", "")
    y = draw_field(draw, x + 30, y, "Survey No", "145/A")
    y = draw_field(draw, x + 30, y, "Village", "Hinjewadi")
    y = draw_field(draw, x + 30, y, "Taluka / District", "Mulshi / Pune")
    y = draw_field(draw, x + 30, y, "State", "Maharashtra")
    y = draw_field(draw, x + 30, y, "Total Area", "5.0 acres (approx. 20,234 sq. meters)")
    y += 10

    y = draw_field(draw, x, y, "Consideration Amount", "INR 2,50,00,000 (Two Crore Fifty Lakhs)")
    y = draw_field(draw, x, y, "Stamp Duty Paid", "INR 12,50,000")
    y = draw_field(draw, x, y, "Registration Fee", "INR 30,000")
    y += 20

    y = draw_left_text(draw, x, y,
        "The Seller hereby transfers all rights, title, and interest in the above-described "
        "property to the Buyer. The property is free from all encumbrances, liens, and "
        "legal disputes.",
        FONTS["body"])
    y += 30

    # Signatures
    draw.text((100, y), "Seller: ___________________", font=FONTS["body"], fill=TEXT_COLOR)
    draw.text((650, y), "Buyer: ___________________", font=FONTS["body"], fill=TEXT_COLOR)
    y += 40
    draw.text((100, y), "(Shri. Ramesh Kulkarni)", font=FONTS["small"], fill=TEXT_COLOR)
    draw.text((650, y), "(Vidya Bharati Edu. Trust)", font=FONTS["small"], fill=TEXT_COLOR)

    # Seal
    draw_seal(draw, PAGE_W - 180, PAGE_H - 220, 80,
              ["Sub-Registrar", "Office", "Pune", "★"])

    return img


def gen_trust_cert_a() -> Image.Image:
    """Generate a clean trust registration certificate for Set A."""
    img, draw = create_page()
    y = 60

    y = draw_centered_text(draw, y, "OFFICE OF THE CHARITY COMMISSIONER", FONTS["subtitle"], HEADER_COLOR)
    y = draw_centered_text(draw, y, "Government of Maharashtra", FONTS["body"], HEADER_COLOR)
    y = draw_horizontal_line(draw, y + 10)
    y = draw_centered_text(draw, y + 10, "CERTIFICATE OF REGISTRATION OF TRUST", FONTS["title"], HEADER_COLOR)
    y = draw_horizontal_line(draw, y + 5)
    y += 25

    x = 80
    y = draw_left_text(draw, x, y,
        "This is to certify that the following Trust has been duly registered under "
        "the Bombay Public Trusts Act, 1950.",
        FONTS["body"])
    y += 15

    y = draw_field(draw, x, y, "Trust Name", "Vidya Bharati Educational Trust")
    y = draw_field(draw, x, y, "Registration No", "MH/TR/2019/00456")
    y = draw_field(draw, x, y, "Date of Registration", "10-01-2019")
    y = draw_field(draw, x, y, "Registered Under", "Bombay Public Trusts Act, 1950")
    y = draw_field(draw, x, y, "Registering Authority", "Charity Commissioner, Maharashtra")
    y = draw_field(draw, x, y, "Status", "Active")
    y += 10

    y = draw_field(draw, x, y, "Registered Office", "Survey No. 145/A, Hinjewadi, Pune - 411057")
    y = draw_field(draw, x, y, "Nature of Trust", "Educational / Charitable")
    y += 10

    y = draw_left_text(draw, x, y, "Board of Trustees:", FONTS["body_bold"])
    trustees = [
        "1. Shri. Mohan Joshi (Managing Trustee)",
        "2. Smt. Sunita Deshpande (Secretary)",
        "3. Shri. Arun Patwardhan (Treasurer)",
        "4. Dr. Leela Ranade (Member)",
        "5. Shri. Prasad Gokhale (Member)",
    ]
    for t in trustees:
        y = draw_left_text(draw, x + 30, y, t, FONTS["body"])
    y += 30

    y = draw_left_text(draw, x, y,
        "This certificate is issued subject to the provisions of the Bombay Public "
        "Trusts Act, 1950 and the rules made thereunder.",
        FONTS["body"])
    y += 40

    draw.text((650, y), "Sd/-", font=FONTS["body_bold"], fill=TEXT_COLOR)
    y += 28
    draw.text((650, y), "Charity Commissioner", font=FONTS["body"], fill=TEXT_COLOR)
    y += 25
    draw.text((650, y), "Maharashtra State", font=FONTS["small"], fill=TEXT_COLOR)

    draw_seal(draw, 200, PAGE_H - 220, 80,
              ["Charity", "Commissioner", "Maharashtra", "★"])

    return img


def gen_noc_a() -> Image.Image:
    """Generate a clean NOC letter for Set A."""
    img, draw = create_page()
    y = 60

    y = draw_centered_text(draw, y, "DIRECTORATE OF TECHNICAL EDUCATION", FONTS["subtitle"], HEADER_COLOR)
    y = draw_centered_text(draw, y, "Government of Maharashtra", FONTS["body"], HEADER_COLOR)
    y = draw_centered_text(draw, y, "3, Mahapalika Marg, Mumbai - 400001", FONTS["small"], HEADER_COLOR)
    y = draw_horizontal_line(draw, y + 10)
    y = draw_centered_text(draw, y + 10, "NO OBJECTION CERTIFICATE", FONTS["title"], HEADER_COLOR)
    y = draw_horizontal_line(draw, y + 5)
    y += 20

    x = 80
    y = draw_field(draw, x, y, "Reference No", "DTE/NOC/2026/1234")
    y = draw_field(draw, x, y, "Date", "01-06-2026")
    y += 15

    y = draw_left_text(draw, x, y, "To Whom It May Concern,", FONTS["body_bold"])
    y += 10

    y = draw_left_text(draw, x, y,
        "This is to certify that the Directorate of Technical Education, Government of "
        "Maharashtra, has No Objection to the establishment of the following institution:",
        FONTS["body"])
    y += 15

    y = draw_field(draw, x + 30, y, "Institution Name", "Vidya Bharati Institute of Technology")
    y = draw_field(draw, x + 30, y, "Sponsoring Body", "Vidya Bharati Educational Trust")
    y = draw_field(draw, x + 30, y, "Location", "Hinjewadi, Pune, Maharashtra")
    y = draw_field(draw, x + 30, y, "Proposed Courses", "B.Tech in CS, ECE, ME")
    y += 15

    y = draw_left_text(draw, x, y,
        "This NOC is issued subject to the institution complying with all norms and "
        "standards prescribed by the All India Council for Technical Education (AICTE) "
        "and the affiliating university.",
        FONTS["body"])
    y += 10

    y = draw_field(draw, x, y, "Valid From", "01-06-2026")
    y = draw_field(draw, x, y, "Valid Until", "31-12-2027")
    y += 30

    draw.text((650, y), "Sd/-", font=FONTS["body_bold"], fill=TEXT_COLOR)
    y += 28
    draw.text((650, y), "Director of Technical Education", font=FONTS["body"], fill=TEXT_COLOR)
    y += 25
    draw.text((650, y), "Maharashtra State", font=FONTS["small"], fill=TEXT_COLOR)

    draw_stamp_rectangle(draw, 100, PAGE_H - 180, "APPROVED", STAMP_COLOR)
    draw_seal(draw, PAGE_W - 180, PAGE_H - 220, 80,
              ["DTE", "Maharashtra", "NOC", "★"])

    return img


def gen_faculty_list_a() -> Image.Image:
    """Generate a clean faculty list document for Set A."""
    img, draw = create_page()
    y = 60

    y = draw_centered_text(draw, y, "VIDYA BHARATI INSTITUTE OF TECHNOLOGY", FONTS["subtitle"], HEADER_COLOR)
    y = draw_centered_text(draw, y, "Hinjewadi, Pune, Maharashtra", FONTS["small"], HEADER_COLOR)
    y = draw_horizontal_line(draw, y + 10)
    y = draw_centered_text(draw, y + 10, "FACULTY LIST", FONTS["title"], HEADER_COLOR)
    y = draw_centered_text(draw, y, "Academic Year 2026-27", FONTS["body"], TEXT_COLOR)
    y = draw_horizontal_line(draw, y + 5)
    y += 15

    # Table header
    cols = [60, 160, 420, 680, 880, 1020]  # x positions
    headers = ["S.No", "Name", "Qualification", "Designation", "Dept.", "ID"]
    for i, h in enumerate(headers):
        draw.text((cols[i], y), h, font=FONTS["table_header"], fill=HEADER_COLOR)
    y += 28
    draw.line([(50, y), (PAGE_W - 50, y)], fill=TABLE_LINE, width=2)
    y += 10

    # Faculty data
    faculty = [
        ("1", "Dr. Anita Sharma", "Ph.D. (Computer Science)", "Professor", "CSE", "FAC001"),
        ("2", "Dr. Suresh Patel", "Ph.D. (Electronics)", "Professor", "ECE", "FAC002"),
        ("3", "Mr. Amit Kumar", "M.Tech (Mechanical)", "Asst. Prof.", "ME", "FAC003"),
        ("4", "Dr. Priya Nair", "Ph.D. (Mathematics)", "Assoc. Prof.", "Science", "FAC004"),
        ("5", "Ms. Kavita Reddy", "M.Tech (Civil)", "Asst. Prof.", "Civil", "FAC005"),
        ("6", "Dr. Vikram Singh", "Ph.D. (Computer Sci.)", "Professor", "CSE", "FAC006"),
    ]
    for row in faculty:
        for i, cell in enumerate(row):
            draw.text((cols[i], y), cell, font=FONTS["table_cell"], fill=TEXT_COLOR)
        y += 30
        draw.line([(50, y - 5), (PAGE_W - 50, y - 5)], fill=LIGHT_GRAY, width=1)

    y += 20
    y = draw_field(draw, 80, y, "Total Faculty", "6")
    y = draw_field(draw, 80, y, "Professors", "3")
    y = draw_field(draw, 80, y, "Associate Professors", "1")
    y = draw_field(draw, 80, y, "Assistant Professors", "2")
    y += 30

    draw.text((650, y), "Sd/-", font=FONTS["body_bold"], fill=TEXT_COLOR)
    y += 28
    draw.text((650, y), "Principal", font=FONTS["body"], fill=TEXT_COLOR)

    draw_stamp_rectangle(draw, 100, PAGE_H - 160, "VERIFIED", STAMP_COLOR)

    return img


# ---------------------------------------------------------------------------
# Set B document generators (problem application)
# ---------------------------------------------------------------------------

def gen_land_deed_b() -> Image.Image:
    """Generate a TAMPERED land deed for Set B.

    Simulates tampering by drawing a white rectangle over the area field
    and re-writing a different value, making it detectable via Error Level
    Analysis (ELA).
    """
    img, draw = create_page()
    y = 60

    # Header
    y = draw_centered_text(draw, y, "GOVERNMENT OF MAHARASHTRA", FONTS["subtitle"], HEADER_COLOR)
    y = draw_centered_text(draw, y, "Office of the Sub-Registrar, Nagpur", FONTS["body"], HEADER_COLOR)
    y = draw_horizontal_line(draw, y + 10)
    y = draw_centered_text(draw, y + 10, "SALE DEED / CONVEYANCE DEED", FONTS["title"], HEADER_COLOR)
    y = draw_horizontal_line(draw, y + 5)
    y += 20

    x = 80
    y = draw_field(draw, x, y, "Document No", "NAG/SD/2020/007891")
    y = draw_field(draw, x, y, "Date of Execution", "20-05-2020")
    y = draw_field(draw, x, y, "Date of Registration", "25-05-2020")
    y += 10

    y = draw_left_text(draw, x, y,
        "This Sale Deed is executed by Shri. Prakash Deshmukh (Seller) in favour of "
        "Vidya Bharati Educational Trust (Buyer/Purchaser), represented by its "
        "Managing Trustee, Shri. Mohan Joshi.",
        FONTS["body"])
    y += 15

    y = draw_field(draw, x, y, "Property Description", "")
    y = draw_field(draw, x + 30, y, "Survey No", "78/B")
    y = draw_field(draw, x + 30, y, "Village", "Hingna")
    y = draw_field(draw, x + 30, y, "Taluka / District", "Nagpur / Nagpur")
    y = draw_field(draw, x + 30, y, "State", "Maharashtra")

    # --- TAMPERED AREA ---
    # First write the "original" value
    area_y = y
    y = draw_field(draw, x + 30, y, "Total Area", "2.0 acres (approx. 8,094 sq. meters)")

    # Now simulate tampering: white rectangle over the area value, then new value
    label_text = "Total Area: "
    label_w = draw.textlength(label_text, font=FONTS["body_bold"])
    tamper_x = int(x + 30 + label_w)
    # White-out rectangle (slightly different shade to enable ELA detection)
    draw.rectangle(
        [tamper_x - 2, area_y - 2, tamper_x + 420, area_y + 26],
        fill=TAMPER_BG,  # Pure white vs off-white background
    )
    # Re-write tampered value
    draw.text(
        (tamper_x, area_y),
        "5.0 acres (approx. 20,234 sq. meters)",
        font=FONTS["body"],
        fill=TEXT_COLOR,
    )
    # --- END TAMPER ---

    y += 10
    y = draw_field(draw, x, y, "Consideration Amount", "INR 1,00,00,000 (One Crore)")
    y = draw_field(draw, x, y, "Stamp Duty Paid", "INR 5,00,000")
    y = draw_field(draw, x, y, "Registration Fee", "INR 30,000")
    y += 20

    y = draw_left_text(draw, x, y,
        "The Seller hereby transfers all rights, title, and interest in the above-described "
        "property to the Buyer.",
        FONTS["body"])
    y += 30

    draw.text((100, y), "Seller: ___________________", font=FONTS["body"], fill=TEXT_COLOR)
    draw.text((650, y), "Buyer: ___________________", font=FONTS["body"], fill=TEXT_COLOR)
    y += 40
    draw.text((100, y), "(Shri. Prakash Deshmukh)", font=FONTS["small"], fill=TEXT_COLOR)
    draw.text((650, y), "(Vidya Bharati Edu. Trust)", font=FONTS["small"], fill=TEXT_COLOR)

    draw_seal(draw, PAGE_W - 180, PAGE_H - 220, 80,
              ["Sub-Registrar", "Office", "Nagpur", "★"])

    # Add a PNG text chunk as metadata hint about editing (for demo purposes)
    from PIL import PngImagePlugin
    meta = PngImagePlugin.PngInfo()
    meta.add_text("Comment", "Area value edited from 2.0 to 5.0 acres")
    meta.add_text("Software", "Adobe Photoshop 24.0")
    img.info["pnginfo"] = meta  # We'll use this when saving

    return img


def gen_trust_cert_b() -> Image.Image:
    """Generate a trust certificate for Set B with a subtle name mismatch.

    Trust name is 'Vidya Bharti Educational Trust' (Bharti, not Bharati).
    Registration number is also different.
    """
    img, draw = create_page()
    y = 60

    y = draw_centered_text(draw, y, "OFFICE OF THE CHARITY COMMISSIONER", FONTS["subtitle"], HEADER_COLOR)
    y = draw_centered_text(draw, y, "Government of Maharashtra", FONTS["body"], HEADER_COLOR)
    y = draw_horizontal_line(draw, y + 10)
    y = draw_centered_text(draw, y + 10, "CERTIFICATE OF REGISTRATION OF TRUST", FONTS["title"], HEADER_COLOR)
    y = draw_horizontal_line(draw, y + 5)
    y += 25

    x = 80
    y = draw_left_text(draw, x, y,
        "This is to certify that the following Trust has been duly registered under "
        "the Bombay Public Trusts Act, 1950.",
        FONTS["body"])
    y += 15

    # NOTE: "Bharti" instead of "Bharati" - intentional mismatch
    y = draw_field(draw, x, y, "Trust Name", "Vidya Bharti Educational Trust")
    y = draw_field(draw, x, y, "Registration No", "MH/TR/2019/00789")
    y = draw_field(draw, x, y, "Date of Registration", "22-03-2019")
    y = draw_field(draw, x, y, "Registered Under", "Bombay Public Trusts Act, 1950")
    y = draw_field(draw, x, y, "Registering Authority", "Charity Commissioner, Maharashtra")
    y = draw_field(draw, x, y, "Status", "Active")
    y += 10

    y = draw_field(draw, x, y, "Registered Office", "Plot 78, Industrial Area, Nagpur - 440001")
    y = draw_field(draw, x, y, "Nature of Trust", "Educational / Charitable")
    y += 10

    y = draw_left_text(draw, x, y, "Board of Trustees:", FONTS["body_bold"])
    trustees = [
        "1. Shri. Mohan Joshi (Managing Trustee)",
        "2. Smt. Asha Bhagwat (Secretary)",
        "3. Shri. Deepak Kale (Treasurer)",
    ]
    for t in trustees:
        y = draw_left_text(draw, x + 30, y, t, FONTS["body"])
    y += 30

    y = draw_left_text(draw, x, y,
        "This certificate is issued subject to the provisions of the Bombay Public "
        "Trusts Act, 1950 and the rules made thereunder.",
        FONTS["body"])
    y += 40

    draw.text((650, y), "Sd/-", font=FONTS["body_bold"], fill=TEXT_COLOR)
    y += 28
    draw.text((650, y), "Charity Commissioner", font=FONTS["body"], fill=TEXT_COLOR)
    y += 25
    draw.text((650, y), "Maharashtra State", font=FONTS["small"], fill=TEXT_COLOR)

    draw_seal(draw, 200, PAGE_H - 220, 80,
              ["Charity", "Commissioner", "Maharashtra", "★"])

    return img


def gen_noc_b() -> Image.Image:
    """Generate a NOC for Set B with mismatched institution name and EXPIRED date."""
    img, draw = create_page()
    y = 60

    y = draw_centered_text(draw, y, "DIRECTORATE OF TECHNICAL EDUCATION", FONTS["subtitle"], HEADER_COLOR)
    y = draw_centered_text(draw, y, "Government of Maharashtra", FONTS["body"], HEADER_COLOR)
    y = draw_centered_text(draw, y, "3, Mahapalika Marg, Mumbai - 400001", FONTS["small"], HEADER_COLOR)
    y = draw_horizontal_line(draw, y + 10)
    y = draw_centered_text(draw, y + 10, "NO OBJECTION CERTIFICATE", FONTS["title"], HEADER_COLOR)
    y = draw_horizontal_line(draw, y + 5)
    y += 20

    x = 80
    y = draw_field(draw, x, y, "Reference No", "DTE/NOC/2023/5678")
    y = draw_field(draw, x, y, "Date", "15-07-2023")
    y += 15

    y = draw_left_text(draw, x, y, "To Whom It May Concern,", FONTS["body_bold"])
    y += 10

    y = draw_left_text(draw, x, y,
        "This is to certify that the Directorate of Technical Education, Government of "
        "Maharashtra, has No Objection to the establishment of the following institution:",
        FONTS["body"])
    y += 15

    # NOTE: Different institution name from application form
    y = draw_field(draw, x + 30, y, "Institution Name", "Vidya Bharti Technical Institute")
    y = draw_field(draw, x + 30, y, "Sponsoring Body", "Vidya Bharti Educational Trust")
    y = draw_field(draw, x + 30, y, "Location", "Nagpur, Maharashtra")
    y = draw_field(draw, x + 30, y, "Proposed Courses", "B.Tech in CS, IT, Civil")
    y += 15

    y = draw_left_text(draw, x, y,
        "This NOC is issued subject to the institution complying with all norms and "
        "standards prescribed by AICTE and the affiliating university.",
        FONTS["body"])
    y += 10

    y = draw_field(draw, x, y, "Valid From", "15-07-2023")
    # NOTE: EXPIRED validity
    y = draw_field(draw, x, y, "Valid Until", "31-12-2024")
    y += 30

    draw.text((650, y), "Sd/-", font=FONTS["body_bold"], fill=TEXT_COLOR)
    y += 28
    draw.text((650, y), "Director of Technical Education", font=FONTS["body"], fill=TEXT_COLOR)
    y += 25
    draw.text((650, y), "Maharashtra State", font=FONTS["small"], fill=TEXT_COLOR)

    draw_stamp_rectangle(draw, 100, PAGE_H - 180, "APPROVED", STAMP_COLOR)
    draw_seal(draw, PAGE_W - 180, PAGE_H - 220, 80,
              ["DTE", "Maharashtra", "NOC", "★"])

    return img


def gen_faculty_list_b() -> Image.Image:
    """Generate a faculty list for Set B with conflicts.

    - FAC006 replaced with FAC007 (employed elsewhere)
    - FAC008 added with insufficient qualification (B.Tech)
    """
    img, draw = create_page()
    y = 60

    y = draw_centered_text(draw, y, "VIDYA BHARTI TECHNICAL INSTITUTE", FONTS["subtitle"], HEADER_COLOR)
    y = draw_centered_text(draw, y, "Nagpur, Maharashtra", FONTS["small"], HEADER_COLOR)
    y = draw_horizontal_line(draw, y + 10)
    y = draw_centered_text(draw, y + 10, "FACULTY LIST", FONTS["title"], HEADER_COLOR)
    y = draw_centered_text(draw, y, "Academic Year 2026-27", FONTS["body"], TEXT_COLOR)
    y = draw_horizontal_line(draw, y + 5)
    y += 15

    # Table header
    cols = [60, 160, 420, 680, 880, 1020]
    headers = ["S.No", "Name", "Qualification", "Designation", "Dept.", "ID"]
    for i, h in enumerate(headers):
        draw.text((cols[i], y), h, font=FONTS["table_header"], fill=HEADER_COLOR)
    y += 28
    draw.line([(50, y), (PAGE_W - 50, y)], fill=TABLE_LINE, width=2)
    y += 10

    faculty = [
        ("1", "Dr. Anita Sharma", "Ph.D. (Computer Science)", "Professor", "CSE", "FAC001"),
        ("2", "Dr. Suresh Patel", "Ph.D. (Electronics)", "Professor", "ECE", "FAC002"),
        ("3", "Mr. Amit Kumar", "M.Tech (Mechanical)", "Asst. Prof.", "ME", "FAC003"),
        ("4", "Dr. Priya Nair", "Ph.D. (Mathematics)", "Assoc. Prof.", "Science", "FAC004"),
        ("5", "Ms. Kavita Reddy", "M.Tech (Civil)", "Asst. Prof.", "Civil", "FAC005"),
        # FAC007 - employed at ABC Engineering College (conflict)
        ("6", "Dr. Rajesh Verma", "Ph.D. (Computer Sci.)", "Professor", "CSE", "FAC007"),
        # FAC008 - B.Tech qualification (below minimum for faculty)
        ("7", "Mr. Ravi Tiwari", "B.Tech (IT)", "Lecturer", "IT", "FAC008"),
    ]
    for row in faculty:
        for i, cell in enumerate(row):
            draw.text((cols[i], y), cell, font=FONTS["table_cell"], fill=TEXT_COLOR)
        y += 30
        draw.line([(50, y - 5), (PAGE_W - 50, y - 5)], fill=LIGHT_GRAY, width=1)

    y += 20
    y = draw_field(draw, 80, y, "Total Faculty", "7")
    y = draw_field(draw, 80, y, "Professors", "3")
    y = draw_field(draw, 80, y, "Associate Professors", "1")
    y = draw_field(draw, 80, y, "Assistant Professors", "2")
    y = draw_field(draw, 80, y, "Lecturers", "1")
    y += 30

    draw.text((650, y), "Sd/-", font=FONTS["body_bold"], fill=TEXT_COLOR)
    y += 28
    draw.text((650, y), "Principal", font=FONTS["body"], fill=TEXT_COLOR)

    draw_stamp_rectangle(draw, 100, PAGE_H - 160, "VERIFIED", STAMP_COLOR)

    return img


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Generate all sample documents for both data sets."""
    print("=" * 60)
    print("  SIH26261 - Sample Document Generator")
    print("=" * 60)

    # Create output directories
    SET_A_DIR.mkdir(parents=True, exist_ok=True)
    SET_B_DIR.mkdir(parents=True, exist_ok=True)

    # --- Set A (clean) ---
    print("\n[Set A] Generating clean application documents...")

    generators_a = {
        "land_deed.png": gen_land_deed_a,
        "trust_certificate.png": gen_trust_cert_a,
        "noc_letter.png": gen_noc_a,
        "faculty_list.png": gen_faculty_list_a,
    }
    for filename, gen_fn in generators_a.items():
        img = gen_fn()
        path = SET_A_DIR / filename
        img.save(str(path), "PNG")
        print(f"  [OK] {path}")

    # --- Set B (problems) ---
    print("\n[Set B] Generating problem application documents...")

    generators_b = {
        "land_deed.png": gen_land_deed_b,
        "trust_certificate.png": gen_trust_cert_b,
        "noc_letter.png": gen_noc_b,
        "faculty_list.png": gen_faculty_list_b,
    }
    for filename, gen_fn in generators_b.items():
        img = gen_fn()
        path = SET_B_DIR / filename

        # Special handling for tampered land deed (save PNG metadata)
        if filename == "land_deed.png" and hasattr(img, "info") and "pnginfo" in img.info:
            img.save(str(path), "PNG", pnginfo=img.info["pnginfo"])
        else:
            img.save(str(path), "PNG")
        print(f"  [OK] {path}")

    print("\n" + "=" * 60)
    print("  All sample documents generated successfully!")
    print(f"  Set A: {SET_A_DIR}")
    print(f"  Set B: {SET_B_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
