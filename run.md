# How to Run KAVACH

Follow these steps to start the KAVACH Scam Shield project on your local machine.

## Prerequisites
- **Python 3.8+** installed.
- **Tesseract OCR** (Required for screenshot analysis):
    - [Download for Windows](https://github.com/UB-Mannheim/tesseract/wiki)
    - Ensure it is added to your System PATH.

## Step-by-Step Guide

### 1. Open Terminal
Open your project folder in VS Code and open a new terminal (Ctrl + `).

### 2. Install Dependencies
Run the following command to install all necessary Python libraries:
```powershell
pip install -r requirements.txt
```

### 3. Start the Backend Server
Run this command to start the FastAPI server with auto-reload enabled:
```powershell
python -m uvicorn backend.main:app --reload
```
You should see output saying: `INFO: Application startup complete.`

### 4. Access the Dashboard
Open your web browser (Chrome or Edge) and go to:
**[http://localhost:8000](http://localhost:8000)**

---

## Features Usage

### 📸 Screenshot Detector
1. Select the **Screenshot Detector** tab.
2. Click **Camera** to scan a physical receipt or **Browse Files** to upload a screenshot.
3. Click **Analyze Receipt** for instant results.

### 🔍 QR Code Scanner
1. Select the **QR Code Scanner** tab.
2. Click **Camera** to scan a physical QR code.
3. Point your laptop camera at the QR code and click the **Capture** button.
4. Click **Verify Destination**.

### 🌐 Website Phishing Scan
1. Select the **Website Phishing Scan** tab.
2. Enter or paste a URL and click **Scan URL**.
3. If suspicious, use the **Report as Scam** button to flag it.

---

## Troubleshooting

### Camera Not Opening?
- **Permissions**: Look for a camera icon in the Chrome address bar and select **"Always allow"**.
- **Switch Camera**: If it gets stuck on a virtual camera (like moto g64), use the **Switch (Refresh)** button in the camera modal to pick your laptop's built-in webcam.

### Server Port Busy?
If you see an error saying "Port 8000 is already in use", run this to find and kill the process:
```powershell
netstat -ano | findstr :8000
# Then (replace <PID> with the number from the last column):
taskkill /F /PID <PID>
```
