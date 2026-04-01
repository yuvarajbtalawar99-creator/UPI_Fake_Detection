# KAVACH – Real Time Scam Shield for Rural India

KAVACH is an advanced fraud detection system designed to protect users against UPI payment scams, QR code fraud, and phishing URLs.

## Features
- **Enhanced Screenshot Analysis**: Multi-stage OCR preprocessing with OpenCV and 10+ weighted rule-based fraud scoring.
- **Layout Validation**: Region-based layout checks for PhonePe, Google Pay, and Paytm screenshots.
- **QR Fraud Shield**: Robust UPI URI decoding and safety validation (malformed URI, personal-as-merchant, suspicious handles).
- **Phishing Protection**: Heuristic-based URL analysis with homograph detection, brand mimicry checks, and WHOIS integration.

## Backend Architecture
- **FastAPI**: High-performance Python backend.
- **OpenCV + Pytesseract**: Image processing and text extraction.
- **Unified Scoring Engine**: Standardized risk levels (Safe, Suspicious, Blocked).

## Evaluation & Dataset Tuning
KAVACH includes a built-in evaluation pipeline to tune detection accuracy for demo usage.

### 1. Prepare Dataset
Add labeled data to the `data/` folder:
- **Screenshots**: Place genuine images in `data/screenshots/real/` and fake/edited ones in `data/screenshots/fake/`.
- **QR Codes**: Place safe QRs in `data/qr/safe/` and fraudulent ones in `data/qr/fake/`.
- **URLs**: Add one URL per line in `data/urls/safe.txt` and `data/urls/fake.txt`.

### 2. Run Evaluation
Execute the evaluation script to see accuracy metrics:
```bash
python evaluate.py
```
This prints Accuracy, Precision, Recall, and F1-score per detector.

### 3. Tuning Rules
You can adjust the weights of fraud rules and thresholds in:
- `backend/services/screenshot_service.py`
- `backend/services/qrcode_service.py`
- `backend/services/url_service.py`
- `backend/utils/scoring.py`

## Installation & Running
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the server:
   ```bash
   python -m uvicorn backend.main:app --reload
   ```
3. Access the dashboard: `http://localhost:8000/`

## API Reference
Standardized output for all analysis endpoints:
```json
{
  "risk_score": 75,
  "status": "blocked",
  "confidence": "high",
  "reasons": ["Suspicious UTR pattern", "Low OCR confidence"],
  "extracted_fields": {"upi_id": "...", "amount": "100.00"},
  "evidence_summary": "2 indicator(s) identified."
}
```
