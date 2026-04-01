# -*- coding: utf-8 -*-
"""
Enhanced OCR utility for KAVACH.
Provides advanced image preprocessing, Tesseract confidence scoring,
and robust field extraction for UPI payment screenshots.
"""

import re
import cv2
import numpy as np
from PIL import Image
import io

# Try importing OCR libraries
import os
import sys

try:
    import pytesseract
    _HAS_TESSERACT = True
    
    # Windows-specific: Try to find tesseract.exe in common locations if not in PATH
    if os.name == 'nt' and not any(os.path.exists(os.path.join(p, "tesseract.exe")) for p in os.environ.get("PATH", "").split(os.pathsep)):
        common_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Tesseract-OCR\tesseract.exe"),
            r"C:\Users\ariha\Tesseract-OCR\tesseract.exe" # User-specific potential path
        ]
        for path in common_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                break
except ImportError:
    _HAS_TESSERACT = False

try:
    import easyocr
    _HAS_EASYOCR = True
    _EASYOCR_READER = None # Delay initialization
except ImportError:
    _HAS_EASYOCR = False


def preprocess_image(img: np.ndarray) -> np.ndarray:
    """
    Apply multi-stage preprocessing to improve OCR accuracy.
    Sequence: Grayscale -> Bilateral Filter -> CLAHE -> Thresholding
    """
    if img is None:
        return None
        
    try:
        # 1. Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 2. Denoising
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        
        # 3. Contrast Enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # 4. Adaptive Thresholding
        thresh = cv2.adaptiveThreshold(
            enhanced, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        return thresh
    except Exception as e:
        print(f"Preprocessing error: {e}")
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img is not None else None


def get_ocr_data_with_confidence(img: np.ndarray) -> tuple:
    """
    Extract text and calculate confidence using Pytesseract or EasyOCR.
    Returns (full_text, average_confidence).
    """
    full_text = ""
    avg_conf = 0.0
    
    # 1. Try Pytesseract if available
    if _HAS_TESSERACT:
        try:
            # Check if tesseract_cmd is set or in path
            tess_found = False
            if os.name == 'nt' and os.path.exists(pytesseract.pytesseract.tesseract_cmd):
                tess_found = True
            else:
                import subprocess
                try:
                    subprocess.run(['tesseract', '--version'], capture_output=True, check=True)
                    tess_found = True
                except: pass
            
            if tess_found:
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                confidences = [int(c) for c in data['conf'] if int(c) != -1]
                text_parts = [data['text'][i] for i, c in enumerate(data['conf']) if int(c) != -1]
                full_text = " ".join(text_parts)
                avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
                
                if full_text.strip():
                    return full_text, avg_conf
        except Exception as e:
            print(f"Tesseract error: {e}")

    # 2. Try EasyOCR if available and Tesseract failed/missing
    if _HAS_EASYOCR:
        global _EASYOCR_READER
        try:
            if _EASYOCR_READER is None:
                print("KAVACH: Initializing EasyOCR Reader (English)...")
                _EASYOCR_READER = easyocr.Reader(['en'], gpu=False) # GPU off for compatibility
            
            # EasyOCR returns list of (bbox, text, confidence)
            results = _EASYOCR_READER.readtext(img)
            text_parts = [res[1] for res in results]
            confidences = [res[2] * 100 for res in results]
            
            full_text = " ".join(text_parts)
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
            
            return full_text, avg_conf
        except Exception as e:
            print(f"EasyOCR error: {e}")

    return full_text, avg_conf


def extract_ui_fields(text: str) -> dict:
    """
    Comprehensive regex-based field extraction from OCR text.
    """
    # Patterns
    patterns = {
        # UTR / Transaction ID (12 digits for bank ref, or alphanumeric 8-30 for others)
        'txn_id': [
            r'\b(T[0-9]{12,25})\b', # PhonePe T-prefix pattern
            r'(?:TRANSACTION|TXN|UTR|REF|REFERENCE|ID)\s*(?:ID|NO|#:)?\s*[:#\- ]*\s*([A-Z0-9]{10,30})',
            r'\b([0-9]{12})\b', # Pure 12-digit UTR
        ],
        # UPI ID (pa=merchant@bank)
        'upi_id': [
            r'\b([a-zA-Z0-9\.\-_]+@[a-zA-Z0-9\.]+)\b',
        ],
        # Amount (₹ or Rs followed by digits)
        'amount': [
            r'(?:₹|Rs\.?)\s*([\d,]+(?:\.\d{2})?)',
            r'AMOUNT\s*[:\- ]*\s*(?:₹|Rs\.?)\s*([\d,]+(?:\.\d{2})?)',
        ],
        # Merchant / Payee Name 
        'merchant_name': [
            r'(?:PAID TO|TO:?|PAYING|TRANSFER TO)\s*\n?([A-Z ]{3,30})',
            r'([A-Z][a-z]+ [A-Z][a-z]+(?: [A-Z][a-z]+)?)' # Title case names
        ],
        # Bank Reference / Ref No
        'bank_ref': [
            r'(?:BANK REF|REF|UTR)\s*[:\- ]*\s*([0-9]{10,20})',
        ],
        # Date and Time
        'date_time': [
            r'(\d{1,2}\s*[A-Z][a-z]{2,8}\s*\d{2,4})', # 12 Mar 2024
            r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',   # 12/03/2024
            r'(\d{1,2}:\d{2}(?:\s*[AP]M)?)',         # 02:30 PM
        ],
        # Payment Status
        'status': [
            r'\b(SUCCESS|COMPLETED|PAID|FAILED|PENDING|PROCESSING)\b',
        ]
    }

    results = {
        'txn_id': None,
        'upi_id': None,
        'amount': None,
        'merchant_name': None,
        'bank_ref': None,
        'date': None,
        'time': None,
        'status': None
    }

    lines = text.split('\n')
    full_text_upper = text.upper()

    # 1. Amount
    for p in patterns['amount']:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            results['amount'] = m.group(1).replace(',', '')
            break

    # 2. UPI ID
    for p in patterns['upi_id']:
        m = re.search(p, text)
        if m:
            results['upi_id'] = m.group(1).lower()
            break

    # 3. Transaction ID / UTR
    for p in patterns['txn_id']:
        m = re.search(p, full_text_upper)
        if m:
            results['txn_id'] = m.group(1)
            break

    # 4. Bank Reference
    for p in patterns['bank_ref']:
        m = re.search(p, full_text_upper)
        if m:
            results['bank_ref'] = m.group(1)
            break

    # 5. Dates and Times
    for p in patterns['date_time']:
        m = re.search(p, text)
        if m:
            val = m.group(1)
            if ':' in val:
                results['time'] = val
            else:
                results['date'] = val

    # 6. Status
    for p in patterns['status']:
        m = re.search(p, full_text_upper)
        if m:
            results['status'] = m.group(1).lower()
            break

    # 7. Merchant Name (more heuristic)
    # Often the largest text or follows "Paid to"
    for p in patterns['merchant_name']:
        m = re.search(p, text)
        if m:
            candidate = m.group(1).strip()
            if candidate.upper() not in ['SUCCESS', 'HOME', 'DETAILS', 'DONE']:
                results['merchant_name'] = candidate
                break

    return results


def analyze_image_ocr(image_bytes: bytes) -> dict:
    """
    Perform full OCR analysis: Preprocessing -> OCR -> Extraction -> Confidence.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return {"error": "Invalid image format"}

    # 1. Preprocess
    processed = preprocess_image(img)
    
    # 2. Extract Text & Confidence
    full_text, confidence = get_ocr_data_with_confidence(processed)
    
    # 3. Fallback to raw if processed is too dark/empty (rare)
    if not full_text.strip() and _HAS_TESSERACT:
        full_text, confidence = get_ocr_data_with_confidence(img)

    # 4. Extract Structured Fields
    fields = extract_ui_fields(full_text)
    
    # Add raw text for debugging (truncated)
    fields['ocr_confidence'] = confidence
    fields['raw_text_preview'] = full_text[:500]
    
    return fields


# Maintain compatibility with existing service calls if any
def extract_text_from_bytes(image_bytes: bytes) -> str:
    """Old interface compatibility."""
    res = analyze_image_ocr(image_bytes)
    return res.get('raw_text_preview', '')

def ocr_extract_fields(text: str) -> dict:
    """Old interface compatibility."""
    return extract_ui_fields(text)
