#!/usr/bin/env python3
"""
End-to-end demo runner for SIH26261 prototype.

Runs both Set A (clean) and Set B (problem) applications through the
full pipeline and prints a formatted report for each.

Usage:
    cd demo_data
    python run_demo.py

    # Or with a custom backend URL:
    python run_demo.py --url http://localhost:8000
"""
import argparse
import json
import os
import sys
import time

try:
    import requests
except ImportError:
    print("ERROR: 'requests' library not installed. Run: pip install requests")
    sys.exit(1)

# ── Banner ────────────────────────────────────────────────────────────────────

BANNER = """
==================================================================
   SIH26261 -- AI-Powered Application Validation Demo Runner
   AICTE New Engineering Institution Approval
   [!] All data is fictional and created for demonstration only
==================================================================
"""

# ── Demo Application Data ─────────────────────────────────────────────────────

SET_A = {
    "meta": {"label": "Set A -- Clean Application", "expected": "High trust score, fast-track"},
    "form": {
        "institution_name": "Vidya Bharati Institute of Technology",
        "trust_name": "Vidya Bharati Educational Trust",
        "address": "Survey No. 145/A, Hinjewadi, Pune, Maharashtra",
        "pin_code": "411057",
        "land_area_acres": 5.0,
        "proposed_courses": "Computer Science, Electronics, Mechanical",
        "total_intake": 180,
        "faculty_count": 6,
        "application_date": "2026-08-15",
    },
    "documents": [
        os.path.join("set_a", "land_deed.png"),
        os.path.join("set_a", "trust_certificate.png"),
        os.path.join("set_a", "noc_letter.png"),
        os.path.join("set_a", "faculty_list.png"),
    ],
}

SET_B = {
    "meta": {"label": "Set B -- Problem Application", "expected": "Low trust score, senior-review, multiple flags"},
    "form": {
        "institution_name": "Vidya Bharati Institute of Technology",
        "trust_name": "Vidya Bharati Educational Trust",
        "address": "Plot 78, Industrial Area, Nagpur, Maharashtra",
        "pin_code": "440001",
        "land_area_acres": 5.0,  # Claims 5 acres; deed is tampered from 2→5
        "proposed_courses": "Computer Science, Information Technology, Civil Engineering",
        "total_intake": 240,
        "faculty_count": 7,
        "application_date": "2026-09-01",
    },
    "documents": [
        os.path.join("set_b", "land_deed.png"),        # tampered
        os.path.join("set_b", "trust_certificate.png"), # "Bharti" not "Bharati"
        os.path.join("set_b", "noc_letter.png"),        # expired NOC
        os.path.join("set_b", "faculty_list.png"),      # dual-employed faculty
    ],
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def sep(char="-", width=66):
    print(char * width)

def h1(text):
    print(f"\n{'='*66}\n  {text}\n{'='*66}")

def h2(text):
    print(f"\n-- {text} {'-'*(62 - len(text))}")

def ok(msg):   print(f"  [OK]   {msg}")
def warn(msg): print(f"  [WARN] {msg}")
def err(msg):  print(f"  [ERR]  {msg}")


def run_demo_set(base_url: str, demo: dict) -> dict | None:
    meta = demo["meta"]
    form = demo["form"]
    docs = demo["documents"]

    h1(meta["label"])
    print(f"  Expected: {meta['expected']}\n")

    # ── Step 1: Create application ──
    h2("Step 1: Create Application")
    resp = requests.post(f"{base_url}/applications", json=form)
    if resp.status_code not in (200, 201):
        err(f"Failed to create application: {resp.status_code} - {resp.text[:200]}")
        return None
    app = resp.json()
    app_id = app["id"]
    ok(f"Application created: ID #{app_id}")

    # ── Step 2: Upload documents ──
    h2("Step 2: Upload Documents")
    missing = []
    for doc_path in docs:
        full_path = os.path.join(os.path.dirname(__file__), doc_path)
        if not os.path.exists(full_path):
            warn(f"Document not found (run generate_samples.py first): {doc_path}")
            missing.append(doc_path)
        else:
            ok(f"Found: {doc_path}")

    if missing:
        warn(f"{len(missing)} document(s) missing - generating placeholder text files...")
        for mp in missing:
            full_path = os.path.join(os.path.dirname(__file__), mp)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            # Create a tiny placeholder PNG (1x1 white pixel)
            with open(full_path, "wb") as f:
                # Minimal valid PNG bytes for a 1x1 white image
                f.write(bytes.fromhex(
                    "89504e470d0a1a0a0000000d49484452000000010000000108020000009001"
                    "2e00000000c4944415478016360f8ff000000020001e221bc330000000049454e44ae426082"
                ))

    files_payload = []
    file_handles = []
    for doc_path in docs:
        full_path = os.path.join(os.path.dirname(__file__), doc_path)
        fname = os.path.basename(doc_path)
        fh = open(full_path, "rb")
        file_handles.append(fh)
        files_payload.append(("files", (fname, fh, "image/png")))

    resp = requests.post(f"{base_url}/applications/{app_id}/documents", files=files_payload)
    for fh in file_handles:
        fh.close()

    if resp.status_code not in (200, 201):
        err(f"Upload failed: {resp.status_code} - {resp.text[:200]}")
        return None
    uploaded = resp.json()
    ok(f"Uploaded {len(uploaded)} document(s)")

    # ── Step 3: Process ──
    h2("Step 3: Run Full AI Pipeline")
    print("  Processing (OCR -> tamper detection -> cross-verification -> compliance)...")
    resp = requests.post(f"{base_url}/applications/{app_id}/process")
    if resp.status_code != 200:
        err(f"Processing failed: {resp.status_code} - {resp.text[:200]}")
        return None
    result = resp.json()
    ok(f"Processing complete: {result.get('message', '')}")

    # ── Step 4: Report ──
    h2("Step 4: Results")
    resp = requests.get(f"{base_url}/applications/{app_id}/report")
    if resp.status_code != 200:
        err(f"Report fetch failed: {resp.status_code}")
        return None
    report = resp.json()

    sb = report.get("score_breakdown", {})
    trust  = sb.get("trust_score", "N/A")
    comp   = sb.get("compliance_score", "N/A")
    route  = sb.get("route", "N/A")

    print()
    print(f"  {'TRUST SCORE':.<30} {trust}/100")
    print(f"  {'COMPLIANCE SCORE':.<30} {comp}/100")
    print(f"  {'REVIEW ROUTE':.<30} {str(route).upper()}")
    print()

    # Findings
    findings = report.get("findings", [])
    if findings:
        warn(f"{len(findings)} cross-verification finding(s):")
        for f in findings[:8]:  # show first 8
            sev = f.get("severity", "").upper()
            print(f"    [{sev}] {f.get('description', '')[:80]}")
        if len(findings) > 8:
            print(f"    ... and {len(findings) - 8} more")
    else:
        ok("No cross-verification issues found")

    # Rule results
    rules = report.get("rule_results", [])
    non_compliant = [r for r in rules if r.get("status") != "compliant"]
    compliant = [r for r in rules if r.get("status") == "compliant"]
    ok(f"{len(compliant)}/{len(rules)} rules compliant")
    if non_compliant:
        warn(f"{len(non_compliant)} non-compliant / needs-clarification rule(s):")
        for r in non_compliant[:5]:
            print(f"    [{r.get('rule_id')}] {r.get('rule_description','')[:60]} -> {r.get('status')}")

    return {
        "app_id": app_id,
        "trust_score": trust,
        "compliance_score": comp,
        "route": route,
        "findings": len(findings),
        "non_compliant_rules": len(non_compliant),
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SIH26261 demo runner")
    parser.add_argument("--url", default="http://localhost:8000", help="Backend base URL")
    args = parser.parse_args()
    base_url = args.url.rstrip("/")

    print(BANNER)

    # Health check
    try:
        resp = requests.get(f"{base_url}/docs", timeout=5)
        ok(f"Backend reachable at {base_url}")
    except Exception as e:
        err(f"Cannot reach backend at {base_url}: {e}")
        err("Start the backend with: cd backend && python main.py")
        sys.exit(1)

    results = {}

    for label, demo in [("set_a", SET_A), ("set_b", SET_B)]:
        result = run_demo_set(base_url, demo)
        if result:
            results[label] = result
        print()
        time.sleep(1)

    # ── Summary ──
    h1("Demo Summary")
    for label, r in results.items():
        meta = SET_A["meta"] if label == "set_a" else SET_B["meta"]
        print(f"\n  {meta['label']} (App #{r['app_id']})")
        print(f"    Trust Score:      {r['trust_score']}/100")
        print(f"    Compliance Score: {r['compliance_score']}/100")
        print(f"    Route:            {str(r['route']).upper()}")
        print(f"    Findings:         {r['findings']}")
        print(f"    Failed Rules:     {r['non_compliant_rules']}")

    print("\n  Open the officer dashboard to review:")
    for label, r in results.items():
        print(f"    App #{r['app_id']}: http://localhost:5173/application/{r['app_id']}")

    print("\n  Notice: external APIs (DigiLocker, MCA, land records)")
    print("    are simulated via mock_registry.json — not live data.")
    print()


if __name__ == "__main__":
    main()
