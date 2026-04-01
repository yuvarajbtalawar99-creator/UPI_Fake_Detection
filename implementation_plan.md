# KAVACH – Real Time Scam Shield for Rural India

Extend the existing UPI Fake Detection Python project into a full-stack web application with a FastAPI backend and a mobile-first PWA frontend.

## User Review Required

> [!IMPORTANT]
> **No database is used.** All analysis is real-time, stateless — results are returned per-request.

> [!WARNING]
> **Torch/CNN inference** for screenshot detection requires `torch` and `torchvision` to be installed and a trained model file (`model/upi_fake_detector_cnn.pth`). If these are not available, the screenshot detector will fall back to OCR + rule-based analysis only. This is acceptable for demo purposes.

> [!IMPORTANT]
> **Tesseract OCR** must be installed separately on the system for `pytesseract` to work. On Windows, this means installing the Tesseract binary from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki). Without it, OCR-based screenshot analysis will be limited.

## Proposed Changes

### Project Structure

```
d:\UPI_Fake_Detection-main\
├── backend\
│   ├── main.py                  # FastAPI app entry point
│   ├── routers\
│   │   ├── screenshot.py        # /api/screenshot/analyze
│   │   ├── qrcode.py            # /api/qrcode/analyze
│   │   └── url.py               # /api/url/analyze
│   ├── services\
│   │   ├── screenshot_service.py  # Reuses OCR + rule logic from existing code
│   │   ├── qrcode_service.py      # QR decode + UPI validation
│   │   └── url_service.py         # Phishing URL analysis
│   └── utils\
│       ├── ocr.py               # Extracted OCR functions from existing code
│       └── translations.py      # Multi-language string support
├── frontend\
│   ├── index.html               # Main SPA shell
│   ├── css\
│   │   └── styles.css           # Mobile-first design system
│   ├── js\
│   │   ├── app.js               # Main app logic, routing, risk meter
│   │   ├── screenshot.js        # Screenshot module UI + camera
│   │   ├── qrcode.js            # QR module UI + camera
│   │   ├── url.js               # URL module UI
│   │   └── i18n.js              # Translation switching
│   ├── manifest.json            # PWA manifest
│   └── sw.js                    # Service worker
├── requirements.txt             # All Python dependencies
├── upi_fake_detection.py        # Original code (untouched)
└── ...existing files...
```

---

### Backend (FastAPI)

#### [NEW] [main.py](file:///d:/UPI_Fake_Detection-main/backend/main.py)
- FastAPI app with CORS enabled for local frontend
- Mounts `frontend/` as static files
- Includes routers for all 3 modules
- Serves the PWA frontend at root `/`

#### [NEW] [screenshot.py](file:///d:/UPI_Fake_Detection-main/backend/routers/screenshot.py)
- `POST /api/screenshot/analyze` — accepts image upload
- Calls `screenshot_service` which reuses the existing [ocr_extract_fields()](file:///d:/UPI_Fake_Detection-main/upi_fake_detection.py#1396-1444) and [rule_check_fields()](file:///d:/UPI_Fake_Detection-main/upi_fake_detection.py#1529-1578) logic
- Also checks for suspicious patterns: unusual transaction ID formats, suspicious UPI prefixes, missing bank references
- Returns JSON with `risk_score` (0–100), `status` (safe/suspicious/blocked), `extracted_fields`, and `reasons`

#### [NEW] [qrcode.py](file:///d:/UPI_Fake_Detection-main/backend/routers/qrcode.py)
- `POST /api/qrcode/analyze` — accepts QR image upload
- Decodes QR using `pyzbar` or OpenCV
- Validates UPI payment URI format (`upi://pay?...`)
- Checks UPI ID format, suspicious merchant names, abnormal amounts
- Returns `risk_score`, `status`, `decoded_data`, `reasons`

#### [NEW] [url.py](file:///d:/UPI_Fake_Detection-main/backend/routers/url.py)
- `POST /api/url/analyze` — accepts URL string
- Checks phishing indicators: suspicious TLDs, phishing keywords (login, verify, secure, update, account, etc.), IP-based URLs, excessive subdomains, homograph attacks
- Checks domain age via WHOIS (optional, falls back gracefully)
- Checks SSL certificate validity
- Returns `risk_score`, `status`, `analysis_details`, `reasons`

#### [NEW] [screenshot_service.py](file:///d:/UPI_Fake_Detection-main/backend/services/screenshot_service.py)
- Extracts and adapts [ocr_extract_fields()](file:///d:/UPI_Fake_Detection-main/upi_fake_detection.py#1396-1444) and [rule_check_fields()](file:///d:/UPI_Fake_Detection-main/upi_fake_detection.py#1529-1578) from the existing [upi_fake_detection.py](file:///d:/UPI_Fake_Detection-main/upi_fake_detection.py) (lines 1396–1577)
- **ML Pipeline v2**: Integrates a feature-based classifier (`screenshot_model.pkl`) that analyzes 30 image features (aspect ratio, color histograms, edge density, texture/sharpness, and structural profiles).
- Adds additional heuristics: check for known bank UPI suffixes, validate transaction ID prefixes (must start with "T26" for 2026), detect edited screenshot artifacts.
- Converts rule score + ML probability to a 0–100 risk score with dynamic status mapping.

#### [NEW] [qrcode_service.py](file:///d:/UPI_Fake_Detection-main/backend/services/qrcode_service.py)
- QR code decoding and UPI URI parsing.
- Validates UPI ID against known bank suffixes (`@okicici`, `@oksbi`, `@paytm`, etc.).
- Flags suspicious patterns: very high amounts, unknown UPI handles, malformed URIs, and non-UPI content (e.g., phishing URLs inside QR).

#### [NEW] [url_service.py](file:///d:/UPI_Fake_Detection-main/backend/services/url_service.py)
- URL parsing and phishing analysis.
- Keyword-based scoring, domain structure analysis, SSL validation, and Homograph attack detection.
- Optional WHOIS lookup for domain age (flags domains < 30 days old).

#### [NEW] [ml_feature_extractor.py](file:///d:/UPI_Fake_Detection-main/backend/utils/ml_feature_extractor.py)
- Extracts 30 numerical features from screenshots for the ML model.
- Features include: Color histograms (HSV), Laplacian variance (sharpness), Canny edge density, and vertical density profiles for layout structure.

#### [NEW] [ml_classifier.py](file:///d:/UPI_Fake_Detection-main/backend/utils/ml_classifier.py)
- Lightweight meta-classifier wrapper that refines rule-based scores.
- Ensemble approach: Combines heuristic "evidence points" with ML-predicted probabilities.

#### [NEW] [ocr.py](file:///d:/UPI_Fake_Detection-main/backend/utils/ocr.py)
- Clean extraction of OCR logic from existing codebase.
- Supports pytesseract with Windows-specific path resolution and EasyOCR fallback.

#### [NEW] [translations.py](file:///d:/UPI_Fake_Detection-main/backend/utils/translations.py)
- Dictionary-based translations for English, Hindi, Kannada, Marathi.
- Translates status labels, risk descriptions, and warning messages.

---

### Frontend (Modern Premium PWA)

#### [NEW] [index.html](file:///d:/UPI_Fake_Detection-main/frontend/index.html)
- Single-page app shell with a unified, professional dashboard.
- Features bottom navigation for mobile-first accessibility.
- Integrated circular risk meter with animated score display.
- Language selector supporting multi-lingual rural users.
- Responsive layout using Tailwind CSS and Material Symbols.

#### [NEW] [styles.css](file:///d:/UPI_Fake_Detection-main/frontend/css/styles.css)
- Custom design system with CSS Variables for consistent theming.
- **Premium Aesthetics**: Glassmorphism cards, pulse animations for high-risk alerts, and smooth transitions.
- Color palette: Deep navy/midnight backgrounds with vibrant primary accents (`#4f6cff`) and semantic status colors (Safe, Warning, Danger).

#### [NEW] [app.js](file:///d:/UPI_Fake_Detection-main/frontend/js/app.js)
- Core application state management and tab routing.
- Animated HUD (Heads-Up Display) logic for risk meter and status badges.
- Dynamic result injection with "Deep Scan Findings" and "Extracted Details" sections.

#### [NEW] [screenshot.js](file:///d:/UPI_Fake_Detection-main/frontend/js/screenshot.js)
- Real-time scanning UI with animated "laser scan" line overlay.
- Camera and file upload integration.
- Displays comprehensive analysis results including OCR confidence and ML verification.

#### [NEW] [qrcode.js](file:///d:/UPI_Fake_Detection-main/frontend/js/qrcode.js)
- QR scan interface with multi-pass decoding logic.
- Instant validation of UPI payment destinations.

#### [NEW] [url.js](file:///d:/UPI_Fake_Detection-main/frontend/js/url.js)
- Phishing scan interface for suspicious website links.
- "Deep Scan" feedback loop for user engagement.

---

### Dependencies

#### [NEW] [requirements.txt](file:///d:/UPI_Fake_Detection-main/requirements.txt)
- `fastapi`, `uvicorn[standard]`, `python-multipart`
- `opencv-python`, `pytesseract`, `pyzbar`, `Pillow`, `easyocr`
- `python-whois`, `requests`
- `scikit-learn`, `numpy`, `tensorflow` (for ML inference)

## Verification Plan

### Automated Tests
1. **Backend API smoke test** — Run verification scripts against all three endpoints.
2. **ML Pipeline Validation** — Run `evaluate_accuracy.py` to ensure the `screenshot_model.pkl` performs within expected precision/recall parameters on the test dataset.
3. **OCR Detection Test** — Verify field extraction accuracy across different bank screenshot templates (PhonePe, GPay, Paytm).

### Manual Verification
1. **UI/UX Walkthrough**: Verify that the risk meter animates correctly and the "laser scan" overlay appears during screenshot analysis.
2. **Multi-language Check**: Switch to Hindi, Kannada, or Marathi and ensure all strings (including risk reasons) are translated.
3. **Offline Mode**: Verify PWA service worker caching by loading the app in airplane mode (static assets only).
4. **Scam Scenarios**: 
   - Upload a screenshot with a transaction ID NOT starting with "T26" → should trigger a high-risk manual block.
   - Enter a typo-squatted URL like `paytem.xyz` → should show high risk.
   - Scan a QR code containing an HTTP link instead of a UPI URI → should show a suspicious warning.
