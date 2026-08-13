# 🛡️ Enterprise PII Redaction & De-Identification Engine

An enterprise-grade PII (Personally Identifiable Information) detection, anonymization, and web service application built for processing complex documents (such as **Red Herring Prospectuses**, financial reports, and customer ticket logs).

It features both a **Command-Line Engine** and a **Live FastAPI Web Application** with an ultra-sleek **Glassmorphism Drag-and-Drop Web UI**.

---

## 🎯 Executive Overview & Evaluation Criteria Summary

| Evaluation Criteria | Our Solution & Implementation |
| :--- | :--- |
| **Recall (Catching all PII)** | **95.65% Recall** (Prioritizes data leakage prevention across all 9 required PII types) |
| **Precision (Avoiding False Alarms)** | **64.71% Precision** (Controlled via static header `ALLOW_LIST` and confidence thresholding) |
| **Code Quality & Extensibility** | Modular Presidio engine architecture; adding a new entity type requires just 3 lines of code |
| **Communication & Deployment** | Live **FastAPI Web App** + **Render Cloud Deployment** configuration (`render.yaml`) |

---

## 🏗️ System Architecture & Web Workflow

The application combines a deterministic Pattern Recognizer (Regex) layer, a Named Entity Recognition (NER) NLP layer, and an asynchronous FastAPI web service.

```
[ User Browser / REST API Client ]
          │
          ▼  (File Upload via Drag & Drop or POST /api/redact)
┌────────────────────────────────────────────────────────┐
│  FastAPI Asynchronous Web Server (app.py)              │
│  ├── GET  /             -> Serves Glassmorphism Dashboard UI
│  ├── POST /api/redact   -> Runs Redaction & Stream Download
│  └── GET  /docs         -> Interactive OpenAPI/Swagger Docs
└─────────────────────────┬──────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│  Presidio Analyzer Engine                              │
│  ├── 1. Custom Regex Recognizers (PAN, Aadhaar, Phone) │
│  ├── 2. spaCy NER Engine (PERSON, ORG, LOCATION)       │
│  └── 3. Static ALLOW_LIST Filter (Preserves Headers)   │
└─────────────────────────┬──────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────┐
│  Presidio Anonymizer Engine + Faker Generator          │
└─────────────────────────┬──────────────────────────────┘
                          │
                          ▼
[ Redacted Output Document (.docx) Stream Download ]
```

---

## ✨ Key Features & Entity Support

At minimum, the pipeline detects and redacts **all 9 required PII categories** plus custom domain-specific extensions:

1. **Full Names (`PERSON`):** Contextual extraction via spaCy NLP.
2. **Email Addresses (`EMAIL_ADDRESS`):** High-precision regex pattern matching.
3. **Phone Numbers (`PHONE_NUMBER`):** Custom recognizer supporting international (`+91`) and regional landlines.
4. **Company Names (`ORGANIZATION`):** Corporate entity extraction via NLP.
5. **Physical/Mailing Addresses (`LOCATION`):** Street addresses, cities, and pin codes.
6. **Social Security & National IDs (`US_SSN` / `IN_PAN` / `IN_AADHAAR`):** 
   * **PAN Card (Indian Tax ID):** `\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b`
   * **Aadhaar Card (Indian Unique ID):** `\b[2-9]{1}[0-9]{3}\s?[0-9]{4}\s?[0-9]{4}\b`
7. **Credit Card Numbers (`CREDIT_CARD`):** 16-digit sequences with Luhn checksum validation.
8. **Dates of Birth (`DATE_TIME`):** Strict DOB regex patterns (`DD/MM/YYYY` and `YYYY-MM-DD`).
9. **IP Addresses (`IP_ADDRESS`):** IPv4 address validation.

---

## ⚖️ Trade-offs & Real-World False Positive Analysis

### 1. Security Trade-off: Recall (95.65%) vs. Precision (64.71%)
In compliance engineering, **False Negatives (missing a real SSN or phone number) result in severe legal fines and privacy breaches**. Conversely, **False Positives (over-redacting a generic word) are a minor inconvenience**. Therefore, the pipeline is intentionally configured with a score threshold (`0.40`) that favors high Sensitivity/Recall.

### 2. Observed False Positive & Solution (`ALLOW_LIST`)
* **The Issue:** The spaCy NLP model occasionally misclassified static table column headers and structural label prefixes (e.g. `"E-MAIL AND TELEPHONE"`, `"REGISTERED OFFICE"`, `"PROMOTERS"`) as corporate or person names, redacting `"E-MAIL AND TELEPHONE"` into `"Flores and Sons AND TELEPHONE"`.
* **The Solution:** We introduced a static `ALLOW_LIST` containing document headers and label prefixes. Passing `allow_list=ALLOW_LIST` directly to Presidio eliminated **26 false positive redactions** on the Red Herring Prospectus document.

---

## 📊 Empirical Evaluation Metrics

Metrics were computed programmatically using `evaluate.py` against an annotated ground-truth benchmark suite:

| Entity Type | True Positives (TP) | False Positives (FP) | False Negatives (FN) | Precision | Recall | F1-Score | Accuracy |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **PERSON** | 3 | 0 | 0 | **100.0%** | **100.0%** | **100.0%** | **100.0%** |
| **EMAIL_ADDRESS** | 4 | 0 | 0 | **100.0%** | **100.0%** | **100.0%** | **100.0%** |
| **CREDIT_CARD** | 1 | 0 | 0 | **100.0%** | **100.0%** | **100.0%** | **100.0%** |
| **IP_ADDRESS** | 2 | 0 | 0 | **100.0%** | **100.0%** | **100.0%** | **100.0%** |
| **LOCATION** | 3 | 1 | 0 | **75.0%** | **100.0%** | **85.7%** | **87.5%** |
| **US_SSN / PAN / Aadhaar**| 2 | 0 | 1 | **100.0%** | **66.7%** | **80.0%** | **80.0%** |
| **DATE_TIME** | 3 | 3 | 0 | **50.0%** | **100.0%** | **66.7%** | **66.7%** |
| **ORGANIZATION** | 2 | 5 | 0 | **28.6%** | **100.0%** | **44.4%** | **42.9%** |
| **PHONE_NUMBER** | 2 | 3 | 0 | **40.0%** | **100.0%** | **57.1%** | **50.0%** |
| **OVERALL SYSTEM** | **22** | **12** | **1** | **64.71%** | **95.65%** | **77.19%** | **70.45%** |

---

## 🚀 Local Execution & Deployment Guide

### 1. Environment Setup & Installation

#### Option A: Fast Setup with `uv` (Recommended)
If you have [Astral's `uv`](https://github.com/astral-sh/uv) installed:
```bash
# Create virtual environment & install dependencies instantly
uv venv
uv pip install -r requirements.txt
uv run python -m spacy download en_core_web_sm
```

#### Option B: Standard `pip` Setup
```bash
# Create virtual environment & install dependencies
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m spacy download en_core_web_sm
```

### 2. Local Web App Execution
To launch the live FastAPI web dashboard locally:
```bash
# Using uv
uv run python app.py

# Or using standard python
.\venv\Scripts\python.exe app.py
```
Open `http://localhost:10000` in your browser to access the Drag & Drop Web UI, or visit `http://localhost:10000/docs` for interactive Swagger API documentation.

### 3. CLI Execution
```bash
# Using uv
uv run python redact.py "Red Herring Prospectus.docx" "Redacted_Output.docx"

# Or using standard python
.\venv\Scripts\python.exe redact.py "Red Herring Prospectus.docx" "Redacted_Output.docx"
```

### 3. Deploying to Render (Free Cloud Hosting)
This repository includes a native `render.yaml` blueprint configuration for 1-click deployment on Render:

1. Push this repository to **GitHub**.
2. Log in to [Render Dashboard](https://dashboard.render.com/) and click **New → Blueprint**.
3. Connect your GitHub repository. Render will automatically detect `render.yaml`.
4. Click **Apply**. Render will automatically build the environment, download the spaCy model, and deploy your live URL (e.g. `https://pii-redactor.onrender.com`).

---

## 🧩 Extensibility: How to Add a New PII Type

The codebase is designed for modular extension. To add a new entity type (e.g. **Indian Passport Number**), simply register a new `PatternRecognizer` in `redact.py`:

```python
# 1. Define Pattern & Recognizer
passport_pattern = Pattern(name="passport_pattern", regex=r"\b[A-Z]{1}[0-9]{7}\b", score=0.95)
passport_recognizer = PatternRecognizer(supported_entity="PASSPORT", patterns=[passport_pattern])

# 2. Register with Presidio
analyzer.registry.add_recognizer(passport_recognizer)

# 3. Add Replacement Mapping in Operators
operators["PASSPORT"] = OperatorConfig("custom", {"lambda": lambda x: fake.bothify(text='?#######')})
```

---

## 📁 Deliverables Checklist

* `app.py`: FastAPI Web application server & REST API.
* `templates/index.html`: Ultra-sleek dark mode Glassmorphism Web UI dashboard.
* `redact.py`: Core redaction engine with Presidio, custom recognizers, and `ALLOW_LIST`.
* `evaluate.py`: Programmatic evaluation suite generating Precision, Recall, F1, and Accuracy.
* `evaluation_report.md`: Detailed evaluation report detailing methodology, metrics, and compliance standards.
* `render.yaml` & `Procfile`: 1-click Render cloud deployment configurations.
* `Redacted_Output_Final_Final.docx`: Clean redacted output Word document (1,893 elements sanitized).
* `requirements.txt`: Dependencies.
