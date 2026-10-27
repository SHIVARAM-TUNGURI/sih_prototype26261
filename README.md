# SIH26261 – AI-Powered Application Validation, Document Authentication & Regulatory Compliance Verification

> **Prototype** for Smart India Hackathon 2026  
> Application Type: New Engineering Institution Approval (AICTE)

## 🎯 What This Does

An end-to-end system that helps AICTE officers verify applications for new engineering institutions by:

1. **Accepting** applications and supporting documents through a portal
2. **Extracting** data from documents using OCR and field extraction
3. **Detecting** tampered documents using Error Level Analysis (ELA)
4. **Cross-verifying** data across documents and a mock government registry
5. **Checking** regulatory compliance against AICTE rules with clause citations
6. **Scoring** applications with a trust score and compliance score
7. **Routing** applications to the appropriate review track
8. **Providing** officers with a decision dashboard

## ⚠️ Limitations (Stated Openly)

- Government APIs (DigiLocker, MCA, land records) are **simulated** with a mock JSON registry
- ELA tamper detection is a **heuristic** – it can produce false positives on heavily compressed scans
- Rule thresholds cover a **subset** of AICTE norms
- Tuned for a small sample set – not production-ready accuracy
- The blockchain registry is replaced with **SHA-256 hash verification**
- Human officers make the **final decision** – the system assists, not replaces

## 🏗 Architecture

```
[Institution Portal] → [FastAPI Backend] → [Processing Pipeline] → [SQLite DB]
       (React)              (Python)               │
                                     ┌─────────────┼─────────────┐
                                     ▼             ▼             ▼
                              Pre-validation    OCR +       Tamper Detection
                              (completeness)  Extraction     (ELA + metadata)
                                     │             │             │
                                     ▼             ▼             ▼
                              Cross-verification  Rules Engine  Scoring
                              (+ mock registry)  (+ clauses)   (+ routing)
                                                   │
                                                   ▼
                                          [Officer Dashboard]
```

## 📁 Project Structure

```
sih26261-prototype/
├── backend/
│   ├── main.py                 # FastAPI application with all endpoints
│   ├── database.py             # SQLAlchemy database setup
│   ├── models.py               # ORM models (Application, Document, Finding, etc.)
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── requirements.txt        # Python dependencies
│   ├── data/
│   │   ├── rules.json          # Regulatory compliance rules
│   │   ├── clauses.json        # AICTE clause text lookup
│   │   └── mock_registry.json  # Simulated government registry
│   ├── modules/
│   │   ├── intake.py           # Application intake & pre-validation
│   │   ├── ocr_extraction.py   # OCR, classification, field extraction
│   │   ├── tamper_detection.py # ELA heatmap, metadata check
│   │   ├── cross_verification.py # Cross-document & registry checks
│   │   ├── rules_engine.py     # Regulatory compliance engine
│   │   ├── scoring.py          # Trust/compliance scoring & routing
│   │   └── integrity.py        # SHA-256 hash verification
│   └── uploads/                # Uploaded document storage
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Main app with routing
│   │   ├── api.js              # API client
│   │   ├── pages/              # Dashboard, ApplicationForm, ApplicationDetail
│   │   └── components/         # ScoreCard, StatusBadge, Modals
│   ├── package.json
│   └── vite.config.js
├── demo_data/
│   ├── generate_samples.py     # Generate sample document images
│   ├── run_demo.py             # End-to-end demo script
│   ├── set_a/                  # Clean application documents
│   └── set_b/                  # Problem application documents
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+** and **npm** (or pnpm)
- **Tesseract OCR** (optional – the system has a fallback simulation mode)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Start the server
python main.py
# or: uvicorn main:app --reload --port 8000
```

The API is available at **http://localhost:8000**.  
Interactive API docs: **http://localhost:8000/docs**

### Frontend Setup

```bash
cd frontend

npm install
npm run dev
```

The frontend is available at **http://localhost:5173**.

### Generate Demo Data

```bash
cd demo_data

# Generate sample document images
python generate_samples.py

# Run the full end-to-end demo (backend must be running)
python run_demo.py
```

## 📊 Demo Scenarios

### Set A – Clean Application
- All names, areas, and dates are consistent
- Trust is found in the mock registry and active
- Meets all AICTE rules
- **Expected**: High trust score (~90+), fast-track routing

### Set B – Problem Application
- Land deed edited (2 acres → 5 acres) – tamper detected via ELA
- Trust name mismatch ("Bharati" vs "Bharti") across documents
- One faculty member already employed at another institution
- NOC expired
- **Expected**: Low trust score, multiple flags, senior-review routing

## 🔌 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/applications` | Create an application with form data |
| GET | `/applications` | List all applications (officer queue) |
| GET | `/applications/{id}` | Get application details |
| POST | `/applications/{id}/documents` | Upload documents |
| POST | `/applications/{id}/process` | Run the full processing pipeline |
| GET | `/applications/{id}/report` | Get scores, findings, rule results |
| GET | `/documents/{id}/heatmap` | Get tamper detection heatmap image |
| GET | `/documents/{id}/verify-hash` | SHA-256 integrity verification |
| POST | `/applications/{id}/decision` | Approve / reject / raise deficiency |
| GET | `/applications/{id}/audit-log` | Get audit trail |

## 🧪 Testing

| Test | What to Verify |
|------|---------------|
| Completeness | A missing document is caught before processing |
| OCR | Key fields extracted correctly from sample documents |
| Tamper | Set B deed is flagged; Set A documents are not |
| Cross-check | Every planted mismatch appears in findings |
| Rules | Each rule gives expected status on both sets |
| Scoring | Scores match penalty table; routing is correct |
| Integrity hash | Altering a file after upload shows "Altered" |
| End-to-end | Both sets run through without manual intervention |

## 🛣 Roadmap

- Live integrations with DigiLocker, MCA, land records, AISHE
- Trained forgery-detection model on a larger dataset
- Full RAG over the complete AICTE handbook
- Blockchain-backed document registry
- More application types (extension, closure, name change)
- Multilingual UI, notifications, guidance chatbot
- Pilot with one AICTE regional office

## 📝 Tech Stack

| Layer | Choice |
|-------|--------|
| Frontend | React + Tailwind CSS + Vite |
| Backend | FastAPI (Python) |
| OCR | Tesseract (with simulation fallback) |
| Tamper Detection | OpenCV + Pillow (Error Level Analysis) |
| Database | SQLite (via SQLAlchemy) |
| Mock Registry | JSON files |
| Integrity | SHA-256 hash |

---

*All names, institutions, and data in this prototype are entirely fictional and created for demonstration purposes only.*
