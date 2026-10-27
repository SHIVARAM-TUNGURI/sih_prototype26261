# SIH26261 Demo Datasets & Sample Generator

This directory contains synthetic datasets, sample document generators, and automated end-to-end demo scripts for the AICTE Smart Verification Prototype.

> **DISCLAIMER:** All personal names, trust titles, institution names, registration numbers, and dates in these datasets are **100% fictional** and generated exclusively for testing regulatory compliance, OCR extraction, and document authentication algorithms.

---

## Directory Structure

```
demo_data/
├── generate_samples.py    # Pillow-based high-res realistic document synthesizer
├── run_demo.py            # End-to-end automated testing script (Set A & Set B)
├── set_a/                 # Clean, authentic application documents (Fast-track)
│   ├── land_deed.png
│   ├── trust_certificate.png
│   ├── noc_letter.png
│   └── faculty_list.png
└── set_b/                 # Problematic, altered application documents (Senior-review)
    ├── land_deed.png      # (Digitally altered area from 2.0 to 5.0 acres)
    ├── trust_certificate.png  # (Minor name variation: "Vidya Bharti" vs "Vidya Bharati")
    ├── noc_letter.png     # (Expired validity date)
    └── faculty_list.png   # (Dual-employed faculty & under-qualified candidate)
```

---

## Demo Scenarios

### Set A: Clean Application (Expected: Fast-Track Route)
- **Institution:** Vidya Bharati Institute of Technology
- **Trust:** Vidya Bharati Educational Trust
- **Land Area:** 5.0 acres (meets the >= 2.5 acre AICTE engineering norm)
- **Status in Registry:** Active trust, clear land title, faculty without dual-employment conflicts
- **Integrity:** Untampered scans with consistent Error Level Analysis (ELA)
- **Outcome:** High Trust Score (≥90/100), high Compliance Score (≥90/100), routed to **Fast-Track**.

### Set B: Problem Application (Expected: Senior Review / Inspection)
- **Land Deed Tampering:** Area was edited from 2.0 to 5.0 acres in an image editor. Caught by **Error Level Analysis (ELA)** heatmap and local standard deviation checks.
- **Name Inconsistency:** Form states *Vidya Bharati Educational Trust*, but trust certificate reads *Vidya Bharti Educational Trust*. Caught by **Token-Sort Fuzzy Ratio** as `partial_match`.
- **Dual Employment:** Dr. Rajesh Verma (FAC007) is detected in `mock_registry.json` as concurrently employed at another engineering college.
- **Qualification Deficit:** Includes a faculty member holding only a B.Tech degree (violates AICTE minimum PG/PhD norm).
- **Expired NOC:** Clearance letter validity expired prior to the evaluation date.
- **Outcome:** Trust Score drops below 50, multiple high-severity findings flagged, routed to **Senior Review / Physical Inspection**.

---

## How to Run

### 1. Synthesize Document Images
```bash
python generate_samples.py
```
This generates authentic-looking high-resolution PNG documents with simulated stamps, registrar seals, and typography.

### 2. Run Automated Verification Demo
Make sure the backend is running (`uvicorn main:app --reload --port 8000`), then:
```bash
python run_demo.py
```
This script will:
1. Ping the backend API health
2. Submit Application A and upload Set A documents
3. Trigger pipeline processing and display the verified report
4. Submit Application B and upload Set B documents
5. Trigger pipeline processing and display flagged violations, deductions, and routing decisions.
