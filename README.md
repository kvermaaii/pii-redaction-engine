# PII Redaction Tool

A Python script using Microsoft Presidio and Faker to detect and redact PII from Word (.docx) documents.

## Setup
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Usage
```bash
python redact.py "Red Herring Prospectus.docx" "Redacted_Output.docx"
```
